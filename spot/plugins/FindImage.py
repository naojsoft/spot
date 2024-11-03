"""
FindImage.py -- Download images matching a target

J. Merchant

Requirements
============

naojsoft packages
-----------------
- ginga
"""
import numpy as np
import datetime
import re

from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.skyview import SkyView
#from astroquery.sdss import SDSS
from astropy.table import Table

# ginga
from ginga.gw import Widgets, GwHelp
from ginga import GingaPlugin
from ginga.util import wcs, catalog, dp
from ginga.AstroImage import AstroImage

from spot.util.target import normalize_ra_dec_equinox

image_sources = {
    'SkyView: DSS1 Blue': dict(),
    'SkyView: DSS1 Red': dict(),
    'SkyView: DSS2 Red': dict(),
    'SkyView: DSS2 Blue': dict(),
    'SkyView: DSS2 IR': dict(),
    'SkyView: SDSSg': dict(),
    'SkyView: SDSSi': dict(),
    'SkyView: SDSSr': dict(),
    'SkyView: SDSSu': dict(),
    'SkyView: SDSSz': dict(),
    'SkyView: 2MASS-J': dict(),
    'SkyView: 2MASS-H': dict(),
    'SkyView: 2MASS-K': dict(),
    'SkyView: WISE 3.4': dict(),
    'SkyView: WISE 4.6': dict(),
    'SkyView: WISE 12': dict(),
    'SkyView: WISE 22': dict(),
    'SkyView: AKARI N60': dict(),
    'SkyView: AKARI WIDE-S': dict(),
    'SkyView: AKARI WIDE-L': dict(),
    'SkyView: AKARI N160': dict(),
    'SkyView: NVSS': dict(),
    'SkyView: GALEX Near UV': dict(),
    'SkyView: GALEX Far UV': dict(),
    'ESO: DSS1': dict(),
    'ESO: DSS2-red': dict(),
    'ESO: DSS2-blue': dict(),
    'ESO: DSS2-infrared': dict(),
    # 'PanSTARRS-1: color': dict(),
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
    #'SDSS: 17': dict(),
}

service_urls = {
    'ESO': """https://archive.eso.org/dss/dss?ra={ra}&dec={dec}&mime-type=application/x-fits&x={arcmin}&y={arcmin}&Sky-Survey={survey}&equinox={equinox}""",
    'STScI': """https://archive.stsci.edu/cgi-bin/dss_search?v={survey}&r={ra_deg}&d={dec_deg}&e={equinox}&h={arcmin}&w={arcmin}&f=fits&c=none&fov=NONE&v3=""",
    'PanSTARRS-1': """https://ps1images.stsci.edu/cgi-bin/fitscut.cgi?ra={ra}&dec={dec}&size={size}&format={format}&output_size=1024"""
}

# replaced with astroquery
# 'SkyView': """https://skyview.gsfc.nasa.gov/cgi-bin/images?Survey={survey}&coordinates={coordinates}&position={position}&imscale={imscale}&size={size}&Return=FITS""",
# 'SDSS-DR16': """https://skyserver.sdss.org/dr16/SkyServerWS/ImgCutout/getjpeg?ra={ra_deg}&dec={dec_deg}&scale=0.4&height={size}&width={size}""",
# 'SDSS-DR7': """https://skyservice.pha.jhu.edu/DR7/ImgCutout/getjpeg.aspx?ra={ra_deg}&dec={dec_deg}&scale=0.39612%20%20%20&width={size}&height={size}"""


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
              area updated by the telescope's actual position (the
              "Lock Target" checkbox must be unchecked to allow the
              coordinates to be updated).  Further, the image in the
              finding viewer will be panned according to the telescope's
              current position, allowing you to follow a dithering pattern
              (for example).

    Loading an image from an image source
    -------------------------------------
    Once RA/DEC coordinates are displayed in the "Pointing" area, an image
    can be downloaded using the controls in the "Image Source" area.
    Choose an image source from the drop-down control labeled "Source",
    select a size (in arcminutes) using the "Size" control and click the
    "Find Image" button.  It may take a little while for the image to be
    downloaded and displayed in the finder viewer.

    .. note:: Alternatively, you can click "Create Blank" to create a blank
              image with a WCS set to the desired location.  This may
              possibly be useful if an image source is not available.

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
                                   telescope_update_interval=3.0,
                                   color_map='ds9_cool')
        self.settings.load(onError='silent')

        self.viewer = self.fitsimage
        self.dc = fv.get_draw_classes()
        canvas = self.dc.DrawingCanvas()
        canvas.set_surface(self.viewer)
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

        self.size = (3, 3)

        self.sitesel = None
        self.targets = None
        self.tmr = GwHelp.Timer(duration=self.settings['telescope_update_interval'])
        self.tmr.add_callback('expired', self.update_tel_timer_cb)
        self.gui_up = False

    def build_gui(self, container):

        if not self.chname.endswith('_FIND'):
            raise Exception(f"This plugin is not designed to run in channel {self.chname}")

        wsname, _ = self.channel.name.split('_')
        channel = self.fv.get_channel(wsname + '_TGTS')
        self.sitesel = channel.opmon.get_plugin('SiteSelector')
        self.targets = channel.opmon.get_plugin('Targets')

        top = Widgets.VBox()
        top.set_border_width(4)

        fr = Widgets.Frame("Image Source")

        captions = (('Source:', 'label', 'image_source', 'combobox',
                     'Size (arcmin):', 'label', 'size', 'spinbutton'),
                    ('__ph1', 'spacer', 'Find image', 'button'),
                    ('__ph2', 'spacer', 'Create Blank', 'button'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        for name in image_sources.keys():
            b.image_source.append_text(name)
        b.find_image.add_callback('activated', self.find_image_cb)

        b.size.set_limits(1, 120, incr_value=1)
        b.size.set_value(self.size[0])
        b.size.add_callback('value-changed', self.set_size_cb)

        b.create_blank.set_tooltip("Create a blank image")
        b.create_blank.add_callback('activated',
                                    lambda w: self.create_blank_image())

        fr = Widgets.Frame("Pointing")

        captions = (('RA:', 'label', 'ra', 'llabel', 'DEC:', 'label',
                     'dec', 'llabel'),
                    ('Equinox:', 'label', 'equinox', 'llabel',
                     'Name:', 'label', 'tgt_name', 'llabel'),
                    ('Get Selected', 'button', 'Lock Target', 'checkbox',
                     '__ph4', 'spacer', "Follow telescope", 'checkbox')
                    )

        w, b = Widgets.build_info(captions)
        b.ra.set_text('')
        b.dec.set_text('')
        b.equinox.set_text('')
        b.tgt_name.set_text('')
        b.get_selected.set_tooltip("Get the coordinates from the selected target in Targets table")
        b.get_selected.add_callback('activated', self.get_selected_target_cb)
        b.lock_target.set_tooltip("Lock target from changing by selections in 'Targets'")
        b.follow_telescope.set_tooltip("Set pan position to telescope position")
        b.follow_telescope.set_state(self.settings['follow_telescope'])
        self.w.update(b)
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

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
        self.canvas.ui_set_active(False)

        self.update_tel_timer_cb(self.tmr)

    def stop(self):
        self.tmr.stop()
        self.gui_up = False
        # remove the canvas from the image
        p_canvas = self.viewer.get_canvas()
        p_canvas.delete_object(self.canvas)

    def redo(self):
        """This is called when a new image arrives or the data in the
        existing image changes.
        """
        pass

    def set_size_cb(self, w, val):
        self.size = (val, val)

    def change_skyradius_cb(self, setting, radius_arcmin):
        radius = int(np.ceil(radius_arcmin) * 1.5)
        self.size = (radius, radius)
        if self.gui_up:
            self.w.size.set_value(radius)

    def find_image_cb(self, w):
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

            sv = SkyView()

            position = SkyCoord(ra=ra_deg * u.degree, dec=dec_deg * u.degree)
            radius = u.Quantity(arcmin, unit=u.arcmin)

            self.logger.info(f'position={position}, survey={survey}, radius={radius}')

            im_lst = sv.get_image_list(position=position,
                                       survey=[survey],
                                       radius=radius)
            self.logger.debug(f'im_lst={im_lst}')
            service_url = list(im_lst)[0]
            self.logger.debug(f'SkyView url={service_url}')
            self.fv.gui_do(self.fv.open_uris, [service_url],
                           chname=self.channel.name)

        # elif service == "SDSS":
        #     position = SkyCoord(ra=ra_deg * u.degree, dec=dec_deg * u.degree)
        #     radius = u.Quantity(arcmin, unit=u.arcmin)

        #     self.logger.info(f'position={position}, survey={survey}, radius={radius}')

        #     im_tbl = SDSS.query_region(coordinates=position,
        #                                radius=radius,
        #                                spectro=False,
        #                                data_release=int(survey))

        #     # TBD

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
        self.fitsimage.onscreen_message("Creating blank field...",
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
        self.fitsimage.set_image(image)

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
        self.fitsimage.redraw(whence=3)

    def get_radec(self):
        try:
            ra_str = self.w.ra.get_text().strip()
            dec_str = self.w.dec.get_text().strip()
            if len(ra_str) == 0 or len(dec_str) == 0:
                self.fv.show_error("Please select a target and click 'Get Selected'")

            ra_deg, dec_deg, eq = normalize_ra_dec_equinox(ra_str, dec_str,
                                                           2000.0)
        except Exception as e:
            self.logger.error(f"error getting coordinate: {e}", exc_info=True)
            self.fv.show_error("Error getting coordinate: please check selected target")

        return (ra_deg, dec_deg)

    def get_radec_list(self, ra_deg, dec_deg):
        ra_sgm, dec_sgm = wcs.ra_deg_to_str(ra_deg), wcs.dec_deg_to_str(dec_deg)
        ra_list, dec_list = ra_sgm.split(':'), dec_sgm.split(':')
        return (ra_list, dec_list)

    def update_info(self, status):
        self.fv.assert_gui_thread()
        if self.w.follow_telescope.get_state():
            if not self.w.lock_target.get_state():
                try:
                    self.w.ra.set_text(wcs.ra_deg_to_str(status.ra_deg))
                    self.w.dec.set_text(wcs.dec_deg_to_str(status.dec_deg))
                    self.w.equinox.set_text(str(status.equinox))

                except Exception as e:
                    self.logger.error(f"error updating info: {e}", exc_info=True)

            # Try to set the pan position of the viewer to our location
            try:
                image = self.viewer.get_image()
                if image is not None:
                    x, y = image.radectopix(status.ra_deg, status.dec_deg)
                    self.viewer.set_pan(x, y)

            except Exception as e:
                self.logger.error(f"Could not set pan position: {e}",
                                  exc_info=True)

    def update_tel_timer_cb(self, timer):
        timer.start()

        status = self.sitesel.get_status()

        if self.gui_up:
            self.fv.gui_do(self.update_info, status)

    def get_selected_target_cb(self, w):
        if self.w.lock_target.get_state():
            # target is locked
            self.fv.show_error("existing target is locked--uncheck 'Lock Target' ?")
            return

        selected = self.targets.get_selected_targets()
        if len(selected) != 1:
            self.fv.show_error("Please select exactly one target in the Targets table!")
            return
        tgt = list(selected)[0]
        self.w.ra.set_text(wcs.ra_deg_to_str(tgt.ra))
        self.w.dec.set_text(wcs.dec_deg_to_str(tgt.dec))
        self.w.equinox.set_text(str(tgt.equinox))
        self.w.tgt_name.set_text(tgt.name)

    def __str__(self):
        return 'findimage'
