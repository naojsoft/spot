#
# altitude.py -- matplotlib plots for target altitude
#
# Some code based on "Observer" module by Daniel Magee
#   Copyright (c) 2008 UCO/Lick Observatory.
#
from datetime import datetime, timedelta
import numpy as np

import matplotlib.dates as mpl_dt

from ginga.util import plots


class AltitudePlot(plots.Plot):

    def __init__(self, width, height, logger=None):
        super().__init__(width=width, height=height, logger=logger)

        # time increments, by minute
        self.time_inc_min = 15

        # colors used for successive points
        self.colors = ['r', 'b', 'g', 'c', 'm', 'y']

    def setup(self):
        pass

    def get_figure(self):
        return self.fig

    def clear(self):
        #self.ax.cla()
        self.fig.clf()
        self.redraw()

    def redraw(self):
        canvas = self.fig.canvas
        if canvas is not None:
            canvas.draw()

    def plot_altitude(self, site, tgt_data, tz, current_time=None,
                      plot_moon_distance=False,
                      show_target_legend=False,
                      center_time=None,
                      satellite_barh_data=None,
                      collision_barh_data=None):
        self._plot_altitude(self.fig, site, tgt_data, tz, current_time=current_time,
                            plot_moon_distance=plot_moon_distance,
                            show_target_legend=show_target_legend,
                            center_time=center_time,
                            satellite_barh_data=satellite_barh_data,
                            collision_barh_data=collision_barh_data)

    def _plot_altitude(self, figure, site, tgt_data, tz, current_time=None,
                       plot_moon_distance=False,
                       show_target_legend=False,
                       center_time=None,
                       satellite_barh_data=None,
                       collision_barh_data=None):
        """
        Plot into `figure` an altitude chart using target data from `info`
        with time plotted in timezone `tz` (a tzinfo instance).
        """
        # set major ticks to hours
        majorTick = mpl_dt.HourLocator(tz=tz)
        # Set the major format of the x-axis to display the time in
        # hours followed by an "h", e.g., "19h". ConciseDateFormatter
        # also puts the date at the left end of the x-axis.
        f = ['%Y', '%b', '%d', '%Hh', '%H:%M', '%S.%f']
        majorFmt = mpl_dt.ConciseDateFormatter(majorTick, tz=tz, formats=f)
        # set minor ticks to 15 min intervals
        minorTick = mpl_dt.MinuteLocator(list(range(0, 59, 15)), tz=tz)

        figure.clf()
        ax1 = figure.add_subplot(111)
        self.ax = ax1
        if show_target_legend:
            figure.set_tight_layout(False)
            figure.subplots_adjust(left=0.05, right=0.65, bottom=0.12, top=0.95)

        lstyle = '-'
        #lstyle = 'solid'
        # convert to desired time zone for plot
        lt_data_first = np.array([t.astimezone(tz)
                                  for t in tgt_data[0].history['ut']])

        # get the date of the first target. Also get the end date
        # so that we can include it in the plot title.
        localdate_start = lt_data_first[0]
        localdate_end = lt_data_first[-1]
        localdate_start_str = localdate_start.strftime('%Y-%b-%d %H:%M')
        localdate_end_str = localdate_end.strftime('%Y-%b-%d %H:%M')

        min_interval = 4
        targets, legend = [], []

        # plot targets elevation vs. time
        for i, info in enumerate(tgt_data):
            lt_data = np.array([t.astimezone(tz)
                                for t in info.history['ut']])
            alt_data = info.history['alt_deg']
            alt_min = np.argmin(alt_data)
            alt_data_dots = alt_data
            color = info.get('color', self.colors[i % len(self.colors)])
            alpha = info.get('alpha', 1.0)
            zorder = info.get('zorder', 1.0)
            textbg = info.get('textbg', None)
            lg = ax1.plot(lt_data, alt_data_dots, color=color,
                          alpha=alpha, linewidth=2.0, linestyle=lstyle,
                          marker=None, zorder=zorder, aa=True)
            legend.extend(lg)

            targets.append("{0} {1} {2}".format(info.target.name,
                                                info.target.ra,
                                                info.target.dec))

            if plot_moon_distance:
                alt_interval = alt_data[0:-1:min_interval]
                moon_sep = info.history['moon_sep']
                moon_sep = moon_sep[0:-1:min_interval]

                # plot moon separations
                mt = lt_data[0:-1:min_interval]
                for x, y, v in zip(mt, alt_interval, moon_sep):
                    if y < 0:
                        continue
                    ax1.text(x, y, '%.1f' % v, fontsize=7, ha='center',
                             va='bottom', clip_on=True)
                    ax1.plot(x, y, 'ko', ms=3)

            # plot object label
            targname = info.target.name
            ax1.text(mpl_dt.date2num(lt_data[alt_data.argmax()]),
                     alt_data.max() + 4.0, targname, color=color,
                     alpha=alpha, zorder=zorder, backgroundcolor=textbg,
                     ha='center', va='center', clip_on=True)

        # legend target list
        if show_target_legend:
            self.fig.legend(legend, targets,
                            loc='upper right', fontsize=9, framealpha=0.5,
                            frameon=True, ncol=1, bbox_to_anchor=[0.3, 0.865, .7, 0.1])

        ax1.set_ylim(0.0, 90.0)
        ax1.set_xlim(lt_data_first[0], lt_data_first[-1])
        ax1.xaxis.set_major_locator(majorTick)
        ax1.xaxis.set_minor_locator(minorTick)
        ax1.xaxis.set_major_formatter(majorFmt)
        labels = ax1.get_xticklabels()
        ax1.grid(True, color='#999999')

        # label axes
        title = f'Visibility from {localdate_start_str} to {localdate_end_str} {tz.tzname(localdate_start)}'
        ax1.set_title(title)
        # label x-axis with a readable timezone name
        ax1.set_xlabel(tz.tzname(localdate_start))
        ax1.set_ylabel('Altitude (deg)')

        # Plot moon trajectory and illumination
        moon_data = tgt_data[0].history['moon_alt']
        illum_time = lt_data_first[moon_data.argmax()]
        moon_illum = site.moon_illumination(date=illum_time)
        moon_color = '#CDBE70'
        moon_name = "Moon (%.2f %%)" % (moon_illum * 100)
        ax1.plot(lt_data_first, moon_data, moon_color, linewidth=3.0,
                 alpha=0.9, aa=True)
        ax1.text(mpl_dt.date2num(illum_time),
                 moon_data.max() + 4.0, moon_name, color=moon_color,
                 ha='center', va='center', clip_on=True)

        # Plot airmass scale
        altitude_ticks = np.array([20, 30, 40, 50, 60, 70, 80, 90])
        airmass_ticks = 1.0 / np.cos(np.radians(90 - altitude_ticks))
        airmass_ticks = ["%.3f" % n for n in airmass_ticks]

        ax2 = ax1.twinx()
        #ax2.set_ylim(None, 0.98)
        #ax2.set_xlim(lt_data_first[0], lt_data_first[-1])
        ax2.set_yticks(altitude_ticks)
        ax2.set_yticklabels(airmass_ticks)
        ax2.set_ylim(ax1.get_ylim())
        ax2.set_ylabel('Airmass')
        ax2.set_xlabel('')
        ax2.yaxis.tick_right()

        # plot moon label
        targname = "moon"
        ## ax1.text(mpl_dt.date2num(moon_data[moon_data.argmax()]),
        ##          moon_data.max() + 0.08, targname.upper(), color=color,
        ##          ha='center', va='center', clip_on=True)

        # plot lower and upper safe limits for clear observing
        min_alt, max_alt = 30.0, 75.0
        self._plot_limits(ax1, min_alt, max_alt)

        # Add yesterday's and today's twilight to the plot.
        self._plot_twilight(ax1, site, localdate_start - timedelta(1), tz,
                            show_legend=show_target_legend)
        self._plot_twilight(ax1, site, localdate_start, tz,
                            show_legend=show_target_legend)

        # plot current hour. If current_time wasn't supplied, use
        # computer time and specified time zone. Otherwise use
        # specified current_time in specified time zone.
        if current_time is None:
            lo = datetime.now(tz)
        else:
            lo = current_time.astimezone(tz)
        hi = lo + timedelta(0, 3600.0)
        if lt_data_first[0] < lo < lt_data_first[-1]:
            self._plot_current_time(ax1, lo, hi)

        # drawing the line of center_time
        if center_time is not None:
            ymin, ymax = ax1.get_ylim()
            ax1.vlines(center_time, ymin, ymax, colors='blue',
                       linestyles='dashed', label='Time Center')

        # plot moon's position at midnight
        #self._moon_position(ax1, site)

        # plot satellite open/close windows if that info was provided
        if satellite_barh_data is not None:
            self._plot_satellite_windows(ax1, satellite_barh_data, lt_data_first[-1])

        # plot collisions open/close windows if that info was provided
        if collision_barh_data is not None:
            self._plot_collision_windows(ax1, collision_barh_data, lt_data_first[-1])

        canvas = self.fig.canvas
        if canvas is not None:
            canvas.draw()

    def _plot_twilight(self, ax, site, localdate, tz, show_legend=False):
        # plot sunset
        t = site.sunset(date=localdate).astimezone(tz)

        # plot evening twilight 6/12/18 degrees
        et6 = site.evening_twilight_6(t).astimezone(tz)
        et12 = site.evening_twilight_12(t).astimezone(tz)
        et18 = site.evening_twilight_18(t).astimezone(tz)

        ymin, ymax = ax.get_ylim()
        # civil twilight 6 degree
        ct = ax.axvspan(t, et6, facecolor='#FF6F00', lw=None, ec='none', alpha=0.35)
        # nautical twilight 12 degree
        nt = ax.axvspan(et6, et12, facecolor='#947DC0', lw=None, ec='none', alpha=0.5)
        # astronomical twilight 18 degree
        at = ax.axvspan(et12, et18, facecolor='#3949AB', lw=None, ec='none', alpha=0.65)

        ss = ax.vlines(t, ymin, ymax, colors=['red'],
                       linestyles=['dashed'], label='Sunset')

        if show_legend:
            sunset = "Sunset {}".format(t.strftime("%H:%M:%S"))
            civil_twi = "Civil Twi {}".format(et6.strftime("%H:%M:%S"))
            nautical_twi = "Nautical Twi {}".format(et12.strftime("%H:%M:%S"))
            astro_twi = "Astronomical Twi {}".format(et18.strftime("%H:%M:%S"))

            self.fig.legend((ss, ct, nt, at),
                            (sunset, civil_twi, nautical_twi, astro_twi),
                            loc='lower left', fontsize=7, framealpha=0.5,
                            bbox_to_anchor=[0.045, -0.02, .7, 0.113])

        # plot morning twilight 6/12/18 degrees
        mt6 = site.morning_twilight_6(et6).astimezone(tz)
        mt12 = site.morning_twilight_12(et12).astimezone(tz)
        mt18 = site.morning_twilight_18(et18).astimezone(tz)

        # plot sunrise
        t2 = site.sunrise(mt18).astimezone(tz)

        # astronomical twilight 18 degree
        at = ax.axvspan(mt18, mt12, facecolor='#3949AB', lw=None, ec='none', alpha=0.65)
        # nautical twilight 12 degree
        nt = ax.axvspan(mt12, mt6, facecolor='#947DC0', lw=None, ec='none', alpha=0.5)
        # civil twilight 6 degree
        ct = ax.axvspan(mt6, t2, facecolor='#FF6F00', lw=None, ec='none', alpha=0.35)

        sr = ax.vlines(t2, ymin, ymax, colors=['red'],
                       linestyles=['dashed'], label='Sunrise')

        if show_legend:
            sunrise = "Sunrise {}".format(t2.strftime("%H:%M:%S"))
            civil_twi = "Civil Twi {}".format(mt6.strftime("%H:%M:%S"))
            nautical_twi = "Nautical Twi {}".format(mt12.strftime("%H:%M:%S"))
            astro_twi = "Astronomical Twi {}".format(mt18.strftime("%H:%M:%S"))

            self.fig.legend((sr, ct, nt, at),
                            (sunrise, civil_twi, nautical_twi, astro_twi),
                            loc='lower right', fontsize=7, framealpha=0.5,
                            bbox_to_anchor=[-0.043, -0.02, .7, 0.113])

    def _plot_current_time(self, ax, lo, hi):
        ax.axvspan(lo, hi, facecolor='#7FFFD4', alpha=0.25)

    def _plot_limits(self, ax, lo_lim, hi_lim):
        ymin, ymax = ax.get_ylim()
        ax.axhspan(ymin, lo_lim, facecolor='#F9EB4E', alpha=0.20)

        ax.axhspan(hi_lim, ymax, facecolor='#F9EB4E', alpha=0.20)

    def _plot_satellite_windows(self, ax, dt_boxes, x_lim_end):
        # plot the open windows
        ax.broken_barh(dt_boxes, (3, 8),
                       facecolors=[0.267, 0.482, 0.804],
                       edgecolors='white')
        # hack to get "SAT" annotation in a decent spot
        x_pos = x_lim_end - timedelta(hours=1)
        ax.annotate('SAT', xy=(x_pos, 5),
                    color='pink', fontsize=14, ha='left')

    def _plot_collision_windows(self, ax, dt_boxes, x_lim_end):

        # plot the open windows
        ax.broken_barh(dt_boxes, (12, 8),
                       facecolors=[0.804, 0.482, 0.267],
                       edgecolors='white')

        # hack to get "TEL" annotation in a decent spot
        x_pos = x_lim_end - timedelta(hours=1)
        ax.annotate('TEL', xy=(x_pos, 14),
                    color='cyan', fontsize=14, ha='left')
