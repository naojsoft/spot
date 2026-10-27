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
    * select "Monochrome" to convert color images to a monochrome

Selecting a different image source inputs different images, which are often
different sizes. To set an image to the size of the current screen locate
the button portraying a magnifying glass with "[:]" within it. This is found
in the bottom row of plugins of the UI.

The second section, titled "Differential Image," has these controls:

    * select "Show Differential Image" to portray a differential image
    * select "Derotate Sky" to rotate the previous image with the sky
      before subtracting it, so that stars cancel out
    * "Threshold" sets how large a change (in units of the image noise)
      counts as cloud
    * "Cloud Cover" shows the percentage of the sky within 75 degrees of
      the zenith that changed by more than the threshold

The differential image shows the change between the current and previous
images from the camera.  Brighter areas are shown in red and darker areas
in blue; areas that did not change are black.  Both images are reduced to
monochrome, downsampled and median filtered (which removes most stars),
and the previous image is scaled to match the overall brightness of the
current one, so that changes in camera exposure do not show up as clouds.
The change is then divided by an estimate of the image noise.

The sky rotates by about a quarter of a degree per minute, so stars move
between images.  With "Derotate Sky" selected, the previous image is
rotated about the celestial pole by the time between the two images, so
that only clouds (and other real changes) remain.  This relies on the
camera orientation in skycams.yml being correct (North up, East left, as
in the PolarSky plot) and on the latitude of the selected site.

If the source was recently selected from the "Camera Server" and a
second image from the source has not been received yet, a message on
screen will appear telling the user that it is waiting to receive a second
image to create the differential image.

Images are downloaded on a timer set in skycams.yml, which is not
synchronized with the camera.  If a download returns the same image as the
previous one, it is ignored and the existing differential image is kept.

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
import yaml
import tempfile

# ginga
from ginga import trcalc, cmap
from ginga.AstroImage import AstroImage
from ginga.RGBImage import RGBImage
from ginga import GingaPlugin
from ginga.misc import Future
from ginga.util.paths import ginga_home

# where our config files are stored
from spot import __file__
from spot.util.config import get_workspace_settings, save_settings
from spot.util import skydiff
from spot.locale import _tr, get_plugin_doc
cfgdir = os.path.join(os.path.dirname(__file__), 'config')

# Color maps for the differential image, as (label, name, control points).
# Each control point is (position, r, g, b); position 0.5 is "no change".
# They are chosen to keep the target and telescope overlays readable.
diff_cmaps = [
    ("Gray", 'skydiff_gray',
     [(0.0, 0.0, 0.0, 0.0), (0.5, 0.35, 0.35, 0.35), (1.0, 1.0, 1.0, 1.0)]),
    # magnitude of the change regardless of sign
    ("Change", 'skydiff_change',
     [(0.0, 1.0, 1.0, 1.0), (0.5, 0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0)]),
    ("Teal/Amber", 'skydiff_tealamber',
     [(0.0, 0.45, 0.85, 0.85), (0.25, 0.15, 0.4, 0.4), (0.5, 0.0, 0.0, 0.0),
      (0.75, 0.5, 0.4, 0.15), (1.0, 1.0, 0.85, 0.5)]),
    ("Blue/Red", 'skydiff_bluered',
     [(0.0, 0.35, 0.65, 1.0), (0.25, 0.1, 0.35, 0.9), (0.5, 0.0, 0.0, 0.0),
      (0.75, 0.9, 0.25, 0.1), (1.0, 1.0, 0.75, 0.3)]),
]


def register_diff_cmaps():
    """Add the differential image color maps to ginga (so that they also
    show up in ginga's own color map choices).
    """
    names = cmap.get_names()
    pos = np.linspace(0.0, 1.0, 256)
    for _label, name, ctrl in diff_cmaps:
        if name in names:
            continue
        ctrl = np.asarray(ctrl)
        clst = tuple(zip(*[np.interp(pos, ctrl[:, 0], ctrl[:, i])
                           for i in (1, 2, 3)]))
        cmap.add_cmap(name, clst)


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
    Areas that became brighter since the previous image are shown in red,
    and areas that became darker in blue.  Select "Derotate Sky" to rotate
    the previous image with the sky so that stars cancel out (this requires
    that the camera orientation in skycams.yml is correct).  "Cloud Cover"
    shows the percentage of the sky near the zenith that changed by more
    than "Threshold" times the image noise.

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
    You can also give the latitude of the camera in degrees (negative
    in the southern hemisphere); this is used to derotate the sky for the
    differential image.  Without it, the latitude of the selected site is
    used.

    Restart spot and you should be able to pick your new camera from the list.
    """
    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super().__init__(fv, fitsimage)

        if not self.chname.endswith('_TGTS'):
            return

        # get SkyCam preferences
        wsname = self.chname.rsplit('_', 1)[0]
        self.settings = get_workspace_settings(wsname, 'SkyCam',
                                               logger=self.logger)
        self.settings.add_defaults(download_folder=tempfile.gettempdir(),
                                   image_update_interval=60.0,
                                   default_camera=None,
                                   show_sky_image=False,
                                   show_diff_image=False,
                                   image_convert_monochrome=True,
                                   image_radius=1000,
                                   diff_derotate=True,
                                   diff_threshold_sigma=5.0,
                                   diff_display_sigma=10.0,
                                   diff_median_size=3,
                                   diff_work_size=700,
                                   diff_max_za_deg=75.0,
                                   diff_color_map='skydiff_gray')
        self.settings.load(onError='silent')

        self.viewer = self.fitsimage
        self.dc = fv.get_draw_classes()
        self.std = np.array([0.2126, 0.7152, 0.0722])
        self.cur_data = None
        self.cur_coverage = None
        # reduced working frames for differencing, and their arrival times
        self.cur_work = None
        self.old_work = None
        self.cur_work_t = None
        self.old_work_t = None
        self.bin_factor = 1
        self.cc_pct = None

        # The sky image is drawn with the viewer's color map and cut
        # levels, so the user can adjust them.  The normal and the
        # differential image need very different ones, so we keep a
        # snapshot of the viewer's settings for each mode and swap them
        # when the mode changes.
        register_diff_cmaps()
        self.view_mode = 'normal'
        self.view_state = dict(normal=None, diff=None)
        self.view_keys = (list(self.viewer.get_rgbmap().settings_keys) +
                          ['cuts'])
        # auto-level the next normal image
        self.need_autolevels = True
        self.img_src_name = self.settings.get('default_camera', None)

        self.read_skycams_config()

        self.sky_image_path = None
        self._last_img_update_dt = None
        self.flag_use_sky_image = self.settings.get('show_sky_image', False)
        self.flag_use_diff_image = self.settings.get('show_diff_image', False)

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

        Widgets = self.fv.get_widget_classes()
        # re-read skycams config, in case user is tweaking settings
        self.read_skycams_config()

        # initialize site and date/time/tz
        obj = self.channel.opmon.get_plugin('SiteSelector')
        obj.cb.add_callback('time-changed', self.time_changed_cb)

        top = Widgets.VBox()
        top.set_border_width(4)
        fr = Widgets.Frame(_tr("All Sky Camera"))

        captions = (('Show Sky Image', 'checkbox',
                     'Monochrome', 'checkbox'),
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
            _tr("Place the all sky image on the background"))
        b.monochrome.set_state(self.settings['image_convert_monochrome'])
        b.monochrome.add_callback('activated',
                                  self.mono_image_toggle_cb)
        b.monochrome.set_tooltip(
            _tr("Convert a color image to monochrome by channel mixing"))

        for name in self.configs.keys():
            b.image_source.append_text(name)
        b.image_source.add_callback('activated',
                                    self.image_source_cb)

        fr = Widgets.Frame(_tr("Differential Image"))
        captions = (('Show Differential Image', 'checkbutton',
                     'Derotate Sky', 'checkbutton'),
                    ('Threshold:', 'label', 'Threshold', 'spinfloat'),
                    ('Color Map:', 'label', 'Diff Color Map', 'combobox'),
                    ('Cloud Cover:', 'label', 'Cloud Cover', 'llabel'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        b.show_differential_image.set_state(self.flag_use_diff_image)
        b.show_differential_image.add_callback('activated',
                                               self.diff_image_toggle_cb)
        b.show_differential_image.set_tooltip(
            _tr("Show the change since the previous image: "
                "red is brighter, blue is darker"))
        b.derotate_sky.set_state(self.settings['diff_derotate'])
        b.derotate_sky.add_callback('activated', self.derotate_toggle_cb)
        b.derotate_sky.set_tooltip(
            _tr("Rotate the previous image with the sky so that stars cancel "
                "(requires a correctly oriented camera and site latitude)"))
        b.threshold.set_limits(1.0, 50.0, incr_value=0.5)
        b.threshold.set_value(self.settings['diff_threshold_sigma'])
        b.threshold.add_callback('value-changed', self.threshold_cb)
        b.threshold.set_tooltip(
            _tr("Change (in units of the image noise) above which a pixel "
                "counts toward cloud cover"))
        names = [name for _label, name, _ctrl in diff_cmaps]
        for label, _name, _ctrl in diff_cmaps:
            b.diff_color_map.append_text(_tr(label))
        cm_name = self.settings['diff_color_map']
        if cm_name in names:
            b.diff_color_map.set_index(names.index(cm_name))
        b.diff_color_map.add_callback('activated', self.diff_color_map_cb)
        b.diff_color_map.set_tooltip(
            _tr("Color map for the differential image (you can also pick "
                "any color map and adjust the cut levels and contrast with "
                "the usual viewer controls)"))
        b.cloud_cover.set_tooltip(
            _tr("Percentage of the sky within {}° of the zenith that "
                "changed by more than the threshold").format(
                    self.settings['diff_max_za_deg']))

        fr = Widgets.Frame(_tr("Image Download Info"))
        image_info_text = _tr("Please select 'Show Sky Image' to display an image")
        self.w.select_image_info = Widgets.Label(image_info_text)

        fr.set_widget(self.w.select_image_info)
        top.add_widget(fr, stretch=0)

        top.add_widget(Widgets.Label(''), stretch=1)

        btns = Widgets.HBox()
        btns.set_border_width(4)
        btns.set_spacing(3)

        btn = Widgets.Button(_tr("Close"))
        btn.add_callback('activated', lambda w: self.close())
        btns.add_widget(btn, stretch=0)
        btn = Widgets.Button(_tr("Help"))
        btn.add_callback('activated', lambda w: self.help())
        btns.add_widget(btn, stretch=0)
        btn = Widgets.Button(_tr("Save config"))
        btn.add_callback('activated', lambda w: self.save_config())
        btn.set_tooltip(_tr("Save this plugin's configuration for the workspace"))
        btns.add_widget(btn, stretch=0)
        btns.add_widget(Widgets.Label(''), stretch=1)

        top.add_widget(btns, stretch=0)

        container.add_widget(top, stretch=1)
        self.gui_up = True

    def close(self):
        self.fv.stop_local_plugin(self.chname, str(self))
        return True

    def help(self):
        name, doc = get_plugin_doc(self)
        self.fv.help_text(name, doc, text_kind='rst', trim_pfx=4)

    def save_config(self):
        try:
            # record the current selection (more settings may be added later)
            self.settings.set(default_camera=self.img_src_name)
            save_settings(self.settings, self.fv)
            self.fv.show_status(_tr("Saved configuration for {}").format(str(self)))
        except Exception as e:
            self.fv.show_error(_tr("Error saving {} config: {}").format(str(self), e))

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

        # if a saved config restored show_sky_image=True, kick off a
        # download now rather than waiting for the timed update loop
        # (mirrors what sky_image_toggle_cb does on a manual toggle)
        if self.flag_use_sky_image and self.sky_image_path is None:
            self.download_sky_image()

    def stop(self):
        self.gui_up = False
        # leave the viewer with the normal color map and cut levels
        self._set_view_mode('normal')
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
        cvt_mono = self.settings['image_convert_monochrome']

        if imgpath.endswith('.fits'):
            img = AstroImage(logger=self.logger)
        else:
            img = RGBImage(logger=self.logger)
        img.load_file(imgpath)

        # cut out the sky circle into a square centered on the zenith
        # (padding it if the circle runs off the frame), rotate it about
        # the zenith and flip it as necessary; RGB images are also
        # flipped vertically
        xc, yc = self.settings['image_center']
        r = self.settings['image_radius']
        data_np, coverage = skydiff.orient_frame(
            img.get_data(), xc, yc, r, rot_deg=rot_deg,
            flip_x=flip_x, flip_y=flip_y, swap_xy=swap_xy,
            flip_ud=isinstance(img, RGBImage))
        self.cur_coverage = coverage

        self._update_work_frame(data_np, coverage)

        if isinstance(img, RGBImage):
            if len(data_np.shape) == 3 and data_np.shape[2] > 2 and cvt_mono:
                # if this is a color RGB image, convert to monochrome
                # via the standard channel mixing technique
                data_np = (data_np[:, :, 0] * self.std[0] +
                           data_np[:, :, 1] * self.std[1] +
                           data_np[:, :, 2] * self.std[2])

                ht, wd = data_np.shape[:2]
                data_np = data_np.reshape((ht, wd))

        self.cur_data = data_np
        self.refresh_image()

    def _update_work_frame(self, data_np, coverage):
        """Reduce a newly arrived frame to a working frame for the
        differential image, and shift the previous one to be the
        reference.
        """
        t_start = time.time()
        wd = data_np.shape[1]
        self.bin_factor = skydiff.get_bin_factor(
            wd, self.settings['diff_work_size'])
        work = skydiff.make_work_frame(
            data_np, bin_factor=self.bin_factor,
            median_size=self.settings['diff_median_size'],
            coverage=coverage)

        if (self.cur_work is not None and work.shape == self.cur_work.shape
                and np.array_equal(work, self.cur_work, equal_nan=True)):
            # the camera has not produced a new image since our last
            # download (or the same file was reloaded)--keep the
            # existing pair so the difference stays meaningful
            self.logger.info("sky image unchanged since last download")
            return

        if self.cur_work is not None and work.shape != self.cur_work.shape:
            # camera changed size; start over
            self.cur_work = None

        self.old_work, self.old_work_t = self.cur_work, self.cur_work_t
        self.cur_work, self.cur_work_t = work, t_start
        self.logger.debug("work frame %s (bin %d) made in %.3f sec" % (
            str(work.shape), self.bin_factor, time.time() - t_start))

    def _set_view_mode(self, mode):
        """Switch the viewer's color map, cut levels, etc. between those
        for the normal ('normal') and differential ('diff') image.
        """
        if mode == self.view_mode:
            return
        t_ = self.viewer.get_settings()
        self.view_state[self.view_mode] = {k: t_[k] for k in self.view_keys
                                           if t_.has_key(k)}
        self.view_mode = mode
        state = self.view_state[mode]
        if state is None:
            # first time showing the differential image
            state = self._default_diff_view_state()
        t_.set(**state)

    def _default_diff_view_state(self):
        ds = self.settings['diff_display_sigma']
        return dict(color_map=self.settings['diff_color_map'],
                    intensity_map='ramp', color_algorithm='linear',
                    color_map_invert=False, color_map_rot_pct=0.0,
                    contrast=0.5, brightness=0.5, cuts=(-ds, ds))

    def _get_latitude(self):
        # prefer the camera's own latitude, since the camera need not be
        # at the site selected in SPOT (it may even be in the other
        # hemisphere, which would rotate the sky the wrong way)
        lat = self.config.get('latitude', None)
        if lat is not None:
            return float(lat)
        try:
            obj = self.channel.opmon.get_plugin('SiteSelector')
            return obj.get_status()['latitude_deg']
        except Exception as e:
            self.logger.warning(f"can't get site latitude: {e}")
            return None

    def _make_diff_image(self):
        """Compute the differential image from the working frames.
        Returns a ginga AstroImage, or None if there are not two frames
        yet.
        """
        if self.old_work is None or self.cur_work is None:
            self.cc_pct = None
            return None
        res = skydiff.sky_diff(
            self.cur_work, self.old_work,
            dt_sec=self.cur_work_t - self.old_work_t,
            lat_deg=self._get_latitude(),
            derotate_sky=self.settings['diff_derotate'],
            threshold_sigma=self.settings['diff_threshold_sigma'],
            max_za_deg=self.settings['diff_max_za_deg'],
            noise_step=max(1, self.settings['diff_median_size']))
        self.cc_pct = res['cc_pct']
        self.logger.info("sky diff: CC=%.1f%% sigma=%.3g gain=%.3f" % (
            res['cc_pct'], res['sigma'], res['gain']))

        sig = res['sig']
        valid = np.isfinite(sig)
        mx = np.finfo(np.float32).max
        data_np = np.dstack((np.where(valid, sig, 0.0),
                             valid * mx)).astype(np.float32)
        img = AstroImage(data_np=data_np, logger=self.logger)
        img.set(name=self.img_src_name, nothumb=True, path=None)
        return img

    def _show_cloud_cover(self):
        if not self.gui_up:
            return
        if self.flag_use_diff_image and self.cc_pct is not None:
            self.w.cloud_cover.set_text("{:.1f}%".format(self.cc_pct))
        else:
            self.w.cloud_cover.set_text("--")

    def refresh_image(self):
        if self.flag_use_diff_image:
            img = self._make_diff_image()
            self._show_cloud_cover()
            if img is not None:
                self.w.select_image_info.set_text('')
                self.fv.gui_do(self.__update_display, img,
                               scale=self.bin_factor, mode='diff')
                return
            # no previous frame yet--show the plain image meanwhile
            self.w.select_image_info.set_text(
                _tr("Waiting for the next image to create a differential sky..."))
        else:
            self._show_cloud_cover()
            self.w.select_image_info.set_text('')

        data_np = self.cur_data
        if data_np is None:
            return
        ht, wd = data_np.shape[:2]

        img = AstroImage(data_np=data_np, logger=self.logger)
        ctr_x, ctr_y = wd // 2, ht // 2
        self.crop_circ.x = ctr_x
        self.crop_circ.y = ctr_y
        self.crop_circ.radius = ctr_x
        mask = img.get_shape_mask(self.crop_circ)
        if (self.cur_coverage is not None and
                self.cur_coverage.shape == mask.shape):
            # hide areas outside the camera's field
            mask &= self.cur_coverage

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

    def __update_display(self, img, scale=1, mode='normal'):
        self.fv.assert_gui_thread()
        with self.viewer.suppress_redraw:
            self._set_view_mode(mode)
            wd, ht = img.get_size()
            rx, ry = wd * scale * 0.5, ht * scale * 0.5
            cvs_img = self.dc.NormImage(-rx, -ry, img,
                                        scale_x=scale, scale_y=scale)
            cvs_img.is_data = True
            self.canvas.delete_all_objects()
            self.canvas.add(cvs_img)
            self.viewer.set_limits(((-rx * 1.25, -ry * 1.25),
                                    (rx * 1.25, ry * 1.25)))
            # the differential image is in units of sigma, so its cut
            # levels stay meaningful from image to image; for the normal
            # image, leave the user's cut levels alone unless the viewer
            # is set to auto cut each new image
            if mode == 'normal' and (self.need_autolevels or
                                     self.viewer.get_settings().get(
                                         'autocuts', 'off') != 'off'):
                self.viewer.auto_levels()
                self.need_autolevels = False
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

            url = self.settings['image_url']
            _, ext = os.path.splitext(url)
            outpath = os.path.join(self.settings['download_folder'],
                                   'allsky' + ext)
            start_time = time.time()
            # Delegate the actual download to the central object, which
            # transparently handles both the threaded backend (desktop /
            # pg-over-websocket) and the in-situ async backend (Pyodide,
            # routing through a CORS proxy).
            future = Future.Future()
            future.add_callback('resolved', self._sky_image_downloaded_cb,
                                start_time)
            self.fv.nongui_do(self.fv.download_file, url, outpath, future)

        except Exception as e:
            self._notify_download_failed(e)

    def _sky_image_downloaded_cb(self, future, start_time):
        try:
            filepath = future.get_value(block=False)
        except Exception as e:
            self._notify_download_failed(e)
            return
        self.logger.info("download finished in %.4f sec" % (
            time.time() - start_time))
        self.sky_image_path = filepath
        self.fv.gui_do(self.update_sky_image)

    def _notify_download_failed(self, e):
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
        self.settings.set(show_sky_image=tf)
        self._sky_image_canvas_setup()
        if self.flag_use_sky_image and self.sky_image_path is None:
            # if user now wants a background image and we don't have one
            # initiate a download; otherwise timed loop will pull one in
            # eventually
            self.download_sky_image()

    def mono_image_toggle_cb(self, w, tf):
        self.settings.set(image_convert_monochrome=tf)
        # reload the current image (the differential image always works
        # from luminance, so it is not affected)
        self.cur_data = None
        self.fv.gui_do(self.update_sky_image)

    def diff_image_toggle_cb(self, w, tf):
        self.flag_use_diff_image = tf
        self.settings.set(show_diff_image=tf)
        message = "Waiting for the next image to create a differential sky..."
        if self.flag_use_diff_image and self.old_work is None:
            self.w.select_image_info.set_text(message)
        self.refresh_image()

    def derotate_toggle_cb(self, w, tf):
        self.settings.set(diff_derotate=tf)
        if self.flag_use_diff_image:
            self.refresh_image()

    def diff_color_map_cb(self, w, idx):
        _label, name, _ctrl = diff_cmaps[idx]
        self.settings.set(diff_color_map=name)
        if self.view_mode == 'diff':
            self.viewer.set_color_map(name)
        elif self.view_state['diff'] is not None:
            self.view_state['diff']['color_map'] = name

    def threshold_cb(self, w, val):
        self.settings.set(diff_threshold_sigma=float(val))
        if self.flag_use_diff_image:
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
            'update_interval': config['update_interval'],
            'latitude': config.get('latitude', None),
        }
        self.update_settings()
        self.cur_data = None
        self.cur_work = self.old_work = None
        self.cur_work_t = self.old_work_t = None
        self.cc_pct = None
        self.need_autolevels = True
        self._show_cloud_cover()
        try:
            self.canvas.delete_all_objects()
            self._sky_image_canvas_setup()
            self.download_sky_image()

        except Exception as e:
            self.w.select_image_info.set_text(_tr("Error downloading, check log"))
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
