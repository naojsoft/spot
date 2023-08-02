"""
PolarSky.py -- Overlay objects on polar sky plot

E. Jeschke

Requirements
============

naojsoft packages
-----------------
- ginga
"""
# 3rd party
import numpy as np

# ginga
from ginga.gw import Widgets
from ginga import GingaPlugin
#from ginga.AstroImage import AstroImage
from ginga.misc import Bunch

# qplan
from qplan.util import calcpos


class PolarSky(GingaPlugin.LocalPlugin):

    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super().__init__(fv, fitsimage)

        # get PolarSky preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_PolarSky')
        self.settings.add_defaults(image_radius=1850,
                                   times_update_interval=1.0)
        self.settings.load(onError='silent')

        self.base_circ = None

        self.viewer = self.fitsimage
        self.dc = fv.get_draw_classes()
        canvas = self.dc.DrawingCanvas()
        canvas.set_surface(self.fitsimage)
        self.canvas = canvas

        self.orig_bg = self.viewer.get_bg()
        self.orig_fg = self.viewer.get_fg()

        # these are set in callbacks
        self.site_obj = None
        self.dt_utc = None
        self.cur_tz = None

        self.gui_up = False

    def get_time_info(self):
        dt = self.dt_utc.astimezone(self.cur_tz)
        info = Bunch.Bunch()

        # TODO: still need LST
        tzname = self.cur_tz.tzname(dt)
        info.update(dict(date_current = dt.strftime("%Y-%m-%d"),
                         local_current = dt.strftime("%H:%M:%S") + f" [{tzname}]",
                         utc = self.dt_utc.strftime("%H:%M:%S")))
        return info

    def get_sunmoon_info(self):
        dt = self.dt_utc.astimezone(self.cur_tz)
        site = self.site_obj.observer
        info = Bunch.Bunch()

        info.update(dict(
            # Sun rise/set info
            sun_set = (site.sunset(dt)).strftime("%H:%M:%S"),
            nautical_set = (site.evening_twilight_12(
                dt)).strftime("%H:%M:%S"),
            astronomical_set = (site.evening_twilight_18(
                dt)).strftime("%H:%M:%S"),
            sun_rise = (site.sunrise(dt)).strftime("%H:%M:%S"),
            nautical_rise = (site.morning_twilight_12(
                dt)).strftime("%H:%M:%S"),
            astronomical_rise = (site.morning_twilight_18(
                dt)).strftime("%H:%M:%S")))

        moon_data = calcpos.Moon.calc(site, dt)
        info.update(dict(
            # Moon info here
            moon_rise = (site.moon_rise(dt)).strftime("%H:%M:%S"),
            moon_set = (site.moon_set(dt)).strftime("%H:%M:%S"),
            moon_illum = str("%.2f%%" % ((site.moon_phase(
                dt)) * 100)),
            moon_ra = str(moon_data.ra),
            moon_dec = str(moon_data.dec)))

        return info

    def build_gui(self, container):
        obj = self.channel.opmon.get_plugin('SiteSelector')
        self.site_obj = obj.get_site()
        self.dt_utc, self.cur_tz = obj.get_datetime()
        obj.cb.add_callback('site-changed', self.site_changed_cb)
        obj.cb.add_callback('time-changed', self.time_changed_cb)

        top = Widgets.VBox()
        top.set_border_width(4)

        # Date info - TODO: add LST
        info = self.get_time_info()
        fr = Widgets.Frame('Site Date/Time')
        self.w.dt_table = Widgets.GridBox(rows=3, columns=2)
        self.w.dt_table.add_widget(Widgets.Label('Date:'), 0, 0)
        self.w.dt_table.add_widget(Widgets.Label('Time:'), 1, 0)
        self.w.dt_table.add_widget(Widgets.Label('UTC:'), 2, 0)
        self.w.date_current = Widgets.Label(info.date_current)
        self.w.dt_table.add_widget(self.w.date_current, 0, 1)
        self.w.local_current = Widgets.Label(info.local_current)
        self.w.dt_table.add_widget(self.w.local_current, 1, 1)
        self.w.utc = Widgets.Label(info.utc)
        self.w.dt_table.add_widget(self.w.utc, 2, 1)

        dt_hbox = Widgets.HBox()
        dt_hbox.add_widget(self.w.dt_table, stretch=0)
        dt_hbox.add_widget(Widgets.Label(''), stretch=1)
        fr.set_widget(dt_hbox)
        top.add_widget(fr, stretch=0)

        info = self.get_sunmoon_info()

        # Sun info
        fr = Widgets.Frame('Sun')
        sun_table = Widgets.GridBox(rows=4, columns=3)
        self.w.sun_table = sun_table
        sun_table.add_widget(Widgets.Label(''), 0, 0)
        sun_table.add_widget(Widgets.Label('Site:'), 1, 0)
        sun_table.add_widget(Widgets.Label('Nautical:'), 2, 0)
        sun_table.add_widget(Widgets.Label('Astronomical:'), 3, 0)
        sun_table.add_widget(Widgets.Label('Sunset'), 0, 1)
        self.w.sun_set = Widgets.Label(info.sun_set)
        sun_table.add_widget(self.w.sun_set, 1, 1)
        self.w.nautical_set = Widgets.Label(info.nautical_set)
        sun_table.add_widget(self.w.nautical_set, 2, 1)
        self.w.astronomical_set = Widgets.Label(info.astronomical_set)
        sun_table.add_widget(self.w.astronomical_set, 3, 1)
        sun_table.add_widget(Widgets.Label('Sunrise'), 0, 2)
        self.w.sun_rise = Widgets.Label(info.sun_rise)
        sun_table.add_widget(self.w.sun_rise, 1, 2)
        self.w.nautical_rise = Widgets.Label(info.nautical_rise)
        sun_table.add_widget(self.w.nautical_rise, 2, 2)
        self.w.astronomical_rise = Widgets.Label(info.astronomical_rise)
        sun_table.add_widget(self.w.astronomical_rise, 3, 2)

        sun_hbox = Widgets.HBox()
        sun_hbox.add_widget(self.w.sun_table, stretch=0)
        sun_hbox.add_widget(Widgets.Label(''), stretch=1)
        fr.set_widget(sun_hbox)
        top.add_widget(fr, stretch=0)

        # Moon Info
        fr = Widgets.Frame('Moon')
        moon_table = Widgets.GridBox(rows=2, columns=6)
        self.w.moon_table = moon_table
        moon_table.add_widget(Widgets.Label('Rise:'), 0, 0)
        moon_table.add_widget(Widgets.Label('Set:'), 1, 0)
        moon_table.add_widget(Widgets.Label('Illum:'), 2, 0)
        moon_table.add_widget(Widgets.Label('RA:'), 3, 0)
        moon_table.add_widget(Widgets.Label('DEC:'), 4, 0)
        self.w.moon_rise = Widgets.Label(info.moon_rise)
        moon_table.add_widget(self.w.moon_rise, 0, 1)
        self.w.moon_set = Widgets.Label(info.moon_set)
        moon_table.add_widget(self.w.moon_set, 1, 1)
        self.w.moon_illum = Widgets.Label(info.moon_illum)
        moon_table.add_widget(self.w.moon_illum, 2, 1)
        self.w.moon_ra = Widgets.Label(info.moon_ra)
        moon_table.add_widget(self.w.moon_ra, 3, 1)
        self.w.moon_dec = Widgets.Label(info.moon_dec)
        moon_table.add_widget(self.w.moon_dec, 4, 1)

        moon_hbox = Widgets.HBox()
        moon_hbox.add_widget(self.w.moon_table, stretch=0)
        moon_hbox.add_widget(Widgets.Label(''), stretch=1)
        fr.set_widget(moon_hbox)
        top.add_widget(fr, stretch=0)

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
        # self.viewer.set_bg(0.95, 0.95, 0.95)
        # self.viewer.set_fg(0.25, 0.25, 0.75)

        # surreptitiously share setting of image_radius with SkyCam plugin
        # so that when they update setting we redraw our plot
        skycam = self.channel.opmon.get_plugin('SkyCam')
        skycam.settings.share_settings(self.settings,
                                       keylist=['image_radius'])
        self.settings.get_setting('image_radius').add_callback(
                                  'set', self.change_radius_cb)

        # insert canvas, if not already
        p_canvas = self.fitsimage.get_canvas()
        if self.canvas not in p_canvas:
            # Add our canvas
            p_canvas.add(self.canvas)

        self.canvas.delete_all_objects()

        self.initialize_plot()

        self.resume()

    def pause(self):
        self.canvas.ui_set_active(False)

    def resume(self):
        self.canvas.ui_set_active(True, viewer=self.viewer)

    def stop(self):
        self.viewer.set_bg(*self.orig_bg)
        self.viewer.set_fg(*self.orig_fg)

        self.gui_up = False
        # remove the canvas from the image
        p_canvas = self.fitsimage.get_canvas()
        if self.canvas in p_canvas:
            p_canvas.delete_object(self.canvas)

    def redo(self):
        """This is called when a new image arrives or the data in the
        existing image changes.
        """
        pass

    def site_changed_cb(self, cb, site_obj):
        self.logger.debug("site has changed")
        self.site_obj = site_obj
        obj = self.channel.opmon.get_plugin('SiteSelector')
        self.dt_utc, self.cur_tz = obj.get_datetime()
        self.update_times()
        self.update_sunmoon()

    def time_changed_cb(self, cb, time_utc, cur_tz):
        old_dt_utc = self.dt_utc
        self.dt_utc = time_utc
        self.cur_tz = cur_tz

        elapsed = abs((self.dt_utc - old_dt_utc).total_seconds())
        if elapsed > self.settings['times_update_interval']:
            self.update_times()

        if elapsed > 60 * 60 * 12:  # every 12 hours
            self.update_sunmoon()

    def replot_all(self):
        self.initialize_plot()

    def update_times(self):
        info = self.get_time_info()
        if self.gui_up:
            self.w.date_current.set_text(info.date_current)
            self.w.local_current.set_text(info.local_current)
            self.w.utc.set_text(info.utc)

    def update_sunmoon(self):
        info = self.get_sunmoon_info()
        if self.gui_up:
            self.w.sun_set.set_text(info.sun_set)
            self.w.nautical_set.set_text(info.nautical_set)
            self.w.astronomical_set.set_text(info.astronomical_set)
            self.w.sun_rise.set_text(info.sun_rise)
            self.w.nautical_rise.set_text(info.nautical_rise)
            self.w.astronomical_rise.set_text(info.astronomical_rise)

            self.w.moon_rise.set_text(info.moon_rise)
            self.w.moon_set.set_text(info.moon_set)
            self.w.moon_illum.set_text(info.moon_illum)
            self.w.moon_ra.set_text(info.moon_ra)
            self.w.moon_dec.set_text(info.moon_dec)

    def change_radius_cb(self, setting, radius):
        self.replot_all()

    def initialize_plot(self):
        self.canvas.delete_object_by_tag('elev')

        objs = []

        # plot circles
        els = [85, 70, 50, 30, 15]
        # els.insert(0, 89)
        # plot circles
        circ_color = 'darkgreen'
        # circ_fill = 'palegreen1'
        circ_fill = '#fdf6f6'
        image = self.viewer.get_image()
        # fillalpha = 0.5 if image is None else 0.0
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
        # TODO: re-enable after being able to change between different
        # azimuth-orientations (N = 0 or S = 0)
        # for r, t in [(92, 0), (92, 45), (92, 90), (98, 135),
        #              (100, 180), (100, 225), (95, 270), (92, 315)]:
        #     ang = (t + 90) % 360
        #     x, y = self.p2r(r, t)
        #     objs.append(self.dc.Text(x, y, "{}\u00b0".format(ang),
        #                              fontscale=True, fontsize_min=12,
        #                              color='brown'))

        # plot compass directions
        for r, t, txt in [(110, 0, 'W'), (100, 90, 'N'),
                          (110, 180, 'E'), (100, 270, 'S')]:
            x, y = self.p2r(r, t)
            objs.append(self.dc.Text(x, y, txt, color='brown', fontscale=True,
                                     fontsize_min=16))

        o = self.dc.CompoundObject(*objs)
        self.canvas.add(o, tag='elev')

        # cx, cy = self.settings['image_center']
        r = self.settings['image_radius'] * 1.25

        # data_np = np.zeros((int(r)*2, int(r)*2), dtype=float)
        # img = AstroImage(data_np=data_np, logger=self.logger)
        # img.info_xy = self._info_xy
        # cvs_img = self.dc.NormImage(-r, -r, img)
        # objs.append(cvs_img)

        with self.viewer.suppress_redraw:
            self.viewer.set_limits(((-r, -r), (r, r)))
            self.viewer.zoom_fit()
            self.viewer.set_pan(0.0, 0.0)

    def p2r(self, r, t):
        # TODO: take into account fisheye distortion
        t_rad = np.radians(t)

        # cx, cy = self.settings['image_center']
        cx, cy = 0.0, 0.0
        scale = self.get_scale()

        x = cx + r * np.cos(t_rad) * scale
        y = cy + r * np.sin(t_rad) * scale

        return (x, y)

    def r2xyr(self, r):
        # TODO: take into account fisheye distortion
        # cx, cy = self.settings['image_center']
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
        return az + 90.0, 90.0 - alt

    def r2p(self, x, y):
        r = np.sqrt(x ** 2 + y ** 2)
        t = np.arctan(y / x)
        return (r, t)

    # def _info_xy(self, data_x, data_y, settings):
    #     info = super().info_xy(data_x, data_y, settings)

    #     r, t = self.r2p(data_x, data_y)
    #     az = t - 90.0
    #     alt = 90.0 - r
    #     ra_lbl, dec_lbl = "Az", "El"
    #     ra_txt, dec_txt = "%+.3f" % (az), "%+.3f" % (alt)
    #     info.update(dict(itype='astro', ra_txt=ra_txt, dec_txt=dec_txt,
    #                      ra_lbl=ra_lbl, dec_lbl=dec_lbl))
    #     return info

    def tel_posn_toggle_cb(self, w, tf):
        self.fv.gui_do(self.update_telescope_plot)

    def __str__(self):
        return 'polarsky'
