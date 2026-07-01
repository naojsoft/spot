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

from spot.util.eph_cache import EphemerisCache, split_array

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
