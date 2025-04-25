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
"""
# stdlib
from datetime import timedelta
import threading

# 3rd party
import numpy as np
import pandas as pd
from dateutil import tz

# ginga
from ginga.gw import Widgets, Plot
from ginga.misc import Bunch
from ginga import GingaPlugin, colors

from spot.plots.altitude import AltitudePlot


class Visibility(GingaPlugin.LocalPlugin):
    """
    +++++++++++++++
    Visibility Plot
    +++++++++++++++

    This window contains a display which shows the altitude over time of
    selected targets in your target list.

    .. note:: This window will be blank if there are no targets selected.

    Highlighted regions
    ===================

    The yellow regions at the top and bottom are the warning areas. In those
    regions observations are difficult due to high airmass or very high elevation.
    The dashed red vertical lines are the site sunset and sunrise times. The
    vertical orange region demarcates the time of Civil Twilight, the vertical
    lavender region demarcates the time of Nautical Twilight, and the vertical
    blue region demarcates the time of Astronomical Twilight. The green region
    marks the next hour from the current time.

    Setting time interval
    =====================

    To change the plotted time interval, press the button next to "Centered on:"
    to open a drop down menu. Three options are available, Night Center,
    Day Center, and Current. "Night Center" will center the time axis on the middle
    of the night, which can be found in the :doc:`polarsky` window. The time axis
    will extend from a little before sunset to a little after sunrise. "Day
    Center" will center the time axis on the middle of the day, and the time
    axis will extend from sunrise to sunset. "Current" will set the time axis
    to extend from about -2 to +7 hours, and will automatically adjust as time
    passes.

    Checking moon separation
    ========================

    The visibility window can display the moon-object separation by pressing the
    checkbox next to "Plot moon sep" at the bottom left corner of the window.
    Selecting this option will display the separation in degrees at every hour
    while the object is above the horizon.

    Plot Options
    ============

    The drop down menu by "Plot:" controls which targets are plotted on the
    visibility plot. Selecting "All" will show all of the targets,
    selecting "Uncollapsed" will show any targets that are not collapsed
    (hidden) in the Target table as well as tagged and selected targets,
    selecting "Tagged+Selected" will show all of the targets which have been
    tagged or are selected, and selecting "Selected" will show only the
    targets which are selected.
    """
    def __init__(self, fv, fitsimage):
        super().__init__(fv, fitsimage)

        if not self.chname.endswith('_TGTS'):
            return

        # get preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_Visibility')
        self.settings.add_defaults(targets_update_interval=60.0,
                                   color_selected='dodgerblue1',
                                   color_tagged='mediumorchid1',
                                   color_normal='mediumseagreen',
                                   plot_interval_min=10)
        self.settings.load(onError='silent')

        # these are set via callbacks from the SiteSelector plugin
        self.site = None
        self.lock = threading.RLock()
        self.dt_utc = None
        self.cur_tz = None
        self.full_tgt_list = []
        self.tagged = set([])
        self.selected = set([])
        self.uncollapsed = set([])
        self._targets = []
        self._last_tgt_update_dt = None
        self._columns = ['ut', 'alt_deg', 'az_deg', 'airmass',
                         'moon_alt', 'moon_sep']
        self.vis_dict = dict()
        self.plot_moon_sep = False
        self.plot_polar_azel = False
        self.plot_legend = False
        self.plot_which = 'selected'
        self._satellite_barh_data = None
        self._collision_barh_data = None
        self.gui_up = False

        self.time_axis_options = ('Night Center', 'Day Center', 'Current')
        self.time_axis_default_mode = 'Night Center'
        self.time_axis_default_index = self.time_axis_options.index(self.time_axis_default_mode)

        # When time_axis_mode is "Current", x-axis range will be
        # time_range_current_mode hours.
        self.time_range_current_mode = 10  # hours

        self.viewer = self.fitsimage
        self.dc = fv.get_draw_classes()
        canvas = self.dc.DrawingCanvas()
        canvas.enable_draw(False)
        #canvas.register_for_cursor_drawing(self.fitsimage)
        canvas.set_surface(self.fitsimage)
        canvas.set_draw_mode('pick')
        self.canvas = canvas

        self.tmr_replot = self.fv.make_timer()
        self.tmr_replot.add_callback('expired', lambda tmr: self.replot())
        self.replot_after_sec = 0.2

    def build_gui(self, container):

        if not self.chname.endswith('_TGTS'):
            raise Exception(f"This plugin is not designed to run in channel {self.chname}")

        # initialize site and date/time/tz
        obj = self.channel.opmon.get_plugin('SiteSelector')
        with self.lock:
            self.site = obj.get_site()
            obj.cb.add_callback('site-changed', self.site_changed_cb)
            self.dt_utc, self.cur_tz = obj.get_datetime()
            obj.cb.add_callback('time-changed', self.time_changed_cb)

        obj = self.channel.opmon.get_plugin('Targets')
        self.full_tgt_list = obj.get_targets()
        obj.cb.add_callback('targets-changed', self.targets_changed_cb)
        self.tagged = set(obj.get_tagged_targets())
        obj.cb.add_callback('tagged-changed', self.tagged_changed_cb)
        self.selected = set(obj.get_selected_targets())
        obj.cb.add_callback('selection-changed', self.selection_changed_cb)
        self.uncollapsed = set(obj.get_uncollapsed_targets())
        obj.cb.add_callback('uncollapsed-changed', self.uncollapsed_changed_cb)
        self.tgts_obj = obj

        top = Widgets.VBox()
        top.set_border_width(4)

        self.plot = AltitudePlot(700, 500, logger=self.logger)
        #obj = self.channel.opmon.get_plugin('Targets')
        #self.plot.colors = obj.colors

        plot_w = Plot.PlotWidget(self.plot, width=700, height=500)

        top.add_widget(plot_w, stretch=1)

        captions = (('Plot moon sep', 'checkbox',
                     'Plot polar AzEl', 'checkbox',
                     'Time axis:', 'label', 'mode', 'combobox',
                     'Plot:', 'label', 'plot', 'combobox'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b
        b.plot_moon_sep.set_state(self.plot_moon_sep)
        b.plot_moon_sep.add_callback('activated', self.toggle_mon_sep_cb)
        b.plot_moon_sep.set_tooltip("Show moon separation on plot lines")
        b.plot_polar_azel.set_state(self.plot_polar_azel)
        b.plot_polar_azel.add_callback('activated', self.plot_polar_azel_cb)
        b.plot_polar_azel.set_tooltip("Plot Az/El paths on polar plot")

        for name in self.time_axis_options:
            b.mode.append_text(name)
        b.mode.set_index(self.time_axis_default_index)
        self.time_axis_mode = self.time_axis_default_mode.lower()
        b.mode.set_tooltip("Set time axis for visibility plot")
        b.mode.add_callback('activated', self.set_time_axis_mode_cb)

        for option in ['All', 'Uncollapsed', 'Tagged+selected', 'Selected']:
            b.plot.append_text(option)
        b.plot.set_text(self.plot_which.capitalize())
        b.plot.add_callback('activated', self.configure_plot_cb)
        b.plot.set_tooltip("Choose what is plotted")

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
        self._set_target_subset()

        # insert canvas, if not already
        p_canvas = self.viewer.get_canvas()
        if self.canvas not in p_canvas:
            # Add our canvas
            p_canvas.add(self.canvas)

        self.canvas.delete_all_objects()

    def stop(self):
        self.gui_up = False
        # remove the canvas from the image
        p_canvas = self.fitsimage.get_canvas()
        if self.canvas in p_canvas:
            p_canvas.delete_object(self.canvas)

    def redo(self):
        pass

    def initialize_plot(self):
        self.plot.setup()

    def clear_plot(self):
        self.plot.clear()
        self.canvas.delete_object_by_tag('targets')

    def plot_targets(self, targets):
        """Plot targets.
        """
        # remove no longer used targets
        new_tgts = set(targets)
        with self.lock:
            dt_utc = self.dt_utc
            cur_tz = self.cur_tz
            satellite_barh_data = self._satellite_barh_data
            collision_barh_data = self._collision_barh_data
            self._targets = targets

        if not self.gui_up:
            return

        # TODO: work with site object directly, not observer
        site = self.site.observer

        # get times of sun to figure out dates to plot
        obj = self.channel.opmon.get_plugin('SiteSelector')
        sun_info = obj.get_sun_info()

        if self.time_axis_mode == 'night center':
            # plot period 15 minutes before sunset to 15 minutes after sunrise
            delta = timedelta(minutes=15)
            start_time = sun_info.sun_set - delta
            stop_time = sun_info.sun_rise + delta
            center_time = start_time + \
                timedelta(seconds=int((stop_time - start_time).total_seconds() * 0.5))

        elif self.time_axis_mode == 'day center':
            # plot period 15 minutes before sunrise to 15 minutes after sunset
            delta = timedelta(minutes=15)
            start_time = sun_info.prev_sun_rise - delta
            stop_time = sun_info.sun_set + delta
            center_time = start_time + \
                timedelta(seconds=int((stop_time - start_time).total_seconds() * 0.5))

        elif self.time_axis_mode == 'current':
            # Plot a time period and put the current time at 1/4 from
            # the left edge of the period.
            time_period_sec = 60 * 60 * self.time_range_current_mode
            start_offset_from_current_sec = time_period_sec / 4
            start_time = dt_utc - timedelta(seconds=start_offset_from_current_sec)
            stop_time = dt_utc + timedelta(seconds=time_period_sec)
            center_time = dt_utc

        # round start time to every interval minutes
        interval_min = self.settings.get('plot_interval_min', 15)
        start_minute = start_time.minute // interval_min * interval_min
        start_time = start_time.replace(minute=start_minute,
                                        second=0, microsecond=0)
        stop_minute = stop_time.minute // interval_min * interval_min
        stop_time = stop_time.replace(minute=stop_minute,
                                      second=0, microsecond=0)

        target_data = self.get_target_data(targets, start_time, stop_time,
                                           interval_min)
        # make altitude plot
        self.clear_plot()

        if len(target_data) == 0:
            self.logger.debug("no targets for plotting airmass")
        else:
            self.logger.debug("plotting altitude/airmass")
            self.fv.error_wrap(self.plot.plot_altitude, site,
                               target_data, cur_tz,
                               current_time=dt_utc,
                               plot_moon_distance=self.plot_moon_sep,
                               show_target_legend=self.plot_legend,
                               center_time=center_time,
                               satellite_barh_data=satellite_barh_data,
                               collision_barh_data=collision_barh_data)
        self.fv.error_wrap(self.plot.draw)

        self.plot_azalt(target_data, 'targets')

    def get_target_data(self, targets, start_time, stop_time, interval_min):
        num_tgts = len(targets)
        target_data = []
        if num_tgts == 0:
            return target_data

        # TODO: work with site object directly, not observer
        site = self.site.observer

        site.set_date(start_time)
        # create date array
        dt_arr = np.arange(start_time.astimezone(tz.UTC),
                           stop_time.astimezone(tz.UTC),
                           timedelta(minutes=interval_min))

        for tgt in targets:
            vis_dct = self.vis_dict.get(tgt, None)
            if vis_dct is None:
                # no history for this target, so calculate values for full
                # time period
                cres = site.calc(tgt, dt_arr)
                vis_dct = cres.get_dict(columns=self._columns)
                vis_dct['time'] = dt_arr
                self.vis_dict[tgt] = vis_dct

            else:
                # we have some possible history for this target,
                # so only calculate values for the new time period
                # that we haven't already calculated
                t_arr = vis_dct['time']
                # remove any old calculations not in this time period
                mask = np.isin(t_arr, dt_arr, invert=True)
                if np.any(mask):
                    num_rem = mask.sum()
                    self.logger.debug(f"removing results for {num_rem} times")
                    for key in self._columns + ['time']:
                        vis_dct[key] = vis_dct[key][~mask]

                # add any new calculations in this time period
                add_arr = np.setdiff1d(dt_arr, t_arr)
                num_add = len(add_arr)
                if num_add == 0:
                    self.logger.debug("no new calculations needed")
                elif num_add > 0:
                    self.logger.debug(f"adding results for {num_add} new times")
                    # only calculate for new times
                    cres = site.calc(tgt, add_arr)
                    dct = cres.get_dict(columns=self._columns)
                    dct['time'] = add_arr
                    if len(vis_dct['time']) == 0:
                        # we removed all the old data
                        vis_dct.update(dct)
                    elif add_arr.max() < vis_dct['time'].min():
                        # prepend new data
                        for key in self._columns + ['time']:
                            vis_dct[key] = np.append(dct[key],
                                                     vis_dct[key])
                    else:
                        # append new data
                        for key in self._columns + ['time']:
                            vis_dct[key] = np.append(vis_dct[key],
                                                     dct[key])

            df = pd.DataFrame.from_dict(vis_dct, orient='columns')
            color, alpha, zorder, textbg = self._get_target_color(tgt)
            color = colors.lookup_color(color, format='hash')
            target_data.append(Bunch.Bunch(history=df,
                                           color=color,
                                           alpha=alpha,
                                           zorder=zorder,
                                           textbg=textbg,
                                           target=tgt))

        return target_data

    def plot_azalt(self, target_data, tag):
        """Plot targets.
        """
        self.canvas.delete_object_by_tag(tag)

        if not self.plot_polar_azel:
            return

        self.logger.info("plotting {} azimuths tag {}".format(len(target_data), tag))
        objs = []
        alpha = 1.0
        # plot targets elevation vs. time
        for i, info in enumerate(target_data):
            alt_data = np.array(info.history['alt_deg'], dtype=float)
            az_data = np.array(info.history['az_deg'], dtype=float)
            for alt_data, az_data in split_on_positive_alt(alt_data, az_data):
                if len(az_data) == 0:
                    continue
                t, r = self.map_azalt(az_data, alt_data)
                x, y = self.p2r(r, t)
                pts = np.array((x, y)).T
                path = self.dc.Path(pts, color=info.color, linewidth=1, alpha=alpha)
                objs.append(path)
                tgtname = info.target.name
                x, y = pts[-1]
                text = self.dc.Text(x, y, tgtname,
                                    color=info.color, alpha=alpha,
                                    fill=True, fillcolor=info.color,
                                    fillalpha=alpha, linewidth=0,
                                    font="Roboto condensed bold",
                                    fontscale=True,
                                    fontsize=None, fontsize_min=12,
                                    fontsize_max=16)#,
                                    # bgcolor='floralwhite', bgalpha=bg_alpha,
                                    # bordercolor='orangered1', borderlinewidth=2,
                                    # borderalpha=bg_alpha)
                objs.append(text)

        o = self.dc.CompoundObject(*objs)
        self.canvas.add(o, tag=tag, redraw=False)

        self.canvas.update_canvas(whence=3)

    def replot(self):
        with self.lock:
            targets = self._targets
        if targets is not None:
            self.plot_targets(targets)

    def _get_target_color(self, tgt):
        if tgt in self.selected:
            color = self.settings['color_selected']
            alpha = 1.0
            zorder = 10.0
            textbg = '#FFFAF0FF'
        elif tgt in self.tagged:
            color = self.settings['color_tagged']
            alpha = 0.85
            zorder = 5.0
            textbg = '#FFFFFF00'
        else:
            color = tgt.get('color', self.settings['color_normal'])
            alpha = 0.75
            zorder = 1.0
            textbg = '#FFFFFF00'
        return color, alpha, zorder, textbg

    def toggle_mon_sep_cb(self, w, tf):
        self.plot_moon_sep = tf
        self.replot()

    def plot_polar_azel_cb(self, w, tf):
        self.plot_polar_azel = tf
        self.replot()

    def toggle_show_legend_cb(self, w, tf):
        self.plot_legend = tf
        self.replot()

    def configure_plot_cb(self, w, idx):
        option = w.get_text()
        self.plot_which = option.lower()
        self.replot()

    def set_time_axis_mode_cb(self, w, index):
        self.time_axis_mode = w.get_text().lower()
        self.vis_dict = dict()
        self.logger.info(f'self.time_axis_mode set to {self.time_axis_mode}')
        self.replot()

    def _set_target_subset(self):
        with self.lock:
            if self.plot_which == 'all':
                self._targets = self.full_tgt_list
            elif self.plot_which == 'uncollapsed':
                self._targets = list(self.uncollapsed.union(self.tagged.union(self.selected)))
            elif self.plot_which == 'tagged+selected':
                self._targets = list(self.tagged.union(self.selected))
            elif self.plot_which == 'selected':
                self._targets = list(self.selected)

        #self.fv.gui_do(self.replot)
        self.tmr_replot.set(self.replot_after_sec)

    def configure_plot_cb(self, w, idx):
        option = w.get_text()
        self.plot_which = option.lower()
        self._set_target_subset()

    def targets_changed_cb(self, cb, targets):
        self.logger.info("targets changed")
        self.full_tgt_list = targets

        self._set_target_subset()
        #self.fv.gui_do(self.replot)

    def tagged_changed_cb(self, cb, tagged):
        self.tagged = tagged

        self._set_target_subset()
        #self.fv.gui_do(self.replot)

    def uncollapsed_changed_cb(self, cb, uncollapsed):
        self.uncollapsed = uncollapsed

        self._set_target_subset()
        #self.fv.gui_do(self.replot)

    def selection_changed_cb(self, cb, selected):
        self.selected = selected

        self._set_target_subset()
        self.tmr_replot.set(self.replot_after_sec)

    def time_changed_cb(self, cb, time_utc, cur_tz):
        with self.lock:
            self.dt_utc = time_utc
            self.cur_tz = cur_tz

        if (self._last_tgt_update_dt is None or
            abs((time_utc - self._last_tgt_update_dt).total_seconds()) >
            self.settings.get('targets_update_interval')):
            self.logger.debug("updating visibility plot")
            self._last_tgt_update_dt = time_utc
            self.fv.gui_do(self.replot)

    def site_changed_cb(self, cb, site_obj):
        self.logger.debug("site has changed")
        with self.lock:
            self.site = site_obj
            self.vis_dict = dict()

        self.fv.gui_do(self.replot)

    def p2r(self, r, t):
        obj = self.channel.opmon.get_plugin('PolarSky')
        return obj.p2r(r, t)

    # def get_scale(self):
    #     obj = self.channel.opmon.get_plugin('PolarSky')
    #     return obj.get_scale()

    def map_azalt(self, az, alt):
        obj = self.channel.opmon.get_plugin('PolarSky')
        return obj.map_azalt(az, alt)

    def set_satellite_windows(self, windows):
        with self.lock:
            if windows is None:
                self._satellite_barh_data = None
            else:
                windows_open, windows_close = windows.T
                windows_dur_sec = windows_close - windows_open
                windows_dur = np.array((windows_open, windows_dur_sec)).T
                self._satellite_barh_data = windows_dur

        self.replot()

    def set_collision_windows(self, windows):
        with self.lock:
            if windows is None:
                self._collision_barh_data = None
            else:
                windows_open, windows_close = windows.T
                windows_dur_sec = windows_close - windows_open
                windows_dur = np.array((windows_open, windows_dur_sec)).T
                self._collision_barh_data = windows_dur

        self.replot()

    def __str__(self):
        return 'visibility'


def split_on_positive_alt(alt_arr, az_arr):
    if len(alt_arr) == 0:
        return []

    # Identify indices where the value transitions between >0 and <=0
    transitions = np.where((alt_arr[:-1] > 0) != (alt_arr[1:] > 0))[0] + 1

    # Split the array at these indices
    alt_res = np.split(alt_arr, transitions)
    az_res = np.split(az_arr, transitions)

    # return only the arrays where elev > 0
    return [(alt_res[i], az_res[i]) for i in range(len(alt_res))
            if alt_res[i][0] > 0]
