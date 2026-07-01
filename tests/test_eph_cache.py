#
# test_eph_cache.py -- unit tests for EphemerisCache merge logic
#
# These exercise the cache's array bookkeeping (the keep_old incremental
# merge and the multi-period sort/de-dup) with a *fake* site, so they run
# fast and need no skyfield ephemeris.  Each column value is a distinct,
# deterministic function of its timestamp, so the assertions catch any
# scrambling of values vs. times (or between columns) during a merge.
#
import logging
from datetime import datetime

import numpy as np
from dateutil import tz
import pytest

from spot.util.eph_cache import (EphemerisCache, split_array,
                                 populate_periods_mp, _process_chunk, have_mp)

COLS = ['alt_deg', 'az_deg']
BASE = np.datetime64('2020-01-01T00:00:00')


def _minutes(times):
    return (times - BASE) / np.timedelta64(1, 'm')


def val_for(col, times):
    """A distinct deterministic value per (column, time)."""
    m = _minutes(times)
    return m if col == 'alt_deg' else (m * 2.0 + 1.0)


def dtarr(start_min, n, step=5):
    """A UTC-naive datetime64 array (as stored internally), n points."""
    return BASE + (np.arange(n) * step + start_min).astype('timedelta64[m]')


class _FakeResult:
    """Stand-in for calcpos.CalculationResult."""
    def __init__(self, times):
        self._times = times

    def get_dict(self, columns=None):
        return {col: val_for(col, self._times).copy() for col in columns}


class _FakeSite:
    """Stand-in for calcpos.Observer: no skyfield, deterministic values."""
    def calc(self, target, dt_arr):
        return _FakeResult(dt_arr)


def make_cache():
    log = logging.getLogger('test_eph_cache')
    log.addHandler(logging.NullHandler())
    return EphemerisCache(log, precision_minutes=5, columns=COLS)


def make_cache_default():
    """Cache with the default columns (incl. moon_alt/moon_sep), for the
    real-ephemeris parallel tests."""
    log = logging.getLogger('test_eph_cache')
    log.addHandler(logging.NullHandler())
    return EphemerisCache(log, precision_minutes=5)


# real observing windows (5-min aligned) for the parallel/skyfield tests
_HST = tz.gettz('US/Hawaii')
P_START = datetime(2024, 5, 16, 20, 0, tzinfo=_HST)
P_MID = datetime(2024, 5, 16, 20, 30, tzinfo=_HST)
P_STOP = datetime(2024, 5, 16, 21, 0, tzinfo=_HST)
PERIOD = (P_START, P_STOP)


def assert_consistent(vis_dct, expected_times):
    """time_utc matches, is strictly sorted, and every column value is
    still paired with its own timestamp."""
    t = vis_dct['time_utc']
    assert np.array_equal(t, expected_times), \
        (t.astype('datetime64[m]'), expected_times.astype('datetime64[m]'))
    # strictly increasing -> sorted and duplicate-free
    assert np.all(np.diff(t.astype('int64')) > 0)
    for col in COLS:
        assert np.array_equal(vis_dct[col], val_for(col, t)), \
            f"value/time pairing broken for column {col!r}"


class TestEphCacheKeepOld:

    def test_fresh_populate(self):
        cache, site = make_cache(), _FakeSite()
        res = {}
        cache._populate_target_data(res, {'t1': object()}, site,
                                    dtarr(0, 5), keep_old=True)
        assert_consistent(res['t1'], dtarr(0, 5))

    def test_keep_old_true_extend_and_overlap(self):
        # second window overlaps the first (10,15,20) and extends it (25,30);
        # result should be the union, sorted, with no duplicates
        cache, site = make_cache(), _FakeSite()
        res = {}
        tgt = {'t1': object()}
        cache._populate_target_data(res, tgt, site, dtarr(0, 5), keep_old=True)
        cache._populate_target_data(res, tgt, site, dtarr(10, 5), keep_old=True)
        assert_consistent(res['t1'], dtarr(0, 7))     # 0,5,10,15,20,25,30

    def test_keep_old_false_prune(self):
        # keep_old=False drops previously-cached times outside the new window
        # (exercises the removal loop that used to shadow `key`)
        cache, site = make_cache(), _FakeSite()
        res = {}
        tgt = {'t1': object()}
        cache._populate_target_data(res, tgt, site, dtarr(0, 5), keep_old=True)
        cache._populate_target_data(res, tgt, site, dtarr(10, 5), keep_old=False)
        # 0,5 pruned; 10,15,20 kept; 25,30 added -> exactly the new window
        assert_consistent(res['t1'], dtarr(10, 5))

    def test_keep_old_true_noop(self):
        # re-populating an identical window changes nothing (no duplicates)
        cache, site = make_cache(), _FakeSite()
        res = {}
        tgt = {'t1': object()}
        cache._populate_target_data(res, tgt, site, dtarr(10, 5), keep_old=True)
        cache._populate_target_data(res, tgt, site, dtarr(10, 5), keep_old=True)
        assert_consistent(res['t1'], dtarr(10, 5))

    def test_multiple_targets_independent(self):
        cache, site = make_cache(), _FakeSite()
        res = {}
        tgt = {'a': object(), 'b': object()}
        cache._populate_target_data(res, tgt, site, dtarr(0, 5), keep_old=True)
        cache._populate_target_data(res, tgt, site, dtarr(10, 5), keep_old=True)
        assert_consistent(res['a'], dtarr(0, 7))
        assert_consistent(res['b'], dtarr(0, 7))


class TestEphCacheMultiPeriod:
    # the np.unique() hardening in populate_periods()

    @staticmethod
    def _utc(minute, hour=0):
        return datetime(2020, 1, 1, hour, minute, tzinfo=tz.UTC)

    def test_overlapping_periods_sorted_unique(self):
        cache, site = make_cache(), _FakeSite()
        # two overlapping periods: [00:00,00:20] and [00:10,00:30]
        periods = [(self._utc(0), self._utc(20)),
                   (self._utc(10), self._utc(30))]
        cache.populate_periods({'t1': object()}, site, periods, keep_old=True)
        assert_consistent(cache.get_target_data('t1'), dtarr(0, 7))

    def test_unordered_periods_sorted(self):
        cache, site = make_cache(), _FakeSite()
        # later period listed first -> must still come out sorted
        periods = [(self._utc(20), self._utc(40)),
                   (self._utc(0), self._utc(20))]
        cache.populate_periods({'t1': object()}, site, periods, keep_old=True)
        assert_consistent(cache.get_target_data('t1'), dtarr(0, 9))  # 0..40

    def test_get_closest_after_multiperiod(self):
        # get_closest relies on searchsorted, which needs sorted/unique times
        cache, site = make_cache(), _FakeSite()
        periods = [(self._utc(0), self._utc(20)),
                   (self._utc(10), self._utc(30))]
        cache.populate_periods({'t1': object()}, site, periods, keep_old=True)
        res = cache.get_closest('t1', datetime(2020, 1, 1, 0, 12, tzinfo=tz.UTC))
        assert np.datetime64(res['time_utc']) == np.datetime64('2020-01-01T00:10')


class TestPopulatePeriodsMP:
    # the stdlib (concurrent.futures) parallel populate, incl. keep_old.
    # These use a real Observer, since the worker rebuilds one via
    # Observer.from_spec (a fake site can't round-trip through get_spec).

    FLOAT_COLS = ['alt_deg', 'az_deg', 'airmass', 'pang_deg',
                  'moon_alt', 'moon_sep']

    @staticmethod
    def _setup(n):
        from spot.util import sites
        from spot.util.calcpos import Body
        sites.configure_default_sites()
        site = sites.get_site('subaru')
        site.initialize()
        rng = np.random.default_rng(3)
        tgts = {f"s{i}": Body(f"s{i}", float(rng.uniform(0, 360)),
                              float(rng.uniform(-40, 80)), 2000.0)
                for i in range(n)}
        return site.observer, tgts

    def _assert_same(self, a, b):
        assert np.array_equal(a['time_utc'], b['time_utc'])
        for col in self.FLOAT_COLS:
            assert np.allclose(a[col], b[col], equal_nan=True), col

    def test_process_chunk_matches_serial(self):
        # worker function, in-process (no pool): result == serial populate
        obs, tgts = self._setup(5)
        dt_arr = np.unique(make_cache_default().get_date_array(*PERIOD))
        cache = make_cache_default()
        cache._populate_target_data(cache.vis_catalog, tgts, obs, dt_arr,
                                    keep_old=True)
        res = _process_chunk(list(tgts.items()), {}, obs.get_spec(),
                             dt_arr, cache._columns, True)
        for k in tgts:
            self._assert_same(cache.vis_catalog[k], res[k])

    def test_process_chunk_keep_old_seed(self):
        # seed the worker with first-half results, extend with keep_old=True;
        # must match a single serial populate over the full window
        obs, tgts = self._setup(5)
        c = make_cache_default()
        first = np.unique(c.get_date_array(P_START, P_MID))
        full = np.unique(c.get_date_array(P_START, P_STOP))
        c._populate_target_data(c.vis_catalog, tgts, obs, first, keep_old=True)
        existing = {k: c.vis_catalog[k] for k in tgts}

        res = _process_chunk(list(tgts.items()), existing, obs.get_spec(),
                             full, c._columns, True)

        ref = make_cache_default()
        ref._populate_target_data(ref.vis_catalog, tgts, obs, full,
                                  keep_old=True)
        for k in tgts:
            self._assert_same(ref.vis_catalog[k], res[k])
        # the window really was extended past the seeded first half
        assert len(res['s0']['time_utc']) > len(first)

    @pytest.mark.skipif(not have_mp, reason="no process-based parallelism")
    def test_populate_mp_matches_serial(self):
        # end-to-end pool run (>= _MP_MIN_TARGETS targets triggers the pool)
        obs, tgts = self._setup(20)
        c_ser = make_cache_default()
        c_ser.populate_periods(tgts, obs, [PERIOD], keep_old=True)
        c_mp = make_cache_default()
        populate_periods_mp(c_mp, tgts, obs, [PERIOD], keep_old=True)
        for k in tgts:
            self._assert_same(c_ser.get_target_data(k), c_mp.get_target_data(k))

    @pytest.mark.skipif(not have_mp, reason="no process-based parallelism")
    def test_populate_mp_keep_old_false_prunes(self):
        # keep_old=False must trim samples outside the new period (the
        # Visibility time-axis switch relies on this).  Populate an initial
        # window, then a shifted/overlapping one with keep_old=False; the
        # result must equal a fresh populate of only the second window.
        obs, tgts = self._setup(20)
        first = (P_START, P_MID)                 # 20:00 - 20:30
        second = (P_MID, P_STOP)                 # 20:30 - 21:00
        c_mp = make_cache_default()
        populate_periods_mp(c_mp, tgts, obs, [first], keep_old=False)
        populate_periods_mp(c_mp, tgts, obs, [second], keep_old=False)

        ref = make_cache_default()
        ref.populate_periods(tgts, obs, [second], keep_old=False)
        for k in tgts:
            self._assert_same(ref.get_target_data(k), c_mp.get_target_data(k))

    @pytest.mark.skipif(not have_mp, reason="no process-based parallelism")
    def test_populate_mp_keep_old_extends(self):
        # two MP passes with keep_old=True == one full serial populate
        obs, tgts = self._setup(20)
        c_mp = make_cache_default()
        populate_periods_mp(c_mp, tgts, obs, [(P_START, P_MID)], keep_old=True)
        n_first = len(c_mp.get_target_data('s0')['time_utc'])
        populate_periods_mp(c_mp, tgts, obs, [(P_MID, P_STOP)], keep_old=True)

        ref = make_cache_default()
        ref.populate_periods(tgts, obs, [PERIOD], keep_old=True)
        for k in tgts:
            self._assert_same(ref.get_target_data(k), c_mp.get_target_data(k))
        assert len(c_mp.get_target_data('s0')['time_utc']) > n_first


class TestSplitArray:

    def test_contiguous(self):
        out = split_array(np.array([3, 4, 5, 6]))
        assert len(out) == 1
        assert np.array_equal(out[0], [3, 4, 5, 6])

    def test_gaps(self):
        out = split_array(np.array([0, 1, 5, 6, 7, 10]))
        assert [list(a) for a in out] == [[0, 1], [5, 6, 7], [10]]

    @pytest.mark.parametrize("arr", [np.array([]), np.array([7])])
    def test_short(self, arr):
        out = split_array(arr)
        assert len(out) == 1
        assert np.array_equal(out[0], arr)
