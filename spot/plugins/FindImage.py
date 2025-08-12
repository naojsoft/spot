"""
FindImage.py -- Download images matching a target

J. Merchant
T. Inagaki
E. Jeschke

Requirements
============
- astropy
- astroquery

naojsoft packages
-----------------
- ginga
"""
import numpy as np
import datetime
import re

from astropy import units as u
from astropy.table import Table

# ginga
from ginga.gw import Widgets
from ginga import GingaPlugin
from ginga.util import wcs, catalog, dp
from ginga.AstroImage import AstroImage

from spot.util import target as spot_target

image_sources = {
    'SkyView: DSS1+Blue': dict(),
    'SkyView: DSS1+Red': dict(),
    'SkyView: DSS2+Red': dict(),
    'SkyView: DSS2+Blue': dict(),
    'SkyView: DSS2+IR': dict(),
    'SkyView: SDSSg': dict(),
    'SkyView: SDSSi': dict(),
    'SkyView: SDSSr': dict(),
    'SkyView: SDSSu': dict(),
    'SkyView: SDSSz': dict(),
    'SkyView: 2MASS-J': dict(),
    'SkyView: 2MASS-H': dict(),
    'SkyView: 2MASS-K': dict(),
    'SkyView: WISE+3.4': dict(),
    'SkyView: WISE+4.6': dict(),
    'SkyView: WISE+12': dict(),
    'SkyView: WISE+22': dict(),
    'SkyView: AKAIR+N60': dict(),
    'SkyView: AKAIR+WIDE-S': dict(),
    'SkyView: AKAIR+WIDE-L': dict(),
    'SkyView: AKAIR+N160': dict(),
    'SkyView: NAVSS': dict(),
    'SkyView: GALEX+Near+UV': dict(),
    'SkyView: GALEX+Far+UV': dict(),
    'ESO: DSS1': dict(),
    'ESO: DSS2-red': dict(),
    'ESO: DSS2-blue': dict(),
    'ESO: DSS2-infrared': dict(),
    'PanSTARRS-1: g': dict(),
    'PanSTARRS-1: r': dict(),
    'PanSTARRS-1: i': dict(),
    'PanSTARRS-1: z': dict(),
    'PanSTARRS-1: y': dict(),
    'STScI: poss1_blue': dict(),
    'STScI: poss1_red': dict(),
    'STScI: poss2ukstu_blue': dict(),
    'STScI: poss2ukstu_red': dict(),
    'STScI: poss2ukstu_ir': dict(),
}

service_urls = {
    'SkyView': """https://skyview.gsfc.nasa.gov/cgi-bin/images?Survey={survey}&position={position}&coordinates={coordinates}&projection=Tan&sampler=LI&Pixels={pixels}&size={size}&Return=FITS""",
    'ESO': """https://archive.eso.org/dss/dss?ra={ra}&dec={dec}&mime-type=application/x-fits&x={arcmin}&y={arcmin}&Sky-Survey={survey}&equinox={equinox}""",
    'STScI': """https://archive.stsci.edu/cgi-bin/dss_search?v={survey}&r={ra_deg}&d={dec_deg}&e={equinox}&h={arcmin}&w={arcmin}&f=fits&c=none&fov=NONE&v3=""",
    'PanSTARRS-1': """https://ps1images.stsci.edu/cgi-bin/fitscut.cgi?ra={ra}&dec={dec}&size={size}&format={format}&output_size=1024"""
}


class FindImage(GingaPlugin.LocalPlugin):
    """
    FindImage
    =========
    The FindImage plugin is used to download and display images from
    image catalogs for known coordinates.  It uses the "{wsname}_FIND"
    viewer to show the images found.

    .. note:: Make sure you have the "Targets" plugin also open, as it is
              used in conjunction with this plugin.

    Selecting a Target
    ------------------
    In the "Targets" plugin, select a single target to uniquely select it.
    Then click the "Get Selected" button in the "Pointing" area of FindImage.
    This should populate the "RA", "DEC", "Equinox" and "Name" fields.

    .. note:: If you have working telescope status integration, you can
              click the "Follow telescope" checkbox to have the "Pointing"
              area updated by the telescope's actual position, if it
              matches a target that is loaded into the Targets plugin.
              Further, the image in the finding viewer will be downloaded
              and panned according to the telescope's current position,
              allowing you to follow a dithering pattern (for example).

    Loading an image from an image source
    -------------------------------------
    Once RA/DEC coordinates are displayed in the "Pointing" area, an image
    can be downloaded using the controls in the "Image Source" area.
    Choose an image source from the drop-down control labeled "Source",
    select a size (in arcminutes) using the "Size" control and click the
    "Find Image" button.  It may take a little while for the image to be
    downloaded and displayed in the finder viewer.

    .. note:: Alternatively, "Load FITS" can be used to load a local FITS
              file with a working WCS of the region, or you can click
              "Create Blank" to create a blank image with a WCS set to the
              desired location.  Either of these may possibly be useful if
              an image source is not available via download.

    """
    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super().__init__(fv, fitsimage)

        if not self.chname.endswith('_FIND'):
            return

        # get FOV preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_FindImage')
        self.settings.add_defaults(name_sources=catalog.default_name_sources,
                                   sky_radius_arcmin=3,
                                   follow_telescope=False,
                                   mark_target=False,
                                   telescope_update_interval=3.0,
                                   targets_update_interval=10.0,
                                   nonsidereal_plot_local_time=True,
                                   color_map='ds9_cool')
        self.settings.load(onError='silent')

        self.viewer = self.fitsimage
        self.dc = fv.get_draw_classes()
        canvas = self.dc.DrawingCanvas()
        canvas.set_surface(self.viewer)
        canvas.register_for_cursor_drawing(self.viewer)
        canvas.set_draw_mode('pick')
        self.canvas = canvas

        compass = self.dc.Compass(0.15, 0.15, 0.08,
                                  fontsize=14, coord='percentage',
                                  color='orange')
        self.canvas.add(compass, redraw=False)

        self.lbl_obj = self.dc.Text(0.025, 0.975, text='', color='gold',
                                    bgcolor='black', bgalpha=1.0,
                                    fontsize=9,
                                    coord='percentage')
        self.canvas.add(self.lbl_obj, redraw=False)

        bank = self.fv.get_server_bank()

        # add name services found in configuration file
        name_sources = self.settings.get('name_sources', [])
        for d in name_sources:
            typ = d.get('type', None)
            obj = None
            if typ == 'astroquery.names':
                if catalog.have_astroquery:
                    obj = catalog.AstroqueryNameServer(self.logger,
                                                       d['fullname'],
                                                       d['shortname'], None,
                                                       d['fullname'])
            else:
                self.logger.debug("Unknown type ({}) specified for catalog source--skipping".format(typ))

            if obj is not None:
                bank.add_name_server(obj)

        # these are set via callbacks from the SiteSelector plugin
        self.site = None
        self.dt_utc = None
        self.cur_tz = None
        self._last_tgt_update_dt = None

        self.size = (3, 3)
        self.targets = None
        self._cur_target = None

        settings = self.viewer.get_settings()
        settings.get_setting('scale').add_callback('set', self.redraw_cb)
        settings.get_setting('pan').add_callback('set', self.redraw_cb)
        settings.get_setting('rot_deg').add_callback('set', self.redraw_cb)
        self.gui_up = False

    def build_gui(self, container):

        if not self.chname.endswith('_FIND'):
            raise Exception(f"This plugin is not designed to run in channel {self.chname}")

        wsname, _ = self.channel.name.split('_')
        channel = self.fv.get_channel(wsname + '_TGTS')
        obj = channel.opmon.get_plugin('SiteSelector')
        self.site = obj.get_site()
        obj.cb.add_callback('site-changed', self.site_changed_cb)
        self.dt_utc, self.cur_tz = obj.get_datetime()
        obj.cb.add_callback('time-changed', self.time_changed_cb)

        self.targets = channel.opmon.get_plugin('Targets')
        have_telpos = channel.opmon.has_plugin('TelescopePosition')
        if have_telpos:
            self.telpos = channel.opmon.get_plugin('TelescopePosition')
            self.telpos.cb.add_callback('telescope-status-changed',
                                        self.telpos_changed_cb)

        top = Widgets.VBox()
        top.set_border_width(4)

        fr = Widgets.Frame("Pointing")

        captions = (('RA:', 'label', 'ra', 'llabel', 'DEC:', 'label',
                     'dec', 'llabel'),
                    ('Equinox:', 'label', 'equinox', 'llabel',
                     'Name:', 'label', 'tgt_name', 'llabel'),
                    ('Get Selected', 'button', "Follow telescope", 'checkbox',
                     'Mark target', 'checkbox', 'Reset pan', 'button'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b
        b.ra.set_text('')
        b.dec.set_text('')
        b.equinox.set_text('')
        b.tgt_name.set_text('')

        follow_telescope = self.settings.get('follow_telescope', False)
        if not have_telpos:
            follow_telescope = False
            b.follow_telescope.set_enabled(False)
        else:
            b.follow_telescope.set_state(follow_telescope)
        b.follow_telescope.set_tooltip("Set pan position to telescope position")
        b.follow_telescope.add_callback('activated', self.follow_telescope_cb)
        b.get_selected.set_tooltip("Get the coordinates from the selected target in Targets table")
        b.get_selected.add_callback('activated', self.get_selected_target_cb)
        b.get_selected.set_enabled(not follow_telescope)
        b.reset_pan.add_callback('activated', self.reset_pan_cb)
        b.reset_pan.set_tooltip("Center on target position")
        b.mark_target.set_tooltip("Mark the target position")
        b.mark_target.set_state(self.settings['mark_target'])
        b.mark_target.add_callback('activated', self.mark_target_cb)

        self.w.update(b)
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        fr = Widgets.Frame("Image Source")

        captions = (("Source:", 'label', 'image_source', 'combobox',
                     "Size (arcmin):", 'label', 'size', 'spinbutton'),
                    ('__ph1', 'spacer', "Find image", 'button',
                     "Create Blank", 'button', "Load FITS", 'button'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        for name in image_sources.keys():
            b.image_source.append_text(name)
        b.find_image.add_callback('activated', lambda w: self.find_image())

        b.size.set_limits(1, 120, incr_value=1)
        b.size.set_value(self.size[0])
        b.size.add_callback('value-changed', self.set_size_cb)

        b.create_blank.set_tooltip("Create a blank image")
        b.create_blank.add_callback('activated',
                                    lambda w: self.create_blank_image())
        b.load_fits.set_tooltip("Load a FITS image with WCS")
        b.load_fits.add_callback('activated',
                                 lambda w: self.load_fits_image())

        fr = Widgets.Frame("Image Download Info")
        image_info_text = "Please select 'Find image' to find your selected image"
        self.w.select_image_info = Widgets.Label(image_info_text)
        # TODO - Need to find place for 'image download failed' message as
        # error messages aren't thrown from FindImage file

        fr.set_widget(self.w.select_image_info)
        top.add_widget(fr, stretch=0)

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
        # surreptitiously share setting of sky_radius with InsFov plugin
        # so that when they update setting we redraw our plot
        skycam = self.channel.opmon.get_plugin('InsFov')
        skycam.settings.share_settings(self.settings,
                                       keylist=['sky_radius_arcmin'])
        self.settings.get_setting('sky_radius_arcmin').add_callback(
            'set', self.change_skyradius_cb)

        self.viewer.set_color_map(self.settings.get('color_map', 'ds9_cool'))

        # insert canvas, if not already
        p_canvas = self.viewer.get_canvas()
        if self.canvas not in p_canvas:
            p_canvas.add(self.canvas)
        self.canvas.ui_set_active(True)

    def stop(self):
        self.canvas.ui_set_active(False)
        self.gui_up = False
        # remove the canvas from the image
        p_canvas = self.viewer.get_canvas()
        p_canvas.delete_object(self.canvas)

    def get_target(self):
        return self._cur_target

    def redo(self):
        """This is called when a new image arrives or the data in the
        existing image changes.
        """
        tgt = self._cur_target
        if tgt is not None:
            # if we have a target set, then pan to that position
            # since image center may not be that
            image = self.viewer.get_image()
            data_x, data_y = image.radectopix(tgt.ra, tgt.dec)
            self.viewer.set_pan(data_x, data_y)

    def set_size_cb(self, w, val):
        self.size = (val, val)

    def change_skyradius_cb(self, setting, radius_arcmin):
        length = int(np.ceil(radius_arcmin * 2))
        self.size = (length, length)
        if self.gui_up:
            self.w.size.set_value(length)

    def map_arcmin_to_pixels(self, size_arcmin):

        # Clamp the input to the valid range
        size_arcmin = max(3, min(110, size_arcmin))

        # Define ranges
        arcmin_min, arcmin_max = 3, 110
        pixel_min, pixel_max = 1024, 2048

        # Linear interpolation formula
        scale = (size_arcmin - arcmin_min) / (arcmin_max - arcmin_min)
        pixel_count = int(pixel_min + scale * (pixel_max - pixel_min))

        return pixel_count

    def find_image(self):
        try:
            self.fv.assert_gui_thread()
            ra_deg, dec_deg = self.get_radec()
            equinox_str = self.w.equinox.get_text().strip()
            equinox = re.findall('[0-9]+', equinox_str)
            if not equinox:
                equinox = 2000
            else:
                equinox = int(equinox[0])

            # initiate the download
            i_source = self.w.image_source.get_text().strip()
            service_name, survey = i_source.split(":")
            survey = survey.strip()

            arcmin = self.w.size.get_value()

            image_timestamp = datetime.datetime.now()
            image_info_text = "Initiating image download at: " + \
                image_timestamp.strftime("%D %H:%M:%S")
            self.w.select_image_info.set_text(image_info_text)

            self.fv.nongui_do(self.download_image, ra_deg, dec_deg,
                              equinox, service_name, survey, arcmin)

        except Exception as e:
            image_timestamp = datetime.datetime.now()
            image_info_text = "Image download failed at: " + \
                image_timestamp.strftime("%D %H:%M:%S")
            self.w.select_image_info.set_text(image_info_text)
            errmsg = f"failed to find image: {e}"
            self.logger.error(errmsg, exc_info=True)
            self.fv.show_error(errmsg)

    def download_image(self, ra_deg, dec_deg, equinox, service_name,
                       survey, arcmin):
        try:
            self.fv.assert_nongui_thread()

            self.do_download_image(ra_deg, dec_deg, equinox, service_name,
                                   survey, arcmin)

            image_timestamp = datetime.datetime.now()
            image_info_text = "Image download complete, displayed at: " + \
                image_timestamp.strftime("%D %H:%M:%S")
            self.fv.gui_do(self.w.select_image_info.set_text, image_info_text)

        except Exception as e:
            image_timestamp = datetime.datetime.now()
            image_info_text = "Image download failed at: " + \
                image_timestamp.strftime("%D %H:%M:%S")
            self.fv.gui_do(self.w.select_image_info.set_text, image_info_text)
            errmsg = f"failed to find image: {e}"
            self.logger.error(errmsg, exc_info=True)
            self.fv.gui_do(self.fv.show_error, errmsg)

    def do_download_image(self, ra_deg, dec_deg, equinox, service_name,
                          survey, arcmin):
        self.fv.assert_nongui_thread()
        position_deg = f'{ra_deg}+{dec_deg}'

        radius = u.Quantity(arcmin, unit=u.arcmin)
        imscale = size = arcmin / 60.0
        service_name = service_name.strip()
        # service_url = service_urls[service_name]

        img = AstroImage(logger=self.logger)

        self.logger.info(f'service_name={service_name}')

        service = service_name.upper()
        if service == "SKYVIEW":
            self.logger.info(f'service name={service_name}')

            position_deg = f'{ra_deg}+{dec_deg}'
            size = arcmin / 60.0

            equinox_str = f'J{equinox}'

            pixels = self.map_arcmin_to_pixels(arcmin)

            params = {'survey': survey,
                      'coordinates': equinox_str,
                      'position': position_deg,
                      'size': size,
                      'pixels': pixels
                      }

            self.logger.debug(f'Skyview params={params}')

            service_url = service_urls[service_name]
            service_url = service_url.format(**params)
            self.logger.debug(f'SkyView url={service_url}')
            self.fv.gui_do(self.fv.open_uris, [service_url],
                           chname=self.channel.name)

        elif service == "ESO":
            self.logger.debug('ESO...')
            ra_list, dec_list = self.get_radec_list(ra_deg, dec_deg)
            ra = f'{ra_list[0]}%20{ra_list[1]}%20{ra_list[2]}'
            dec = f'{dec_list[0]}%20{dec_list[1]}%20{dec_list[2]}'

            params = {'survey': survey,
                      # options are: J2000 or B1950, but digits only.
                      # e.g. J2000->2000, B1950->1950
                      'equinox': equinox,
                      'ra': ra,
                      'dec': dec,
                      'arcmin': radius.value,
                      }

            service_url = service_urls[service_name]
            service_url = service_url.format(**params)
            self.logger.debug(f'ESO url={service_url}')
            self.fv.gui_do(self.fv.open_uris, [service_url],
                           chname=self.channel.name)

        elif service == "PANSTARRS-1":
            self.logger.debug('Panstarrs 1...')
            panstarrs_filter = survey.strip()

            self.logger.debug(f'Panstarrs1 ra={ra_deg}, dec={dec_deg}, filter={panstarrs_filter}')

            def get_image_table(ra, dec, filters):
                service = "https://ps1images.stsci.edu/cgi-bin/ps1filenames.py"
                url = f"{service}?ra={ra_deg}&dec={dec_deg}&filters={filters}"
                self.logger.debug(f'table url={url}')
                # Read the ASCII table returned by the url
                table = Table.read(url, format='ascii')
                return table

            def get_imurl(ra, dec):

                pixel_arcmin = 240  # 240 pixels/1 arcmin
                size = arcmin * pixel_arcmin
                service_url = service_urls[service_name]
                self.logger.debug(f'url w params={service_url}')

                if panstarrs_filter == 'color':
                    filters = "grizy"
                else:
                    filters = panstarrs_filter

                table = get_image_table(ra, dec, filters)
                self.logger.debug(f'table={table}')

                if panstarrs_filter == 'color':
                    if len(table) < 3:
                        raise ValueError("at least three filters are required for an RGB color image")
                    # If more than 3 filters, pick 3 filters from the availble results

                    params = {'ra': ra, 'dec': dec, 'size': size, 'format': 'jpg'}
                    service_url = service_url.format(**params)

                    if len(table) > 3:
                        table = table[[0, len(table) // 2, len(table) - 1]]
                        # Create the red, green, and blue files for our image
                    for i, param in enumerate(["red", "green", "blue"]):
                        service_url = service_url + f"&{param}={table['filename'][i]}"
                else:
                    params = {'ra': ra, 'dec': dec, 'size': size, 'format': 'fits'}
                    service_url = service_url.format(**params)
                    service_url = service_url + "&red=" + table[0]['filename']

                self.logger.debug(f'service_url={service_url}')
                return service_url

            service_url = get_imurl(ra_deg, dec_deg)

            self.logger.debug(f'Panstarrs1 url={service_url}')
            self.fv.gui_do(self.fv.open_uris, [service_url],
                           chname=self.channel.name)

        elif service == "STSCI":
            self.logger.debug('STScI...')
            equinox = str(int(equinox))
            if equinox == '2000':
                equinox = 'J2000'
            elif equinox == '1950':
                equinox = 'B1950'

            params = {'survey': survey,
                      'ra_deg': ra_deg,
                      'dec_deg': dec_deg,
                      'equinox': equinox,  # J2000 or B1950
                      'arcmin': arcmin,
                      }

            service_url = service_urls[service_name]
            service_url = service_url.format(**params)
            self.logger.debug(f'STScI url={service_url}')
            self.fv.gui_do(self.fv.open_uris, [service_url],
                           chname=self.channel.name)

    def create_blank_image(self):
        self.viewer.onscreen_message("Creating blank field...",
                                     delay=1.0)
        self.fv.update_pending()

        arcmin = self.w.size.get_value()
        fov_deg = arcmin / 60.0
        pa_deg = 0.0
        px_scale = 0.000047

        ra_deg, dec_deg = self.get_radec()
        image = dp.create_blank_image(ra_deg, dec_deg,
                                      fov_deg, px_scale, pa_deg,
                                      cdbase=[-1, 1],
                                      logger=self.logger)
        image.set(nothumb=True, path=None)
        self.viewer.set_image(image)

    def load_fits_image(self):
        self.fv.start_local_plugin(self.chname, "FBrowser")

    def label_image(self):
        image_timestamp = datetime.datetime.now()
        image_info_text = "Image download complete, displayed at: " + \
            image_timestamp.strftime("%D %H:%M:%S")
        self.w.select_image_info.set_text(image_info_text)

        # TODO: add image source
        ra_deg, dec_deg = self.get_radec()
        name = self.w.tgt_name.get_text()

        ra_sgm, dec_sgm = wcs.ra_deg_to_str(ra_deg), wcs.dec_deg_to_str(dec_deg)
        lbl = f"{name} (RA: {ra_sgm} / DEC: {dec_sgm})"
        self.lbl_obj.text = lbl
        self.viewer.redraw(whence=3)

    def get_radec(self):
        try:
            ra_str = self.w.ra.get_text().strip()
            dec_str = self.w.dec.get_text().strip()
            if len(ra_str) == 0 or len(dec_str) == 0:
                self.fv.show_error("Please select a target and click 'Get Selected'")

            ra_deg, dec_deg, eq = spot_target.normalize_ra_dec_equinox(ra_str,
                                                                       dec_str,
                                                                       2000.0)
        except Exception as e:
            self.logger.error(f"error getting coordinate: {e}", exc_info=True)
            self.fv.show_error("Error getting coordinate: please check selected target")

        return (ra_deg, dec_deg)

    def get_radec_list(self, ra_deg, dec_deg):
        ra_sgm, dec_sgm = wcs.ra_deg_to_str(ra_deg), wcs.dec_deg_to_str(dec_deg)
        ra_list, dec_list = ra_sgm.split(':'), dec_sgm.split(':')
        return (ra_list, dec_list)

    def set_pan_pos(self, ra_deg, dec_deg):
        self.fv.assert_gui_thread()
        # Try to set the pan position of the viewer to our location
        try:
            image = self.viewer.get_image()
            if image is not None:
                x, y = image.radectopix(ra_deg, dec_deg)
                self.viewer.set_pan(x, y)

        except Exception as e:
            self.logger.error(f"Could not set pan position: {e}",
                              exc_info=True)

    def telpos_changed_cb(self, cb, status, target):
        self.fv.assert_gui_thread()
        if not self.gui_up or not self.settings.get('follow_telescope', False):
            return
        tel_status = status.tel_status.lower()
        self.logger.info(f"telescope status is '{tel_status}'")
        if tel_status not in ['tracking', 'guiding']:
            # don't do anything unless telescope is stably tracking/guiding
            return

        ra_deg, dec_deg = status.ra_deg, status.dec_deg

        self.logger.info(f"target is {target}")
        if target is None:
            # telescope is not tracking a known target, but may be dithering
            # just change position in window and return
            self.logger.info(f"changing pan position to {ra_deg},{dec_deg}")
            self.set_pan_pos(ra_deg, dec_deg)
        elif target is self._cur_target:
            self.logger.info(f"changing pan position to {ra_deg},{dec_deg}")
            self.set_pan_pos(ra_deg, dec_deg)
        else:
            # <-- moved to a different known target
            # set target info and try to download the image
            self._cur_target = target
            self.set_pointing(target.ra, target.dec, target.equinox, target.name)
            self.plot_target()
            self.find_image()

    def get_selected_target_cb(self, w):
        if self.settings.get('follow_telescope', False):
            # target is following telescope
            self.fv.show_error("uncheck 'Follow telescope' to get selection")
            return

        selected = self.targets.get_selected_targets()
        if len(selected) != 1:
            self.fv.show_error("Please select exactly one target in the Targets table!")
            return
        tgt = list(selected)[0]
        self._cur_target = tgt
        self.set_pointing(tgt.ra, tgt.dec, tgt.equinox, tgt.name)

        self.plot_target()

    def mark_target_cb(self, w, tf):
        self.settings.set(mark_target=tf)
        self.plot_target()

    def follow_telescope_cb(self, w, tf):
        self.settings.set(follow_telescope=tf)
        self.w.get_selected.set_enabled(not tf)

    def reset_pan_cb(self, w):
        if self._cur_target is None:
            return

        ra_deg, dec_deg = self._cur_target.ra, self._cur_target.dec
        self.viewer.set_pan(ra_deg, dec_deg, coord='wcs')

    def site_changed_cb(self, cb, site_obj):
        self.logger.debug("site has changed")
        self.site = site_obj
        # TODO: not sure how to alter plot for site changing
        # probably need to signal that non-sidereal targets are inaccurate

    def time_changed_cb(self, cb, time_utc, cur_tz):
        self.dt_utc = time_utc
        self.cur_tz = cur_tz
        if not self.gui_up:
            return

        if (self._last_tgt_update_dt is None or
            abs((self.dt_utc - self._last_tgt_update_dt).total_seconds()) >
            self.settings.get('targets_update_interval')):
            self.logger.info("updating targets")
            self._last_tgt_update_dt = time_utc
            self.plot_target()

    def set_pointing(self, ra_deg, dec_deg, equinox, tgt_name):
        if not self.gui_up:
            return
        self.w.ra.set_text(wcs.ra_deg_to_str(ra_deg))
        self.w.dec.set_text(wcs.dec_deg_to_str(dec_deg))
        self.w.equinox.set_text(str(equinox))
        self.w.tgt_name.set_text(tgt_name)

    def plot_target(self):
        self.canvas.delete_object_by_tag('target')

        image = self.viewer.get_image()
        if image is None:
            return

        tgt = self._cur_target
        if not self.settings.get('mark_target', False) or tgt is None:
            return
        name = tgt.name

        scale = self.get_scale()
        pt_radius = max(5, min(scale * 10, 30))
        cl_radius = pt_radius * 2
        color = tgt.get('color', 'seagreen2')
        alpha = 1.0
        objs = []

        if tgt.get('nonsidereal', False):
            # <-- non-sidereal target.  We will show the track annotated
            # with dates/times
            track = tgt.get('track', None)
            if track is None:
                raise ValueError("nonsidereal target does not contain a tracking table")

            # update current target position, if necessary
            spot_target.update_nonsidereal_targets([tgt], self.dt_utc)

            # mark track with a path
            coord = np.array((track['RA'], track['DEC'])).T
            pts = image.wcs.wcspt_to_datapt(coord)
            path = self.dc.Path(pts, color=color, linewidth=2, alpha=alpha)
            path.pickable = True
            path.add_callback('pick-enter', self._show_time, tgt)
            objs.append(path)

            x1, y1 = pts[0]
            x2, y2 = pts[-1]
            # convoluted way of trying to find a consistently spaced set
            # of points annotating the track
            path_len = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            path_len_px = path_len * self.viewer.get_scale()
            # as length of track becomes shorter, skip size should increase
            skip = max(5, int(1 / (path_len_px / len(pts)) * 10))

            # find range of view and don't plot annotations outside of that
            (x_min, y_min, x_max, y_max) = self.viewer.get_data_rect()
            ann_pts = np.array([i for i in range(0, len(track), skip)
                                if x_min < pts[i][0] < x_max and
                                y_min < pts[i][1] < y_max], dtype=int)

            dt = track['DateTime'][0]
            tzname = dt.tzinfo.tzname(dt)
            plot_local_time = self.settings.get('nonsidereal_plot_local_time',
                                                False)
            # figure out angles to plot text so that it doesn't obscure
            cur_rot_deg = self.viewer.get_rotation()
            m = (y2 - y1) / (x2 - x1)   # find slope
            ang = np.arctan(-1 / m)
            _c, _s = np.cos(ang), np.sin(ang)
            l = pt_radius * 0.5  # length of perpendicular lines
            ang_deg = np.degrees(ang)
            flip_x, flip_y, swap_xy = self.viewer.get_transforms()
            ll = l
            if flip_x:
                ang_deg = -ang_deg
                ll = -l
            text_rot_deg = cur_rot_deg + ang_deg
            k = 5
            for j, i in enumerate(ann_pts):
                x, y = pts[i]
                objs.append(self.dc.Line(x + l * _c, y + l * _s,
                                         x - l * _c, y - l * _s,
                                         color=color, linewidth=1, alpha=alpha))
                if j % k == 0:
                    # label the time every Kth element
                    dt = track['DateTime'][i]
                    if plot_local_time:
                        dt = dt.astimezone(self.cur_tz)
                        tzname = self.cur_tz.tzname(dt)
                    text = dt.strftime("%m-%d %H:%M " + tzname)
                    objs.append(self.dc.Text(x + ll * _c, y + ll * _s,
                                             text=text,
                                             rot_deg=text_rot_deg,
                                             color=color, alpha=alpha,
                                             font="Roboto condensed bold",
                                             fontscale=True,
                                             fontsize=None, fontsize_min=8,
                                             fontsize_max=12))
            if not (track['DateTime'][0] < self.dt_utc < track['DateTime'][-1]):
                # signal that target is out of time range
                color = 'orangered2'

        x, y = image.radectopix(tgt.ra, tgt.dec)
        point = self.dc.Point(x, y, radius=pt_radius,
                              style='cross',
                              color=color, fillcolor=color,
                              linewidth=2, alpha=alpha,
                              fill=False)
        objs.append(point)
        circle = self.dc.Circle(x, y, cl_radius, color=color,
                                linewidth=1, alpha=alpha,
                                fill=False)
        objs.append(circle)
        text = self.dc.Text(x, y + cl_radius, name,
                            color=color, alpha=alpha,
                            font="Roboto condensed bold",
                            fontscale=True,
                            fontsize=None, fontsize_min=12,
                            fontsize_max=16)
        objs.append(text)

        star = self.dc.CompoundObject(*objs)
        star.opaque = False
        #star.pickable = False
        self.canvas.add(star, tag='target', redraw=True)

    def _show_time(self, path, canvas, event, pt, tgt):
        # TODO: show tooltip with time, ra, dec
        pass

    def get_scale(self):
        v_scale = self.viewer.get_scale()
        image = self.viewer.get_image()
        if image is None:
            scale = 1.0
            return scale

        header = image.get_header()
        # get scale of image in deg/pix
        rot, iscale_dim1, iscale_dim2 = wcs.get_rotation_and_scale(header,
                                                                   skew_threshold=0.1)
        # adjust by viewer scale
        scale = max(iscale_dim1, iscale_dim2) / v_scale
        return scale

    def redraw_cb(self, setting, scale):
        if not self.gui_up:
            return

        # scale, pan or rotation has changed--need to redraw our overlay
        self.plot_target()

    def __str__(self):
        return 'findimage'
