"""
RotCalc.py -- Rotation check and calculator

Requirements
============

naojsoft packages
-----------------
- g2cam
- ginga
"""
from datetime import timedelta
import os

import numpy as np

# ginga
from ginga.gw import Widgets, GwHelp
from ginga.misc import Bunch
from ginga import GingaPlugin
from ginga.util import wcs

# local
from spot.util import calcpos
from spot.util.rot import calc_rotation_choices

# spot
#from spot.util.polar import subaru_normalize_az

default_report = os.path.join(os.path.expanduser('~'), "rot_report.csv")


class RotCalc(GingaPlugin.LocalPlugin):

    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super().__init__(fv, fitsimage)

        # get preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_RotCalc')
        self.settings.add_defaults(telescope_update_interval=3.0,
                                   default_report=default_report)
        self.settings.load(onError='silent')

        self.viewer = self.fitsimage

        self.columns = [('Time', 'time'),
                        ('Name', 'name'),
                        ('PA', 'pa_deg'),
                        ('Rot cur', 'rot_cur_deg'),
                        ('Rot1 start', 'rot1_start_deg'),
                        ('Rot1 stop', 'rot1_stop_deg'),
                        ('Rot2 start', 'rot2_start_deg'),
                        ('Rot2 stop', 'rot2_stop_deg'),
                        ('Min Rot Move', 'min_rot_move'),
                        ('Max Rot Time', 'max_rot_time'),
                        ('Rot Chosen', 'rot_chosen'),
                        ('RA', 'ra_str'),
                        ('DEC', 'dec_str'),
                        ('Cur Az', 'az_cur_deg'),
                        ('Az1 start', 'az1_start_deg'),
                        ('Az1 stop', 'az1_stop_deg'),
                        ('Az2 start', 'az2_start_deg'),
                        ('Az2 stop', 'az2_stop_deg'),
                        ('Alt', 'alt_deg'),
                        ('Min Az Move', 'min_az_move'),
                        ('Max Az Time', 'max_az_time'),
                        ('Chosen Az', 'az_chosen'),
                        ]
        self.rot_deg = 0.0
        self.rot_cmd_deg = 0.0
        self.az_deg = 0.0
        self.az_cmd_deg = 0.0
        self.rot_limits = (-174, 174)
        self.az_limits = (-270, 270)
        self.pa_deg = 0.0
        self.time_sec = 15 * 60
        self.tbl_dct = dict()
        self.time_str = None
        self.tgt_locked = False
        self._autosave = False
        # these are set via callbacks from the SiteSelector plugin
        self.site = None
        self.dt_utc = None
        self.cur_tz = None
        self.gui_up = False

        self.tmr = GwHelp.Timer(duration=self.settings['telescope_update_interval'])
        self.tmr.add_callback('expired', self.update_tel_timer_cb)

    def build_gui(self, container):

        # initialize site and date/time/tz
        obj = self.channel.opmon.get_plugin('SiteSelector')
        self.site = obj.get_site()
        obj.cb.add_callback('site-changed', self.site_changed_cb)
        self.dt_utc, self.cur_tz = obj.get_datetime()
        obj.cb.add_callback('time-changed', self.time_changed_cb)

        targets = self.channel.opmon.get_plugin('Targets')
        targets.cb.add_callback('tagged-changed', self.target_selection_cb)

        top = Widgets.VBox()
        top.set_border_width(4)

        fr = Widgets.Frame("Current Rot / Az")
        captions = (('Cur Rot:', 'label', 'cur_rot', 'llabel',
                     'Cmd Rot:', 'label', 'cmd_rot', 'llabel',
                     'Cur Az:', 'label', 'cur_az', 'llabel',
                     'Cmd Az:', 'label', 'cmd_az', 'llabel'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        fr = Widgets.Frame("PA / Time /Az El")

        captions = (('PA (deg):', 'label', 'pa', 'entryset',
                     'Time (sec):', 'label', 'secs', 'entryset'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)

        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        b.pa.set_text("0.00")
        b.pa.add_callback('activated', self.set_pa_cb)
        b.pa.set_tooltip("Set desired position angle")
        b.secs.set_text("{}".format(15 * 60.0))
        b.secs.add_callback('activated', self.set_time_cb)
        b.secs.set_tooltip("Number of seconds on target")

        fr = Widgets.Frame("Pointing")

        captions = (('RA:', 'label', 'ra', 'entry', 'DEC:', 'label',
                     'dec', 'entry',  # ),
                     #('Equinox:', 'label', 'equinox', 'entry',
                     'Name:', 'label', 'tgt_name', 'entry'),
                    ('__ph1', 'spacer', 'Setup', 'button',
                     '__ph2', 'spacer', 'Record', 'button',
                     '__ph3', 'spacer', 'Lock Target', 'checkbox',
                     "Send Target", 'button')
                    )

        w, b = Widgets.build_info(captions)
        b.lock_target.set_tooltip("Lock target from changing by selections in 'Targets'")
        b.lock_target.set_state(self.tgt_locked)
        b.lock_target.add_callback('activated', self._lock_target_cb)
        b.setup.add_callback('activated', lambda w: self.setup())
        b.record.add_callback('activated', lambda w: self.record())
        b.record.set_enabled(False)
        b.send_target.add_callback('activated', self.send_target_cb)
        b.send_target.set_tooltip("Send the target coordinates to Gen2")
        self.w.update(b)
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        self.w.rot_tbl = Widgets.TreeView(auto_expand=True,
                                          selection='single',
                                          sortable=True,
                                          use_alt_row_color=True)
        self.w.rot_tbl.setup_table(self.columns, 1, 'time')
        top.add_widget(self.w.rot_tbl, stretch=1)

        self.w.rot_tbl.set_optimal_column_widths()

        #top.add_widget(Widgets.Label(''), stretch=1)

        fr = Widgets.Frame("Report")

        captions = (('File:', 'label', 'filename', 'entry',
                     'Save', 'button', 'Auto Save', 'checkbox'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)
        b.save.add_callback('activated', self.save_report_cb)
        b.auto_save.set_state(self._autosave)
        b.auto_save.add_callback('activated', self.autosave_cb)
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

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
        self.update_tel_timer_cb(self.tmr)

    def stop(self):
        self.tmr.cancel()
        self.gui_up = False

    def setup(self):
        if self.time_str is not None:
            self.cancel()
            return
        self.time_str = self.dt_utc.astimezone(self.cur_tz).strftime("%H:%M:%S")
        name = self.w.tgt_name.get_text().strip()
        ra_str = self.w.ra.get_text().strip()
        dec_str = self.w.dec.get_text().strip()

        ra_deg = wcs.hmsStrToDeg(ra_str)
        dec_deg = wcs.dmsStrToDeg(dec_str)
        equinox = 2000.0
        body = calcpos.Body(name, ra_deg, dec_deg, equinox)

        cres_start = body.calc(self.site.observer, self.dt_utc)
        cres_stop = body.calc(self.site.observer,
                              self.dt_utc + timedelta(seconds=self.time_sec))
        res = calc_rotation_choices(cres_start, cres_stop, self.pa_deg)

        # calculate which rotator position requires less time to achieve
        rot_mov1 = self.rot_deg - res.rot1_start_deg
        rot_mov2 = self.rot_deg - res.rot2_start_deg
        min_rot_move = res.rot1_start_deg if abs(rot_mov1) < abs(rot_mov2) \
            else res.rot2_start_deg

        # calculate which rotator position gives the most time
        if not (self.rot_limits[0] <= res.rot1_start_deg <= self.rot_limits[1]):
            tot1_deg = -1
        else:
            if res.rot1_start_deg < res.rot1_stop_deg:
                tot1_deg = abs(self.rot_limits[1] - res.rot1_start_deg)
            else:
                tot1_deg = abs(self.rot_limits[0] - res.rot1_start_deg)

        if not (self.rot_limits[0] <= res.rot2_start_deg <= self.rot_limits[1]):
            tot2_deg = -1
        else:
            if res.rot2_start_deg < res.rot2_stop_deg:
                tot2_deg = abs(self.rot_limits[1] - res.rot2_start_deg)
            else:
                tot2_deg = abs(self.rot_limits[0] - res.rot2_start_deg)

        if tot1_deg < 0:
            if tot2_deg < 0:
                max_rot_time = -9999
            else:
                max_rot_time = res.rot2_start_deg
        else:
            if tot2_deg < 0:
                max_rot_time = res.rot1_start_deg
            else:
                max_rot_time = res.rot1_start_deg \
                    if tot1_deg < tot2_deg else res.rot2_start_deg

        res2 = self.normalize_az(res)

        # calculate which azimuth position requires less time to achieve
        az_mov1 = self.az_deg - res2.az1_start_deg
        az_mov2 = self.az_deg - res2.az2_start_deg
        min_az_move = res2.az1_start_deg if abs(az_mov1) < abs(az_mov2) \
            else res2.az2_start_deg

        # calculate which rotator position gives the most time
        if not (self.az_limits[0] <= res2.az1_start_deg <= self.az_limits[1]):
            tot1_deg = -1
        else:
            if res2.az1_start_deg < res2.az1_stop_deg:
                tot1_deg = abs(self.az_limits[1] - res2.az1_start_deg)
            else:
                tot1_deg = abs(self.az_limits[0] - res2.az1_start_deg)

        if not (self.az_limits[0] <= res2.az2_start_deg <= self.az_limits[1]):
            tot2_deg = -1
        else:
            if res2.az2_start_deg < res2.az2_stop_deg:
                tot2_deg = abs(self.az_limits[1] - res2.az2_start_deg)
            else:
                tot2_deg = abs(self.az_limits[0] - res2.az2_start_deg)

        if tot1_deg < 0:
            if tot2_deg < 0:
                max_az_time = -9999
            else:
                max_az_time = res2.az2_start_deg
        else:
            if tot2_deg < 0:
                max_az_time = res2.az1_start_deg
            else:
                max_az_time = res2.az1_start_deg \
                    if tot1_deg < tot2_deg else res2.az2_start_deg

        self.tbl_dct[self.time_str] = dict(time=self.time_str, name=name,
                                           ra_str=ra_str, dec_str=dec_str,
                                           pa_deg=("%.1f" % self.pa_deg),
                                           rot_cur_deg=("%.1f" % self.rot_deg),
                                           rot1_start_deg=("%.1f" % res.rot1_start_deg),
                                           rot1_stop_deg=("%.1f" % res.rot1_stop_deg),
                                           rot2_start_deg=("%.1f" % res.rot2_start_deg),
                                           rot2_stop_deg=("%.1f" % res.rot2_stop_deg),
                                           min_rot_move=("%.1f" % min_rot_move),
                                           max_rot_time=("%.1f" % max_rot_time),
                                           rot_chosen=("%.1f" % -9999),
                                           az_cur_deg=("%.1f" % self.az_deg),
                                           az1_start_deg=("%.1f" % res2.az1_start_deg),
                                           az1_stop_deg=("%.1f" % res2.az1_stop_deg),
                                           az2_start_deg=("%.1f" % res2.az2_start_deg),
                                           az2_stop_deg=("%.1f" % res2.az2_stop_deg),
                                           alt_deg=("%.1f" % res.alt_start_deg),
                                           min_az_move=("%.1f" % min_az_move),
                                           max_az_time=("%.1f" % max_az_time),
                                           az_chosen=("%.1f" % -9999),
                                           )
        self.w.rot_tbl.set_tree(self.tbl_dct)
        self.w.setup.set_text("Cancel")
        self.w.record.set_enabled(True)

    def record(self):
        if self.time_str is None:
            self.fv.show_error("Please set up a target")
            return
        self.tbl_dct[self.time_str]['rot_chosen'] = ("%.1f" % self.rot_cmd_deg)
        self.tbl_dct[self.time_str]['az_chosen'] = ("%.1f" % self.az_cmd_deg)
        self.w.rot_tbl.set_tree(self.tbl_dct)
        self.time_str = None
        self.w.setup.set_text("Setup")
        self.w.record.set_enabled(False)

        if self._autosave:
            self.save_report_cb(self.w.save)

    def cancel(self):
        if self.time_str is not None:
            if self.time_str in self.tbl_dct:
                del self.tbl_dct[self.time_str]
            self.time_str = None
        self.w.rot_tbl.set_tree(self.tbl_dct)
        self.w.setup.set_text("Setup")
        self.w.record.set_enabled(False)

    def set_pa_cb(self, w):
        self.pa_deg = float(w.get_text().strip())

    def set_time_cb(self, w):
        self.time_sec = float(w.get_text().strip())

    def target_selection_cb(self, cb, targets):
        if len(targets) == 0:
            return
        tgt = next(iter(targets))
        if self.gui_up:
            if self.tgt_locked:
                # target is locked
                self.logger.info("target is locked")
                return
            self.w.ra.set_text(wcs.ra_deg_to_str(tgt.ra))
            self.w.dec.set_text(wcs.dec_deg_to_str(tgt.dec))
            #self.w.equinox.set_text(str(tgt.equinox))
            self.w.tgt_name.set_text(tgt.name)

    def send_target_cb(self, w):
        ra_deg = wcs.hmsStrToDeg(self.w.ra.get_text())
        dec_deg = wcs.dmsStrToDeg(self.w.dec.get_text())
        ra_soss = wcs.ra_deg_to_str(ra_deg, format='%02d%02d%02d.%03d')
        dec_soss = wcs.dec_deg_to_str(dec_deg, format='%s%02d%02d%02d.%02d')
        equinox = 2000.0
        status_dict = {"GEN2.SPOT.RA": ra_soss,
                       "GEN2.SPOT.DEC": dec_soss,
                       "GEN2.SPOT.EQUINOX": equinox}
        try:
            obj = self.fv.gpmon.get_plugin('Gen2Int')
            obj.send_status(status_dict)

        except Exception as e:
            errmsg = f"Failed to send status: {e}"
            self.fv.show_error(errmsg)
            self.logger.error(errmsg, exc_info=True)

    def _lock_target_cb(self, w, tf):
        self.tgt_locked = tf

    def site_changed_cb(self, cb, site_obj):
        self.logger.debug("site has changed")
        self.site = site_obj

    def time_changed_cb(self, cb, time_utc, cur_tz):
        self.dt_utc = time_utc
        self.cur_tz = cur_tz

    def update_status(self, status):
        self.rot_deg = status.rot_deg
        self.rot_cmd_deg = status.rot_cmd_deg
        self.az_deg = status.az_deg
        self.az_cmd_deg = status.az_cmd_deg

        if self.gui_up:
            self.w.cur_az.set_text("%.2f" % self.az_deg)
            self.w.cmd_az.set_text("%.2f" % self.az_cmd_deg)
            self.w.cur_rot.set_text("%.2f" % self.rot_deg)
            self.w.cmd_rot.set_text("%.2f" % self.rot_cmd_deg)

    def normalize_az(self, res):
        new_res = Bunch.Bunch(az1_start_deg=subaru_normalize_az(res.az1_start_deg),
                              az1_stop_deg=subaru_normalize_az(res.az1_stop_deg),
                              az2_start_deg=subaru_normalize_az(res.az2_start_deg),
                              az2_stop_deg=subaru_normalize_az(res.az2_stop_deg))
        return new_res

    def update_tel_timer_cb(self, timer):
        timer.start()

        obj = self.channel.opmon.get_plugin('SiteSelector')
        status = obj.get_status()

        self.update_status(status)

    def save_report(self, filepath):
        if len(self.tbl_dct) == 0:
            return

        try:
            import pandas as pd
        except ImportError:
            self.fv.show_error("Please install 'pandas' and "
                               "'openpyxl' to use this feature")
            return

        try:
            self.logger.info("writing table: {}".format(filepath))

            col_hdr = [colname for colname, key in self.columns]
            rows = [list(d.values()) for d in self.tbl_dct.values()]
            df = pd.DataFrame(rows, columns=col_hdr)

            if filepath.endswith('.csv'):
                df.to_csv(filepath, index=False, header=True)

            else:
                df.to_excel(filepath, index=False, header=True)

        except Exception as e:
            self.logger.error("Error writing table: {}".format(e),
                              exc_info=True)

    def save_report_cb(self, w):
        filepath = self.w.filename.get_text().strip()
        if len(filepath) == 0:
            filepath = self.settings.get('default_report')
            self.w.filename.set_text(filepath)

        self.save_report(filepath)

    def autosave_cb(self, w, tf):
        self._autosave = tf

    def __str__(self):
        return 'rotcalc'


def subaru_normalize_az(az_deg, normalize_angle=True):
    div = 360.0 if az_deg >= 0.0 else -360.0
    az_deg = az_deg + 180.0
    if normalize_angle:
        az_deg = np.remainder(az_deg, div)

    return az_deg
