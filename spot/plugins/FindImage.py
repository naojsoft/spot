"""
FindImage.py -- Download images matching a target

E. Jeschke
T. Inagaki
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

import tempfile

from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.skyview import SkyView
from astroquery.sdss import SDSS

# ginga
from ginga.gw import Widgets, GwHelp
from ginga import GingaPlugin, trcalc
from ginga.util import wcs, catalog, dp

from ginga.AstroImage import AstroImage

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
    'SkyView: AKAIR N60': dict(),
    'SkyView: AKAIR WIDE-S': dict(),
    'SkyView: AKAIR WIDE-L': dict(),
    'SkyView: AKAIR N160': dict(),
    'SkyView: NAVSS': dict(),
    'SkyView: GALEX Near UV': dict(),
    'SkyView: GALEX Far UV': dict(),
    'ESO: DSS1': dict(),
    'ESO: DSS2-red': dict(),
    'ESO: DSS2-blue': dict(),
    'ESO: DSS2-infrared': dict(),
    'PanSTARRS-1: color': dict(),
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
    'SDSS: 17': dict(),
    }

service_urls = {
    'ESO': """https://archive.eso.org/dss/dss?ra={ra}&dec={dec}&mime-type=application/x-fits&x={arcmin}&y={arcmin}&Sky-Survey={survey}&equinox={equinox}""",
    'PanSTARRS-1':  """http://ps1images.stsci.edu/cgi-bin/ps1cutouts?pos={pos}&filter={filter}&filetypes=stack&auxiliary=data&size={size}&output_size=1024&verbose=0&autoscale=99.500000&catlist=""",
    'STScI': """https://archive.stsci.edu/cgi-bin/dss_search?v={survey}&r={ra_deg}&d={dec_deg}&e={equinox}&h={arcmin}&w={arcmin}&f=fits&c=none&fov=NONE&v3=""",
}

# replaced with astroquery
# 'SkyView': """https://skyview.gsfc.nasa.gov/cgi-bin/images?Survey={survey}&coordinates={coordinates}&position={position}&imscale={imscale}&size={size}&Return=FITS""",
# 'SDSS-DR16': """https://skyserver.sdss.org/dr16/SkyServerWS/ImgCutout/getjpeg?ra={ra_deg}&dec={dec_deg}&scale=0.4&height={size}&width={size}""",
# 'SDSS-DR7': """https://skyservice.pha.jhu.edu/DR7/ImgCutout/getjpeg.aspx?ra={ra_deg}&dec={dec_deg}&scale=0.39612%20%20%20&width={size}&height={size}"""


class FindImage(GingaPlugin.LocalPlugin):

    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super().__init__(fv, fitsimage)

        # get FOV preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_FindImage')
        self.settings.add_defaults(name_sources=catalog.default_name_sources)
        self.settings.load(onError='silent')

        self.viewer = self.fitsimage
        self.dc = fv.get_draw_classes()
        canvas = self.dc.DrawingCanvas()
        canvas.set_surface(self.viewer)
        self.canvas = canvas

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

        self.gui_up = False

    def build_gui(self, container):

        wsname, _ = self.channel.name.split('_')
        channel = self.fv.get_channel(wsname + '_TGTS')
        targets = channel.opmon.get_plugin('Targets')
        targets.cb.add_callback('selection-changed', self.target_selection_cb)

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
        # b.image_source.add_callback('activated', self.select_source_cb)
        b.find_image.add_callback('activated', self.find_image_cb)

        b.size.set_limits(1, 120, incr_value=1)
        b.size.set_value(3)
        b.size.add_callback('value-changed', self.set_size_cb)

        b.create_blank.set_tooltip("Create a blank image")
        b.create_blank.add_callback('activated',
                                    lambda w: self.create_blank_image())

        fr = Widgets.Frame("Pointing")

        captions = (('RA:', 'label', 'ra', 'entry', 'DEC:', 'label',
                     'dec', 'entry'),
                    ('Equinox:', 'label', 'equinox', 'entry'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        # name resolver
        vbox = Widgets.VBox()
        fr = Widgets.Frame(" Name Server ")
        fr.set_widget(vbox)

        captions = (('Server:', 'llabel', 'server', 'combobox',
                     '_x1', 'spacer'),
                    ('Name:', 'llabel', 'Name', 'entry',
                     'Search name', 'button')
                    )
        w, b = Widgets.build_info(captions)
        self.w.update(b)
        b.search_name.add_callback('activated', lambda w: self.getname_cb())
        b.search_name.set_tooltip("Lookup name and populate ra/dec coordinates")
        vbox.add_widget(w, stretch=0)

        combobox = b.server
        index = 0
        self.name_server_options = list(self.fv.imgsrv.get_server_names(
            kind='name'))
        for name in self.name_server_options:
            combobox.append_text(name)
            index += 1
        index = 0
        if len(self.name_server_options) > 0:
            combobox.set_index(index)
        combobox.set_tooltip("Choose the object name resolver")

        top.add_widget(fr, stretch=0)

        fr = Widgets.Frame("Image Download Info")
        image_info_text = "Please select 'Find image' to find your selected image"
        self.w.select_image_info = Widgets.Label(image_info_text)
        # TODO - Need to find place for 'image download failed' message as
        # error messages aren't thrown from FindImage file

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
        # insert canvas, if not already
        p_canvas = self.viewer.get_canvas()
        if self.canvas not in p_canvas:
            p_canvas.add(self.canvas)

        self.resume()

    def pause(self):
        self.canvas.ui_set_active(False)

    def resume(self):
        self.canvas.ui_set_active(True, viewer=self.viewer)

    def stop(self):
        self.gui_up = False
        # remove the canvas from the image
        p_canvas = self.viewer.get_canvas()
        p_canvas.delete_object(self.canvas)

    def redo(self):
        """This is called when a new image arrives or the data in the
        existing image changes.
        """
        pass

    def select_source_cb(self, w, idx):
        pass

    def set_size_cb(self, w, val):
        self.size = (val, val)

    def find_image_cb(self, w):
        try:
            image_timestamp = datetime.datetime.now()
            image_info_text = "Initiating image download at: "+(
                               image_timestamp.strftime("%D %H:%M:%S"))
            self.w.select_image_info.set_text(image_info_text)
            self.download_image()
        except Exception as e:
            image_timestamp = datetime.datetime.now()
            image_info_text = "Image download failed at: "+(
                               image_timestamp.strftime("%D %H:%M:%S"))
            self.w.select_image_info.set_text(image_info_text)
            self.logger.error("failed to find image: {}"
                              .format(e), exc_info=True)

    def download_image(self):
        ra_deg, dec_deg = self.get_radec()

        # initiate the download
        i_source = self.w.image_source.get_text().strip()
        service_name, survey = i_source.split(":")
        survey = survey.strip()

        arcmin = self.w.size.get_value()

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

            ra_deg, dec_deg = self.get_radec()
            position = SkyCoord(ra=ra_deg*u.degree, dec=dec_deg*u.degree)
            radius = u.Quantity(arcmin, unit=u.arcmin)

            self.logger.info(f'position={position}, survey={survey}, radius={radius}')

            im = sv.get_images(position=position,
                               survey=[survey],
                               radius=radius)
            self.logger.info(f'im={im}')

            tmp_file = tempfile.mktemp()
            self.logger.info(f'loading SkyView image. file={tmp_file}')
            im[0].writeto(tmp_file, overwrite=True)
            self.fv.load_file(tmp_file, chname=self.channel.name)

            image_timestamp = datetime.datetime.now()
            image_info_text = "Image download complete, displayed at: "+(
                               image_timestamp.strftime("%D %H:%M:%S"))
            self.w.select_image_info.set_text(image_info_text)

        elif service == "SDSS":
            ra_deg, dec_deg = self.get_radec()
            position = SkyCoord(ra=ra_deg*u.degree, dec=dec_deg*u.degree)
            radius = u.Quantity(arcmin, unit=u.arcmin)

            self.logger.info(f'position={position}, survey={survey}, radius={radius}')

            im = SDSS.get_images(coordinates=position,
                                 radius=radius,
                                 data_release=int(survey))
            tmp_file = tempfile.mktemp()
            self.logger.info(f'loading SDSS image. file={tmp_file}')
            im[0].writeto(tmp_file, overwrite=True)
            self.fv.load_file(tmp_file, chname=self.channel.name)

            image_timestamp = datetime.datetime.now()
            image_info_text = "Image download complete, displayed at: "+(
                               image_timestamp.strftime("%D %H:%M:%S"))
            self.w.select_image_info.set_text(image_info_text)

            return

        elif service == "ESO":
            self.logger.debug('ESO...')
            ra_list, dec_list = self.get_radec_list()
            ra = f'{ra_list[0]}%20{ra_list[1]}%20{ra_list[2]}'
            dec = f'{dec_list[0]}%20{dec_list[1]}%20{dec_list[2]}'

            equinox_str = self.w.equinox.get_text().strip()
            equinox = re.findall('[0-9]+', equinox_str)

            if not equinox:
                equinox = 2000
            else:
                equinox = equinox[0]

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
            self.fv.open_uris([service_url], chname=self.channel.name)

            image_timestamp = datetime.datetime.now()
            image_info_text = "Image download complete, displayed at: "+(
                               image_timestamp.strftime("%D %H:%M:%S"))
            self.w.select_image_info.set_text(image_info_text)

        elif service == "PANSTARRS-1":
            self.logger.debug('Panstarrs 1...')
            ra_list, dec_list = self.get_radec_list()

            if ra_list[0].startswith("+"):
                ra_list[0] = ra_list[0][1:]

            pos = f'{ra_list[0]}%3A{ra_list[1]}%3A{ra_list[2]}+{dec_list[0]}%3A{dec_list[1]}%3A{dec_list[2]}'

            pixel_arcmin = 240  # 240 pixels/1 arcmin
            size = arcmin * pixel_arcmin
            params = {'filter': survey,
                      'pos': pos,
                      'size': size,
                      }

            service_url = service_urls[service_name]
            service_url = service_url.format(**params)
            self.logger.debug(f'Panstarrs1 url={service_url}')
            self.fv.open_uris([service_url], chname=self.channel.name)

            image_timestamp = datetime.datetime.now()
            image_info_text = "Image download complete, displayed at: "+(
                               image_timestamp.strftime("%D %H:%M:%S"))
            self.w.select_image_info.set_text(image_info_text)

        elif service == "STSCI":
            self.logger.debug('STScI...')
            ra_deg, dec_deg = self.get_radec()
            equinox = self.w.equinox.get_text().strip()

            params = {'survey': survey,
                      'ra_deg': ra_deg,
                      'dec_deg': dec_deg,
                      'equinox': equinox,  # J2000 or B1950
                      'arcmin': arcmin,
                      }

            service_url = service_urls[service_name]
            service_url = service_url.format(**params)
            self.logger.debug(f'STScI url={service_url}')
            self.fv.open_uris([service_url], chname=self.channel.name)

            image_timestamp = datetime.datetime.now()
            image_info_text = "Image download complete, displayed at: "+(
                               image_timestamp.strftime("%D %H:%M:%S"))
            self.w.select_image_info.set_text(image_info_text)

    def create_blank_image(self):
        self.fitsimage.onscreen_message("Creating blank field...",
                                        delay=1.0)
        self.fv.update_pending()

        fov_deg = 0.01
        pa_deg = 0.0
        px_scale = 0.000047

        ra_deg, dec_deg = self.get_radec()
        image = dp.create_blank_image(ra_deg, dec_deg,
                                      fov_deg, px_scale, pa_deg,
                                      cdbase=[-1, 1],
                                      logger=self.logger)
        image.set(nothumb=True)
        self.fitsimage.set_image(image)

    def get_radec(self):
        ra_str = self.w.ra.get_text().strip()
        dec_str = self.w.dec.get_text().strip()

        if ':' in ra_str:
            from ginga.util import wcs
            ra_deg = wcs.hmsStrToDeg(ra_str)
            dec_deg = wcs.dmsStrToDeg(dec_str)
        else:
            from oscript.util import ope
            ra_deg = ope.funkyHMStoDeg(ra_str)
            dec_deg = ope.funkyDMStoDeg(dec_str)

        return (ra_deg, dec_deg)

    def get_radec_list(self):
        ra_str = self.w.ra.get_text().strip()
        dec_str = self.w.dec.get_text().strip()

        if ':' in ra_str:
            ra_list = ra_str.split(':')
            dec_list = dec_str.split(':')
        else:
            # SOSS format
            ra_list = [ra_str[:2], ra_str[2:4], ra_str[4:]]
            dec_list = [dec_str[:2], dec_str[2:4], dec_str[4:]]

        return (ra_list, dec_list)

    def getname_cb(self):
        name = self.w.name.get_text().strip()
        server = self.w.server.get_text()

        try:
            srvbank = self.fv.get_server_bank()
            namesvc = srvbank.get_name_server(server)
            self.logger.info("looking up name '{}' at {}".format(name, server))

            ra_str, dec_str = namesvc.search(name)

            # populate the image server UI coordinate
            self.w.ra.set_text(ra_str)
            self.w.dec.set_text(dec_str)

        except Exception as e:
            errmsg = "Name service query exception: %s" % (str(e))
            self.logger.error(errmsg, exc_info=True)
            # pop up the error in the GUI under "Errors" tab
            self.fv.gui_do(self.fv.show_error, errmsg)

    def target_selection_cb(self, cb, targets):
        if len(targets) == 0:
            return
        tgt = next(iter(targets))
        if self.gui_up:
            self.w.ra.set_text(tgt.ra)
            self.w.dec.set_text(tgt.dec)
            self.w.equinox.set_text(str(tgt.equinox))

    def __str__(self):
        return 'findimage'
