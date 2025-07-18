"""
TelescopePosition.py -- Overlay telescope position on polar plot

Requirements
============

naojsoft packages
-----------------
- ginga
"""
# stdlib
import math
from datetime import timedelta

import numpy as np

# ginga
from ginga.gw import Widgets
from ginga import GingaPlugin
from ginga.misc.Callback import Callbacks
from ginga.util import wcs
from ginga.util.syncops import Shelf

# local
from spot.util.target import Target
from spot.util.rot import normalize_angle


class TelescopePosition(GingaPlugin.LocalPlugin):
    """
    ++++++++++++++++++
    Telescope Position
    ++++++++++++++++++

    The telescope position plugin displays live telescope and commanded (target)
    positions.

    .. note:: In order to successfully use this plugin, it is necessary
              to write a custom companion plugin to provide the status
              necessary to draw these positions.  If you didn't create such
              a plugin, it will look as though the telescope is parked.

    The telescope and target positions are shown in both Right Ascension/
    Declination and Azimuth/Elevation.  RA and DEC are displayed in sexigesimal
    notation as HH:MM:SS.SSS for RA, and DD:MM:SS.SS for DEC.
    AZ and EL are both displayed in degrees as decimal values.
    In the "Telescope" section, the telescope status, such as pointing or
    slewing, is shown along with the slew time in h:mm:ss.

    The "Plot telescope position" option will show the Target and Telescope
    positions on the Targets window when the checkbox is selected.

    The "Target follow telescope" option will cause a target to be selected
    in the Targets plugin table when the telescope is "close" to that target
    (close being defined as within approximately 10 arc minutes). The closest
    actual target to the telescope's coordinate is selected.

    .. note:: If a target is manually selected by the user after checking this
              box it will automatically uncheck the option.  To restore the
              target following the telescope, simply recheck the box.

    The "Pan to telescope position" option will cause the TGTS viewer to pan
    to the telescope position.  This can be helpful when there are a lot of
    targets plotted and you have zoomed in to show only a part of the polar
    sky field.

    Writing a Companion Plugin
    ==========================

    Download the SPOT source code and look in the "spot/examples" folder
    for a plugin template called "TelescopePosition_Companion".  Modify
    as described in the template.
    """
    def __init__(self, fv, fitsimage):
        super().__init__(fv, fitsimage)

        if not self.chname.endswith('_TGTS'):
            return

        # get TelescopePosition preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_TelescopePosition')
        self.settings.add_defaults(pan_to_telescope_position=False,
                                   tel_fov_deg=1.5,
                                   color_telescope='skyblue1',
                                   color_slew='thistle1',
                                   color_target='tan1',
                                   min_delta_arcsec=600.0,
                                   slew_distance_threshold=0.05,
                                   telescope_update_interval=3.0)
        self.settings.load(onError='silent')

        self.cb = Callbacks()
        for name in ['telescope-status-changed']:
            self.cb.enable_callback(name)

        self.site = None
        self._last_tel_update_dt = None
        # Az, Alt/El current tel position and commanded position
        self.telescope_pos = [-90.0, 89.5]
        self.telescope_cmd = [-90.0, 89.5]
        self.telescope_diff = [0.0, 0.0]

        # minimum distance from tracking to be considered the "same target"
        # (in arcsec)
        self.min_delta_arcsec = self.settings.get('min_delta_arcsec', 600.0)
        self._follow_target = False
        self.target_shelf = Shelf()
        self.target_stocker = self.target_shelf.get_stocker()
        self._last_tel_update_dt = None
        self._cur_tel_target = None

        self.viewer = self.fitsimage
        self.dc = fv.get_draw_classes()
        canvas = self.dc.DrawingCanvas()
        canvas.set_surface(self.fitsimage)
        self.canvas = canvas

        # create telescope object
        objs = []
        color_tel = self.settings.get('color_telescope', 'skyblue1')
        scale = self.get_scale()
        r = self.settings.get('tel_fov_deg') * 0.5 * scale
        objs.append(self.dc.Circle(0.0, 0.0, r, linewidth=3, color=color_tel))
        off = 4 * scale
        objs.append(self.dc.Line(r, r, r + off, r + off, linewidth=3,
                                 arrow='start', color=color_tel))
        objs.append(self.dc.Text(r + off, r + off, text='Telescope',
                                 color=color_tel,
                                 bgcolor='black', bgalpha=0.7,
                                 fontscale=True, fontsize_min=12,
                                 rot_deg=-45.0))
        color_slew = self.settings.get('color_slew', 'thistle1')
        objs.append(self.dc.Line(0.0, 0.0, 0.0, 0.0, color=color_slew,
                                 linewidth=2, linestyle='solid', arrow='none',
                                 alpha=0.0))
        objs.append(self.dc.Path([(0, 0), (0, 0)],
                                 color=color_slew,
                                 linewidth=2, linestyle='solid', arrow='end',
                                 alpha=0.0))
        color_tgt = self.settings.get('color_target', 'tan1')
        objs.append(self.dc.Circle(0.0, 0.0, r, linewidth=3, color=color_tgt,
                                   linestyle='dash', alpha=1.0))
        objs.append(self.dc.Line(0.0, 0.0, 0.0, 0.0, linewidth=3,
                                 arrow='start', color=color_tgt))
        objs.append(self.dc.Text(0.0, 0.0, text='Target',
                                 color=color_tgt,
                                 bgcolor='black', bgalpha=0.7,
                                 fontscale=True, fontsize_min=12,
                                 rot_deg=-45.0))
        self.tel_obj = self.dc.CompoundObject(*objs)

        self.gui_up = False

    def build_gui(self, container):

        if not self.chname.endswith('_TGTS'):
            raise Exception(f"This plugin is not designed to run in channel {self.chname}")

        # initialize site
        obj = self.channel.opmon.get_plugin('SiteSelector')
        self.site = obj.get_site()
        obj.cb.add_callback('site-changed', self.site_changed_cb)
        obj.cb.add_callback('time-changed', self.time_changed_cb)
        self.targets = self.channel.opmon.get_plugin('Targets')
        self.targets.cb.add_callback('selection-changed',
                                     self.target_selection_cb)

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

        captions = (("Plot telescope position", 'checkbox',
                     "Target follows telescope", 'checkbox'),
                    ('sp1', 'spacer',
                     "Pan to telescope position", 'checkbox'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)

        top.add_widget(w, stretch=0)
        b.plot_telescope_position.add_callback('activated',
                                               self.tel_posn_toggle_cb)
        b.plot_telescope_position.set_state(True)
        b.plot_telescope_position.set_tooltip("Plot the telescope position")

        b.target_follows_telescope.set_state(self._follow_target)
        b.target_follows_telescope.add_callback('activated',
                                                self.follow_target_cb)
        b.target_follows_telescope.set_tooltip("Track target by telescope position")
        b.pan_to_telescope_position.set_state(self.settings.get('pan_to_telescope_position',
                                                                False))
        b.pan_to_telescope_position.set_tooltip("Pan to the position of the target")
        b.pan_to_telescope_position.add_callback('activated',
                                                 self.pan_to_tel_pos_cb)

        btns = Widgets.HBox()
        btns.set_border_width(4)
        btns.set_spacing(3)

        btn = Widgets.Button("Close")
        btn.add_callback('activated', lambda w: self.close())
        btns.add_widget(btn, stretch=0)
        btn = Widgets.Button("Help")
        btn.add_callback('activated', lambda w: self.help())
        btns.add_widget(btn, stretch=0)
        btns.add_widget(Widgets.Label(''), stretch=1)

        top.add_widget(btns, stretch=0)

        container.add_widget(top, stretch=1)
        self.gui_up = True

    def close(self):
        self.fv.stop_local_plugin(self.chname, str(self))
        return True

    def help(self):
        name = str(self).capitalize()
        self.fv.help_text(name, self.__doc__, trim_pfx=4)

    def start(self):
        # insert canvas, if not already
        p_canvas = self.fitsimage.get_canvas()
        if self.canvas not in p_canvas:
            # Add our canvas
            p_canvas.add(self.canvas)
        # NOTE: Targets plugin canvas needs to be the active one
        self.canvas.ui_set_active(False)

        self.canvas.delete_all_objects()

        self.canvas.add(self.tel_obj, tag='telescope', redraw=False)

        status = self.site.get_status()
        self.fv.gui_do(self.update_status, status)

    def stop(self):
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

        direction = int(np.sign(az_dif))
        if np.isclose(direction, 0.0):
            direction = 1
        bcurve.points = self.get_arc_points(origin, dest, direction)

        with self.fitsimage.suppress_redraw:
            if self.settings.get('pan_to_telescope_position', False):
                self.fitsimage.set_pan(x2, y2, coord='data')

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

    def find_target_by_telpos(self, status, select=False):
        tel_pos = Target(name="telescope", ra=status.ra_deg,
                         dec=status.dec_deg, equinox=status.equinox)
        self.logger.debug(f"tel position {status.ra_deg, status.dec_deg}")

        # Now find this target in our "regular" target list, if possible
        tgt = self.targets.get_target_by_separation(tel_pos,
                                                    min_delta_sep_arcsec=self.min_delta_arcsec)
        if not select:
            return tgt

        targets = []
        if tgt is not None:
            # select target in Targets table
            targets = [tgt]
        with self.target_stocker:
            self.targets.select_targets(targets)

        return tgt

    def follow_target_cb(self, w, tf):
        self._follow_target = tf

        if self._follow_target:
            status = self.site.get_status()
            self.find_target_by_telpos(status, select=True)

    def update_status(self, status):
        self.telescope_pos[0] = status.az_deg
        self.telescope_pos[1] = status.alt_deg

        self.telescope_cmd[0] = status.az_cmd_deg
        self.telescope_cmd[1] = status.alt_cmd_deg

        self.telescope_diff[0] = status.az_diff_deg
        self.telescope_diff[1] = status.alt_diff_deg

        if not self.gui_up:
            return

        self.update_info(status)
        self.update_telescope_plot()

        tgt = self.find_target_by_telpos(status, select=self._follow_target)
        self.cb.make_callback('telescope-status-changed', status, tgt)

    def time_changed_cb(self, cb, time_utc, cur_tz):
        if (self._last_tel_update_dt is None or
            abs((time_utc - self._last_tel_update_dt).total_seconds()) >
            self.settings.get('telescope_update_interval')):
            self.logger.debug("updating telescope position on plot")
            self._last_tel_update_dt = time_utc
            status = self.site.get_status()
            self.fv.gui_do(self.update_status, status)

    def site_changed_cb(self, cb, site_obj):
        self.logger.info("site has changed")
        self.site = site_obj

        status = self.site.get_status()
        self.fv.gui_do(self.update_status, status)

    def target_selection_cb(self, cb, targets):
        """Called when the user selects targets in the Target table"""
        if not self.target_shelf.is_blocked():
            if self.gui_up:
                self.w.target_follows_telescope.set_state(False)
            self._follow_target = False

    def tel_posn_toggle_cb(self, w, tf):
        self.fv.gui_do(self.update_telescope_plot)

    def pan_to_tel_pos_cb(self, w, tf):
        self.settings.set(pan_to_telescope_position=tf)
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

    def get_arc_points(self, origin, dest, direction):
        t, r = origin
        t = normalize_angle(int(t), limit='full')
        td, rd = dest
        td = normalize_angle(int(td), limit='full')
        pts = []
        while abs(td - t) > 1:
            x, y = self.p2r(r, t)
            pts.append((x, y))
            t = t + direction
            if t < 0:
                t = t + 360.0
            elif t >= 360.0:
                t = t - 360.0
        x, y = self.p2r(rd, td)
        pts.append((x, y))
        return pts

    def __str__(self):
        return 'telescopeposition'
