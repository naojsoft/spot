"""
TargetGenerator.py -- Target Generator

Requirements
============

naojsoft packages
-----------------
- g2cam
- ginga
"""
import numpy as np
import pandas as pd

# ginga
from ginga.gw import Widgets
from ginga import GingaPlugin
from ginga.util import wcs


class TargetGenerator(GingaPlugin.LocalPlugin):
    """
    TargetGenerator
    ===============
    TargetGenerator allows you to generate an RA/DEC target from an AZ/EL
    location.

    .. note:: Make sure you have the "Targets" plugin also open, as it is
              used in conjunction with this plugin.

    Generating a Target
    -------------------
    Simply type in an azimuth into the "Az:" box and an elevation into the
    "El:" box.  If desired, type a name to distinguish the target into the
    "Name:" box (otherwise a generic name will be used).

    Press "Gen Target" to generate a target.  It will show up in the targets
    table in the "Targets" plugin.  Select it there to see it in the "PolarSky"
    plot.
    """
    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super().__init__(fv, fitsimage)

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

        fr = Widgets.Frame("Target Generator")

        captions = (('Az:', 'label', 'az', 'entry', 'El:', 'label',
                     'el', 'entry', "Name:", 'label',
                     'choose_name', 'entry', "Gen Target", 'button'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)

        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        b.gen_target.set_tooltip("Generate a target from AZ/EL at given time")
        b.gen_target.add_callback('activated', self.azel_to_radec_cb)
        b.gen_target.set_tooltip("Generate a target from AZ/EL at given time")

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
        equinox = 2000.0
        name = self.w.choose_name.get_text().strip()
        if len(name) == 0:
            name = f"ra={ra_deg:.2f},dec={dec_deg:.2f}"

        tgt_df = pd.DataFrame([(name, ra_deg, dec_deg, equinox)],
                              columns=["Name", "RA", "DEC", "Equinox"])
        obj = self.channel.opmon.get_plugin('Targets')
        obj.add_targets("Targets", tgt_df, merge=True)

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
