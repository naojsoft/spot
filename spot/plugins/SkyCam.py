"""
SkyCam.py -- Overlay objects on all sky camera

E. Jeschke

Requirements
============
python packages
---------------
- requests

naojsoft packages
-----------------
- ginga
"""
# stdlib
import os
import time
import threading

# 3rd party
import numpy as np
import requests

# ginga
from ginga import trcalc
from ginga.gw import Widgets
from ginga.AstroImage import AstroImage
from ginga.RGBImage import RGBImage
from ginga import GingaPlugin


class SkyCam(GingaPlugin.LocalPlugin):

    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super().__init__(fv, fitsimage)

        # get SkyCam preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_SkyCam')
        self.settings.add_defaults(image_center=(2660, 1850),
                                   image_radius=1850,
                                   image_rotation=-158.0,
                                   #image_rotation=-20.0,
                                   image_transform=(False, False, False),
                                   image_update_interval=60.0)
        self.settings.load(onError='silent')

        self.ev_quit = threading.Event()
        self.sky_image_path = None
        self.flag_use_sky_image = False

        self.viewer = self.fitsimage
        self.dc = fv.get_draw_classes()
        canvas = self.dc.DrawingCanvas()
        canvas.set_surface(self.fitsimage)
        self.canvas = canvas

        xc, yc = self.settings['image_center']
        r = self.settings['image_radius']
        self.crop_circ = self.dc.Circle(xc, yc, r)
        self.crop_circ.crdmap = self.viewer.get_coordmap('data')

        # set up some settings in our channel
        self.fitsimage.settings.set(autozoom='off', autocenter='off',
                                    auto_orient=False)
        self.fitsimage.transform(False, False, False)

        self.gui_up = False

    def build_gui(self, container):

        top = Widgets.VBox()
        top.set_border_width(4)

        captions = (('Use sky image bg', 'checkbutton'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b

        top.add_widget(w, stretch=0)
        b.use_sky_image_bg.add_callback('activated', self.sky_image_toggle_cb)
        b.use_sky_image_bg.set_tooltip("Place the all sky image on the background")
        #b.use_sky_image_bg.set_state(True)

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
        # insert canvas, if not already
        p_canvas = self.fitsimage.get_canvas()
        if self.canvas not in p_canvas:
            # Add our canvas layer
            p_canvas.add(self.canvas)

        self.canvas.delete_all_objects()
        self.ev_quit.clear()

        #self.canvas.add(self.cvs_img, tag='skyimage', redraw=False)
        self.initialize_plot()

        # start the image update loop
        self.fv.nongui_do(self.image_update_loop, self.ev_quit)

        self.resume()

    def pause(self):
        self.canvas.ui_set_active(False)

    def resume(self):
        self.canvas.ui_set_active(True, viewer=self.viewer)

    def stop(self):
        self.ev_quit.set()
        self.gui_up = False
        # restore normal
        cvs_img = self.fitsimage.get_canvas_image()
        cvs_img.x = 0
        cvs_img.y = 0
        # remove the canvas from the image
        p_canvas = self.fitsimage.get_canvas()
        p_canvas.delete_object(self.canvas)

    def redo(self):
        """This is called when a new image arrives or the data in the
        existing image changes.
        """
        pass

    def initialize_plot(self):
        #cx, cy = self.settings['image_center']
        r = self.settings['image_radius'] * 1.25
        with self.viewer.suppress_redraw:
            self.viewer.set_limits(((-r, -r), (r, r)))
            self.viewer.zoom_fit()
            self.viewer.set_pan(0.0, 0.0)

    def update_image(self, imgpath):
        # TODO: just keep updating a single image?

        cx, cy = self.settings['image_center']
        #r = self.settings['image_radius']
        flip_x, flip_y, swap_xy = self.settings['image_transform']
        rot_deg = self.settings['image_rotation']

        if imgpath.endswith('.fits'):
            img = AstroImage(logger=self.logger)
        else:
            img = RGBImage(logger=self.logger)
        img.load_file(imgpath)

        # rotate and transform image as necessary to align with plot
        # orientation
        data_np = img.get_data()
        data_np = trcalc.transform(data_np, flip_x=flip_x,
                                   flip_y=flip_y, swap_xy=swap_xy)
        if not np.isclose(rot_deg, 0.0):
            data_np = trcalc.rotate_clip(data_np, rot_deg,
                                         rotctr_x=cx, rotctr_y=cy)

        # cut out the center part and mask everything outside the circle
        view, mask = img.get_shape_view(self.crop_circ)
        data_np = img._slice(view)
        data_np[np.logical_not(mask)] = 0

        if isinstance(img, RGBImage):
            data_np = np.flipud(data_np)

        img.set_data(data_np)

        self.fv.gui_do(self.__update_display, img)

    def __update_display(self, img):
        with self.viewer.suppress_redraw:
            self.viewer.set_image(img)
            cvs_img = self.viewer.get_canvas_image()
            #cx, cy = self.settings['image_center']
            wd, ht = img.get_size()
            rx, ry = wd * 0.5, ht * 0.5
            cvs_img.x = -rx
            cvs_img.y = -ry
            # r = self.settings['image_radius'] * 1.25
            # self.viewer.set_limits(((-r, -r), (r, r)))
            self.viewer.set_limits(((-rx * 1.25, -ry * 1.25), (rx * 1.25, ry * 1.25)))
            self.viewer.redraw(whence=0)

    def download_sky_image(self):
        try:
            start_time = time.time()
            url = self.settings['image_url']
            _, ext = os.path.splitext(url)
            self.logger.info("downloading '{}'...".format(url))
            interval = self.settings.get('image_update_interval')
            r = requests.get(url, timeout=(60, interval))
            outpath = os.path.join(self.settings['download_folder'],
                                   'allsky' + ext)
            with open(outpath, 'wb') as out_f:
                out_f.write(r.content)
            self.logger.info("download finished in %.4f sec" % (
                time.time() - start_time))
            self.sky_image_path = outpath

            self.fv.gui_do(self.update_sky_image)

        except Exception as e:
            self.logger.error("failed to download/update sky image: {}".format(e),
                              exc_info=True)

    def update_sky_image(self):
        if self.w.use_sky_image_bg.get_state():
            if self.sky_image_path is not None:
                self.update_image(self.sky_image_path)
        else:
            self.fitsimage.clear()

    def image_update_loop(self, ev_quit):
        interval = self.settings['image_update_interval']

        while not ev_quit.is_set():
            time_deadline = time.time() + interval
            if self.flag_use_sky_image:
                self.download_sky_image()

            ev_quit.wait(max(0, time_deadline - time.time()))

    def get_scale(self):
        """Return scale in pix/deg"""
        obj = self.channel.opmon.get_plugin('SkyCam')
        return obj.get_scale()

    def sky_image_toggle_cb(self, w, tf):
        self.flag_use_sky_image = tf
        self.update_sky_image()
        if self.flag_use_sky_image and self.sky_image_path is None:
            # if user now wants a background image and we don't have one
            # initiate a download; otherwise timed loop will pull one in
            # eventually
            self.fv.nongui_do(self.download_sky_image)

    def __str__(self):
        return 'skycam'
