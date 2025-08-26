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
from datetime import datetime, timedelta
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
from spot.util.eph_cache import EphemerisCache


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

    Setting plot range
    ==================

    To change the plotted time interval, press the button labeled "Time axis:"
    to open a drop down menu. Three options are available, Night Center,
    Day Center, and Current. "Night Center" will center the time axis on the
    middle of the night, which can be found in the :doc:`polarsky` window.
    The time axis will extend from a little before sunset to a little after
    sunrise. "Day Center" will center the time axis on the middle of the day,
    and the time axis will extend from sunrise to sunset. "Current" will set
    the time axis to extend from about -2 to +7 hours, and will automatically
    adjust as time passes.

    Target Selection
    ================

    The drop down menu by "Plot:" controls which targets are plotted on the
    visibility plot. Selecting "All" will show all of the targets,
    selecting "Uncollapsed" will show any targets that are not collapsed
    (hidden) in the Target table as well as tagged and selected targets,
    selecting "Tagged+Selected" will show all of the targets which have been
    tagged or are selected, and selecting "Selected" will show only the
    targets which are selected.

    Settings Menu
    =============
    Clicking the "Settings" button will invoke a pop-up menu to enable certain
    settings.

    * Plot moon separation.  Checking this option will display the separation
      in degrees at every hour along each plot line while the object is above
      the horizon.
    * Plot polar Az/El.  Checking this option will create a line on the
      "<wsname>_TGTS" viewer that marks the position of each target during
      the period selected for the time axis (see above), and for the targets
      selected by the plot target selection.  This allows you to see more
      than the target's position according to the time in the SiteSelector.
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
        self._telescope_target = None
        self._last_tgt_update_dt = None
        self.eph_cache = EphemerisCache(self.logger,
                                        precision_minutes=self.settings['plot_interval_min'],
                                        default_period_check=True)
        self.plot_moon_sep = False
        self.plot_polar_azel = False
        self.plot_legend = False
        self.plot_which = 'selected'
        self._satellite_barh_data = None
        self._collisions = None
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

        have_telpos = self.channel.opmon.has_plugin('TelescopePosition')
        if have_telpos:
            obj = self.channel.opmon.get_plugin('TelescopePosition')
            obj.cb.add_callback('telescope-status-changed',
                                self.telescope_status_cb)

        top = Widgets.VBox()
        top.set_border_width(4)

        self.plot = AltitudePlot(700, 500, logger=self.logger)
        #obj = self.channel.opmon.get_plugin('Targets')
        #self.plot.colors = obj.colors

        plot_w = Plot.PlotWidget(self.plot, width=700, height=500)

        top.add_widget(plot_w, stretch=1)

        self.w.toolbar2 = Widgets.Toolbar(orientation='horizontal')
        self.w.toolbar2.add_spacer()

        self.w.mode = Widgets.ComboBox()
        for name in self.time_axis_options:
            self.w.mode.append_text(name)
        self.w.mode.set_index(self.time_axis_default_index)
        self.time_axis_mode = self.time_axis_default_mode.lower()
        self.w.mode.set_tooltip("Set time axis for visibility plot")
        self.w.mode.add_callback('activated', self.set_time_axis_mode_cb)
        self.w.toolbar2.add_widget(Widgets.Label("Time axis:"))
        self.w.toolbar2.add_widget(self.w.mode)

        self.w.toolbar2.add_spacer()
        #self.w.toolbar2.add_separator()

        self.w.plot = Widgets.ComboBox()
        for option in ['Selected', 'Tagged+selected', 'Uncollapsed', 'All']:
            self.w.plot.append_text(option)
        self.w.plot.set_text(self.plot_which.capitalize())
        self.w.plot.add_callback('activated', self.configure_plot_cb)
        self.w.plot.set_tooltip("Choose what is plotted")
        self.w.toolbar2.add_widget(Widgets.Label("Plot:"))
        self.w.toolbar2.add_widget(self.w.plot)

        self.w.toolbar2.add_spacer()

        menu = self.w.toolbar2.add_menu("Settings", mtype='menu')
        menu.set_tooltip("Configure some settings for this plugin")
        self.w.settings = menu

        plot_moon_sep = menu.add_name("Plot moon separation", checkable=True)
        plot_moon_sep.set_state(self.plot_moon_sep)
        plot_moon_sep.add_callback('activated', self.toggle_mon_sep_cb)
        plot_moon_sep.set_tooltip("Show moon separation on plot lines")

        plot_polar_azel = menu.add_name("Plot polar AzEl", checkable=True)
        plot_polar_azel.set_state(self.plot_polar_azel)
        plot_polar_azel.add_callback('activated', self.plot_polar_azel_cb)
        plot_polar_azel.set_tooltip("Plot Az/El paths on polar plot")

        top.add_widget(self.w.toolbar2, stretch=0)

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

    def calc_targets(self, targets):
        """Calculate target visibility and replot."""
        # Although this is calculation-bound, running it in a different
        # thread seems to leave our GUI a little more reponsive
        self.fv.assert_nongui_thread()

        # remove no longer used targets
        with self.lock:
            self._targets = targets
            if not self.gui_up:
                return
            dt_utc = self.dt_utc
            cur_tz = self.cur_tz
            satellite_barh_data = self._satellite_barh_data
            collisions = self._collisions

        new_tgts = set(targets)
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
            time_period_sec = int(60 * 60 * self.time_range_current_mode)
            start_offset_from_current_sec = int(time_period_sec / 4)
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

        # this does the heavy lifting
        target_data = self.get_target_data(targets, start_time, stop_time,
                                           interval_min)

        collision_barh_data = None
        if self._telescope_target in targets and collisions is not None:
            # only plot the laser collision windows if we are viewing
            # one of the targets that the telescope is pointing at
            collision_barh_data = self.calc_collision_windows(start_time,
                                                              stop_time,
                                                              collisions)

        # plot results back in the GUI thread
        self.fv.gui_do(self._plot_targets, site, target_data, dt_utc, cur_tz,
                       center_time, satellite_barh_data, collision_barh_data)

    def _plot_targets(self, site, target_data, dt_utc, cur_tz,
                      center_time, satellite_barh_data, collision_barh_data):
        """Plot visibility results."""
        self.fv.assert_gui_thread()
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

        start_time_utc = start_time.astimezone(tz.UTC)
        stop_time_utc = stop_time.astimezone(tz.UTC)

        # populate ephemeris cache
        tgt_dct = {tgt: tgt for tgt in targets}
        periods = [(start_time_utc, stop_time_utc)]
        self.eph_cache.populate_periods(tgt_dct, site, periods,
                                        keep_old=False)

        for tgt in targets:
            vis_dct = self.eph_cache.get_target_data(tgt)

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
                path = self.dc.Path(pts, color='goldenrod1',
                                    linewidth=1, alpha=alpha)
                objs.append(path)
                tgtname = info.target.name
                x, y = pts[-1]
                text = self.dc.Text(x, y, tgtname,
                                    color='goldenrod1', alpha=alpha,
                                    fill=True, fillcolor='goldenrod1',
                                    fillalpha=0.75, linewidth=0,
                                    font="Roboto condensed",
                                    fontscale=True,
                                    fontsize=None, fontsize_min=12,
                                    fontsize_max=16)
                objs.append(text)

        o = self.dc.CompoundObject(*objs)
        self.canvas.add(o, tag=tag, redraw=False)

        self.canvas.update_canvas(whence=3)

    def replot(self):
        with self.lock:
            targets = self._targets
        if targets is not None:
            self.fv.nongui_do(self.calc_targets, targets)

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

    def set_time_axis_mode_cb(self, w, index):
        self.time_axis_mode = w.get_text().lower()
        #self.eph_cache.clear_all()
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
            self.eph_cache.clear_all()

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

    def telescope_status_cb(self, cb, status, target):
        # this is called when the telescope target changes, if the
        # TelescopePosition plugin has been enabled and working
        old_tgt, self._telescope_target = self._telescope_target, target
        targets = [] if self._targets is None else self._targets
        if old_tgt is not target:
            # change of target by telescope
            if old_tgt in targets or target in targets:
                self.replot()

    def set_collisions(self, collisions):
        # this is called by the LTCS plugin (if active, it is part of the
        # spot-subaru package) to inform us of laser collisions
        replot = False
        with self.lock:
            if collisions is None and self._collisions is not None:
                self._collisions = collisions
                replot = True
            else:
                _collisions = set(collisions)
                if self._collisions is None or len(_collisions.difference(self._collisions)) > 0:
                    self._collisions = _collisions
                    replot = True

        if replot and self.gui_up:
            self.replot()

    def calc_collision_windows(self, dt_start, dt_stop, collisions,
                               use_datetime=True):
        # convert collisions list queried from database to open windows
        sse_start = dt_start.timestamp()
        sse_stop = dt_stop.timestamp()

        # sort collisions by starting time
        collisions_closed = list(collisions)
        collisions_closed.sort(key=lambda coll: coll.time_start_sse)
        self.logger.info(f'collisions_closed {collisions_closed}')

        # adjust collision times to account for
        # overlapping collisions
        mod_collisions_closed = []
        prev_start = prev_end = sse_start
        for coll in collisions_closed:
            # Consider only collisions that start inside
            # the range of the plot window.
            if coll.time_start_sse < sse_stop:
                now_start = prev_end if coll.time_start_sse < prev_end else coll.time_start_sse
                now_end = prev_end if coll.time_stop_sse < prev_end else coll.time_stop_sse
                if now_start < now_end:
                    mod_collisions_closed.append([now_start, now_end])
                prev_start, prev_end = now_start, now_end
        self.logger.info(f'mod_collisions_closed {mod_collisions_closed}')

        # convert from closed windows to open windows
        prev_end = sse_start
        collisions_open = []
        for coll_start_sse, coll_stop_sse in mod_collisions_closed:
            close_sse = min(coll_start_sse, sse_stop)
            window = (prev_end, close_sse)
            prev_end = coll_stop_sse
            if coll_start_sse < sse_stop:
                collisions_open.append(window)
        self.logger.info(f'collisions_open {collisions_open}')

        if prev_end < sse_stop:
            window = (prev_end, sse_stop)
            collisions_open.append(window)
        windows = np.array(collisions_open)
        #self.logger.debug(f'windows {windows}')

        windows_open, windows_close = windows.T
        windows_dur_sec = windows_close - windows_open
        if not use_datetime:
            windows_dur = np.array((windows_open, windows_dur_sec)).T
        else:
            windows_dur = np.array(([datetime.fromtimestamp(sse).replace(tzinfo=self.cur_tz)
                                     for sse in windows_open],
                                    [timedelta(seconds=sec) for sec in windows_dur_sec])).T
        self.logger.debug(f'windows duration {windows_dur}')
        return windows_dur

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
