"""
SkyCam.py -- Overlay objects on all sky camera

J. Merchant

``SkyCam`` displays current images of sky conditions at inputted telescopes,
and plots a differential image to portray changing sky conditions.

**Plugin Type: Local**

``SkyCam`` is a local plugin, which means it is associated with a channel.
An instance can be opened for each channel.

**Usage**

The SkyCam plugin uses sky camera images from different observatories based off
of inputted camera settings. These settings are found in the skycams.yml file
in the users $HOME/.spot directory.

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

    * select "Show Sky Image" to portray image from selected source
    * select "Camera Server" dropdown to display available image sources

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

If the source was recently selected from the "Camera Server" and a
second image from the source has not been displayed yet, a message on screen
will appear telling the user that it is waiting to recieve a second image to
put into the differential image equation.

Lastly, the images are updated in a timer specific to the skycams.yml file and
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
import datetime

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

# where our config files are stored
from spot import __file__
cfgdir = os.path.join(os.path.dirname(__file__), 'config')


class SkyCam(GingaPlugin.LocalPlugin):
    """
    ++++++++
    Sky Cams
    ++++++++

    The SkyCam plugin is used to place an all sky camera image on the background
    of the Targets channel to assist with monitoring sky conditions. There is a
    drop-down menu with several sites to choose from.

    Setting the Sky Image
    =====================

    Select the camera server you would like to use from the drop down menu
    under "All Sky Camera". Then, press the checkbox next to "Show Sky Image"
    to display the image in the `<wsname>_TGTS` window. It may take a few
    moments before the sky image appears.  When the image updates,
    the time and date of the last image will be displayed at the bottom of the
    window underneath "Image Download Info".

    The SkyCam plugin can also generate a differential image from the selected
    channel server by selecting the checkbox next to "Show Differential Image".

    Adding new cameras
    ==================

    You can easily add your own all-sky camera images if you have a suitable
    feed of images that can be fetched via web protocols.
    If you have the SPOT source code checked out, you can find the file
    "skycams.yml" in .../spot/spot/config/.  Copy this file to $HOME/.spot
    and edit it to add your own camera.  You will need to provide a URL
    for downloading images, a title, a center pixel (X and Y coords) in the
    image representing the zenith, the radius of the circle to the horizon
    in pixels, a rotation to be applied, whether to flip the image in X or
    Y dimensions, and an update interval measured in seconds.

    Restart spot and you should be able to pick your new camera from the list.
    """
    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super().__init__(fv, fitsimage)

        if not self.chname.endswith('_TGTS'):
            return

        # get SkyCam preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_SkyCam')
        self.settings.add_defaults(download_folder=tempfile.gettempdir(),
                                   image_update_interval=60.0,
                                   default_camera=None,
                                   image_radius=1000)
        self.settings.load(onError='silent')

        self.viewer = self.fitsimage
        self.dc = fv.get_draw_classes()
        self.std = np.array([0.2126, 0.7152, 0.0722])
        self.old_data = None
        self.cur_data = None
        self.img_src_name = self.settings.get('default_camera', None)

        self.read_skycams_config()

        self.sky_image_path = None
        self._last_img_update_dt = None
        self.flag_use_sky_image = False
        self.flag_use_diff_image = False

        canvas = self.dc.DrawingCanvas()
        canvas.set_surface(self.viewer)
        self.canvas = canvas

        self.gui_up = False

    # Updates settings to current image source
    def update_settings(self):
        self.settings.set(image_url=self.config.get('url'),
                          image_center=(self.config.get('ctr_x'),
                                        self.config.get('ctr_y')),
                          image_radius=self.config.get('radius'),
                          image_rotation=self.config.get('rot_deg', 0.0),
                          image_transform=(self.config.get('flip_x', False),
                                           self.config.get('flip_y', False),
                                           False),
                          image_update_interval=self.config.get(
                              'update_interval', 120.0))

        xc, yc = self.settings['image_center']
        r = self.settings['image_radius']
        self.crop_circ = self.dc.Circle(xc, yc, r)
        self.crop_circ.crdmap = self.viewer.get_coordmap('data')

    def read_skycams_config(self):
        # see if user has a custom list of sky cams
        path = os.path.join(ginga_home, "skycams.yml")
        if not os.path.exists(path):
            # open stock list of skycams
            path = os.path.join(cfgdir, "skycams.yml")

        with open(path, 'rt', encoding='utf-8') as cam_f:
            self.configs = yaml.safe_load(cam_f)

        if self.img_src_name is None:
            self.img_src_name = list(self.configs.keys())[0]
        self.config = self.configs[self.img_src_name]
        self.update_settings()

    def build_gui(self, container):

        if not self.chname.endswith('_TGTS'):
            raise Exception(f"This plugin is not designed to run in channel {self.chname}")

        # re-read skycams config, in case user is tweaking settings
        self.read_skycams_config()

        # initialize site and date/time/tz
        obj = self.channel.opmon.get_plugin('SiteSelector')
        obj.cb.add_callback('time-changed', self.time_changed_cb)

        top = Widgets.VBox()
        top.set_border_width(4)
        fr = Widgets.Frame("All Sky Camera")

        captions = (('Show Sky Image', 'checkbutton'),
                    ('Camera Server:', 'label',
                     'Image Source', 'combobox'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        b.show_sky_image.set_state(self.flag_use_sky_image)
        b.show_sky_image.add_callback('activated',
                                      self.sky_image_toggle_cb)
        b.show_sky_image.set_tooltip(
            "Place the all sky image on the background")

        for name in self.configs.keys():
            b.image_source.append_text(name)
        b.image_source.add_callback('activated',
                                    self.image_source_cb)

        fr = Widgets.Frame("Differential Image")
        captions = (('Show Differential Image', 'checkbutton'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        b.show_differential_image.set_state(self.flag_use_diff_image)
        b.show_differential_image.add_callback('activated',
                                               self.diff_image_toggle_cb)
        b.show_differential_image.set_tooltip("Use a differential image")

        fr = Widgets.Frame("Image Download Info")
        image_info_text = "Please select 'Show Sky Image' to display an image"
        self.w.select_image_info = Widgets.Label(image_info_text)

        fr.set_widget(self.w.select_image_info)
        top.add_widget(fr, stretch=0)

        top.add_widget(Widgets.Label(''), stretch=1)

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
        # set up some settings in our channel
        self.viewer.settings.set(autozoom='off', autocenter='off',
                                 auto_orient=False)
        self.viewer.transform(False, False, False)

        # insert canvas, if not already
        self.initialize_plot()
        self._last_img_update_dt = None
        self._sky_image_canvas_setup()

        self.canvas.delete_all_objects()

    def stop(self):
        self.gui_up = False
        # remove the canvas from the image
        p_canvas = self.viewer.get_canvas()
        if self.canvas in p_canvas:
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

        self.logger.info(f"image to be loaded is: {imgpath}")
        flip_x, flip_y, swap_xy = self.settings['image_transform']
        rot_deg = self.settings['image_rotation']

        if imgpath.endswith('.fits'):
            img = AstroImage(logger=self.logger)
        else:
            img = RGBImage(logger=self.logger)
        img.load_file(imgpath)

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

        self.old_data = self.cur_data
        self.cur_data = data_np
        self.refresh_image()

    def refresh_image(self):
        data_np = self.cur_data
        if data_np is None:
            return
        ht, wd = data_np.shape[:2]

        if not self.flag_use_diff_image or self.old_data is not None:
            self.w.select_image_info.set_text('')

        if self.flag_use_diff_image:
            if self.old_data is not None:
                data_np = data_np - self.old_data

        img = AstroImage(data_np=data_np, logger=self.logger)
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
        self.fv.assert_gui_thread()
        with self.viewer.suppress_redraw:
            wd, ht = img.get_size()
            rx, ry = wd * 0.5, ht * 0.5
            cvs_img = self.dc.NormImage(-rx, -ry, img)
            cvs_img.is_data = True
            self.canvas.delete_all_objects()
            self.canvas.add(cvs_img)
            self.viewer.set_limits(((-rx * 1.25, -ry * 1.25),
                                    (rx * 1.25, ry * 1.25)))
            self.viewer.auto_levels()
            self.viewer.redraw(whence=0)
        image_timestamp = datetime.datetime.now()
        image_info_text = "Image download complete, displayed at: " + \
            image_timestamp.strftime("%D %H:%M:%S")
        self.w.select_image_info.set_text(image_info_text)

    def download_sky_image(self):
        try:
            self.fv.assert_gui_thread()
            image_timestamp = datetime.datetime.now()
            image_info_text = "Initiating image download at: " + \
                image_timestamp.strftime("%D %H:%M:%S")
            self.w.select_image_info.set_text(image_info_text)
            self.fv.nongui_do(self.do_download_sky_image)

        except Exception as e:
            image_timestamp = datetime.datetime.now()
            image_info_text = "Image download failed at: " + \
                image_timestamp.strftime("%D %H:%M:%S")
            self.w.select_image_info.set_text(image_info_text)
            self.logger.error("failed to download/update sky image: {}"
                              .format(e), exc_info=True)

    def do_download_sky_image(self):
        try:
            self.fv.assert_nongui_thread()
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
            image_timestamp = datetime.datetime.now()
            image_info_text = "Image download failed at: " + \
                image_timestamp.strftime("%D %H:%M:%S")
            self.fv.gui_do(self.w.select_image_info.set_text, image_info_text)
            self.logger.error("failed to download/update sky image: {}"
                              .format(e), exc_info=True)

    def update_sky_image(self):
        self.fv.assert_gui_thread()
        with self.viewer.suppress_redraw:
            if self.sky_image_path is not None:
                self.update_image(self.sky_image_path)

            self.viewer.redraw(whence=0)

    def get_scale(self):
        """Return scale in pix/deg"""
        obj = self.channel.opmon.get_plugin('SkyCam')
        return obj.get_scale()

    def _sky_image_canvas_setup(self):
        p_canvas = self.viewer.get_canvas()
        if self.flag_use_sky_image:
            if self.canvas not in p_canvas:
                # Add our canvas layer
                p_canvas.add(self.canvas)
                p_canvas.lower_object(self.canvas)
            # NOTE: Targets plugin canvas needs to be the active one
            self.canvas.ui_set_active(False)

        else:
            if self.canvas in p_canvas:
                p_canvas.delete_object(self.canvas)

        self.viewer.redraw(whence=0)

    def sky_image_toggle_cb(self, w, tf):
        self.flag_use_sky_image = tf
        self._sky_image_canvas_setup()
        if self.flag_use_sky_image and self.sky_image_path is None:
            # if user now wants a background image and we don't have one
            # initiate a download; otherwise timed loop will pull one in
            # eventually
            self.download_sky_image()

    def diff_image_toggle_cb(self, w, tf):
        self.flag_use_diff_image = tf
        message = "Waiting for the next image to create a differential sky..."
        if self.flag_use_diff_image and self.old_data is None:
            self.w.select_image_info.set_text(message)
        self.refresh_image()

    def image_source_cb(self, w, idx):
        which = w.get_text()
        self.img_src_name = which
        config = self.configs[which]
        self.config = {
            'url': config['url'],
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
            self.canvas.delete_all_objects()
            self._sky_image_canvas_setup()
            self.download_sky_image()

        except Exception as e:
            self.w.select_image_info.set_text("Error downloading, check log")
            self.logger.error(f"Error loading image: {e}", exc_info=True)

    def time_changed_cb(self, cb, time_utc, cur_tz):
        if not self.gui_up or not self.flag_use_sky_image:
            return

        if (self._last_img_update_dt is None or
            abs((time_utc - self._last_img_update_dt).total_seconds()) >
            self.settings.get('image_update_interval')):
            self._last_img_update_dt = time_utc
            self.logger.info("attempting to update image")
            self.download_sky_image()

    def __str__(self):
        return 'skycam'
