"""
Visibility.py -- Overlay objects on all sky camera

Plugin Type: Local
==================

``Visibility`` is a local plugin, which means it is associated with a channel.
An instance can be opened for each channel.

Usage
=====
``Visibility`` is normally used in conjunction with the plugins ``Sites``,
``PolarSky`` and ``Targets``.  Typically, ``Sites`` is started first
on a channel and then ``PolarSky``, ``Targets`` and ``Visibility`` are also
started.

Requirements
============
python packages
---------------
matplotlib

naojsoft packages
-----------------
- ginga
- qplan
"""
# stdlib
from datetime import timedelta

# 3rd party
import numpy as np
import pandas as pd
from dateutil import tz

# ginga
from ginga.gw import Widgets, Plot
from ginga.misc import Bunch
from ginga import GingaPlugin

from spot.plots.altitude import AltitudePlot


class Visibility(GingaPlugin.LocalPlugin):
    """TODO
    """
    def __init__(self, fv, fitsimage):
        super().__init__(fv, fitsimage)

        # get preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_Visibility')
        self.settings.add_defaults(targets_update_interval=60.0)
        self.settings.load(onError='silent')

        # these are set via callbacks from the SiteSelector plugin
        self.site = None
        self.dt_utc = None
        self.cur_tz = None
        self._targets = None
        self.plot_moon_sep = False
        self.plot_legend = False
        self.gui_up = False

        self.time_axis_options = ('Night Center', 'Day Center', 'Current')
        self.time_axis_default_mode = 'Night Center'
        self.time_axis_default_index = self.time_axis_options.index(self.time_axis_default_mode)

        # When time_axis_mode is "Current", x-axis range will be
        # time_range_current_mode hours.
        self.time_range_current_mode = 10  # hours

    def build_gui(self, container):
        # initialize site and date/time/tz
        obj = self.channel.opmon.get_plugin('SiteSelector')
        self.site = obj.get_site()
        obj.cb.add_callback('site-changed', self.site_changed_cb)
        self.dt_utc, self.cur_tz = obj.get_datetime()
        obj.cb.add_callback('time-changed', self.time_changed_cb)

        top = Widgets.VBox()
        top.set_border_width(4)

        self.plot = AltitudePlot(700, 500, logger=self.logger)
        #obj = self.channel.opmon.get_plugin('Targets')
        #self.plot.colors = obj.colors

        plot_w = Plot.PlotWidget(self.plot, width=700, height=500)

        top.add_widget(plot_w, stretch=1)

        captions = (('Plot moon sep', 'checkbox', 'Time axis:', 'label', 'mode', 'combobox'),  # 'Show Legend', 'checkbox'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b
        b.plot_moon_sep.set_state(self.plot_moon_sep)
        b.plot_moon_sep.add_callback('activated', self.toggle_mon_sep_cb)
        b.plot_moon_sep.set_tooltip("Show moon separation on plot lines")

        # b.show_legend.set_state(self.plot_legend)
        # b.show_legend.add_callback('activated', self.toggle_show_legend_cb)
        # b.show_legend.set_tooltip("Show legend on plot")

        for name in self.time_axis_options:
            b.mode.append_text(name)
        b.mode.set_index(self.time_axis_default_index)
        self.time_axis_mode = self.time_axis_default_mode.lower()
        b.mode.set_tooltip("Set time axis for visibility plot")
        b.mode.add_callback('activated', self.set_time_axis_mode_cb)
        top.add_widget(w)

        #top.add_widget(Widgets.Label(''), stretch=1)

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
        self.initialize_plot()
        self.replot()

    def stop(self):
        self.gui_up = False

    def redo(self):
        pass

    def initialize_plot(self):
        self.plot.setup()

    def clear_plot(self):
        self.plot.clear()

    def plot_targets(self, targets):
        """Plot targets.
        """
        # save parameters in case we need to replot
        self._targets = targets
        if not self.gui_up:
            return

        # TODO: work with site object directly, not observer
        site = self.site.observer

        # calc noon on the day of observation in desired time zone
        obj = self.channel.opmon.get_plugin('SiteSelector')
        noon_time = obj.get_obsdate_noon()

        if self.time_axis_mode == 'night center':
            # plot period 15 minutes before sunset to 15 minutes after sunrise
            delta = timedelta(minutes=15)
            start_time = site.sunset(noon_time) - delta
            stop_time = site.sunrise(start_time) + delta
            center_time = start_time + \
                timedelta(seconds=int((stop_time - start_time).total_seconds() * 0.5))

        elif self.time_axis_mode == 'day center':
            # plot period 15 minutes before sunrise to 15 minutes after sunset
            midnight_before = noon_time - timedelta(hours=12)
            delta = timedelta(minutes=15)
            start_time = site.sunrise(midnight_before) - delta
            stop_time = site.sunset(noon_time) + delta
            center_time = start_time + \
                timedelta(seconds=int((stop_time - start_time).total_seconds() * 0.5))

        elif self.time_axis_mode == 'current':
            # Plot a time period and put the current time at 1/4 from
            # the left edge of the period.
            time_period_sec = 60 * 60 * self.time_range_current_mode
            start_offset_from_current_sec = time_period_sec / 4
            start_time = self.dt_utc - timedelta(seconds=start_offset_from_current_sec)
            stop_time = self.dt_utc + timedelta(seconds=time_period_sec)
            center_time = self.dt_utc

        site.set_date(start_time)
        # create date array
        #dt_arr = np.arange(start_time, stop_time, timedelta(minutes=15))
        dt_arr = np.arange(start_time.astimezone(tz.UTC),
                           stop_time.astimezone(tz.UTC),
                           timedelta(minutes=15))

        # make airmass plot
        num_tgts = len(targets)
        target_data = []
        # lengths = []
        if num_tgts > 0:
            for tgt in targets:
                cres = site.calc(tgt, dt_arr)
                dct = cres.get_dict(columns=['ut', 'alt_deg', 'airmass',
                                             'moon_alt', 'moon_sep'])
                df = pd.DataFrame.from_dict(dct, orient='columns')
                target_data.append(Bunch.Bunch(history=df,
                                               target=tgt))
                # lengths.append(len(df))

        # clip all dataframes to same length
        # min_len = 0
        # if len(lengths) > 0:
        #     min_len = min(lengths)
        # for il in target_data:
        #     il.history = il.history[:min_len]

        self.clear_plot()

        if num_tgts == 0:
            self.logger.debug("no targets for plotting airmass")
        else:
            self.logger.debug("plotting airmass")

            # Plot a subset of the targets
            #idx = int((self.controller.idx_tgt_plots / 100.0) * len(target_data))
            #num_tgts = self.controller.num_tgt_plots
            #target_data = target_data[idx:idx+num_tgts]

            self.fv.error_wrap(self.plot.plot_altitude, site,
                               target_data, self.cur_tz,
                               current_time=self.dt_utc,
                               plot_moon_distance=self.plot_moon_sep,
                               show_target_legend=self.plot_legend,
                               center_time=center_time)
        self.fv.error_wrap(self.plot.draw)

    def replot(self):
        if self._targets is not None:
            self.plot_targets(self._targets)

    def toggle_mon_sep_cb(self, w, tf):
        self.plot_moon_sep = tf
        self.replot()

    def toggle_show_legend_cb(self, w, tf):
        self.plot_legend = tf
        self.replot()

    def set_time_axis_mode_cb(self, w, index):
        self.time_axis_mode = w.get_text().lower()
        self.logger.info(f'self.time_axis_mode set to {self.time_axis_mode}')
        self.replot()

    def time_changed_cb(self, cb, time_utc, cur_tz):
        old_dt_utc = self.dt_utc
        self.dt_utc = time_utc
        self.cur_tz = cur_tz
        # we will be called from Targets to replot
        #self.fv.gui_do(self.replot)

    def site_changed_cb(self, cb, site_obj):
        self.logger.debug("site has changed")
        self.site = site_obj
        # we will be called from Targets to replot
        #self.fv.gui_do(self.replot)

    def __str__(self):
        return 'visibility'
