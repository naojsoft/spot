"""
InsFov.py -- Overlay FOV info on images

Requirements
============

naojsoft packages
-----------------
- ginga
"""
import numpy as np

# ginga
from ginga.gw import Widgets
from ginga import GingaPlugin, trcalc
from ginga.util import wcs
from ginga.misc import Bunch

from spot.util import target as spot_target
from spot.util.rot import normalize_angle
# get all overlays
from spot.instruments import inst_dict


class InsFov(GingaPlugin.LocalPlugin):
    """
    ++++++++++++++
    Instrument FOV
    ++++++++++++++

    The Instrument FOV plugin is used to overlay the field of view of an
    instrument over a survey image in the `<wsname>_FIND` window.

    .. note:: It is important to have previously downloaded an image in
              the find viewer (using the "FindImage" plugin) that has an
              accurate WCS in order for this plugin to operate properly.

    Selecting the Instrument
    ========================

    The instrument can be selected by pressing the "Choose" button under
    "Instrument", and then navigating the menu until you find the
    desired instrument. Once the instrument is selected the name will be
    filled in by "Instrument:" and an outline of the instrument's
    field of view will appear in the `<wsname>_FIND` window. The position
    angle can be adjusted, rotating the survey image relative to the
    instrument overlay. The image can also be  flipped across the vertical
    axis by checking the "Flip" box.

    The RA and DEC will be autofilled by setting the pan position in the
    `<wsname>_FIND` window (for example, by Shift-clicking), but can also
    be adjusted manually by entering in the coordinates. The RA and DEC
    can be specified as decimal values (degrees) or sexigesimal notation.

    To center the image on the current telescope pointing, check the box
    next to "Follow telescope" in the ``FindImage`` plugin UI.  This will
    allow you to watch a dither happening on an area of the sky if the WCS
    is reasonably accurate in the finding image.

    .. note:: To get the "Follow telescope" feature to work, you need to
              have written a companion plugin to get the status from your
              telescope as described in the documentation for the
              TelescopePosition plugin.
    """
    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super().__init__(fv, fitsimage)

        if not self.chname.endswith('_FIND'):
            return

        # get FOV preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_InsFov')
        self.settings.add_defaults(sky_radius_arcmin=3,
                                   fov_update_interval=60.0)
        self.settings.load(onError='silent')

        self.viewer = self.fitsimage
        t_ = self.viewer.get_settings()
        t_.get_setting('pan').add_callback('set', self.set_pan_cb)

        self.dc = fv.get_draw_classes()
        canvas = self.dc.DrawingCanvas()
        canvas.set_surface(self.viewer)
        self.canvas = canvas

        # these are set via callbacks from the SiteSelector plugin
        self.site = None
        self.dt_utc = None
        self.cur_tz = None
        self._last_update_dt = None

        self.cur_fov = FOV(self, self.canvas, (0, 0))
        self.flip = False
        self.pa_deg = 0.0
        self.coord = (0.0, 0.0)
        self.target = None
        self.gui_up = False

    def build_gui(self, container):

        if not self.chname.endswith('_FIND'):
            raise Exception(f"This plugin is not designed to run in channel {self.chname}")
        wsname, _ = self.chname.split('_')
        channel = self.fv.get_channel(wsname + '_TGTS')
        obj = channel.opmon.get_plugin('SiteSelector')
        self.site = obj.get_site()
        obj.cb.add_callback('site-changed', self.site_changed_cb)
        self.dt_utc, self.cur_tz = obj.get_datetime()
        obj.cb.add_callback('time-changed', self.time_changed_cb)

        top = Widgets.VBox()
        top.set_border_width(4)

        fr = Widgets.Frame("Instrument")

        captions = (('Instrument:', 'label', 'instrument', 'llabel',
                     'Choose', 'button'),
                    ('PA (deg):', 'label', 'pa', 'entryset',
                     'Flip', 'checkbox'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b

        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        # populate instrument overlays menu
        self.w.insmenu = Widgets.Menu()
        child = self.w.insmenu.add_name('None')
        child.add_callback('activated', self.select_inst_cb, 'None', 'None')
        for telname, fov_dct in inst_dict.items():
            menu = self.w.insmenu.add_menu(telname)
            for insname in fov_dct:
                child = menu.add_name(insname)
                child.add_callback('activated', self.select_inst_cb,
                                   telname, insname)
        b.instrument.set_text('None')
        b.choose.add_callback('activated',
                              lambda w: self.w.insmenu.popup(widget=w))
        b.choose.set_tooltip("Choose instrument overlay")

        b.pa.set_text(f"{self.pa_deg:.2f}")
        b.pa.add_callback('activated', self.set_pa_cb)
        b.pa.set_tooltip("Set desired position angle")
        b.flip.set_state(self.flip)
        # TEMP
        b.flip.set_enabled(False)
        b.flip.set_tooltip("Flip orientation")
        b.flip.add_callback("activated", self.toggle_flip_cb)

        fr = Widgets.Frame("Pointing")

        captions = (('RA:', 'label', 'ra', 'entry', 'DEC:', 'label',
                     'dec', 'entry'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        b.ra.add_callback('activated', self.set_coord_cb)
        b.ra.set_tooltip("The Right Ascension at the target")
        b.dec.add_callback('activated', self.set_coord_cb)
        b.dec.set_tooltip("The Declination at the target")

        sw = Widgets.ScrollArea()
        vbox = Widgets.VBox()
        vbox.set_border_width(4)
        vbox.set_spacing(2)
        sw.set_widget(vbox)
        self.w.fov_gui_box = vbox
        top.add_widget(sw, stretch=1)

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
        p_canvas = self.viewer.get_canvas()
        if self.canvas not in p_canvas:
            p_canvas.add(self.canvas)
        self.canvas.ui_set_active(False)

        self.redo()

    def stop(self):
        self.gui_up = False
        self.coord = (0.0, 0.0)
        self.target = None
        self.cur_fov = FOV(self, self.canvas, (0, 0))
        self.canvas.delete_all_objects()
        # remove the canvas from the image
        p_canvas = self.viewer.get_canvas()
        p_canvas.delete_object(self.canvas)

    def redo(self):
        """This is called when a new image arrives or the data in the
        existing image changes.
        """
        if not self.gui_up:
            return

        self.update_pointing()

        # check pan location
        pos = self.viewer.get_pan(coord='data')[:2]
        data_x, data_y = pos[:2]

        image = self.viewer.get_image()
        if image is None:
            return

        ra_deg, dec_deg = image.pixtoradec(data_x, data_y)
        ra_str = wcs.ra_deg_to_str(ra_deg)
        dec_str = wcs.dec_deg_to_str(dec_deg)
        self.w.ra.set_text(ra_str)
        self.w.dec.set_text(dec_str)

        self.redo_image()

    def redo_image(self):
        image = self.viewer.get_image()
        if image is None:
            return

        ra_deg, dec_deg = self.coord
        pan_pt = image.radectopix(ra_deg, dec_deg)

        # the image rotation necessary to show 0 deg position angle
        self.cur_fov.init_image(image, pan_pt, self.pa_deg, righthand=self.flip)

        self.pa_deg = self.cur_fov.get_pa()
        self.w.pa.set_text(f"{self.pa_deg:.2f}")

        self.cur_fov.update_viewer(self.viewer)

    def select_inst_cb(self, w, telname, insname):
        with self.viewer.suppress_redraw:
            # changing instrument: remove old FOV
            self.cur_fov.remove()
            # remove FOV GUI
            self.w.fov_gui_box.remove_all(delete=True)

            if telname == 'None':
                # 'None' selected
                klass = FOV
                self.w.instrument.set_text(telname)
            else:
                klass = inst_dict[telname][insname]
                self.w.instrument.set_text(f"{telname}/{insname}")

            pt = self.viewer.get_pan(coord='data')
            self.cur_fov = klass(self, self.canvas, pt[:2])

            # this should change the size setting in FindImage
            self.settings.set(sky_radius_arcmin=self.cur_fov.sky_radius_arcmin)

            self.redo_image()

            self.cur_fov.build_gui(self.w.fov_gui_box)

    def set_pa_cb(self, w):
        self.pa_deg = float(w.get_text().strip())
        self.update_fov()

    def update_fov(self):
        self.cur_fov.set_pa(self.pa_deg)
        self.cur_fov.update_viewer(self.viewer)

        # Some FOV my not set the same PA as requested (for example,
        # no rotator or something), so update our PA to what the FOV
        # thinks it is
        self.pa_deg = self.cur_fov.get_pa()
        self.w.pa.set_text(f"{self.pa_deg:.2f}")

    def toggle_flip_cb(self, w, tf):
        self.flip = tf
        self.redo_image()

    def site_changed_cb(self, cb, site_obj):
        self.logger.debug("site has changed")
        self.site = site_obj

        if not self.gui_up:
            return
        self.update_fov()

    def time_changed_cb(self, cb, time_utc, cur_tz):
        old_dt_utc = self.dt_utc
        self.dt_utc = time_utc
        self.cur_tz = cur_tz
        if not self.gui_up:
            return

        if (self._last_update_dt is None or
            abs((self.dt_utc - self._last_update_dt).total_seconds()) >
            self.settings.get('fov_update_interval')):
            self.logger.info("updating FOV")
            self._last_update_dt = time_utc
            self.update_fov()

    def get_cres(self):
        cres = self.target.calc(self.site.observer, self.dt_utc)
        return cres

    def get_site(self):
        return self.site

    def update_pointing(self):
        obj = self.channel.opmon.get_plugin('FindImage')
        target = obj.get_target()

        self.target = target
        if target is None:
            self.coord = (0.0, 0.0)
        else:
            ra_deg, dec_deg = target.ra, target.dec
            self.coord = (ra_deg, dec_deg)

    def set_coord_cb(self, w):
        ra = self.w.ra.get_text().strip()
        dec = self.w.dec.get_text().strip()
        eq = 2000.0
        ra_deg, dec_deg, equinox = spot_target.normalize_ra_dec_equinox(ra, dec, eq)

        image = self.viewer.get_image()
        if image is None:
            return
        data_x, data_y = image.radectopix(ra_deg, dec_deg)
        self.viewer.set_pan(data_x, data_y, coord='data')

    def set_pan_cb(self, setting, val):
        if not self.gui_up:
            return

        # user might have panned somewhere else, so check our location
        # at the pan position
        ra_deg, dec_deg = self.viewer.get_pan(coord='wcs')
        ra_str = wcs.ra_deg_to_str(ra_deg)
        dec_str = wcs.dec_deg_to_str(dec_deg)
        self.w.ra.set_text(ra_str)
        self.w.dec.set_text(dec_str)

    def __str__(self):
        return 'insfov'


class FOV:
    def __init__(self, pl_obj, canvas, pt):
        super().__init__()

        self.pl_obj = pl_obj
        self.canvas = canvas
        self.dc = canvas.get_draw_classes()

        # instrument mounting offset angle that needs to be taken into account
        self.mount_offset_rot_deg = 0.0
        # default sky radius
        self.sky_radius_arcmin = 5

        # center point
        self.pt_ctr = (0.0, 0.0)
        # flip, rotation of supplied image to achieve a 0 deg PA
        self.img_flip_x = False
        self.img_rot_deg = 0.0
        self.scale_x = 1.0
        self.scale_y = 1.0
        # user desired Position Angle
        self.pa_deg = 0.0
        # calculated rotation of overlay to achieve desired PA
        self.pa_rot_deg = 0.0
        # user desires a flip of the image
        self.flip_tf = False

        self.w = Bunch.Bunch()

    def init_image(self, image, pt, pa_deg, righthand=False):
        """Initialize FOV from an image and a pan position on that image.
        """
        header = image.get_header()
        rot, scale = wcs.get_xy_rotation_and_scale(header)

        # figure out the orientation of the image from its WCS, and whether
        # we need to flip it and how much to rotate it to get a 0 deg PA
        data_x, data_y = pt[:2]
        (x, y, xn, yn, xe, ye) = wcs.calc_compass(image, data_x, data_y,
                                                  1.0, 1.0)
        degn = np.degrees(np.arctan2(xn - x, yn - y))
        # self.logger.info("degn=%f xe=%f ye=%f" % (
        #     degn, xe, ye))
        # rotate east point also by degn
        xe2, ye2 = trcalc.rotate_pt(xe, ye, degn, xoff=x, yoff=y)
        dege = np.degrees(np.arctan2(xe2 - x, ye2 - y))
        # self.logger.info("dege=%f xe2=%f ye2=%f" % (
        #     dege, xe2, ye2))

        self.flip_tf = righthand
        # if right-hand image, flip it to make left hand
        xflip = righthand
        if dege > 0.0:
            xflip = not xflip
        if xflip:
            degn = - degn

        # store the flip of the image and the rotation needed to get 0 deg
        # Position Angle on the sky
        self.img_flip_x = xflip
        self.img_rot_deg = degn

        scale_x, scale_y = scale
        self.set_pos(pt)
        self.set_scale(scale_x, scale_y)
        self.set_pa(pa_deg)

        # NOTE: need to do an update_viewer() after this

    def update_viewer(self, viewer):
        viewer.redraw(whence=3)

    def build_gui(self, container):
        pass

    def set_pa(self, pa_deg):
        """Set the desired Position Angle of the FOV.

        NOTE: need to do an update_viewer() after this

        Parameters
        ----------
        pa_deg : float
            Desired position angle in deg
        """
        if False:   # self.flip_tf:
            self.pa_rot_deg = self.img_rot_deg + self.mount_offset_rot_deg - pa_deg
        else:
            self.pa_rot_deg = self.img_rot_deg - self.mount_offset_rot_deg + pa_deg

        self.pa_deg = normalize_angle(pa_deg, limit='half')

    def get_pa(self):
        """Return the Position Angle of the field.

        Returns
        -------
        pa_deg : float
            The position angle of the field
        """
        return self.pa_deg

    def set_scale(self, scale_x, scale_y):
        """How the FOV object is told to update its graphics when the scale changes.

        This is usually a result of an image with a different scale being loaded.
        Normally, the FOV should redraw itself by updating the canvas.

        Parameters
        ----------
        scale_x : float
            Scale in the X direction

        scale_y : float
            Scale in the Y direction

        """
        pass

    def set_pos(self, pt):
        """How the FOV object is told to update its graphics when the position changes.

        Normally, the FOV should redraw itself by updating the canvas.

        Parameters
        ----------
        pt : tuple of (float, float)
            X and Y position (in pixels) on the image
        """
        self.pt_ctr = pt

    def rotate(self, rot_deg):
        """Called when the rotation changes for the viewer. Can be used
        to adjust the angle of text elements in overlays, for example.
        """
        pass

    def remove(self):
        """How the FOV object is told to remove its graphics from the canvas.

        Typically, because a different instrument FOV is being loaded.
        """
        pass

    def flip_x(self, comp_obj, x_ctr):
        for obj in comp_obj.objects:
            obj.points = np.array([(x_ctr - (pt[0] - x_ctr), pt[1])
                                   for pt in obj.points], dtype=float)
