"""
TargetGenerator.py -- Target Generator

Requirements
============

naojsoft packages
-----------------
- ginga
"""
from datetime import UTC
from dateutil.parser import parse as parse_date
import numpy as np
import pandas as pd

import astropy.units as u
from astroquery.jplhorizons import Horizons

# ginga
from ginga.gw import Widgets
from ginga import GingaPlugin
from ginga.util import wcs

from spot.util import target as spot_target


class TargetGenerator(GingaPlugin.LocalPlugin):
    """
    ++++++++++++++++
    Target Generator
    ++++++++++++++++

    TargetGenerator allows you to generate a target dynamically in one of
    several ways.  The target can then be added to the "Targets" plugin
    table.

    .. note:: Make sure you have the "Targets" plugin also open, as it is
              used in conjunction with this plugin.

    Generating a Target from Azimuth/Elevation
    ==========================================

    Simply type in an azimuth into the "Az:" box and an elevation into the
    "El:" box.  Click "Gen Target" to have the AZ/EL coordinates converted
    into RA/DEC coordinates using the set time of the Site.  This will
    populate the "RA", "DEC", "Equinox" and "Name" boxes in the next section.
    From there you can add the target as described in the next section.

    Generating a Target from Known Coordinates
    ==========================================

    If RA/DEC coordinates are known, they can be typed into the boxes labeled
    "RA", "DEC", "Equinox" and "Name".  The values can be given in sexigesimal
    notation or degrees.

    .. note:: "SOSS notation" can also be used if you have the "oscript"
              package installed.

    Click "Add Target" to add the target.  It will show up in the targets
    table in the "Targets" plugin.  Select it there in the usual way to see
    it in the "PolarSky" or "Visibility" plots.

    Looking up a Target from a Name Server
    ======================================

    A target can be looked up via a name server (NED or SIMBAD) using the
    controls in the third area.  Simply select your name server from the
    drop down box labeled "Server", type a name into the "Name" box and
    click "Search name".  If the object is found it will populate the
    boxes labeled "RA", "DEC", "Equinox" and "Name" in the second section.
    From there you can add the target by clicking the "Add Target" button.
    """
    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super().__init__(fv, fitsimage)

        if not self.chname.endswith('_TGTS'):
            return

        # get preferences
        # prefs = self.fv.get_preferences()
        # self.settings = prefs.create_category('plugin_TargetGenerator')
        # self.settings.add_defaults()
        # self.settings.load(onError='silent')

        self.viewer = self.fitsimage

        # these are set via callbacks from the SiteSelector plugin
        self.site = None
        self.dt_utc = None
        self.cur_tz = None
        self.az_offset = 0.0
        self.gui_up = False

    def build_gui(self, container):

        if not self.chname.endswith('_TGTS'):
            raise Exception(f"This plugin is not designed to run in channel {self.chname}")

        # initialize site and date/time/tz
        obj = self.channel.opmon.get_plugin('SiteSelector')
        self.site = obj.get_site()
        obj.cb.add_callback('site-changed', self.site_changed_cb)
        self.dt_utc, self.cur_tz = obj.get_datetime()
        obj.cb.add_callback('time-changed', self.time_changed_cb)

        self.az_offset = 0.0
        status = obj.get_status()
        if status['azimuth_start_direction'] == 'S':
            self.az_offset = 180.0

        top = Widgets.VBox()
        top.set_border_width(4)

        fr = Widgets.Frame("From Azimuth/Elevation")

        captions = (('Az:', 'label', 'az', 'entry', 'El:', 'label',
                     'el', 'entry', "Gen Target", 'button'),
                    )
        w, b = Widgets.build_info(captions)
        self.w.update(b)

        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        b.gen_target.set_tooltip("Generate a target from AZ/EL at given time")
        b.gen_target.add_callback('activated', self.azel_to_radec_cb)

        fr = Widgets.Frame("From RA/DEC Coordinate")

        captions = (('RA:', 'label', 'ra', 'entry', 'DEC:', 'label',
                     'dec', 'entry'),
                    ('Equinox:', 'label', 'equinox', 'entry',
                     'Name:', 'label', 'tgt_name', 'entry'),
                    ('sp1', 'spacer', 'sp2', 'spacer', 'sp3', 'spacer',
                     'Add Target', 'button'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)
        b.add_target.add_callback('activated', self.add_target_cb)
        b.add_target.set_tooltip("Add target to the target list")
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        # name resolver
        vbox = Widgets.VBox()
        fr = Widgets.Frame("From Name Server")
        fr.set_widget(vbox)

        captions = (('Server:', 'llabel', 'server', 'combobox',
                     '_x1', 'spacer'),
                    ('Name:', 'llabel', 'obj_name', 'entry',
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

        fr = Widgets.Frame("JPL Horizons (Non-sidereal)")

        captions = (('Name:', 'label', 'ns_name', 'entry'),
                    ('Start time:', 'label', 'ns_start', 'entry',
                     'Stop time:', 'label', 'ns_stop', 'entry'),
                    ('Step:', 'label', 'ns_step', 'entry',
                     'Lookup name', 'button'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)
        b.ns_name.set_tooltip("Name or code as known to JPL Horizons")
        b.ns_start.set_tooltip("Start time of observation (YYYY-MM-DD HH:MM:SS) in OBSERVER's time")
        b.ns_stop.set_tooltip("Stop time of observation (YYYY-MM-DD HH:MM:SS) in OBSERVER's time")
        b.ns_step.set_text("Step time of observation")
        b.ns_step.set_text('1m')
        b.lookup_name.add_callback('activated', self.get_nonsidereal_cb)
        b.lookup_name.set_tooltip("Lookup non-sidereal target at JPL Horizons")
        fr.set_widget(w)
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
        pass

    def stop(self):
        self.gui_up = False

    def azel_to_radec_cb(self, w):
        az_deg = float(self.w.az.get_text())
        el_deg = float(self.w.el.get_text())
        az_deg = self.adjust_az(az_deg)
        ra_deg, dec_deg = self.site.observer.radec_of(az_deg, el_deg,
                                                      date=self.dt_utc)
        # TODO
        equinox = 2000.0
        self.w.ra.set_text(wcs.ra_deg_to_str(ra_deg))
        self.w.dec.set_text(wcs.dec_deg_to_str(dec_deg))
        self.w.equinox.set_text(str(equinox))
        self.w.tgt_name.set_text(f"ra={ra_deg:.2f},dec={dec_deg:.2f}")

    def getname_cb(self):
        name = self.w.obj_name.get_text().strip()
        server = self.w.server.get_text()

        srvbank = self.fv.get_server_bank()
        namesvc = srvbank.get_name_server(server)

        self.fv.nongui_do(self._getname_bg, name, server, namesvc)

    def _getname_bg(self, name, server, namesvc):
        self.fv.assert_nongui_thread()
        try:
            self.logger.info("looking up name '{}' at {}".format(name, server))

            ra_str, dec_str = namesvc.search(name)

            def _update_gui():
                # populate the image server UI coordinate
                self.w.ra.set_text(ra_str)
                self.w.dec.set_text(dec_str)
                self.w.equinox.set_text('2000.0')  # ??!!
                self.w.tgt_name.set_text(name)

            self.fv.gui_do(_update_gui)

        except Exception as e:
            errmsg = "Name service query exception: %s" % (str(e))
            self.logger.error(errmsg, exc_info=True)
            # pop up the error in the GUI under "Errors" tab
            self.fv.gui_do(self.fv.show_error, errmsg)

    def get_radec_eq(self):
        ra_str = self.w.ra.get_text().strip()
        dec_str = self.w.dec.get_text().strip()
        eq_str = self.w.equinox.get_text().strip()

        ra_deg, dec_deg, equinox = spot_target.normalize_ra_dec_equinox(ra_str,
                                                                        dec_str,
                                                                        eq_str)
        return (ra_deg, dec_deg, equinox)

    def add_target_cb(self, w):
        name = self.w.tgt_name.get_text().strip()
        ra_deg, dec_deg, equinox = self.get_radec_eq()
        if len(name) == 0:
            name = f"ra={ra_deg:.2f},dec={dec_deg:.2f}"
        tgt_df = pd.DataFrame([(name, ra_deg, dec_deg, equinox, True)],
                              columns=["Name", "RA", "DEC", "Equinox", "IsRef"])
        obj = self.channel.opmon.get_plugin('Targets')
        obj.add_targets("Targets", tgt_df, merge=True)

    def get_nonsidereal_cb(self, w):
        # prepare location and epochs as astroquery/JPL Horizons wants them
        status = self.site.get_status()
        location = dict(lat=status['latitude_deg'] * u.deg,
                        lon=status['longitude_deg'] * u.deg,
                        elevation=status['elevation_m'] * u.m)

        try:
            name = self.w.ns_name.get_text().strip()

            dt_start = parse_date(self.w.ns_start.get_text().strip())
            if dt_start.tzinfo is None:
                dt_start = dt_start.replace(tzinfo=self.cur_tz)
            dt_start = dt_start.astimezone(UTC)

            dt_stop = parse_date(self.w.ns_stop.get_text().strip())
            if dt_stop.tzinfo is None:
                dt_stop = dt_stop.replace(tzinfo=self.cur_tz)
            dt_stop = dt_stop.astimezone(UTC)

            step = self.w.ns_step.get_text().strip()

            # Don't add timezone info to 'stop' element or query fails
            epochs = dict(start=dt_start.strftime('%Y-%m-%d %H:%M:%S UT'),
                          stop=dt_stop.strftime('%Y-%m-%d %H:%M:%S'),
                          step=step)

            obj = Horizons(id=name, location=location, epochs=epochs)
            # returns an astropy Table
            eph_tbl = obj.ephemerides()

            obj = self.channel.opmon.get_plugin('Targets')
            obj.process_eph_table_for_target(name, eph_tbl)

        except Exception as e:
            errmsg = f"Exception looking up name '{name}': {e}"
            self.logger.error(errmsg, exc_info=True)
            self.fv.show_error(errmsg)

    def site_changed_cb(self, cb, site_obj):
        self.logger.debug("site has changed")
        self.site = site_obj

        obj = self.channel.opmon.get_plugin('SiteSelector')
        status = obj.get_status()
        if status['azimuth_start_direction'] == 'S':
            self.az_offset = 180.0
        else:
            self.az_offset = 0.0

    def time_changed_cb(self, cb, time_utc, cur_tz):
        self.dt_utc = time_utc
        self.cur_tz = cur_tz

    def adjust_az(self, az_deg, normalize_angle=True):
        div = 360.0 if az_deg >= 0.0 else -360.0
        az_deg = az_deg - self.az_offset
        if normalize_angle:
            az_deg = np.remainder(az_deg, div)

        return az_deg

    def __str__(self):
        return 'targetgenerator'
