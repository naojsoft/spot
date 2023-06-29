"""
SkyCam.py -- Overlay objects on all sky camera

E. Jeschke
J. Merchant

``SkyCam`` displays current images of sky conditions at inputted telescopes,
and plots a differential image to portray changing sky conditions.

**Plugin Type: Local**

``SkyCam`` is a local plugin, which means it is associated with a channel.
An instance can be opened for each channel.

**Usage**

The SkyCam plugin uses sky camera images from different observatories based off
of inputted camera settings. These settings are found in the cameras.yml file
in the users .ginga directory.

A differential image can be substituted for the main graphic, which shows
differences amongst transmitted images from the telescopes' sources.

Often used in tandem with rendered sky camera images is the PolarSky plugin,
which plots a graphical model over each image showing the azimuth, current
telescope position, and N,S,E,W directional pointers.

**UI Controls**

One button at the bottom of the UI, termed "Operation," is used to select
specific plugins for use. Selecting Planning, then SkyCam will bring the user
to the corresponding plugin for eventual use.

A window on the right side of the UI should appear, headered by "IMAGE: SkyCam"
Within said tab are the controls used to manipulate the SkyCam plugin.

The first section, titled "All Sky Camera," has two different controls:

    * select "Use Sky Image Background" to portray image from selected source
    * select "Preset Camera Server" dropdown to display available image sources

Selecting a different image source inputs different images, which are often
different sizes. To set an image to the size of the current screen locate
the button portraying a magnifying glass with "[:]" within it. This is found
in the bottom row of plugins of the UI.

The second section, titled "Differential Image," has one control:

    * select "Show Differential Image" to portray a differential image

The differential image for a specific image source is created using the current
and previous images retrieved from said image source. It subtracts the current
image from the previous, resulting in the changes between images left behind.
These changes are what is portrayed.

If the source was recently selected from the "Preset Camera Server" and a
second image from the source has not been displayed yet, a message on screen
will appear telling the user that it is waiting to recieve a second image to
put into the differential image equation.

Lastly, the images are updated in a timer specific to the cameras.yml file and
not matched to the image sources from the many observatories. This could
possibly allow for some discrepancies between image refresh timing, resulting
in the image becoming completely black. The user will have to wait until the
next image from the source is transmitted and read by the SkyCam plugin, which
will then show the differential image.

**User Configuration**

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
import yaml
import tempfile

# ginga
from ginga import trcalc
from ginga.gw import Widgets
from ginga.AstroImage import AstroImage
from ginga.RGBImage import RGBImage
from ginga import GingaPlugin
from ginga.util.paths import ginga_home


class SkyCam(GingaPlugin.LocalPlugin):

    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super().__init__(fv, fitsimage)

        self.viewer = self.fitsimage
        self.dc = fv.get_draw_classes()
        self.std = np.array([0.2126, 0.7152, 0.0722])
        self.old_data = None
        self.cur_data = None
        self.img_src_name = 'Subaru Telescope (Visible)'

        loaddir = ginga_home
        path = os.path.join(loaddir, "cameras.yml")
        if os.path.exists(path):
            with open(path, 'r') as cam_f:
                self.configs = yaml.safe_load(cam_f)
        else:
            # Sets Subaru Telescope (Visible) as default
            # if cameras.yml does not load
            self.config = {
                'url': "https://allsky.subaru.nao.ac.jp/allsky/api/v0/images/download_most_recent.png",
                'file': "allsky.png",
                'lfile': "allsky-%ld.png",
                'title': "Subaru Telescope (Visible)",
                'ctr_x': 2660,
                'ctr_y': 1850,
                'radius': 1850,
                'rot_deg': 9.5,
                'flip_y': False,
                'update_interval': 120.0}
            self.configs = {self.img_src_name: self.config}
        # Sets config dictionary equal to Subaru Telescope dictionary from
        # within configs nested dictionary to start program as default
        self.config = self.configs[self.img_src_name]

        # get SkyCam preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_SkyCam')
        self.settings.add_defaults(download_folder=tempfile.gettempdir())
        self.update_settings()

        self.settings.load(onError='silent')

        self.ev_quit = threading.Event()
        self.sky_image_path = None
        self.flag_use_sky_image = False
        self.flag_use_diff_image = False

        canvas = self.dc.DrawingCanvas()
        canvas.set_surface(self.fitsimage)
        self.canvas = canvas

        self.gui_up = False

    # Updates settings to current image source
    def update_settings(self):
        self.settings.set(image_url=self.config.get('url'),
                          image_center=(self.config.get('ctr_x'),
                                        self.config.get('ctr_y')),
                          image_radius=self.config.get('radius'),
                          image_rotation=self.config.get('rot_deg'),
                          image_transform=(self.config.get('flip_x'),
                                           self.config.get('flip_y'),
                                           False),
                          image_update_interval=self.config.get(
                                                'update_interval'))

        xc, yc = self.settings['image_center']
        r = self.settings['image_radius']
        self.crop_circ = self.dc.Circle(xc, yc, r)
        self.crop_circ.crdmap = self.viewer.get_coordmap('data')

    def build_gui(self, container):

        top = Widgets.VBox()
        top.set_border_width(4)
        fr = Widgets.Frame("All Sky Camera")

        captions = (('Use Sky Image Background', 'checkbutton'),
                    ('Preset Camera Server:', 'llabel',
                     'Select Image Source', 'combobox'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        b.use_sky_image_background.add_callback(
            'activated', self.sky_image_toggle_cb)
        b.use_sky_image_background.set_tooltip(
            "Place the all sky image on the background")

        for name in self.configs.keys():
            b.select_image_source.append_text(name)
        b.select_image_source.add_callback('activated',
                                           self.select_image_source_cb)

        fr = Widgets.Frame("Differential Image")
        captions = (('Show Differential Image', 'checkbutton'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        b.show_differential_image.add_callback('activated',
                                               self.diff_image_toggle_cb)
        b.show_differential_image.set_tooltip("Use a differential image")

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
        # set up some settings in our channel
        self.fitsimage.settings.set(autozoom='off', autocenter='off',
                                    auto_orient=False)
        self.fitsimage.transform(False, False, False)

        # insert canvas, if not already
        p_canvas = self.fitsimage.get_canvas()
        if self.canvas not in p_canvas:
            # Add our canvas layer
            p_canvas.add(self.canvas)

        self.canvas.delete_all_objects()
        self.ev_quit.clear()

        # self.canvas.add(self.cvs_img, tag='skyimage', redraw=False)
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
        # cx, cy = self.settings['image_center']
        r = self.settings['image_radius'] * 1.25
        with self.viewer.suppress_redraw:
            self.viewer.set_limits(((-r, -r), (r, r)))
            self.viewer.zoom_fit()
            self.viewer.set_pan(0.0, 0.0)

    def update_image(self, imgpath):
        # TODO: just keep updating a single image?

        flip_x, flip_y, swap_xy = self.settings['image_transform']
        rot_deg = self.settings['image_rotation']

        if imgpath.endswith('.fits'):
            img = AstroImage(logger=self.logger)
        else:
            img = RGBImage(logger=self.logger)
        img.load_file(imgpath)
        self.logger.info(imgpath)

        # cut out the center part and mask everything outside the circle
        xc, yc = self.settings['image_center']
        r = self.settings['image_radius']
        self.crop_circ.x = xc
        self.crop_circ.y = yc
        self.crop_circ.radius = r
        view, mask = img.get_shape_view(self.crop_circ)
        data_np = img._slice(view)

        # rotate image as necessary
        if not np.isclose(rot_deg, 0.0):
            ht, wd = data_np.shape[:2]
            ctr_x, ctr_y = wd // 2, ht // 2
            data_np = trcalc.rotate_clip(data_np, rot_deg,
                                         rotctr_x=ctr_x, rotctr_y=ctr_y)
        # transform image as necessary
        data_np = trcalc.transform(data_np, flip_x=flip_x,
                                   flip_y=flip_y, swap_xy=swap_xy)

        if isinstance(img, RGBImage):
            # flip RGB images
            data_np = np.flipud(data_np)

            if len(data_np.shape) == 3 and data_np.shape[2] > 2:
                # if this is a color RGB image, convert to monochrome
                # via the standard channel mixing technique
                data_np = (data_np[:, :, 0] * self.std[0] +
                           data_np[:, :, 1] * self.std[1] +
                           data_np[:, :, 2] * self.std[2])

        ht, wd = data_np.shape[:2]
        data_np = data_np.reshape((ht, wd))
        img = AstroImage(data_np=data_np, logger=self.logger)

        self.old_data = self.cur_data
        self.cur_data = data_np
        self.refresh_image()

    def refresh_image(self):
        data_np = self.cur_data
        if data_np is None:
            return
        ht, wd = data_np.shape[:2]

        if not self.flag_use_diff_image or self.old_data is not None:
            self.fitsimage.onscreen_message_off()

        if self.flag_use_diff_image:
            if self.old_data is not None:
                data_np = data_np - self.old_data

        img = AstroImage(data_np=data_np, logger=self.logger)
        # ht, wd = data_np.shape[:2]
        ctr_x, ctr_y = wd // 2, ht // 2
        self.crop_circ.x = ctr_x
        self.crop_circ.y = ctr_y
        self.crop_circ.radius = ctr_x
        mask = img.get_shape_mask(self.crop_circ)

        mn, mx = trcalc.get_minmax_dtype(data_np.dtype)
        data_np = data_np.clip(0, mx)
        order = trcalc.guess_order(data_np.shape)
        if 'A' not in order:
            # add an alpha layer to mask out unimportant pixels
            alpha = np.full(data_np.shape[:2], mx, dtype=data_np.dtype)
            data_np = trcalc.add_alpha(data_np, alpha=alpha)
        data_np[:, :, -1] = mask * mx

        img.set_data(data_np)
        img.set(name=self.img_src_name, nothumb=True, path=None)

        self.fv.gui_do(self.__update_display, img)

    def __update_display(self, img):
        with self.viewer.suppress_redraw:
            self.viewer.set_image(img)
            cvs_img = self.viewer.get_canvas_image()
            # cx, cy = self.settings['image_center']
            wd, ht = img.get_size()
            rx, ry = wd * 0.5, ht * 0.5
            cvs_img.x = -rx
            cvs_img.y = -ry
            # r = self.settings['image_radius'] * 1.25
            # self.viewer.set_limits(((-r, -r), (r, r)))
            self.viewer.set_limits(((-rx * 1.25, -ry * 1.25),
                                    (rx * 1.25, ry * 1.25)))
            self.viewer.redraw(whence=0)

    def download_sky_image(self):
        try:
            start_time = time.time()
            url = self.settings['image_url']
            _, ext = os.path.splitext(url)
            self.logger.info("downloading '{}'...".format(url))
            interval = self.settings.get('image_update_interval')
            r = requests.get(url, timeout=(120, interval))
            outpath = os.path.join(self.settings['download_folder'],
                                   'allsky' + ext)
            with open(outpath, 'wb') as out_f:
                out_f.write(r.content)
            self.logger.info("download finished in %.4f sec" % (
                time.time() - start_time))
            self.sky_image_path = outpath

            self.fv.gui_do(self.update_sky_image)

        except Exception as e:
            self.logger.error("failed to download/update sky image: {}"
                              .format(e), exc_info=True)

    def update_sky_image(self):
        if self.flag_use_sky_image:
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

    def diff_image_toggle_cb(self, w, tf):
        self.flag_use_diff_image = tf
        message = "Waiting for the next image to create a differential sky..."
        if self.flag_use_diff_image and self.old_data is None:
            self.fitsimage.onscreen_message(message)
        self.refresh_image()

    def select_image_source_cb(self, w, idx):
        which = w.get_text()
        self.img_src_name = which
        config = self.configs[which]
        self.config = {
            'url': config['url'],
            'file': config['file'],
            'lfile': config['lfile'],
            'title': config['title'],
            'ctr_x': config['ctr_x'],
            'ctr_y': config['ctr_y'],
            'radius': config['radius'],
            'rot_deg': config['rot_deg'],
            'flip_y': config['flip_y'],
            'flip_x': config['flip_x'],
            'update_interval': config['update_interval']
        }
        self.update_settings()
        self.cur_data = None
        self.old_data = None
        try:
            self.download_sky_image()

        except Exception as e:
            self.logger.error(f"Error loading image: {e}", exc_info=True)

    def __str__(self):
        return 'skycam'
