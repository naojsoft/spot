"""
Settings.py -- Overlay objects on all sky camera

E. Jeschke

Requirements
============
python packages
---------------

naojsoft packages
-----------------
- g2cam
- ginga
- qplan
- oscript
"""
# stdlib
import time
from datetime import datetime
import dateutil.parser
from dateutil import tz

# ginga
from ginga.gw import Widgets, GwHelp
from ginga import GingaPlugin

# qplan
from qplan.util.calcpos import Observer


class Settings(GingaPlugin.LocalPlugin):

    def __init__(self, fv, fitsimage):
        super().__init__(fv, fitsimage)

        # get preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_Settings')
        self.settings.add_defaults(targets_update_interval=60.0)
        self.settings.load(onError='silent')

        self.site = Observer('Subaru',
                             longitude='-155:28:48.900',
                             latitude='+19:49:42.600',
                             elevation=4163,
                             pressure=615,
                             temperature=0,
                             timezone=tz.gettz('US/Hawaii'))

        self.mode = 0   # 0: now, 1: set time
        self.last_targets_update = 0.0
        self.last_saved_dt = None

        self.tmr = GwHelp.Timer(duration=1.0)
        self.tmr.add_callback('expired', self.update_time_cb)

        self.gui_up = False
        self.tmr.start()

    def build_gui(self, container):

        top = Widgets.VBox()
        top.set_border_width(4)

        captions = (('Mode', 'combobox',
                     'Date:', 'label', 'Date', 'entryset',
                     'Time:', 'label', 'Time', 'entryset'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b

        for option in ["Now", "Set time"]:
            b.mode.append_text(option)
        b.mode.set_index(self.mode)
        b.mode.add_callback('activated', self.set_mode_cb)
        b.date.add_callback('activated', lambda w: self.set_date_time_cb())
        b.time.add_callback('activated', lambda w: self.set_date_time_cb())
        if self.mode == 0:
            self.w.date.set_enabled(False)
            self.w.time.set_enabled(False)

        top.add_widget(w, stretch=0)
        top.add_widget(Widgets.Label(''), stretch=1)

        btns = Widgets.HBox()
        btns.set_border_width(4)
        btns.set_spacing(3)

        btn = Widgets.Button("Close")
        btn.add_callback('activated', lambda w: self.close())
        btns.add_widget(btn, stretch=0)
        btn = Widgets.Button("Help")
        #btn.add_callback('activated', lambda w: self.help())
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

    def redo(self):
        pass

    def get_datetime(self):
        return self.site.date

    def update_time_cb(self, timer):
        timer.start()

        self.update_time()

        t = time.time()
        if t - self.last_targets_update > self.settings['targets_update_interval']:
            self.last_targets_update = t
            self.update_externals()

    def update_externals(self):
        obj = self.channel.opmon.get_plugin('Targets')
        obj.update_all()

    def update_time(self):
        if self.mode != 0:
            return
        dt = datetime.now(tz=self.site.timezone)
        self.site.set_date(dt)
        if not self.gui_up:
            return
        self.w.date.set_text(dt.strftime("%Y-%m-%d"))
        self.w.time.set_text(dt.strftime("%H:%M:%S"))

    def set_date_time_cb(self):
        date_s = self.w.date.get_text()
        time_s = self.w.time.get_text()
        dt = dateutil.parser.parse(f"{date_s} {time_s}")
        dt = dt.replace(tzinfo=self.site.tz_local)
        print("parsed date is", dt.strftime("%Y-%m-%d %H:%M:%S"))
        self.last_saved_dt = dt
        self.site.set_date(dt)
        print("site date is", self.site.date.strftime("%Y-%m-%d %H:%M:%S"))

        self.update_externals()

    def set_mode_cb(self, w, idx):
        print('mode', idx)
        self.mode = idx
        if idx == 0:
            self.w.date.set_enabled(False)
            self.w.time.set_enabled(False)
            self.update_time()

            self.update_externals()
        else:
            self.w.date.set_enabled(True)
            self.w.time.set_enabled(True)
            dt = self.last_saved_dt
            if dt is not None:
                self.w.date.set_text(dt.strftime("%Y-%m-%d"))
                self.w.time.set_text(dt.strftime("%H:%M:%S"))

            self.set_date_time_cb()

    def p2r(self, r, t):
        # TODO: take into account fisheye distortion
        t_rad = np.radians(t)

        #cx, cy = self.settings['image_center']
        cx, cy = 0.0, 0.0
        scale = self.get_scale()

        x = cx + r * np.cos(t_rad) * scale
        y = cy + r * np.sin(t_rad) * scale

        return (x, y)

    def r2xyr(self, r):
        # TODO: take into account fisheye distortion
        #cx, cy = self.settings['image_center']
        cx, cy = 0.0, 0.0
        r = r * self.get_scale()
        return (cx, cy, r)

    def get_scale(self):
        obj = self.channel.opmon.get_plugin('PolarSky')
        scale = obj.get_scale()
        return scale

    def map_azalt(self, az, alt):
        #az = subaru_normalize_az(az)
        return az + 90.0, 90.0 - alt

    def __str__(self):
        return 'settings'
