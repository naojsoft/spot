import pytest
import numpy as np
from dateutil.parser import parse as parse_date

from spot.util import calcpos, sites
sites.configure_default_sites()


test_data = [
    # site and a date/time with object coordinates and calculation results
    dict(site="subaru", time="2024-05-16 22:30 HST", objname="somestar", ra_hms="11:48:16.650", dec_dms="+52:51:50.30", equinox="2000.0",
         res_ra=3.09616, res_ra_deg=177.396771, res_dec=0.9203495, res_dec_deg=52.732143, res_az=5.793692, res_az_deg=331.9541331,
         res_alt=0.86729592, res_alt_deg=49.692396, res_lt_str="2024-05-16 22:30 HST", res_ut_str="2024-05-17 08:30:00 UTC",
         res_jd=2460447.8541666665, res_mjd=60447.354166666664, res_gast=0.052954467, res_gmst=0.0529761, res_last=3.6225696, res_lmst=3.6225208, res_ha=0.5263631,
         res_pang=2.322641, res_pang_deg=133.077528, res_airmass=1.310465, res_moon_alt=50.2342245, res_moon_pct=0.675, res_moon_sep=46.256577,
         res_atmos_disp=dict(guiding=0.00015, observing=0.000155)),
    ]

class TestCalcpos_Result:

    def do_calc(self, td):
        site = sites.get_site(td['site'])
        site.initialize()
        observer = site.observer
        target = calcpos.Body(td['objname'], td['ra_hms'], td['dec_dms'], td['equinox'])
        obstime = observer.get_date(td['time'])
        cres = target.calc(observer, obstime)
        return cres

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_lt(self, td):
        cres = self.do_calc(td)
        expected = parse_date(td['res_lt_str'])
        diff = abs((cres.lt - expected).total_seconds())
        # should be within 1 sec
        assert (diff < 1), \
            Exception("local times differ: {} vs. {}".format(
                cres.lt, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_ut(self, td):
        cres = self.do_calc(td)
        expected = parse_date(td['res_ut_str'])
        diff = abs((cres.ut - expected).total_seconds())
        # should be within 1 sec
        assert (diff < 1), \
            Exception("UT times differ: {} vs. {}".format(
                cres.ut, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_ra(self, td):
        cres = self.do_calc(td)
        expected = td['res_ra']
        assert np.isclose(cres.ra, expected, atol=0.01), \
            Exception("ra differs: {} vs. {}".format(
                cres.ra, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_ra_deg(self, td):
        cres = self.do_calc(td)
        expected = td['res_ra_deg']
        assert np.isclose(cres.ra_deg, expected, atol=0.5), \
            Exception("ra_deg differs: {} vs. {}".format(
                cres.ra_deg, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_dec(self, td):
        cres = self.do_calc(td)
        expected = td['res_dec']
        assert np.isclose(cres.dec, expected, atol=0.01), \
            Exception("dec differs: {} vs. {}".format(
                cres.dec, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_dec_deg(self, td):
        cres = self.do_calc(td)
        expected = td['res_dec_deg']
        assert np.isclose(cres.dec_deg, expected, atol=0.5), \
            Exception("dec_deg differs: {} vs. {}".format(
                cres.dec_deg, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_az(self, td):
        cres = self.do_calc(td)
        expected = td['res_az']
        assert np.isclose(cres.az, expected, atol=0.001), \
            Exception("az differs: {} vs. {}".format(
                cres.az, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_az_deg(self, td):
        cres = self.do_calc(td)
        expected = td['res_az_deg']
        assert np.isclose(cres.az_deg, expected, atol=0.001), \
            Exception("az_deg differs: {} vs. {}".format(
                cres.az_deg, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_alt(self, td):
        cres = self.do_calc(td)
        expected = td['res_alt']
        assert np.isclose(cres.alt, expected, atol=0.001), \
            Exception("alt differs: {} vs. {}".format(
                cres.alt, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_alt_deg(self, td):
        cres = self.do_calc(td)
        expected = td['res_alt_deg']
        assert np.isclose(cres.alt_deg, expected, atol=0.1), \
            Exception("alt_deg differs: {} vs. {}".format(
                cres.alt_deg, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_jd(self, td):
        cres = self.do_calc(td)
        expected = td['res_jd']
        assert np.isclose(cres.jd, expected, atol=0.01), \
            Exception("jd differs: {} vs. {}".format(
                cres.jd, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_mjd(self, td):
        cres = self.do_calc(td)
        expected = td['res_mjd']
        assert np.isclose(cres.mjd, expected, atol=0.01), \
            Exception("mjd differs: {} vs. {}".format(
                cres.mjd, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_gmst(self, td):
        cres = self.do_calc(td)
        expected = td['res_gmst']
        assert np.isclose(cres.gmst, expected, atol=0.01), \
            Exception("gmst differs: {} vs. {}".format(
                cres.gmst, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_gast(self, td):
        cres = self.do_calc(td)
        expected = td['res_gast']
        assert np.isclose(cres.gast, expected, atol=0.01), \
            Exception("gast differs: {} vs. {}".format(
                cres.gast, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_lmst(self, td):
        cres = self.do_calc(td)
        expected = td['res_lmst']
        assert np.isclose(cres.lmst, expected, atol=0.01), \
            Exception("lmst differs: {} vs. {}".format(
                cres.lmst, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_last(self, td):
        cres = self.do_calc(td)
        expected = td['res_last']
        assert np.isclose(cres.last, expected, atol=0.01), \
            Exception("last differs: {} vs. {}".format(
                cres.last, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_ha(self, td):
        cres = self.do_calc(td)
        expected = td['res_ha']
        assert np.isclose(cres.ha, expected, atol=0.01), \
            Exception("ha differs: {} vs. {}".format(
                cres.ha, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_pang(self, td):
        cres = self.do_calc(td)
        expected = td['res_pang']
        assert np.isclose(cres.pang, expected, atol=0.05), \
            Exception("pang differs: {} vs. {}".format(
                cres.pang, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_pang_deg(self, td):
        cres = self.do_calc(td)
        expected = td['res_pang_deg']
        assert np.isclose(cres.pang_deg, expected, atol=1.0), \
            Exception("pang_deg differs: {} vs. {}".format(
                cres.pang_deg, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_airmass(self, td):
        cres = self.do_calc(td)
        expected = td['res_airmass']
        assert np.isclose(cres.airmass, expected, atol=0.001), \
            Exception("airmass differs: {} vs. {}".format(
                cres.airmass, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_moon_alt(self, td):
        cres = self.do_calc(td)
        expected = td['res_moon_alt']
        assert np.isclose(cres.moon_alt, expected, atol=0.01), \
            Exception("moon_alt differs: {} vs. {}".format(
                cres.moon_alt, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_moon_pct(self, td):
        cres = self.do_calc(td)
        expected = td['res_moon_pct']
        assert np.isclose(cres.moon_pct, expected, atol=0.01), \
            Exception("moon_pct differs: {} vs. {}".format(
                cres.moon_pct, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_moon_sep(self, td):
        cres = self.do_calc(td)
        expected = td['res_moon_sep']
        assert np.isclose(cres.moon_sep, expected, atol=0.01), \
            Exception("moon_sep differs: {} vs. {}".format(
                cres.moon_sep, expected))

    @pytest.mark.parametrize(
        ("td"), test_data)
    def test_atmos_disp(self, td):
        cres = self.do_calc(td)
        expected = td['res_atmos_disp']['guiding']
        assert np.isclose(cres.atmos_disp['guiding'], expected, atol=0.0001), \
            Exception("atmos_disp (guiding) differs: {} vs. {}".format(
                cres.atmos_disp['guiding'], expected))
        expected = td['res_atmos_disp']['observing']
        assert np.isclose(cres.atmos_disp['observing'], expected, atol=0.0001), \
            Exception("atmos_disp (observing) differs: {} vs. {}".format(
                cres.atmos_disp['observing'], expected))
