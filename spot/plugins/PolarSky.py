"""
PolarSky.py -- Overlay objects on all sky camera

E. Jeschke

Requirements
============

naojsoft packages
-----------------
- g2cam
- ginga
- qplan
"""
# stdlib
import threading
import math

# 3rd party
import numpy as np

# ginga
from ginga.gw import Widgets, GwHelp
from ginga import GingaPlugin

# g2cam
from g2cam.status.client import StatusClient


class PolarSky(GingaPlugin.LocalPlugin):

    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super().__init__(fv, fitsimage)

        # get SkyCam preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_PolarSky')
        self.settings.add_defaults(rotate_view_to_az=False,
                                   image_radius=1850,
                                   tel_fov_deg=1.5,
                                   slew_distance_threshold=0.05,
                                   tel_update_interval=10.0,
                                   status_client_host=None)
        self.settings.load(onError='silent')

        # Az, Alt/El current tel position and commanded position
        self.telescope_pos = [-90.0, 60.0]
        self.telescope_cmd = [-90.0, 60.0]
        self.telescope_diff = [0.0, 0.0]
        self.ev_quit = threading.Event()
        self.base_circ = None
        self.status_dict = { 'STATS.AZ_DEG': None, 'STATS.EL_DEG': None,
                             'STATS.AZ_ADJ': None,
                             'STATS.AZ_DIF': None, 'STATS.EL_DIF': None,
                             'STATS.SLEWING_STATUS': None,
                             'STATS.SLEWING_TIME': None,
                             'STATS.AZ_CMD': None, 'STATS.EL_CMD': None,
                             }

        self.viewer = self.fitsimage
        self.dc = fv.get_draw_classes()
        canvas = self.dc.DrawingCanvas()
        canvas.set_surface(self.fitsimage)
        self.canvas = canvas

        # create telescope object
        objs = []
        color = 'sienna'
        scale = self.get_scale()
        r = self.settings.get('tel_fov_deg') * 0.5 * scale
        objs.append(self.dc.Circle(0.0, 0.0, r, linewidth=1, color=color))
        off = 4 * scale
        objs.append(self.dc.Line(r, r, r+off, r+off, linewidth=1,
                                 arrow='start', color=color))
        objs.append(self.dc.Text(r+off, r+off, text='Telescope', color=color,
                                 fontscale=True, fontsize_min=12,
                                 rot_deg=-45.0))
        objs.append(self.dc.Line(0.0, 0.0, 0.0, 0.0, color='slateblue',
                                 linewidth=2, linestyle='dash', arrow='end',
                                 alpha=0.0))
        objs.append(self.dc.Circle(0.0, 0.0, r, linewidth=1, color='red',
                                   linestyle='dash', alpha=0.0))
        objs.append(self.dc.Line(0.0, 0.0, 0.0, 0.0, linewidth=1,
                                 arrow='start', color='red'))
        objs.append(self.dc.Text(0.0, 0.0, text='Target', color='red',
                                 fontscale=True, fontsize_min=12,
                                 rot_deg=-45.0))
        self.tel_obj = self.dc.CompoundObject(*objs)

        self.orig_bg = self.viewer.get_bg()
        self.orig_fg = self.viewer.get_fg()

        self.tmr2 = GwHelp.Timer(duration=self.settings['tel_update_interval'])
        self.tmr2.add_callback('expired', self.update_tel_timer_cb)

        self.gui_up = False

    def build_gui(self, container):

        top = Widgets.VBox()
        top.set_border_width(4)

        captions = (('Plot telescope position', 'checkbutton'),
                    ('Rotate view to azimuth', 'checkbutton'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b

        top.add_widget(w, stretch=0)
        b.plot_telescope_position.add_callback('activated',
                                               self.tel_posn_toggle_cb)
        b.plot_telescope_position.set_state(True)
        b.plot_telescope_position.set_tooltip("Plot the telescope position")
        b.rotate_view_to_azimuth.set_state(False)
        b.rotate_view_to_azimuth.set_tooltip("Rotate the display to show the current azimuth at the top")
        b.rotate_view_to_azimuth.add_callback('activated',
                                              self.tel_posn_toggle_cb)

        top.add_widget(Widgets.Label(''), stretch=1)

        btns = Widgets.HBox()
        btns.set_border_width(4)
        btns.set_spacing(3)

        btn = Widgets.Button("Close")
        btn.add_callback('activated', lambda w: self.close())
        btns.add_widget(btn, stretch=0)
        btn = Widgets.Button("Help")
        #btn.add_callback('activated', lambda w: self.help())
        btns.add_widget(btn, stretch=0)
        btns.add_widget(Widgets.Label(''), stretch=1)

        top.add_widget(btns, stretch=0)

        container.add_widget(top, stretch=1)
        self.gui_up = True

    def close(self):
        self.fv.stop_local_plugin(self.chname, str(self))
        return True

    def start(self):
        self.viewer.set_bg(0.95, 0.95, 0.95)
        self.viewer.set_fg(0.25, 0.25, 0.75)

        # insert canvas, if not already
        p_canvas = self.fitsimage.get_canvas()
        if self.canvas not in p_canvas:
            # Add our canvas
            p_canvas.add(self.canvas)

        self.canvas.delete_all_objects()
        self.ev_quit.clear()

        self.canvas.add(self.tel_obj, tag='telescope', redraw=False)
        self.initialize_plot()

        self.update_tel_timer_cb(self.tmr2)

        # set up the status stream interface
        status_host = self.settings.get('status_client_host', None)
        self.st_client = None
        if status_host is None:
            self.w.plot_telescope_position.set_enabled(False)
            self.w.rotate_view_to_azimuth.set_enabled(False)
        else:
            self.st_client = StatusClient(host=self.settings['status_client_host'],
                                          username=self.settings['status_client_user'],
                                          password=self.settings['status_client_pass'])
            self.st_client.connect()

            # start the status update loop
            self.fv.nongui_do(self.status_update_loop, self.ev_quit)

        self.resume()

    def pause(self):
        self.canvas.ui_set_active(False)

    def resume(self):
        self.canvas.ui_set_active(True, viewer=self.viewer)

    def stop(self):
        self.viewer.set_bg(*self.orig_bg)
        self.viewer.set_fg(*self.orig_fg)

        self.ev_quit.set()
        self.gui_up = False
        # remove the canvas from the image
        p_canvas = self.fitsimage.get_canvas()
        p_canvas.delete_object(self.canvas)

    def redo(self):
        """This is called when a new image arrives or the data in the
        existing image changes.
        """
        pass

    def replot_all(self):
        self.initialize_plot()

    def initialize_plot(self):
        self.canvas.delete_object_by_tag('elev')

        objs = []

        # plot circles
        els = [85, 70, 50, 30, 15]
        #els.insert(0, 89)
        # plot circles
        circ_color = 'darkgreen'
        #circ_fill = 'palegreen1'
        circ_fill = '#fdf6f6'
        image = self.viewer.get_image()
        #fillalpha = 0.5 if image is None else 0.0
        fillalpha = 0.0
        alpha = 1.0
        x, y, r = self.r2xyr(90)
        self.base_circ = self.dc.Circle(x, y, r, color=circ_color, linewidth=2,
                                        fill=True, fillcolor=circ_fill,
                                        fillalpha=fillalpha, alpha=1.0)
        objs.append(self.base_circ)

        x, y, r = self.r2xyr(1)
        objs.append(self.dc.Circle(x, y, r, color=circ_color, linewidth=1))
        t = -75
        for el in els:
            r = (90 - el)
            r2 = r + 1
            x, y, _r = self.r2xyr(r)
            objs.append(self.dc.Circle(x, y, _r, color=circ_color))
            x, y = self.p2r(r, t)
            objs.append(self.dc.Text(x, y, "{}".format(el), color='brown',
                                     fontscale=True, fontsize_min=12))

        # plot lines
        for r1, t1, r2, t2 in [(90, 90, 90, -90), (90, 45, 90, -135),
                               (90, 0, 90, -180), (90, -45, 90, 135)]:
            x1, y1 = self.p2r(r1, t1)
            x2, y2 = self.p2r(r2, t2)
            objs.append(self.dc.Line(x1, y1, x2, y2, color=circ_color))

        # plot degrees
        for r, t in [(92, 0), (92, 45), (92, 90), (98, 135),
                     (100, 180), (100, 225), (95, 270), (92, 315)]:
            ang = (t + 90) % 360
            x, y = self.p2r(r, t)
            objs.append(self.dc.Text(x, y, "{}\u00b0".format(ang),
                                     fontscale=True, fontsize_min=12,
                                     color='brown'))

        # plot compass directions
        for r, t, txt in [(110, 0, 'W'), (100, 90, 'N'),
                          (110, 180, 'E'), (100, 270, 'S')]:
            x, y = self.p2r(r, t)
            objs.append(self.dc.Text(x, y, txt, color='brown', fontscale=True,
                                fontsize_min=16))

        o = self.dc.CompoundObject(*objs)
        self.canvas.add(o, tag='elev')

        #cx, cy = self.settings['image_center']
        r = self.settings['image_radius'] * 1.25
        with self.viewer.suppress_redraw:
            self.viewer.set_limits(((-r, -r), (r, r)))
            self.viewer.zoom_fit()
            self.viewer.set_pan(0.0, 0.0)

    def update_telescope_plot(self):
        if not self.w.plot_telescope_position.get_state():
            try:
                self.canvas.delete_object_by_tag('telescope')
            except KeyError:
                pass
            return

        if self.tel_obj not in self.canvas:
            self.canvas.add(self.tel_obj, tag='telescope', redraw=False)

        az, alt = self.telescope_pos
        az_cmd, alt_cmd = self.telescope_cmd
        scale = self.get_scale()
        rd = self.settings.get('tel_fov_deg') * 0.5 * scale
        off = 4 * scale

        (tel_circ, tel_line, tel_text, line, cmd_circ,
         cmd_line, cmd_text) = self.tel_obj.objects

        self.logger.debug(f'updating tel posn to alt={alt},az={az}')
        az = subaru_normalize_az(az)
        az_cmd = subaru_normalize_az(az_cmd)
        t, r = self.map_azalt(az, alt)
        x, y = self.p2r(r, t)
        self.logger.debug(f'updating tel posn to x={x},y={y}')
        tel_circ.x, tel_circ.y = x, y
        tel_line.x1, tel_line.y1 = x + rd, y + rd
        tel_line.x2, tel_line.y2 = x + rd + off, y + rd + off
        tel_text.x, tel_text.y = x + rd + off, y + rd + off

        # calculate distance to commanded position
        az_dif, alt_dif = self.telescope_diff[:2]
        delta_deg = math.fabs(az_dif) + math.fabs(alt_dif)

        threshold = self.settings.get('slew_distance_threshold')
        if delta_deg < threshold:
            #line.alpha, cmd_circ.alpha = 0.0, 0.0
            line.alpha = 0.0
        else:
            #line.alpha, cmd_circ.alpha = 1.0, 1.0
            line.alpha = 1.0
            line.x1, line.y1 = x, y

        t, r = self.map_azalt(az_cmd, alt_cmd)
        x, y = self.p2r(r, t)
        cmd_circ.x, cmd_circ.y = x, y
        line.x2, line.y2 = x, y
        cmd_line.x1, cmd_line.y1 = x - rd, y - rd
        cmd_line.x2, cmd_line.y2 = x - rd - off, y - rd - off
        cmd_text.x, cmd_text.y = x - rd - off, y - rd - off

        with self.fitsimage.suppress_redraw:
            if self.w.rotate_view_to_azimuth.get_state():
                # rotate view to telescope azimuth
                rot_deg = - az
            else:
                rot_deg = 0.0
            self.fitsimage.rotate(rot_deg)
            self.canvas.update_canvas(whence=3)

    def update_tel_timer_cb(self, timer, *args):
        if not self.gui_up:
            return
        timer.start()
        self.update_telescope_plot()

    def status_update_loop(self, ev_quit):
        while not ev_quit.is_set():
            try:
                self.st_client.fetch(self.status_dict)
                #print('status:', self.status_dict)

                if self.status_dict['STATS.AZ_DEG'] is not None:
                    self.telescope_pos[0] = float(self.status_dict['STATS.AZ_DEG'])
                if self.status_dict['STATS.EL_DEG'] is not None:
                    self.telescope_pos[1] = float(self.status_dict['STATS.EL_DEG'])

                if self.status_dict['STATS.AZ_CMD'] is not None:
                    self.telescope_cmd[0] = float(self.status_dict['STATS.AZ_CMD'])
                if self.status_dict['STATS.EL_CMD'] is not None:
                    self.telescope_cmd[1] = float(self.status_dict['STATS.EL_CMD'])

                if self.status_dict['STATS.AZ_DIF'] is not None:
                    self.telescope_diff[0] = float(self.status_dict['STATS.AZ_DIF'])
                if self.status_dict['STATS.EL_DIF'] is not None:
                    self.telescope_diff[1] = float(self.status_dict['STATS.EL_DIF'])

            except Exception as e:
                self.logger.error("Exception fetching status items: {}".format(e),
                                  exc_info=True)

            ev_quit.wait(self.settings.get('tel_update_interval', 60.0))

    def p2r(self, r, t):
        # TODO: take into account fisheye distortion
        t_rad = np.radians(t)

        #cx, cy = self.settings['image_center']
        cx, cy = 0.0, 0.0
        scale = self.get_scale()

        x = cx + r * np.cos(t_rad) * scale
        y = cy + r * np.sin(t_rad) * scale

        return (x, y)

    def r2xyr(self, r):
        # TODO: take into account fisheye distortion
        #cx, cy = self.settings['image_center']
        cx, cy = 0.0, 0.0
        r = r * self.get_scale()
        return (cx, cy, r)

    def get_scale(self):
        """Return scale in pix/deg"""
        # assuming image is a fisheye 180 deg view, radius should be
        # half the diameter or 90 deg worth of pixels
        radius_px = self.settings['image_radius']
        scale = radius_px / 90.0
        return scale

    def map_azalt(self, az, alt):
        #az = subaru_normalize_az(az)
        return az + 90.0, 90.0 - alt

    def tel_posn_toggle_cb(self, w, tf):
        self.fv.gui_do(self.update_telescope_plot)

    def __str__(self):
        return 'polarsky'


def subaru_normalize_az(az_deg):
    az_deg = az_deg + 180.0
    #az_deg = az_deg % 360.0
    if math.fabs(az_deg) >= 360.0:
        az_deg = math.fmod(az_deg, 360.0)
    if az_deg < 0.0:
        az_deg += 360.0

    return az_deg
