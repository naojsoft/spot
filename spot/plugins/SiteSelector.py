"""
SiteSelector.py -- Select observing position

E. Jeschke

Requirements
============

naojsoft packages
-----------------
- ginga
"""
# stdlib
import os.path
from datetime import datetime
from dateutil import tz, parser

# ginga
from ginga.gw import Widgets, GwHelp
from ginga import GingaPlugin
from ginga.misc.Callback import Callbacks
from ginga.util.paths import ginga_home

# 3rd party
import yaml

# local
from spot.util import sites

# where our config files are stored
from spot import __file__
cfgdir = os.path.join(os.path.dirname(__file__), 'config')


class SiteSelector(GingaPlugin.LocalPlugin):

    def __init__(self, fv, fitsimage):
        super().__init__(fv, fitsimage)

        # get SiteSelector preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_SiteSelector')
        self.settings.add_defaults(default_site=None,
                                   timer_update_interval=1.0)
        self.settings.load(onError='silent')

        self.cb = Callbacks()
        for name in ['site-changed', 'time-changed']:
            self.cb.enable_callback(name)

        # see if user has a custom list of sites
        path = os.path.join(ginga_home, "sites.yml")
        if not os.path.exists(path):
            # open stock list of sites
            path = os.path.join(cfgdir, "sites.yml")

        # configure sites
        with open(path, 'r') as site_f:
            sites.configure_sites(yaml.safe_load(site_f))

        default_site = self.settings.get('default_site', None)
        if default_site is None:
            default_site = sites.get_site_names()[0]
        self.site_obj = sites.get_site(default_site)
        self.site_obj.initialize()
        self.status = self.site_obj.get_status()

        self.time_mode = 'now'
        self.cur_tz = tz.tzoffset(self.status.timezone_name,
                                  self.status.timezone_offset_min * 60)
        self.dt_utc = datetime.now(tz=tz.UTC)

        self.tmr = GwHelp.Timer(duration=self.settings['timer_update_interval'])
        self.tmr.add_callback('expired', self.update_timer_cb)

        self.gui_up = False

    def build_gui(self, container):

        top = Widgets.VBox()
        top.set_border_width(4)

        fr = Widgets.Frame("Observing Location")
        captions = (("Site:", 'label', 'site', 'combobox'),
                    )
        w, b = Widgets.build_info(captions)
        self.w = b
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        for site_name in sites.get_site_names():
            b.site.insert_alpha(site_name)
        b.site.set_text(self.site_obj.name)
        b.site.add_callback('activated', self.site_changed_cb)

        fr = Widgets.Frame("Time")

        vbox = Widgets.VBox()
        captions = (("Time mode:", 'llabel', "mode", 'combobox'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)

        for name in 'Now', 'Fixed':
            b.mode.append_text(name)
        b.mode.set_index(0)
        b.mode.set_tooltip("Now or fixed time for visibility calculations")
        b.mode.add_callback('activated', self.set_datetime_cb)
        vbox.add_widget(w, stretch=0)

        captions = (("Date time:", 'llabel', 'datetime', 'entryset'),
                    ("UTC offset (min):", 'llabel', 'timeoff', 'entryset'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)
        b.datetime.set_tooltip("Set date time for visibility calculations")
        b.datetime.add_callback('activated', self.set_datetime_cb)
        b.datetime.set_enabled(False)
        b.timeoff.set_text(str(self.status.timezone_offset_min))
        b.timeoff.set_tooltip("UTC offset for setting fixed time")
        b.timeoff.set_enabled(False)
        b.timeoff.add_callback('activated', self.set_timeoff_cb)
        self.set_datetime_cb()
        vbox.add_widget(w, stretch=0)

        fr.set_widget(vbox)
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
        self.update_timer_cb(self.tmr)

    def stop(self):
        self.gui_up = False

    def get_site(self):
        return self.site_obj

    def get_status(self):
        return self.status

    def get_datetime(self):
        return (self.dt_utc, self.cur_tz)

    def site_changed_cb(self, w, idx):
        self.site_obj = sites.get_site(w.get_text())
        self.site_obj.initialize()
        self.status = self.site_obj.get_status()

        # change time zone to be that of the site
        zone_off_min = self.status.timezone_offset_min
        self.w.timeoff.set_text(str(zone_off_min))
        self.cur_tz = tz.tzoffset(self.status.timezone_name,
                                  zone_off_min * 60)
        self._set_datetime()
        self.cb.make_callback('site-changed', self.site_obj)

    def update_timer_cb(self, timer):
        timer.start()

        # get any updated status from the site
        self.status.update(self.site_obj.fetch_status())

        if self.time_mode == 'now':
            self.dt_utc = datetime.now(tz=tz.UTC)
            dt = self.dt_utc.astimezone(self.cur_tz)
            if self.gui_up:
                self.w.datetime.set_text(dt.strftime("%Y-%m-%d %H:%M:%S"))

            self.cb.make_callback('time-changed', self.dt_utc, self.cur_tz)

    def set_timeoff_cb(self, w):
        zone_off_min = int(w.get_text().strip())
        self.cur_tz = tz.tzoffset('Custom', zone_off_min * 60)

        self._set_datetime()

    def set_datetime_cb(self, *args):
        self.time_mode = self.w.mode.get_text().lower()
        self._set_datetime()

    def _set_datetime(self):
        if self.time_mode == 'now':
            self.dt_utc = datetime.now(tz=tz.UTC)
            dt = self.dt_utc.astimezone(self.cur_tz)
            self.w.datetime.set_text(dt.strftime("%Y-%m-%d %H:%M:%S"))
            self.w.datetime.set_enabled(False)
            self.w.timeoff.set_enabled(False)
        else:
            self.w.datetime.set_enabled(True)
            self.w.timeoff.set_enabled(True)
            dt_str = self.w.datetime.get_text().strip()
            dt = parser.parse(dt_str).replace(tzinfo=self.cur_tz)
            self.dt_utc = dt.astimezone(tz.UTC)

        #self.site_obj.observer.set_date(self.dt_utc)

        self.logger.info("date/time set to: {}".format(self.dt_utc.strftime("%Y-%m-%d %H:%M:%S %z")))
        self.cb.make_callback('time-changed', self.dt_utc, self.cur_tz)

    def __str__(self):
        return 'siteselector'
