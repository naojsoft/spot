#
# test_calcpos_frame_pm.py -- equinox/frame handling and proper motion
#
# Verifies that (a) the equinox is parsed from the several accepted formats,
# (b) non-J2000 coordinates are precessed/rotated to ICRS (FK4 for B1950,
# FK5 otherwise), and (c) proper motion is propagated from the catalog epoch.
# "Truth" comes from direct astropy transforms.
#
from datetime import datetime

import numpy as np
from dateutil import tz
import pytest

from astropy.coordinates import SkyCoord, FK4, FK5, ICRS
from astropy.time import Time
import astropy.units as u

from spot.util import calcpos
from spot.util.target import normalize_ra_dec_equinox as norm

UTC = tz.UTC
T0 = datetime(2024, 5, 16, 8, 0, tzinfo=UTC)


def _obs():
    return calcpos.Observer('subaru', timezone=tz.gettz('US/Hawaii'),
                            longitude=-155.4761, latitude=19.8256,
                            elevation=4139, pressure=615, temperature=0)


def _radec(coord):
    return float(coord.ra.deg), float(coord.dec.deg)


class TestEquinoxParsing:

    @pytest.mark.parametrize("eq,expected", [
        (2000.0, 2000.0), ("2000", 2000.0), ("J2000", 2000.0),
        ("B1950", 1950.0), ("1950", 1950.0), ("J1950", 1950.0),
        (None, 2000.0), ("", 2000.0), (1975.0, 1975.0),
    ])
    def test_equinox_formats(self, eq, expected):
        _, _, out = norm("10:00:00", "+20:00:00", eq)
        assert out == expected


class TestEquinoxFrame:
    RA, DEC = 150.0, 20.0

    def test_j2000_is_icrs_noop(self):
        c = calcpos.Body('j', self.RA, self.DEC, 2000.0)._get_coord(T0)
        assert np.isclose(c.ra.deg, self.RA) and np.isclose(c.dec.deg, self.DEC)

    def test_b1950_precessed_to_icrs(self):
        got = calcpos.Body('b', self.RA, self.DEC, 1950.0)._get_coord(T0)
        want = SkyCoord(self.RA * u.deg, self.DEC * u.deg, frame=FK4,
                        equinox='B1950').transform_to(ICRS())
        assert got.separation(want).arcsec < 1e-3
        # sanity: it really moved (precession over ~50 yr is ~0.7 deg)
        assert got.separation(SkyCoord(self.RA * u.deg, self.DEC * u.deg,
                                       frame=ICRS())).deg > 0.5

    def test_fk5_nonstandard_equinox(self):
        got = calcpos.Body('f', self.RA, self.DEC, 1975.0)._get_coord(T0)
        want = SkyCoord(self.RA * u.deg, self.DEC * u.deg, frame=FK5,
                        equinox=Time('J1975.0')).transform_to(ICRS())
        assert got.separation(want).arcsec < 1e-3

    def test_grid_matches_per_target_b1950(self):
        obs = _obs()
        b = lambda: calcpos.Body('b', self.RA, self.DEC, 1950.0)  # noqa: E731
        g = calcpos.calc_targets(obs, ['b'], [b()], np.array([T0]),
                                 columns=['alt_deg', 'az_deg'])
        d = b().calc(obs, T0).get_dict(columns=['alt_deg', 'az_deg'])
        assert np.isclose(float(g['b']['alt_deg'][0]), float(d['alt_deg']),
                          atol=1e-6)
        assert np.isclose(float(g['b']['az_deg'][0]), float(d['az_deg']),
                          atol=1e-6)

    def test_grid_mixed_equinoxes(self):
        obs = _obs()
        bodies = [calcpos.Body('a', self.RA, self.DEC, 2000.0),
                  calcpos.Body('b', self.RA, self.DEC, 1950.0)]
        g = calcpos.calc_targets(obs, ['a', 'b'], bodies, np.array([T0]),
                                 columns=['alt_deg'])
        # same catalog RA/Dec but different equinox -> different sky position
        assert not np.isclose(float(g['a']['alt_deg'][0]),
                              float(g['b']['alt_deg'][0]), atol=1e-3)
        # each equals its own per-target calc
        for k, body in zip(['a', 'b'], bodies):
            d = body.calc(obs, T0).get_dict(columns=['alt_deg'])
            assert np.isclose(float(g[k]['alt_deg'][0]), float(d['alt_deg']),
                              atol=1e-6)


class TestProperMotion:
    # Barnard's star: very large proper motion
    RA, DEC = 269.4521, 4.6933
    PMRA, PMDEC = -802.8, 10362.5   # mas/yr (pmra = dRA*cos(dec))

    def _expected_icrs(self, ref):
        c = SkyCoord(ra=self.RA * u.deg, dec=self.DEC * u.deg,
                     pm_ra_cosdec=self.PMRA * u.mas / u.yr,
                     pm_dec=self.PMDEC * u.mas / u.yr,
                     obstime=Time('J2000.0'), frame=ICRS)
        import warnings
        import erfa
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', erfa.ErfaWarning)
            return c.apply_space_motion(new_obstime=Time(ref))

    def test_pm_shifts_position(self):
        got = calcpos.Body('barnard', self.RA, self.DEC, 2000.0,
                           pmra=self.PMRA, pmdec=self.PMDEC)._get_coord(T0)
        want = self._expected_icrs(T0)
        assert got.separation(want).arcsec < 1e-3
        # dec should have moved ~+250 arcsec over ~24 yr
        d_dec = (float(got.dec.deg) - self.DEC) * 3600.0
        assert 230.0 < d_dec < 270.0

    def test_no_pm_no_shift(self):
        c = calcpos.Body('x', self.RA, self.DEC, 2000.0)._get_coord(T0)
        assert np.isclose(c.ra.deg, self.RA) and np.isclose(c.dec.deg, self.DEC)

    def test_grid_pm_matches_per_target(self):
        obs = _obs()
        mk = lambda: calcpos.Body('b', self.RA, self.DEC, 2000.0,  # noqa: E731
                                  pmra=self.PMRA, pmdec=self.PMDEC)
        g = calcpos.calc_targets(obs, ['b'], [mk()], np.array([T0]),
                                 columns=['alt_deg', 'az_deg'])
        d = mk().calc(obs, T0).get_dict(columns=['alt_deg', 'az_deg'])
        assert np.isclose(float(g['b']['alt_deg'][0]), float(d['alt_deg']),
                          atol=1e-6)
        assert np.isclose(float(g['b']['az_deg'][0]), float(d['az_deg']),
                          atol=1e-6)

    def test_grid_mixed_pm_and_no_pm(self):
        obs = _obs()
        bodies = [calcpos.Body('pm', self.RA, self.DEC, 2000.0,
                               pmra=self.PMRA, pmdec=self.PMDEC),
                  calcpos.Body('no', self.RA, self.DEC, 2000.0)]
        g = calcpos.calc_targets(obs, ['pm', 'no'], bodies, np.array([T0]),
                                 columns=['dec_deg'])
        # the no-pm target keeps its catalog dec; the pm target does not
        assert np.isclose(float(g['no']['dec_deg'][0]), self.DEC, atol=1e-6)
        assert not np.isclose(float(g['pm']['dec_deg'][0]), self.DEC, atol=1e-3)


def _az_diff(a, b):
    """Smallest absolute azimuth difference in degrees (wrap-aware)."""
    return abs((a - b + 180.0) % 360.0 - 180.0)


class TestAzElRoundTrip:
    """radec_of() and the forward az/el calc are exact inverses at a fixed
    time.

    This is the property the TargetGenerator relies on: converting an
    (az, el) to RA/DEC *at the site's set time* and then computing the
    target's az/el back at that same time must return the original (az, el).
    (A discrepancy at the telescope for a generated target comes from
    observing at a different time than the one used to generate it -- az/el
    is time-dependent -- not from this conversion.)
    """

    AZ_EL = [(120.0, 60.0), (270.0, 30.0), (45.0, 15.0),
             (0.0, 80.0), (359.0, 5.0), (180.0, 45.0)]

    @pytest.mark.parametrize("az_deg,el_deg", AZ_EL)
    def test_radec_of_calc_roundtrip(self, az_deg, el_deg):
        # az/el -> RA/DEC (radec_of), stored as a J2000 target (as the
        # TargetGenerator does), then RA/DEC -> az/el via the forward calc
        obs = _obs()
        ra_deg, dec_deg = obs.radec_of(az_deg, el_deg, date=T0)
        cres = calcpos.Body('rt', ra_deg, dec_deg, 2000.0).calc(obs, T0)
        assert _az_diff(cres.az_deg, az_deg) < 1e-4
        assert np.isclose(cres.alt_deg, el_deg, atol=1e-4)

    @pytest.mark.parametrize("az_deg,el_deg", AZ_EL)
    def test_radec_of_azalt_of_inverse(self, az_deg, el_deg):
        # radec_of and azalt_of are direct inverses at the same time
        obs = _obs()
        ra_deg, dec_deg = obs.radec_of(az_deg, el_deg, date=T0)
        az2, el2 = obs.azalt_of(ra_deg, dec_deg, date=T0)
        assert _az_diff(az2, az_deg) < 1e-4
        assert np.isclose(el2, el_deg, atol=1e-4)

    def test_time_is_honored(self):
        # the conversion actually uses the supplied time: the same (az, el)
        # maps to different RA/DEC at times ~an hour apart, and each still
        # round-trips exactly at its own time
        obs = _obs()
        az_deg, el_deg = 100.0, 40.0
        t1 = datetime(2024, 5, 16, 8, 0, tzinfo=UTC)
        t2 = datetime(2024, 5, 16, 9, 0, tzinfo=UTC)

        ra1, dec1 = obs.radec_of(az_deg, el_deg, date=t1)
        ra2, dec2 = obs.radec_of(az_deg, el_deg, date=t2)
        # an hour of sidereal rotation moves the RA/DEC well clear
        assert SkyCoord(ra1 * u.deg, dec1 * u.deg).separation(
            SkyCoord(ra2 * u.deg, dec2 * u.deg)).deg > 1.0

        for ra, dec, t in [(ra1, dec1, t1), (ra2, dec2, t2)]:
            c = calcpos.Body('t', ra, dec, 2000.0).calc(obs, t)
            assert _az_diff(c.az_deg, az_deg) < 1e-4
            assert np.isclose(c.alt_deg, el_deg, atol=1e-4)
