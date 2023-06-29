"""
TelescopePosition.py -- Overlay telescope position on polar plot

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

# ginga
from ginga.gw import Widgets
from ginga import GingaPlugin

# g2cam
from g2cam.status.client import StatusClient

# local
from spot.util.polar import subaru_normalize_az


class TelescopePosition(GingaPlugin.LocalPlugin):

    def __init__(self, fv, fitsimage):
        super().__init__(fv, fitsimage)

        # get TelescopePosition preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_TelescopePosition')
        self.settings.add_defaults(rotate_view_to_az=False,
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
        self.status_dict = {'STATS.AZ_DEG': None, 'STATS.EL_DEG': None,
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
        # btn.add_callback('activated', lambda w: self.help())
        btns.add_widget(btn, stretch=0)
        btns.add_widget(Widgets.Label(''), stretch=1)

        top.add_widget(btns, stretch=0)

        container.add_widget(top, stretch=1)
        self.gui_up = True

    def close(self):
        self.fv.stop_local_plugin(self.chname, str(self))
        return True

    def start(self):
        # insert canvas, if not already
        p_canvas = self.fitsimage.get_canvas()
        if self.canvas not in p_canvas:
            # Add our canvas
            p_canvas.add(self.canvas)

        self.canvas.delete_all_objects()
        self.ev_quit.clear()

        self.canvas.add(self.tel_obj, tag='telescope', redraw=False)

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
            # line.alpha, cmd_circ.alpha = 0.0, 0.0
            line.alpha = 0.0
        else:
            # line.alpha, cmd_circ.alpha = 1.0, 1.0
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

    def status_update_loop(self, ev_quit):
        while not ev_quit.is_set():
            try:
                self.st_client.fetch(self.status_dict)
                self.logger.debug("status is: %s" % str(self.status_dict))

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

            if not self.gui_up:
                return
            self.fv.gui_do(self.update_telescope_plot)

            ev_quit.wait(self.settings.get('tel_update_interval', 60.0))

    def tel_posn_toggle_cb(self, w, tf):
        self.fv.gui_do(self.update_telescope_plot)

    def p2r(self, r, t):
        obj = self.channel.opmon.get_plugin('PolarSky')
        return obj.p2r(r, t)

    def get_scale(self):
        obj = self.channel.opmon.get_plugin('PolarSky')
        return obj.get_scale()

    def map_azalt(self, az, alt):
        obj = self.channel.opmon.get_plugin('PolarSky')
        return obj.map_azalt(az, alt)

    def __str__(self):
        return 'telescopeposition'
