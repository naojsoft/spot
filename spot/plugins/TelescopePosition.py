"""
TelescopePosition.py -- Overlay telescope position on polar plot

E. Jeschke

Requirements
============

naojsoft packages
-----------------
- ginga
"""
# stdlib
import math
from datetime import timedelta

# ginga
from ginga.gw import Widgets, GwHelp
from ginga import GingaPlugin
from ginga.util import wcs


class TelescopePosition(GingaPlugin.LocalPlugin):

    def __init__(self, fv, fitsimage):
        super().__init__(fv, fitsimage)

        # get TelescopePosition preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_TelescopePosition')
        self.settings.add_defaults(rotate_view_to_az=False,
                                   tel_fov_deg=1.5,
                                   slew_distance_threshold=0.05,
                                   telescope_update_interval=3.0)
        self.settings.load(onError='silent')

        self.site = None
        # Az, Alt/El current tel position and commanded position
        self.telescope_pos = [-90.0, 89.5]
        self.telescope_cmd = [-90.0, 89.5]
        self.telescope_diff = [0.0, 0.0]

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
                                 linewidth=2, linestyle='solid', arrow='none',
                                 alpha=0.0))
        objs.append(self.dc.Path([(0, 0), (0, 0)],
                                 color='slateblue',
                                 linewidth=2, linestyle='solid', arrow='end',
                                 alpha=0.0))
        objs.append(self.dc.Circle(0.0, 0.0, r, linewidth=1, color='red',
                                   linestyle='dash', alpha=1.0))
        objs.append(self.dc.Line(0.0, 0.0, 0.0, 0.0, linewidth=1,
                                 arrow='start', color='red'))
        objs.append(self.dc.Text(0.0, 0.0, text='Target', color='red',
                                 fontscale=True, fontsize_min=12,
                                 rot_deg=-45.0))
        self.tel_obj = self.dc.CompoundObject(*objs)

        self.tmr = GwHelp.Timer(duration=self.settings['telescope_update_interval'])
        self.tmr.add_callback('expired', self.update_tel_timer_cb)

        self.gui_up = False

    def build_gui(self, container):

        # initialize site
        obj = self.channel.opmon.get_plugin('SiteSelector')
        self.site = obj.get_site()
        obj.cb.add_callback('site-changed', self.site_changed_cb)

        top = Widgets.VBox()
        top.set_border_width(4)

        fr = Widgets.Frame("Telescope")
        captions = (("RA:", 'label', 'ra', 'label',
                     "DEC:", 'label', 'dec', 'label'),
                    ("Az:", 'label', 'az', 'label',
                     "El:", 'label', 'el', 'label'),
                    ("Status:", 'label', 'action', 'label',
                     "Slew Time:", 'label', 'slew', 'label'),
                    )
        w, b = Widgets.build_info(captions)
        self.w = b
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        fr = Widgets.Frame("Target")
        captions = (("RA Cmd:", 'label', 'ra_cmd', 'label',
                     "DEC Cmd:", 'label', 'dec_cmd', 'label'),
                    ("Az Cmd:", 'label', 'az_cmd', 'label',
                     "El Cmd:", 'label', 'el_cmd', 'label'),
                    )
        w, b = Widgets.build_info(captions)
        self.w.update(b)
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        top.add_widget(Widgets.Label(''), stretch=1)

        captions = (('Plot telescope position', 'checkbutton'),
                    ('Rotate view to azimuth', 'checkbutton'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)

        top.add_widget(w, stretch=0)
        b.plot_telescope_position.add_callback('activated',
                                               self.tel_posn_toggle_cb)
        b.plot_telescope_position.set_state(True)
        b.plot_telescope_position.set_tooltip("Plot the telescope position")
        b.rotate_view_to_azimuth.set_state(False)
        b.rotate_view_to_azimuth.set_tooltip("Rotate the display to show the current azimuth at the top")
        b.rotate_view_to_azimuth.add_callback('activated',
                                              self.tel_posn_toggle_cb)

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

        self.canvas.add(self.tel_obj, tag='telescope', redraw=False)
        self.update_telescope_plot()

        self.update_tel_timer_cb(self.tmr)

        self.resume()

    def pause(self):
        self.canvas.ui_set_active(False)

    def resume(self):
        self.canvas.ui_set_active(True, viewer=self.viewer)

    def stop(self):
        self.tmr.stop()
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
        if not self.gui_up:
            return
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

        (tel_circ, tel_line, tel_text, line, bcurve, cmd_circ,
         cmd_line, cmd_text) = self.tel_obj.objects

        self.logger.debug(f'updating tel posn to alt={alt},az={az}')
        az = self.site.az_to_norm(az)
        az_cmd = self.site.az_to_norm(az_cmd)
        t, r = self.map_azalt(az, alt)
        x0, y0 = self.p2r(r, t)
        self.logger.debug(f'updating tel posn to x={x0},y={y0}')
        tel_circ.x, tel_circ.y = x0, y0
        tel_line.x1, tel_line.y1 = x0 + rd, y0 + rd
        tel_line.x2, tel_line.y2 = x0 + rd + off, y0 + rd + off
        tel_text.x, tel_text.y = x0 + rd + off, y0 + rd + off
        line.x1, line.y1 = x0, y0

        # calculate distance to commanded position
        az_dif, alt_dif = self.telescope_diff[:2]
        delta_deg = math.fabs(az_dif) + math.fabs(alt_dif)

        threshold = self.settings.get('slew_distance_threshold')
        if delta_deg < threshold:
            # line.alpha, cmd_circ.alpha = 0.0, 0.0
            line.alpha = 0.0
            bcurve.alpha = 0.0
        else:
            # line.alpha, cmd_circ.alpha = 1.0, 1.0
            line.alpha = 1.0
            bcurve.alpha = 1.0

        # this will be the point directly down the elevation
        # the line will follow this path
        t, r = self.map_azalt(az, alt_cmd)
        origin = (t, r)
        x1, y1 = self.p2r(r, t)
        line.x2, line.y2 = x1, y1

        # calculate the point at the destination
        # the curve will follow this path around the azimuth
        t, r = self.map_azalt(az_cmd, alt_cmd)
        dest = (t, r)
        x2, y2 = self.p2r(r, t)
        cmd_circ.x, cmd_circ.y = x2, y2
        cmd_line.x1, cmd_line.y1 = x2 - rd, y2 - rd
        cmd_line.x2, cmd_line.y2 = x2 - rd - off, y2 - rd - off
        cmd_text.x, cmd_text.y = x2 - rd - off, y2 - rd - off

        bcurve.points = self.get_arc_points(origin, dest)

        with self.fitsimage.suppress_redraw:
            if self.w.rotate_view_to_azimuth.get_state():
                # rotate view to telescope azimuth
                rot_deg = - az
            else:
                rot_deg = 0.0
            self.fitsimage.rotate(rot_deg)
            self.canvas.update_canvas(whence=3)

    def update_info(self, status):
        try:
            self.w.ra.set_text(wcs.ra_deg_to_str(status.ra_deg))
            self.w.dec.set_text(wcs.dec_deg_to_str(status.dec_deg))
            self.w.az.set_text("%6.2f" % status.az_deg)
            self.w.el.set_text("%5.2f" % status.alt_deg)
            self.w.action.set_text(status.tel_status)
            slew_time = str(timedelta(seconds=status.slew_time_sec)).split('.')[0]
            self.w.slew.set_text(slew_time)

            self.w.ra_cmd.set_text(wcs.ra_deg_to_str(status.ra_cmd_deg))
            self.w.dec_cmd.set_text(wcs.dec_deg_to_str(status.dec_cmd_deg))
            self.w.az_cmd.set_text("%6.2f" % status.az_cmd_deg)
            self.w.el_cmd.set_text("%5.2f" % status.alt_cmd_deg)

        except Exception as e:
            self.logger.error(f"error updating info: {e}", exc_info=True)

    def update_status(self, status):
        self.telescope_pos[0] = status.az_deg
        self.telescope_pos[1] = status.alt_deg

        self.telescope_cmd[0] = status.az_cmd_deg
        self.telescope_cmd[1] = status.alt_cmd_deg

        self.telescope_diff[0] = status.az_diff_deg
        self.telescope_diff[1] = status.alt_diff_deg

        if not self.gui_up:
            return

        self.fv.gui_do(self.update_info, status)
        self.fv.gui_do(self.update_telescope_plot)

    def update_tel_timer_cb(self, timer):
        timer.start()

        obj = self.channel.opmon.get_plugin('SiteSelector')
        status = obj.get_status()

        self.update_status(status)

    def site_changed_cb(self, cb, site_obj):
        self.logger.debug("site has changed")
        self.site = site_obj

        obj = self.channel.opmon.get_plugin('SiteSelector')
        status = obj.get_status()
        self.update_status(status)

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

    def get_arc_points(self, origin, dest):
        t, r = origin
        td, rd = dest
        direction = -1 if td < t else 1
        pts = []
        while abs(td - t) > 1:
            x, y = self.p2r(r, t)
            pts.append((x, y))
            t += direction
        t, r = dest
        x, y = self.p2r(r, t)
        pts.append((x, y))
        return pts

    def __str__(self):
        return 'telescopeposition'
