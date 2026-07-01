#
# eph_cache.py -- class for caching ephemeris data
#
import os
import sys
import logging
from datetime import timedelta

import numpy as np
from dateutil import tz

from ginga.misc.Bunch import Bunch

from .calcpos import Observer

# Whether process-based parallelism is usable.  It is NOT under
# Pyodide/WASM: there, `import multiprocessing` may even succeed but process
# spawning doesn't work -- so gate on the platform rather than on whether
# the module imports.  The multiprocessing / concurrent.futures imports are
# also deferred into populate_periods_mp() (not done at module load), so
# merely importing this module stays safe in the browser, where importing
# multiprocessing can itself raise.
have_mp = sys.platform not in ('emscripten', 'wasi')

# Below this many targets the process-pool startup cost isn't worth it, so
# populate_periods_mp() runs the serial grid instead.  Because each worker
# already runs the vectorized grid (which is fast), process startup only pays
# off for large catalogs -- keep this threshold high (tune per deployment).
_MP_MIN_TARGETS = 500

# Logger used inside worker processes: inherits the parent's configuration
# under fork; a handler-less no-op under spawn.
_mp_logger = logging.getLogger('spot.util.eph_cache.worker')


class EphemerisCache:

    def __init__(self, logger, precision_minutes=5, columns=None,
                 default_period_check=True):
        self.logger = logger
        self.precision_minutes = precision_minutes
        if columns is None:
            columns = ['ut', 'lt', 'alt_deg', 'az_deg', 'airmass', 'pang_deg',
                       'moon_alt', 'moon_sep']
        self._columns = columns
        self.period_check = default_period_check
        self.vis_catalog = dict()

    def get_target_data(self, key):
        vis_dct = self.vis_catalog.get(key, None)
        return vis_dct

    def clear_target_data(self, key):
        if key in self.vis_catalog:
            del self.vis_catalog[key]

    def clear_all(self):
        self.vis_catalog = dict()

    def get_date_array(self, start_time, stop_time):
        # round start time to every self.interval_min minutes
        int_min = self.precision_minutes
        start_minute = start_time.minute // int_min * int_min
        start_time = start_time.replace(minute=start_minute,
                                        second=0, microsecond=0)
        stop_minute = stop_time.minute // int_min * int_min
        stop_time = stop_time.replace(minute=stop_minute,
                                      second=0, microsecond=0)

        # create date array
        # NOTE: numpy does not like to parse timezone-aware datetimes
        # to np.datetime64
        dt_arr = np.arange(start_time.astimezone(tz.UTC).replace(tzinfo=None),
                           stop_time.astimezone(tz.UTC).replace(tzinfo=None) +
                           timedelta(minutes=int_min),
                           timedelta(minutes=int_min))
        return dt_arr

    def _populate_target_data(self, res_dct, tgt_dct, site, dt_arr,
                              keep_old=True):

        for key, target in tgt_dct.items():

            vis_dct = res_dct.get(key, None)
            if vis_dct is None:
                # no history for this target, so calculate values for full
                # time period
                cres = site.calc(target, dt_arr)
                vis_dct = cres.get_dict(columns=self._columns)
                vis_dct['time_utc'] = dt_arr
                res_dct[key] = vis_dct

            else:
                # we have some possible history for this target,
                # so only calculate values for the new time period
                # that we haven't already calculated
                t_arr = vis_dct['time_utc']
                if not keep_old:
                    # remove any old calculations not in this time period
                    mask = np.isin(t_arr, dt_arr, invert=True)
                    num_rem = mask.sum()
                    if num_rem > 0:
                        self.logger.debug(f"removing results for {num_rem} times")
                        for col in self._columns + ['time_utc']:
                            vis_dct[col] = vis_dct[col][~mask]

                # add any new calculations in this time period
                add_arr = np.setdiff1d(dt_arr, t_arr)
                num_add = len(add_arr)
                if num_add == 0:
                    self.logger.debug("no new calculations needed")
                elif num_add > 0:
                    self.logger.debug(f"adding results for {num_add} new times")
                    # only calculate for new times
                    cres = site.calc(target, add_arr)
                    dct = cres.get_dict(columns=self._columns)
                    dct['time_utc'] = add_arr

                    if len(vis_dct['time_utc']) == 0:
                        # we removed all the old data
                        vis_dct.update(dct)
                    else:
                        idxs = np.searchsorted(vis_dct['time_utc'], add_arr)
                        # insert new data
                        for col in self._columns + ['time_utc']:
                            vis_dct[col] = np.insert(vis_dct[col], idxs, dct[col])

    def populate_periods(self, tgt_dct, site, periods, keep_old=True):
        """Populate ephemeris for many targets over many periods.

        Fixed-star targets are computed in a single vectorized astropy grid
        (calcpos.calc_targets); solar-system bodies -- and any requested
        columns the grid can't produce -- fall back to the per-target engine.
        Incremental over time: only the time slots each target is missing are
        gridded (their union), so a shifting time window recomputes just the
        new slot(s) for all N targets in one (N, K) call.

        Parameters
        ----------
        tgt_dct : dict
            dict mapping keys to targets

        site : ~spot.util.calcpos.Observer
            The site observing the targets

        periods : list of (start_time, stop_time)
            Where times are timezone-aware Python datetimes

        keep_old : bool (optional, defaults to True)
            Whether to keep old period data not specified in this range

        Returns
        -------
        None
        """
        # create one large date array of all periods
        start_time, stop_time = periods[0]
        dt_arr = self.get_date_array(start_time, stop_time)
        for start_time, stop_time in periods[1:]:
            dt_arr_n = self.get_date_array(start_time, stop_time)
            dt_arr = np.append(dt_arr, dt_arr_n, axis=0)
        # sort and de-duplicate: overlapping/unordered periods would
        # otherwise leave time_utc unsorted (breaking the searchsorted
        # assumptions in get_closest() and the incremental insert below)
        dt_arr = np.unique(dt_arr)

        self._populate_via_grid(self.vis_catalog, tgt_dct, site, dt_arr,
                                keep_old=keep_old)

    def _populate_via_grid(self, res_dct, tgt_dct, site, dt_arr, keep_old=True):
        # astropy vectorized grid kernel (works with either Observer backend --
        # calc_targets reads only the observer's lat/lon/elev, not its location
        # object)
        from .calcpos import calc_targets, GRID_COLUMNS

        # The grid can satisfy this request only if every requested column is
        # grid-producible; otherwise fall back entirely to the per-target
        # engine (which computes the full column set).  Independently, only
        # fixed-star targets (carrying ra/dec) can be gridded; solar-system
        # bodies (SSBody) route to the per-target path.
        grid_ok = set(self._columns) <= GRID_COLUMNS
        star_keys, star_bodies, ss_dct = [], [], {}
        for key, tgt in tgt_dct.items():
            if grid_ok and hasattr(tgt, 'ra') and hasattr(tgt, 'dec'):
                star_keys.append(key)
                star_bodies.append(tgt)
            else:
                ss_dct[key] = tgt
        if ss_dct:
            self._populate_target_data(res_dct, ss_dct, site, dt_arr,
                                       keep_old=keep_old)
        if len(star_keys) == 0:
            return

        # per-target missing times; grid only their union (one call)
        need = []
        for key in star_keys:
            vis = res_dct.get(key, None)
            need.append(dt_arr if vis is None
                        else np.setdiff1d(dt_arr, vis['time_utc']))
        nonempty = [n for n in need if len(n) > 0]
        if len(nonempty) == 0:
            union = None
            grid = {}
        else:
            union = np.unique(np.concatenate(nonempty))
            grid = calc_targets(site, star_keys, star_bodies, union,
                                columns=self._columns)
        cols = self._columns

        def _select(key, times):
            # pull `times` (a subset of union) out of the gridded columns
            sel = np.searchsorted(union, times)
            d = {col: np.asarray(grid[key][col])[sel] for col in cols}
            d['time_utc'] = times
            return d

        for key, add_arr in zip(star_keys, need):
            vis = res_dct.get(key, None)
            if vis is None:
                # fresh target: union covers all of dt_arr
                res_dct[key] = _select(key, dt_arr)
                continue

            t_arr = vis['time_utc']
            if not keep_old:
                # drop cached times outside the current window
                mask = np.isin(t_arr, dt_arr, invert=True)
                if mask.sum() > 0:
                    for col in cols + ['time_utc']:
                        vis[col] = vis[col][~mask]

            if len(add_arr) == 0:
                continue
            dct = _select(key, add_arr)
            if len(vis['time_utc']) == 0:
                vis.update(dct)
            else:
                idxs = np.searchsorted(vis['time_utc'], add_arr)
                for col in cols + ['time_utc']:
                    vis[col] = np.insert(vis[col], idxs, dct[col])

    def get_closest(self, key, time_dt, precision_minutes=None):
        """Return the closest set of results for target to time

        Parameters
        ----------
        key : valid Python dict key
            The key that is used to store the results for a target

        time_dt : datetime.datetime
            Python timezone-aware datetime for the period we are interested in

        Returns
        -------
        res : dict of values
            A dict of values keyed by column name
        """
        vis_dct = self.get_target_data(key)
        if vis_dct is None:
            raise KeyError(f"No data for key {key} found")

        t_arr = vis_dct['time_utc']
        dt = time_dt.astimezone(tz.UTC).replace(tzinfo=None)
        idx = np.searchsorted(t_arr, dt, side='left')
        # Get values closest in time to dt
        if idx == len(t_arr):
            idx = idx - 1
        if idx > 0:
            t_lo, t_hi = t_arr[idx - 1].item(), t_arr[idx].item()
            if np.fabs((dt - t_lo).total_seconds()) < np.fabs((t_hi - dt).total_seconds()):
                idx = idx - 1
        res_dct = {key: vis_dct[key][idx]
                   for key in self._columns + ['time_utc']}
        # check closeness of dt to result
        t_res = res_dct['time_utc'].item()
        diff_sec = np.fabs((dt - t_res).total_seconds())

        if precision_minutes is None:
            precision_minutes = self.precision_minutes
        if diff_sec / 60.0 > precision_minutes:
            raise ValueError(f"time diff from result is {diff_sec:.2f} sec")
        return Bunch(res_dct)

    def observable_periods(self, tgt_dct, site, start_time, stop_time,
                           el_min_deg, el_max_deg, time_needed_sec,
                           period_check=None):
        """Check many targets visibility within a time period.

        Parameters
        ----------
        tgt_dct : dict
            dict mapping keys to targets

        site : ~spot.util.calcpos.Observer
            The site observing the targets

        start_time : datetime.datetime
            Starting time as a timezone-aware Python datetime

        stop_time : datetime.datetime
            Stopping time as a timezone-aware Python datetime

        el_min_deg : float or dict of float
            Minimum elevation as a constant or per-target

        el_max_deg : float or dict of float
            Maximum elevation as a constant or per-target

        time_needed_sec : float or dict of float
            Time needed in seconds as a constant or per-target

        period_check : bool or None (optional, defaults to instance choice)
            Whether to check if we need to populate the period

        Returns
        -------
        obs_dct : dict
            dict mapping keys to lists of observability periods

        Each list is like [(start_time, stop_time), ...]
        """
        if period_check is None:
            period_check = self.period_check

        if start_time.tzinfo is None or stop_time.tzinfo is None:
            raise ValueError("Please pass timezone-aware datetimes")
        tz_incoming = start_time.tzinfo

        if period_check:
            # ideally, this should be as efficient as possible if we have
            # already populated the time span
            self.populate_periods(tgt_dct, site,
                                  [(start_time, stop_time)],
                                  keep_old=True)

        _start_time = start_time.astimezone(tz.UTC).replace(tzinfo=None)
        _stop_time = stop_time.astimezone(tz.UTC).replace(tzinfo=None)

        obs_dct = dict()
        # TODO: any way to parallelize this
        for key in tgt_dct:
            vis_dct = self.get_target_data(key)

            # Grab indices for times within our start and stop range
            utc_arr = vis_dct['time_utc']
            time_indices = np.where(np.logical_and(_start_time <= utc_arr,
                                                   utc_arr <= _stop_time))[0]
            utc_inrange = vis_dct['time_utc'][time_indices]

            # Limit altitude check to those indices
            alt_arr = vis_dct['alt_deg'][time_indices]

            # Now limit altitude check by min and max elevation limits
            _el_min_deg, _el_max_deg = el_min_deg, el_max_deg
            if isinstance(el_min_deg, dict):
                # <-- there is a different min limit for each target
                _el_min_deg = el_min_deg[key]
            if isinstance(el_max_deg, dict):
                # <-- there is a different max limit for each target
                _el_max_deg = el_max_deg[key]

            alt_indices = np.where(np.logical_and(_el_min_deg <= alt_arr,
                                                  alt_arr <= _el_max_deg))[0]

            # check for, and separate, any gaps in the indices as separate
            # available visibility slices
            # (target may move above or below acceptable elevation, for example)
            vis_slices = split_array(alt_indices)

            # Report the times for the first available slice that can accomodate
            # the time_needed
            periods = []
            prec_sec = self.precision_minutes * 60.0
            for indices in vis_slices:
                utc_times = utc_inrange[indices]
                if len(utc_times) < 2:
                    continue
                time_rise = utc_times[0].item().replace(tzinfo=tz.UTC)
                time_set = utc_times[-1].item().replace(tzinfo=tz.UTC)

                diff = (time_set - time_rise).total_seconds()
                _time_needed_sec = time_needed_sec
                if isinstance(time_needed_sec, dict):
                    # <-- there is a different time needed for each target
                    _time_needed_sec = time_needed_sec[key]
                can_obs = (diff >= _time_needed_sec)
                if can_obs:
                    if tz_incoming is not None:
                        time_rise = time_rise.astimezone(tz_incoming)
                        # if time_rise we have is close enough to the start_time
                        # passed in, pretend the time_rise is the passed in one
                        if np.fabs((time_rise - start_time).total_seconds()) <= prec_sec:
                            time_rise = start_time

                        time_set = time_set.astimezone(tz_incoming)
                        # ditto for time_set and stop_time
                        if np.fabs((time_set - stop_time).total_seconds()) <= prec_sec:
                            time_set = stop_time
                    periods.append((time_rise, time_set))

            obs_dct[key] = periods

        return obs_dct

    def observable(self, key, target, site, start_time, stop_time,
                   el_min_deg, el_max_deg, time_needed_sec,
                   period_check=None):
        """
        Return True if `target` is observable between `time_start` and
        `time_stop`, defined by whether it is between elevation `el_min`
        and `el_max` during that period, and whether it meets the minimum
        airmass.

        See docstring for observable_periods() for information about
        parameters.
        """
        obs_dct = self.observable_periods({key: target}, site,
                                          start_time, stop_time,
                                          el_min_deg, el_max_deg,
                                          time_needed_sec,
                                          period_check=period_check)
        periods = obs_dct[key]
        if len(periods) == 0:
            return (False, None, None)

        time_rise, time_set = periods[0]
        return (True, time_rise, time_set)


def split_array(arr):
    """Splits a NumPy array into subarrays based on index discontinuities.

    Parameters
    ----------
        arr: A 1D NumPy array.

    Returns
    -------
        A list of NumPy arrays representing the subarrays.
    """
    if len(arr) <= 1:
        return [arr]

    # find differences between i and i+1 indices
    diffs = np.diff(arr)
    # find split indices where the difference is > 1
    split_indices = np.array(np.where(diffs > 1)).flatten() + 1
    # split the array into sub-arrays along these indices
    sub_arrays = np.split(arr, split_indices)
    return sub_arrays


def _num_workers():
    """Number of usable CPUs (honors cgroup / CPU-affinity limits)."""
    try:
        return len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        return os.cpu_count() or 1


def _process_chunk(items, existing, site_spec, dt_arr, columns, keep_old):
    """Worker: vectorized *grid* populate for one chunk (see _populate_via_grid),
    so each worker combines CPU parallelism with the per-chunk grid.  Fixed
    stars go through calc_targets; SSBody / non-grid columns fall back to the
    per-target engine inside _populate_via_grid.

    `existing` is the prior cached ``{key: vis_dct}`` for just these keys, so
    the same incremental ``keep_old`` merge used serially applies here too.
    `site_spec` is rebuilt with ``Observer.from_spec`` (skyfield objects inside
    an Observer don't pickle).  Returns ``{key: vis_dct}`` for the chunk.
    """
    site = Observer.from_spec(site_spec)
    helper = EphemerisCache(_mp_logger, columns=columns)
    res_dct = dict(existing)
    helper._populate_via_grid(res_dct, dict(items), site, dt_arr,
                              keep_old=keep_old)
    return res_dct


def _mp_start_method_context():
    """A multiprocessing context safe for SPOT's multi-threaded GUI: prefer
    'forkserver' (clean single-threaded fork server -- avoids fork-in-threaded
    deadlocks and spawn's __main__ re-import), fall back to 'spawn'."""
    import multiprocessing as mp
    for method in ('forkserver', 'spawn'):
        try:
            return mp.get_context(method)
        except ValueError:
            continue
    return mp.get_context()


def _assemble_dt_arr(eph_cache, periods):
    """One sorted, de-duplicated date array spanning all periods."""
    start_time, stop_time = periods[0]
    dt_arr = eph_cache.get_date_array(start_time, stop_time)
    for start_time, stop_time in periods[1:]:
        dt_arr_n = eph_cache.get_date_array(start_time, stop_time)
        dt_arr = np.append(dt_arr, dt_arr_n, axis=0)
    return np.unique(dt_arr)


def _dispatch_mp(eph_cache, tgt_dct, site, dt_arr, keep_old,
                 worker_fn, serial_fn, min_targets):
    """Chunk the targets across worker processes (round-robin), running
    worker_fn on each chunk and merging the results into the cache.  Falls
    back to serial_fn(vis_catalog, tgt_dct, site, dt_arr, keep_old) when MP
    isn't worthwhile (few targets, 1 CPU) or unavailable (Pyodide).
    """
    n_workers = min(_num_workers(), len(tgt_dct))
    if (not have_mp) or n_workers <= 1 or len(tgt_dct) < min_targets:
        serial_fn(eph_cache.vis_catalog, tgt_dct, site, dt_arr,
                  keep_old=keep_old)
        return

    # round-robin split: every worker gets work even when len(tgt_dct) is only
    # a little above n_workers, and shared args are pickled once per worker
    items = list(tgt_dct.items())
    chunks = [items[i::n_workers] for i in range(n_workers)]
    chunks = [chunk for chunk in chunks if len(chunk) > 0]

    columns = eph_cache._columns
    site_spec = site.get_spec()

    # Imported here (not at module load): the multiprocessing / ProcessPool
    # import chain can fail under Pyodide.  We only reach here when have_mp.
    from concurrent.futures import ProcessPoolExecutor
    ctx = _mp_start_method_context()

    with ProcessPoolExecutor(max_workers=len(chunks), mp_context=ctx) as ex:
        futures = []
        for chunk in chunks:
            existing = {key: eph_cache.vis_catalog[key]
                        for key, _tgt in chunk
                        if key in eph_cache.vis_catalog}
            futures.append(ex.submit(worker_fn, chunk, existing,
                                     site_spec, dt_arr, columns, keep_old))
        for future in futures:
            eph_cache.vis_catalog.update(future.result())


def populate_periods_mp(eph_cache, tgt_dct, site, periods, keep_old=True):
    """Parallel version of populate_periods(): chunk the targets across worker
    processes (stdlib concurrent.futures, no joblib) where *each worker runs
    the vectorized grid* (calc_targets) over its chunk -- combining the
    per-chunk grid with CPU parallelism.  Each worker is seeded with its
    targets' prior cached data, so keep_old incremental merging behaves as in
    the serial path.

    Because the grid is already fast, process-startup cost only pays off for
    large catalogs: below _MP_MIN_TARGETS (or with one CPU, or under Pyodide)
    it falls back to the serial grid populate (populate_periods).
    """
    if len(tgt_dct) == 0:
        return
    dt_arr = _assemble_dt_arr(eph_cache, periods)
    _dispatch_mp(eph_cache, tgt_dct, site, dt_arr, keep_old,
                 _process_chunk, eph_cache._populate_via_grid,
                 _MP_MIN_TARGETS)
