"""
LGS.py -- Laser Tracking Control System plugin

Plugin Type: Local
==================

``LGS`` is a local plugin, which means it is associated with a channel.
An instance can be opened for each channel.

Usage
=====
``LGS`` is normally used in conjunction with the plugins ``Sites``,
``PolarSky``, ``Targets`` and ``Visibility``.

Requirements
============
python packages
---------------
matplotlib

naojsoft packages
-----------------
- ginga
"""
# stdlib
import os
import glob
from datetime import timedelta

import numpy as np

# ginga
from ginga.gw import Widgets
from ginga import GingaPlugin
from ginga.util.paths import home

from spot.util import pamsat, calcpos
from spot.util.target import Target


# default folder for loading satellite window/closure files
default_pam_dir = os.path.join(home, 'Procedure', 'LGS', 'PAM')


class LGS(GingaPlugin.LocalPlugin):
    """TODO
    """
    def __init__(self, fv, fitsimage):
        super().__init__(fv, fitsimage)

        # get preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_LGS')
        self.settings.add_defaults(pam_dir=default_pam_dir,
                                   pad_sec=0, min_delta_arcsec=600.0)
        self.settings.load(onError='silent')

        self.pam_dir = self.settings.get('pam_dir', default_pam_dir)
        # the files currently loaded
        self.pam_filenames = []
        # time (sec) to pad open/close windows
        self.pad_sec = self.settings.get('pad_sec', 0.0)
        # minimum distance from tracking to be considered the "same target"
        # (in arcsec)
        self.min_delta_arcsec = self.settings.get('min_delta_arcsec', 600.0)

        # references to other plugins
        self.visplot = None
        self.targets = None
        # PAM target information
        self.tgt_dict = dict()
        self.tgts_radec = []
        self.mbody_radec = None
        self._cur_target = None
        self._windows = None
        # these are set in callbacks
        self.site_obj = None
        self.dt_utc = None
        self.cur_tz = None

        self.tmr_replot = self.fv.make_timer()
        self.tmr_replot.add_callback('expired', lambda tmr: self.replot())
        self.replot_after_sec = 0.2

        self.gui_up = False

    def build_gui(self, container):
        if not self.chname.endswith('_TGTS'):
            raise Exception(f"This plugin is not designed to run in channel {self.chname}")

        obj = self.channel.opmon.get_plugin('SiteSelector')
        self.site_obj = obj.get_site()
        self.dt_utc, self.cur_tz = obj.get_datetime()
        obj.cb.add_callback('site-changed', self.site_changed_cb)
        obj.cb.add_callback('time-changed', self.time_changed_cb)

        self.targets = self.channel.opmon.get_plugin('Targets')
        self.targets.cb.add_callback('selection-changed', self.target_selection_cb)
        self.visplot = self.channel.opmon.get_plugin('Visibility')

        top = Widgets.VBox()
        top.set_border_width(4)

        fr = Widgets.Frame("Satellites / PAM")

        captions = (("PAM Dir:", 'label', 'pam_dir', 'entryset'),
                    ("PAM Files:", 'label', "tgt_load_label", 'llabel'),
                    ("Target:", 'label', 'target', 'llabel'),
                    ("Sat window:", 'label', 'sat_window_status', 'llabel'),
                    ("sat_time_label", 'label', 'sat_time_countdown', 'llabel'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b
        b.pam_dir.set_text(self.pam_dir)
        b.pam_dir.add_callback('activated', self.set_pamdir_cb)
        b.pam_dir.set_tooltip("Folder where PAM files are stored")
        b.sat_window_status.set_text("")
        b.sat_time_label.set_text("Time left:")
        b.sat_time_countdown.set_text("")
        b.tgt_load_label.set_text("")

        fr.set_widget(w)
        top.add_widget(fr)

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
        self.visplot.set_satellite_windows(None)
        self.gui_up = False

    def redo(self):
        pass

    def load_pam_files(self, pam_dir=None):
        # search for the PAM files in the given directory
        if pam_dir is None:
            pam_dir = self.pam_dir
        else:
            self.pam_dir = pam_dir
        filename_pattern = os.path.join(pam_dir, 'PAM_*.txt')
        self.pam_filenames = glob.glob(filename_pattern)

        num_files = self.load_files(self.pam_filenames)

        # dict of PAM targets
        tgt_dict = {Target(name=f"PAM ra={rec.ra_deg:8.4f},dec={rec.dec_deg:8.4f}",
                           ra=rec.ra_deg, dec=rec.dec_deg,
                           equinox=rec.epoch, category='PAM'): windows
                    for rec, windows in self.tgt_dict.items()
                    if isinstance(rec, pamsat.RaDec_Target)}
        self.tgt_dict = tgt_dict

        # build up a vector of targets
        self.tgts_radec = list(tgt_dict.keys())
        tgts = np.array([(tgt.name, tgt.ra, tgt.dec, tgt.equinox)
                         for tgt in self.tgts_radec])
        num_tgts = len(tgts)
        self.mbody_radec = calcpos.Body(tgts.T[0], tgts.T[1].astype(float),
                                        tgts.T[2].astype(float), tgts.T[3])

        if self.gui_up:
            self.w.tgt_load_label.set_text(f"{num_files} files, {num_tgts} targets loaded")
        # return number of files loaded
        return num_files

    def reload(self):
        self.load_pam_files()

    def load_files(self, paths):
        # read the PAM files
        count = 0
        for path in paths:
            self.load_file(path)
            count += 1

        return count

    def load_file(self, path):
        self.logger.info(f"loading PAM file '{path}'...")
        pamsat.load_pam_file(path, tgt_dict=self.tgt_dict,
                             pad_sec=self.pad_sec, use_datetime=True)

    def replot(self):
        self.show_target_sat_windows(self._cur_target)

    def set_pamdir_cb(self, w):
        # clear out target info
        self.tgt_dict = dict()

        pam_dir = w.get_text().strip()
        if not os.path.isdir(pam_dir):
            self.fv.show_error(f"'{pam_dir}' does not seem to be a directory")
            return
        self.pam_dir = pam_dir

        # load all PAM files found
        self.load_pam_files()

        self.selected_redo()

    def show_target_sat_windows(self, tgt):
        self.fv.assert_gui_thread()

        if tgt is not None:
            pam_tgt = self.get_pam_target(tgt)
            windows = self.tgt_dict.get(pam_tgt, None)
        else:
            windows = None
        self._cur_target = tgt
        self._windows = windows

        self.check_sat_window_status()
        self.visplot.set_satellite_windows(windows)

    def get_pam_target(self, tgt, dt=None, min_delta_sep_arcsec=None):
        """Select an internal PAM target by angular distance from target.

        Parameters
        ----------
        tgt : `~spot.util.target.Target`
            A target to search against

        dt : datetime.datetime (optional, defaults to current time)
            The time of checking

        min_delta_sep_arcsec : float (optional)
            Separation must be less than this value

        Returns
        -------
        tgt : `~spot.util.target.Target`
            Target matching parameter or None
        """
        if self.mbody_radec is None:
            raise ValueError("No targets internalized")

        if dt is None:
            dt = self.dt_utc
        if min_delta_sep_arcsec is None:
            min_delta_sep_arcsec = self.min_delta_arcsec

        cr = self.site_obj.observer.calc(self.mbody_radec, dt)
        # calculate separation from current telescope position
        sep_radec = cr.calc_separation(tgt)

        idx = np.argmin(sep_radec)
        tgt_radec, sep_radec = self.tgts_radec[idx], sep_radec[idx]
        if sep_radec >= min_delta_sep_arcsec:
            # not pointing to the target
            tgt_radec = None
        return tgt_radec

    def target_selection_cb(self, cb, targets):
        """Called when the user selects targets in the Target table"""
        if not self.gui_up:
            return

        target = None
        if self.mbody_radec is None:
            text = "No PAM files loaded"
        else:
            if len(targets) == 0:
                text = "No targets selected"
            elif len(targets) == 1:
                # only show a target if a single one is selected
                target = next(iter(targets))
                text = target.name
            else:
                text = "Multiple targets selected"
        if self.gui_up:
            self.w.target.set_text(text)

        self._cur_target = target
        self.tmr_replot.set(self.replot_after_sec)

    def selected_redo(self):
        # See if anything is selected in targets and plot appropriately
        selected = self.targets.get_selected_targets()
        self.target_selection_cb(None, list(selected))

    def check_sat_window_status(self):
        windows = self._windows
        if windows is not None:
            # TODO: optimize this. Probably can find out how long until
            # the next transition (OPEN->CLOSED, CLOSED->OPEN) and
            # then just check against that future time
            status, reason, t_remain = pamsat.get_window_status(self.dt_utc,
                                                                windows)
            if isinstance(t_remain, timedelta):
                # calculate the remaining time
                seconds = int(t_remain.total_seconds())
                th, rem = divmod(seconds, 3600)
                tm, ts = divmod(rem, 60)
                th, tm, ts = int(th), int(tm), int(ts)
                time_string = f"{th:02d}:{tm:02d}:{ts:02d}"
            else:
                time_string = "-1"

            if not status:
                self.w.sat_window_status.set_text(f'CLOSED: {reason}')
                self.w.sat_time_countdown.set_text(f'{time_string} until opening')
            else:
                self.w.sat_window_status.set_text(f'OPEN: {reason}')
                self.w.sat_time_countdown.set_text(f'{time_string} until closing')
        else:
            self.w.sat_window_status.set_text('')
            self.w.sat_time_countdown.set_text('')

    def site_changed_cb(self, cb, site_obj):
        self.logger.debug("site has changed")
        self.site_obj = site_obj
        obj = self.channel.opmon.get_plugin('SiteSelector')
        self.dt_utc, self.cur_tz = obj.get_datetime()

    def time_changed_cb(self, cb, time_utc, cur_tz):
        old_dt_utc = self.dt_utc
        self.dt_utc = time_utc
        self.cur_tz = cur_tz

        # TODO: calculate satellite window and laser window status
        if self.gui_up:
            self.fv.gui_do(self.check_sat_window_status)

    def __str__(self):
        return 'lgs'
