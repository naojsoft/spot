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

# local
from spot.util.polar import subaru_normalize_az


class PolarSky(GingaPlugin.LocalPlugin):

    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super().__init__(fv, fitsimage)

        # get SkyCam preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_PolarSky')
        self.settings.add_defaults(image_radius=1850)
        self.settings.load(onError='silent')

        self.base_circ = None

        self.viewer = self.fitsimage
        self.dc = fv.get_draw_classes()
        canvas = self.dc.DrawingCanvas()
        canvas.set_surface(self.fitsimage)
        self.canvas = canvas

        self.orig_bg = self.viewer.get_bg()
        self.orig_fg = self.viewer.get_fg()

        self.gui_up = False

    def build_gui(self, container):

        top = Widgets.VBox()
        top.set_border_width(4)

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

        # surreptitiously share setting of image_radius with SkyCam plugin
        # so that when they update setting we redraw our plot
        skycam = self.channel.opmon.get_plugin('SkyCam')
        skycam.settings.share_settings(self.settings,
                                       keylist=['image_radius'])
        self.settings.get_setting('image_radius').add_callback('set', self.change_radius_cb)

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

    def change_radius_cb(self, setting, radius):
        self.replot_all()

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
