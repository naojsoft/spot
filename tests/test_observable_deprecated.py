import warnings

import pytest

from spot.util import calcpos


def _observer():
    return calcpos.Observer('subaru', longitude='-155:28:48.900',
                            latitude='+19:49:42.600', elevation=4163)


def test_observable_emits_deprecation_warning():
    obs = _observer()
    with pytest.warns(DeprecationWarning):
        with pytest.raises(NotImplementedError):
            obs.observable(None, None, None, 15.0, 85.0, 60)


def test_observable_raises_not_implemented():
    obs = _observer()
    # suppress the (expected) DeprecationWarning to isolate the raise
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        with pytest.raises(NotImplementedError):
            obs.observable(None, None, None, 15.0, 85.0, 60)
