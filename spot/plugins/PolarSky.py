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
from datetime import datetime
from dateutil import tz

# ginga
from ginga.gw import Widgets, GwHelp
from ginga import GingaPlugin

# qplan
from qplan.util import calcpos

# local
from spot.util.polar import subaru_normalize_az


class PolarSky(GingaPlugin.LocalPlugin):

    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super().__init__(fv, fitsimage)

        # get PloarSky preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_PolarSky')
        self.settings.add_defaults(image_radius=1850,
                                   table_timer_update_interval=60.0)
        self.settings.load(onError='silent')

        self.base_circ = None

        self.viewer = self.fitsimage
        self.dc = fv.get_draw_classes()
        canvas = self.dc.DrawingCanvas()
        canvas.set_surface(self.fitsimage)
        self.canvas = canvas

        self.orig_bg = self.viewer.get_bg()
        self.orig_fg = self.viewer.get_fg()

        self.tmr_table = GwHelp.Timer(duration=self.settings
                                      ['table_timer_update_interval'])
        self.tmr_table.add_callback('expired', self.update_table_timer_cb)

        self.tmr_sunmoon = GwHelp.Timer(duration=(60*60*12))  # 12 hours total
        self.tmr_sunmoon.add_callback('expired', self.update_sunmoon_timer_cb)

        self.gui_up = False

    def get_time_info(self):
        self.dt_utc = datetime.utcnow().replace(tzinfo=tz.UTC)
        self.dt = self.dt_utc.astimezone(self.tz)

        self.date_current = self.dt.strftime("%Y-%m-%d")
        self.local_current = self.dt.strftime("%H:%M")
        self.utc = self.dt_utc.strftime("%H:%M")

        # STILL NEED LST

    def get_sunmoon_info(self):
        # Sun rise/set info
        self.sun_set = (self.site.sunset(self.dt)).strftime("%H:%M:%S")
        self.nautical_set = (self.site.evening_twilight_12(
                             self.dt)).strftime("%H:%M:%S")
        self.astronomical_set = (self.site.evening_twilight_18(
                                 self.dt)).strftime("%H:%M:%S")
        self.sun_rise = (self.site.sunrise(self.dt)).strftime("%H:%M:%S")
        self.nautical_rise = (self.site.morning_twilight_12(
                              self.dt)).strftime("%H:%M:%S")
        self.astronomical_rise = (self.site.morning_twilight_18(
                                  self.dt)).strftime("%H:%M:%S")

        # Moon info here
        moon_data = calcpos.Moon.calc(self.site, self.dt)
        self.moon_rise = (self.site.moon_rise(self.dt)).strftime("%H:%M:%S")
        self.moon_set = (self.site.moon_set(self.dt)).strftime("%H:%M:%S")
        self.moon_illum = str("%.2f" % ((self.site.moon_phase(
                              self.dt))*100))+"%"
        self.moon_RA = moon_data.ra
        self.moon_DEC = moon_data.dec

    def build_gui(self, container):
        obj = self.channel.opmon.get_plugin('SiteSelector')
        self.site = obj.get_site().observer
        self.dt_utc, self.tz = obj.get_datetime()

        self.get_time_info()
        self.get_sunmoon_info()

        top = Widgets.VBox()
        top.set_border_width(4)

        # Date info - TODO NEEDS LST
        fr = Widgets.Frame('Date/Time Info')
        self.w.dt_table = Widgets.GridBox(rows=3, columns=2)
        self.w.dt_table.add_widget(Widgets.Label('Date:'), 0, 0)
        self.w.dt_table.add_widget(Widgets.Label('Local time:'), 1, 0)
        self.w.dt_table.add_widget(Widgets.Label('UTC'), 2, 0)
        self.w.dt_table.add_widget(Widgets.Label(self.date_current), 0, 1)
        self.w.dt_table.add_widget(Widgets.Label(self.local_current), 1, 1)
        self.w.dt_table.add_widget(Widgets.Label(self.utc), 2, 1)

        dt_hbox = Widgets.HBox()
        dt_hbox.add_widget(self.w.dt_table, stretch=0)
        dt_hbox.add_widget(Widgets.Label(''), stretch=1)
        fr.set_widget(dt_hbox)
        top.add_widget(fr, stretch=0)

        # Sun info
        fr = Widgets.Frame('Sun')
        self.w.sun_table = Widgets.GridBox(rows=4, columns=3)
        self.w.sun_table.add_widget(Widgets.Label(''), 0, 0)
        self.w.sun_table.add_widget(Widgets.Label('Site:'), 1, 0)
        self.w.sun_table.add_widget(Widgets.Label('Nautical:'), 2, 0)
        self.w.sun_table.add_widget(Widgets.Label('Astronomical:'), 3, 0)
        self.w.sun_table.add_widget(Widgets.Label('Sunset'), 0, 1)
        self.w.sun_table.add_widget(Widgets.Label(self.sun_set), 1, 1)
        self.w.sun_table.add_widget(Widgets.Label(self.nautical_set), 2, 1)
        self.w.sun_table.add_widget(Widgets.Label(self.astronomical_set), 3, 1)
        self.w.sun_table.add_widget(Widgets.Label('Sunrise'), 0, 2)
        self.w.sun_table.add_widget(Widgets.Label(self.sun_rise), 1, 2)
        self.w.sun_table.add_widget(Widgets.Label(self.nautical_rise), 2, 2)
        self.w.sun_table.add_widget(Widgets.Label(
                                    self.astronomical_rise), 3, 2)

        sun_hbox = Widgets.HBox()
        sun_hbox.add_widget(self.w.sun_table, stretch=0)
        sun_hbox.add_widget(Widgets.Label(''), stretch=1)
        fr.set_widget(sun_hbox)
        top.add_widget(fr, stretch=0)

        # Moon Info
        fr = Widgets.Frame('Moon')
        self.w.moon_table = Widgets.GridBox(rows=2, columns=6)
        self.w.moon_table.add_widget(Widgets.Label('Rise:'), 0, 0)
        self.w.moon_table.add_widget(Widgets.Label('Set:'), 1, 0)
        self.w.moon_table.add_widget(Widgets.Label('Illum:'), 2, 0)
        self.w.moon_table.add_widget(Widgets.Label('RA:'), 3, 0)
        self.w.moon_table.add_widget(Widgets.Label('DEC:'), 4, 0)
        self.w.moon_table.add_widget(Widgets.Label(self.moon_rise), 0, 1)
        self.w.moon_table.add_widget(Widgets.Label(self.moon_set), 1, 1)
        self.w.moon_table.add_widget(Widgets.Label(self.moon_illum), 2, 1)
        self.w.moon_table.add_widget(Widgets.Label(str(self.moon_RA)), 3, 1)
        self.w.moon_table.add_widget(Widgets.Label(str(self.moon_DEC)), 4, 1)

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
        self.update_table_timer_cb(self.tmr_table)
        self.update_sunmoon_timer_cb(self.tmr_sunmoon)
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
        p_canvas.delete_object(self.canvas)

    def redo(self):
        """This is called when a new image arrives or the data in the
        existing image changes.
        """
        pass

    def replot_all(self):
        self.initialize_plot()

    def update_table_timer_cb(self, timer):
        timer.start()
        self.get_time_info()

    def update_sunmoon_timer_cb(self, timer):
        timer.start()
        self.get_sunmoon_info()

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
        # az = subaru_normalize_az(az)
        return az + 90.0, 90.0 - alt

    def tel_posn_toggle_cb(self, w, tf):
        self.fv.gui_do(self.update_telescope_plot)

    def __str__(self):
        return 'polarsky'
