#
# cloudcover.py -- matplotlib plot of the SkyCam cloud cover history
#
from datetime import datetime, timezone

import numpy as np
import matplotlib.dates as mpl_dt

from ginga.util import plots

from spot.locale import _tr


class CloudCoverPlot(plots.Plot):
    """Cloud cover (%) from the SkyCam differential image versus time."""

    def __init__(self, width, height, logger=None):
        super().__init__(width=width, height=height, logger=logger)

    def plot_history(self, history, tz):
        """Plot `history`, a sequence of (POSIX time, cloud cover %, night)
        tuples, with times shown in timezone `tz` (a tzinfo).  Points taken
        while it was not dark (`night` False) are shown hollow, since the
        cloud cover means little then.
        """
        figure = self.figure
        figure.clf()
        ax = figure.add_subplot(111)
        self.ax = ax

        ax.set_ylim(0.0, 100.0)
        ax.set_ylabel(_tr("Cloud cover (%)"))
        ax.grid(True, alpha=0.4)

        if len(history) > 0:
            t_arr, cc_arr, night_arr = zip(*history)
            dt_arr = [datetime.fromtimestamp(t, tz=timezone.utc)
                      for t in t_arr]
            x_arr = mpl_dt.date2num(dt_arr)
            cc_arr = np.asarray(cc_arr, dtype=float)
            night_arr = np.asarray(night_arr, dtype=bool)

            # don't draw the line across gaps in the data (camera or
            # downloads down, SPOT not running...)
            t_arr = np.asarray(t_arr, dtype=float)
            line_x, line_y = x_arr, cc_arr
            if len(t_arr) > 2:
                dt = np.diff(t_arr)
                max_gap = max(600.0, 5.0 * np.median(dt))
                gaps = np.nonzero(dt > max_gap)[0] + 1
                line_x = np.insert(x_arr, gaps, np.nan)
                line_y = np.insert(cc_arr, gaps, np.nan)
            ax.plot(line_x, line_y, '-', color='tab:blue', lw=1, alpha=0.6)
            ax.plot(x_arr[night_arr], cc_arr[night_arr], 'o',
                    color='tab:blue', ms=4)
            ax.plot(x_arr[~night_arr], cc_arr[~night_arr], 'o',
                    mfc='none', color='gray', ms=4)

            locator = mpl_dt.AutoDateLocator(tz=tz, minticks=3, maxticks=7)
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(
                mpl_dt.ConciseDateFormatter(locator, tz=tz))
            if len(x_arr) == 1:
                # give a single point some room
                ax.set_xlim(x_arr[0] - 0.01, x_arr[0] + 0.01)

        self.redraw()
