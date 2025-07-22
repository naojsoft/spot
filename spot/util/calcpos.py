#
# calcpos.py -- module for wrapping astronomical ephemeris calculations
#
import os

# third-party imports
import numpy as np
from datetime import datetime, time, timedelta
from dateutil import tz
import dateutil.parser
import pandas as pd

from ginga.misc.Bunch import Bunch
# set up download directory for files
from ginga.util.paths import ginga_home
if not os.path.isdir(ginga_home):
    os.mkdir(ginga_home)
datadir = os.path.join(ginga_home, "downloads")
if not os.path.isdir(datadir):
    os.mkdir(datadir)

import erfa
from astropy.coordinates import SkyCoord, Latitude, Longitude, Angle
from astropy.time import Time
from astropy import units as u
from astropy.utils.iers import conf as ap_iers_conf
#ap_iers_conf.auto_download = False
ap_iers_conf.remote_timeout = 5.0
#ap_iers_conf.iers_degraded_accuracy = 'ignore'

from skyfield.api import Star, Loader, wgs84
from skyfield.earthlib import refraction
from skyfield import almanac
# don't download ephemeris to the CWD
load = Loader(datadir)

# Constants
earth_radius_m = 6378136.6
solar_radius_deg = 0.25
moon_radius_deg = 0.26

ssbodies = load('de421.bsp')
timescale = load.timescale()

# used for almanac calculations
horizon_6 = -6.0
horizon_12 = -12.0
horizon_18 = -18.0


def alt2airmass(alt_deg):
    xp = 1.0 / np.sin(np.radians(alt_deg + 244.0 / (165.0 + 47 * alt_deg ** 1.1)))
    return xp


am_inv = np.array([(alt2airmass(alt), alt) for alt in range(0, 91, 1)])


def airmass2alt(am):
    # TODO: vectorize
    if am < am_inv.T[0][-1]:
        return 90.0
    i = np.argmax(am_inv.T[0] < am)
    i = np.clip(i - 1, 0, len(am_inv) - 1)
    return am_inv.T[1][i]

#### Classes ####


class Observer:
    """
    Observer
    """
    def __init__(self, name, timezone=None, longitude=None, latitude=None,
                 elevation=0, pressure=0, temperature=0, humidity=0,
                 horizon_deg=None, date=None, wavelength=None,
                 description=None):
        super().__init__()
        self.name = name
        if timezone is None:
            # default to UTC
            timezone = tz.UTC
        self.tz_local = timezone
        if isinstance(longitude, str):
            self.lon_deg = Longitude(longitude, unit=u.deg, wrap_angle=180 * u.deg).deg
        else:
            self.lon_deg = longitude
        if isinstance(latitude, str):
            self.lat_deg = Latitude(latitude, unit=u.deg).deg
        else:
            self.lat_deg = latitude
        self.elev_m = elevation
        self.pressure_mbar = pressure
        self.temp_C = temperature
        self.rh_pct = humidity / 100.
        if date is None:
            date = datetime.now(tz=self.tz_local)
        self.date = date
        self.wavelength = wavelength
        self.description = description
        if horizon_deg is None:
            horizon_deg = np.degrees(- np.arccos(earth_radius_m / (earth_radius_m + self.elev_m)))
        self.horizon_deg = horizon_deg

        earth = ssbodies['earth']
        self.location = earth + wgs84.latlon(latitude_degrees=self.lat_deg,
                                             longitude_degrees=self.lon_deg,
                                             elevation_m=self.elev_m)

    @property
    def timezone(self):
        return self.tz_local

    @property
    def tz_utc(self):
        return tz.UTC

    def date_to_utc(self, date):
        """Convert a datetime to UTC.
        NOTE: If the datetime object is not timezone aware, it is
        assumed to be in the timezone of the observer.
        """
        if date.tzinfo is not None:
            # date is timezone-aware
            date = date.astimezone(tz.UTC)

        else:
            # date is a naive date: assume expressed in local time
            date = date.replace(tzinfo=self.tz_local)
            # and converted to UTC
            date = date.astimezone(tz.UTC)
        return date

    def date_to_local(self, date):
        """Convert a datetime to the observer's timezone.
        NOTE: If the datetime object is not timezone aware, it is
        assumed to be in UTC.
        """
        if date.tzinfo is not None:
            # date is timezone-aware
            date = date.astimezone(self.tz_local)

        else:
            # date is a naive date: assume expressed in UTC
            date = date.replace(tzinfo=tz.UTC)
            # and converted to local time
            date = date.astimezone(self.tz_local)

        return date

    def set_date(self, date):
        """Set the date for the observer.  This is converted and
        stored internally in the timezone set for the observer.
        """
        self.date = self.date_to_local(date)

    def radec_of(self, az_deg, alt_deg, date=None):
        if date is None:
            date = self.date
        obstime = timescale.from_datetime(date)
        apparent = self.location.at(obstime).from_altaz(alt_degrees=alt_deg,
                                                        az_degrees=az_deg)
        ra, dec, distance = apparent.radec()
        ra_deg, dec_deg = ra._degrees, dec._degrees
        return ra_deg, dec_deg

    def azalt_of(self, ra_deg, dec_deg, date=None):
        if date is None:
            date = self.date
        coord = Star(ra_hours=ra_deg / 15.0, dec_degrees=dec_deg)
        obstime = timescale.from_datetime(date)
        astrometric = self.location.at(obstime).observe(coord)
        apparent = astrometric.apparent()
        alt, az, distance = apparent.altaz(temperature_C=self.temp_C,
                                           pressure_mbar=self.pressure_mbar)
        az_deg, alt_deg = az.degrees, alt.degrees
        return az_deg, alt_deg

    def calc(self, body, time_start):
        return body.calc(self, time_start)

    def get_date(self, date_str, timezone=None):
        """Get a datetime object, converted from a date string.
        The timezone is assumed to be that of the observer, unless
        explicitly supplied in the `timezone` kwarg.
        """
        if timezone is None:
            timezone = self.tz_local

        if isinstance(date_str, datetime):
            # user actually passed a datetime object
            dt = date_str
        else:
            dt = dateutil.parser.parse(date_str)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone)
        else:
            dt = dt.astimezone(timezone)
        return dt

    def distance(self, tgt1, tgt2, time_start):
        c1 = self.calc(tgt1, time_start)
        c2 = self.calc(tgt2, time_start)

        d_alt = c1.alt_deg - c2.alt_deg
        d_az = c1.az_deg - c2.az_deg
        return (d_alt, d_az)

    def _find_setting(self, coord, start_dt, stop_dt, horizon_deg):
        # NOTE: fractional seconds seems to cause an exception inside
        # skyfield
        t0 = timescale.from_datetime(start_dt.replace(microsecond=0))
        t1 = timescale.from_datetime(stop_dt.replace(microsecond=0))
        # TODO: refraction function does not appear to work as expected
        r = refraction(0.0, temperature_C=self.temp_C,
                       pressure_mbar=self.pressure_mbar)
        r = horizon_deg + r
        t, y = almanac.find_settings(self.location, coord, t0, t1,
                                     horizon_degrees=r)
        return t, y

    def _find_rising(self, coord, start_dt, stop_dt, horizon_deg):
        # NOTE: fractional seconds seems to cause an exception inside
        # skyfield
        t0 = timescale.from_datetime(start_dt.replace(microsecond=0))
        t1 = timescale.from_datetime(stop_dt.replace(microsecond=0))
        # TODO: refraction function does not appear to work as expected
        r = refraction(0.0, temperature_C=self.temp_C,
                       pressure_mbar=self.pressure_mbar)
        r = horizon_deg + r
        t, y = almanac.find_risings(self.location, coord, t0, t1,
                                    horizon_degrees=r)
        return t, y

    def get_last(self, date=None):
        """Return the local apparent sidereal time."""
        # TODO: use skyfield to calculate this (see CalculationResult "last")
        if date is None:
            date = self.date
        else:
            date = self.get_date(date)
        last = Time(date).sidereal_time('apparent',
                                        longitude=self.lon_deg * u.deg)
        time_s = str(last).replace('h', ':').replace('m', ':').replace('s', '')
        dt = dateutil.parser.parse(time_s)
        return time(hour=dt.hour, minute=dt.minute, second=dt.second,
                    microsecond=dt.microsecond)

    def sunset(self, date=None):
        """Returns sunset in observer's time."""
        if date is None:
            date = self.date
        else:
            date = self.get_date(date)

        t, y = self._find_setting(ssbodies['sun'], date,
                                  date + timedelta(days=1, hours=1),
                                  self.horizon_deg - solar_radius_deg)
        return t[0].astimezone(self.tz_local)

    def sunrise(self, date=None):
        """Returns sunrise in observer's time."""
        if date is None:
            date = self.date
        else:
            date = self.get_date(date)

        t, y = self._find_rising(ssbodies['sun'], date,
                                 date + timedelta(days=1, hours=1),
                                 self.horizon_deg - solar_radius_deg)
        return t[0].astimezone(self.tz_local)

    def evening_twilight_6(self, date=None):
        """Returns evening 6 degree civil twilight(civil dusk) in observer's time.
        """
        if date is None:
            date = self.date
        else:
            date = self.get_date(date)

        t, y = self._find_setting(ssbodies['sun'], date,
                                  date + timedelta(days=1, hours=0),
                                  horizon_6 - solar_radius_deg)
        return t[0].astimezone(self.tz_local)

    def evening_twilight_12(self, date=None):
        """Returns evening 12 degree (nautical) twilight in observer's time.
        """
        if date is None:
            date = self.date
        else:
            date = self.get_date(date)

        t, y = self._find_setting(ssbodies['sun'], date,
                                  date + timedelta(days=1, hours=0),
                                  horizon_12 - solar_radius_deg)
        return t[0].astimezone(self.tz_local)

    def evening_twilight_18(self, date=None):
        """Returns evening 18 degree (civil) twilight in observer's time.
        """
        if date is None:
            date = self.date
        else:
            date = self.get_date(date)

        t, y = self._find_setting(ssbodies['sun'], date,
                                  date + timedelta(days=1, hours=0),
                                  horizon_18 - solar_radius_deg)
        return t[0].astimezone(self.tz_local)

    def morning_twilight_6(self, date=None):
        """Returns morning 6 degree civil twilight(civil dawn) in observer's time.
        """
        if date is None:
            date = self.date
        else:
            date = self.get_date(date)

        t, y = self._find_rising(ssbodies['sun'], date,
                                 date + timedelta(days=1, hours=0),
                                 horizon_6 - solar_radius_deg)
        return t[0].astimezone(self.tz_local)

    def morning_twilight_12(self, date=None):
        """Returns morning 12 degree (nautical) twilight in observer's time.
        """
        if date is None:
            date = self.date
        else:
            date = self.get_date(date)

        t, y = self._find_rising(ssbodies['sun'], date,
                                 date + timedelta(days=1, hours=0),
                                 horizon_12 - solar_radius_deg)
        return t[0].astimezone(self.tz_local)

    def morning_twilight_18(self, date=None):
        """Returns morning 18 degree (civil) twilight in observer's time.
        """
        if date is None:
            date = self.date
        else:
            date = self.get_date(date)

        t, y = self._find_rising(ssbodies['sun'], date,
                                 date + timedelta(days=1, hours=0),
                                 horizon_18 - solar_radius_deg)
        return t[0].astimezone(self.tz_local)

    def sun_set_rise_times(self, date=None):
        """Sunset, sunrise and twilight times. Returns a tuple with
        (sunset, 12d, 18d, 18d, 12d, sunrise) in observer's time.
        """
        rstimes = (self.sunset(date=date),
                   self.evening_twilight_12(date=date),
                   self.evening_twilight_18(date=date),
                   self.morning_twilight_18(date=date),
                   self.morning_twilight_12(date=date),
                   self.sunrise(date=date))
        return rstimes

    def moon_rise(self, date=None):
        """Returns moon rise time in observer's time."""
        if date is None:
            date = self.date
        else:
            date = self.get_date(date)

        t, y = self._find_rising(ssbodies['moon'], date,
                                 date + timedelta(days=2, hours=0),
                                 self.horizon_deg - moon_radius_deg)
        return t[0].astimezone(self.tz_local)

    def moon_set(self, date=None):
        """Returns moon set time in observer's time."""
        if date is None:
            date = self.date
        else:
            date = self.get_date(date)

        t, y = self._find_setting(ssbodies['moon'], date,
                                  date + timedelta(days=2, hours=0),
                                  self.horizon_deg - moon_radius_deg)
        return t[0].astimezone(self.tz_local)

    def moon_illumination(self, date=None):
        """Returns moon percentage of illumination."""
        if date is None:
            date = self.date
        else:
            date = self.get_date(date)

        cres = Moon.calc(self, date)
        return cres.moon_pct

    # TO BE DEPRECATED
    moon_phase = moon_illumination

    def night_center(self, date=None):
        """Returns night center in observer's time."""
        sunset = self.sunset(date=date)
        sunrise = self.sunrise(date=sunset)
        center = sunset + timedelta(seconds=(sunrise - sunset).total_seconds() / 2.0)
        center = self.date_to_local(center)
        return center

    def get_target_info(self, target, time_start=None, time_stop=None,
                        time_interval=5):
        """Compute various values for a target from sunrise to sunset.
        """
        if time_start is None:
            # default for start time is sunset on the current date
            time_start = self.sunset()
        if time_stop is None:
            # default for stop time is sunrise on the current date
            time_stop = self.sunrise(date=time_start)

        # create date array
        dt_arr = np.arange(time_start, time_stop + timedelta(minutes=time_interval),
                           timedelta(minutes=time_interval))
        return target.calc(self, dt_arr)

    def __repr__(self):
        return self.name

    def get_spec(self):
        return dict(name=self.name, timezone=self.tz_local, longitude=self.lon_deg,
                    latitude=self.lat_deg, elevation=self.elev_m,
                    pressure=self.pressure_mbar, temperature=self.temp_C,
                    humidity=self.rh_pct, horizon_deg=self.horizon_deg,
                    date=self.date, wavelength=self.wavelength,
                    description=self.description)

    @classmethod
    def from_spec(cls, spec_dct):
        spec = Bunch(spec_dct)
        return Observer(spec.name, timezone=spec.timezone, longitude=spec.longitude,
                        latitude=spec.latitude, elevation=spec.elevation,
                        pressure=spec.pressure, temperature=spec.temperature,
                        humidity=spec.humidity, horizon_deg=spec.horizon_deg,
                        date=spec.date, wavelength=spec.wavelength,
                        description=spec.description)

    __str__ = __repr__


class Body:

    def __init__(self, name, ra, dec, equinox, comment='',
                 pmra=None, pmdec=None):
        super().__init__()

        self.name = name
        self.ra = ra
        self.dec = dec
        self.equinox = equinox
        self.comment = comment
        # specify in mas/yr
        self.pmra = pmra
        self.pmdec = pmdec

    def _get_epoch(self, eq):
        if isinstance(eq, str):
            if eq.startswith('J'):
                eq = eq[1:]
        return float(eq)

    def _get_coord(self):   # noqa
        # vector construction, if the value passed is an array
        if isinstance(self.ra, np.ndarray):
            if isinstance(self.ra[0], str):
                # assume units are in hours and parse with astropy
                coord = SkyCoord(self.ra, self.dec,
                                 unit=(u.hourangle, u.degree))
                ra_deg, dec_deg = coord.ra.degree, coord.dec.degree
            else:
                ra_deg, dec_deg = self.ra.astype(float), self.dec.astype(float)

            if isinstance(self.equinox, np.ndarray):
                epoch = [self._get_epoch(eq) for eq in self.equinox]
            else:
                epoch = [self._get_epoch(self.equinox)] * len(self.ra)
            #epoch = timescale.tt(np.array(epoch))
            epoch = np.array(epoch)

            contents = dict(names=self.name, ra_degrees=ra_deg,
                            ra_hours=ra_deg / 15.0, dec_degrees=dec_deg,
                            epoch_year=epoch)
            if self.pmra is not None:
                contents['ra_mas_per_year'] = self.pmra
            if self.pmdec is not None:
                contents['dec_mas_per_year'] = self.pmdec

            df = pd.DataFrame(contents)
            coord = Star.from_dataframe(df)
        else:
            if isinstance(self.ra, str):
                # assume units are in hours and parse with astropy
                coord = SkyCoord(self.ra, self.dec,
                                 unit=(u.hourangle, u.degree))
                ra_deg, dec_deg = coord.ra.degree, coord.dec.degree
            else:
                ra_deg, dec_deg = float(self.ra), float(self.dec)

            epoch = self._get_epoch(self.equinox)

            # NOTE: when you are initializing from kwargs, the kwarg is "epoch"
            # but from a Pandas table it is "epoch_year"
            kwargs = dict()
            # Cannot pass None for optional parameters ra_mas_per_year or
            # dec_mas_per_year--it tries to use the value
            if self.pmra is not None:
                kwargs['ra_mas_per_year'] = self.pmra
            if self.pmdec is not None:
                kwargs['dec_mas_per_year'] = self.pmdec
            coord = Star(ra_hours=ra_deg / 15.0, dec_degrees=dec_deg,
                         epoch=epoch, **kwargs)

        return coord

    def calc(self, observer, date):
        return CalculationResult(self, observer, date)

    def clone(self):
        return Body(self.name, self.ra, self.dec, self.equinox,
                    comment=self.comment, pmra=self.pmra, pmdec=self.pmdec)


class SSBody(object):

    def __init__(self, name, body):
        super(SSBody, self).__init__()

        self.name = name
        self._body = body

    def _get_coord(self):
        return self._body

    def calc(self, observer, date):
        return CalculationResult(self, observer, date)


class CalculationResult(object):

    def __init__(self, body, observer, date):
        """
        `date` is a datetime.datetime object converted to observer's
        time.
        """
        self.observer = observer
        self.body = body
        # vector construction, if the value passed is an array
        if isinstance(date, np.ndarray):
            # NOTE: need to convert numpy.datetime64 to astropy time
            at = Time(date)
            self.obstime = timescale.from_astropy(at)
        else:
            self.obstime = timescale.from_datetime(date)

        # properties
        self._ut = None
        self._lt = None
        self._jd = None
        self._mjd = None
        self._gmst = None
        self._gast = None
        self._lmst = None
        self._last = None
        self._ra = None
        self._dec = None
        self._eq = None
        self._alt = None
        self._az = None
        self._ha = None
        self._pang = None
        self._am = None
        self._moon_alt = None
        self._moon_pct = None
        self._moon_sep = None
        self._atmos_disp = None

        # Conversion factor for wavelengths (Angstrom -> micrometer)
        self.angstrom_to_mm = 1. / 10000.

    @property
    def name(self):
        return self.body.name

    @property
    def ra(self):
        """Return right ascension in radians."""
        if self._ra is None:
            self._calc_radec()
        return self._ra.radians

    @property
    def ra_deg(self):
        """Return right ascension in degrees."""
        return np.degrees(self.ra)

    @property
    def dec(self):
        """Return declination in radians."""
        if self._dec is None:
            self._calc_radec()
        return self._dec.radians

    @property
    def dec_deg(self):
        """Return declination in degrees."""
        return np.degrees(self.dec)

    @property
    def equinox(self):
        if self._eq is None:
            self._calc_radec()
        return self._eq

    @property
    def alt(self):
        """Return altitude in radians."""
        if self._alt is None:
            self._calc_altaz()
        return self._alt.radians

    @property
    def az(self):
        """Return azimuth in radians."""
        if self._az is None:
            self._calc_altaz()
        return self._az.radians

    @property
    def alt_deg(self):
        """Return altitude in degrees."""
        if self._az is None:
            self._calc_altaz()
        return self._alt.degrees

    @property
    def az_deg(self):
        """Return azimuth in degrees."""
        if self._az is None:
            self._calc_altaz()
        return self._az.degrees

    @property
    def lt(self):
        """Return local time as a Python timzezone-aware datetime."""
        if self._lt is None:
            self._lt = self.obstime.astimezone(self.observer.tz_local)
        return self._lt

    @property
    def ut(self):
        """Return universal time as a Python timzezone-aware datetime."""
        if self._ut is None:
            self._ut = self.obstime.utc_datetime()
        return self._ut

    @property
    def jd(self):
        """Return the Julian Date."""
        if self._jd is None:
            self._jd = self.obstime.ut1
        return self._jd

    @property
    def mjd(self):
        """Return the Mean Julian Date."""
        if self._mjd is None:
            self._mjd = self.jd - 2400000.5
        return self._mjd

    @property
    def gmst(self):
        """Return Greenwich Mean Sidereal Time in radians."""
        if self._gmst is None:
            # NOTE:obstime.gmst is in hours
            self._gmst = self.obstime.gmst
        return np.radians(self._gmst * 15.0)

    @property
    def gast(self):
        """Return Greenwich Apparent Sidereal Time in radians."""
        if self._gast is None:
            # NOTE:obstime.gast is in hours
            self._gast = self.obstime.gast
        return np.radians(self._gast * 15.0)

    @property
    def lmst(self):
        """Return Local Mean Sidereal Time in radians."""
        if self._lmst is None:
            # NOTE:obstime.gmst is in hours
            _lmst = self.obstime.gmst + self.observer.lon_deg / 15.0
            # normalize to 24 hour time
            self._lmst = np.fmod(_lmst + 24.0, 24.0)
        return np.radians(self._lmst * 15)

    @property
    def last(self):
        """Return Local Apparent Sidereal Time in radians."""
        if self._last is None:
            # NOTE:obstime.gast is in hours
            _last = self.obstime.gast + self.observer.lon_deg / 15.0
            # normalize to 24 hour time
            self._last = np.fmod(_last + 24.0, 24.0)
        return np.radians(self._last * 15)

    @property
    def ha(self):
        """Return the Hour Angle in radians."""
        if self._ha is None:
            lmst = self.lmst     # force calculation of self._lmst
            _ha = Angle(self._lmst - self.ra_deg / 15.0, unit=u.hour)
            _ha.wrap_at(12 * u.hour, inplace=True)
            self._ha = _ha
        return self._ha.rad

    @property
    def pang(self):
        """Return the parallactic angle of the target(s) in radians."""
        if self._pang is None:
            self._pang = self._calc_parallactic(self.dec,
                                                self.ha,
                                                self.observer.lat_deg)
        return self._pang

    @property
    def pang_deg(self):
        """Return the parallactic angle of the target(s) in degrees."""
        return np.degrees(self.pang)

    @property
    def airmass(self):
        """Return the airmass of the target(s)."""
        if self._am is None:
            #self._am = alt2airmass(self.alt_deg)
            self._am = self._calc_airmass(self.alt_deg)
        return self._am

    @property
    def moon_alt(self):
        """Return the moon's altitude at the time of observation (in degrees)."""
        if self._moon_alt is None:
            # calculate moon altitude
            moon = ssbodies['moon']
            astrometric = self.observer.location.at(self.obstime).observe(moon)
            apparent = astrometric.apparent()
            alt, az, distance = apparent.altaz(temperature_C=self.observer.temp_C,
                                               pressure_mbar=self.observer.pressure_mbar)
            self._moon_alt = alt.degrees
        return self._moon_alt

    @property
    def moon_pct(self):
        """Return the moon's percentage of illumination (range: 0-1)."""
        if self._moon_pct is None:
            e = self.observer.location.at(self.obstime)
            s = e.observe(ssbodies['sun']).apparent()
            m = e.observe(ssbodies['moon']).apparent()
            self._moon_pct = m.fraction_illuminated(ssbodies['sun'])
        return self._moon_pct

    @property
    def moon_sep(self):
        """Return the moon's separation from target(s) (in degrees)."""
        if self._moon_sep is None:
            self._calc_altaz()
        return self._moon_sep

    @property
    def atmos_disp(self):
        if self._atmos_disp is None:
            self._atmos_disp = self._calc_atmos_disp(self.observer)
        return self._atmos_disp

    def _calc_parallactic(self, dec_rad, ha_rad, lat_deg):
        """Compute parallactic angle(s).
        From Meeus, J. [Astronomical Algorithms, p. 98]
        """
        lat_rad = np.radians(lat_deg)
        pang_rad = np.arctan2(np.sin(ha_rad),
                              np.tan(lat_rad) * np.cos(dec_rad) -
                              np.sin(dec_rad) * np.cos(ha_rad))
        return pang_rad

    def _calc_airmass(self, alt_deg):
        """Compute airmass(es)"""
        alt_deg = np.clip(alt_deg, 3.0, None)
        sz = 1.0 / np.sin(np.radians(alt_deg)) - 1.0
        xp = 1.0 + sz * (0.9981833 - sz * (0.002875 + 0.0008083 * sz))
        return xp

    def calc_separation_alt_az(self, body):
        """Compute deltas for azimuth and altitude from another target"""
        cr1 = self.body.calc(self.observer, self.ut)
        cr2 = body.calc(self.observer, self.ut)

        delta_az = cr1.az_deg - cr2.az_deg
        delta_alt = cr1.alt_deg - cr2.alt_deg
        return (delta_alt, delta_az)

    def calc_separation(self, body):
        """Compute separation from another target"""
        coord1 = self.body._get_coord()
        coord2 = body._get_coord()

        e = self.observer.location.at(self.obstime)
        r1 = e.observe(coord1)
        r2 = e.observe(coord2)
        sep = r1.separation_from(r2)

        return sep.arcseconds()

    def _calc_atmos_refco(self, bar_press_mbar, temp_degc, rh_pct, wl_mm):
        """Compute atmospheric refraction coefficients (radians)"""
        refa, refb = erfa.refco(bar_press_mbar, temp_degc, rh_pct, wl_mm)
        return (refa, refb)

    def _calc_atmos_disp(self, observer):
        """Compute atmospheric dispersion (radians)"""
        bar_press_mbar = observer.pressure_mbar
        temp_degc = observer.temp_C
        rh_pct = observer.rh_pct
        wl = observer.wavelength
        zd_rad = np.subtract(np.pi / 2.0, self.alt)
        tzd = np.tan(zd_rad)
        if wl is None:
            raise ValueError('Wavelength is None')
        else:
            if isinstance(wl, dict):
                atmos_disp_rad = {}
                for k, w in wl.items():
                    wl_mm = w * self.angstrom_to_mm
                    refa, refb = self._calc_atmos_refco(bar_press_mbar, temp_degc, rh_pct, wl_mm)
                    atmos_disp_rad[k] = (refa + refb * tzd * tzd) * tzd
            elif isinstance(wl, list):
                atmos_disp_rad = []
                for w in wl:
                    wl_mm = w * self.angstrom_to_mm
                    refa, refb = self._calc_atmos_refco(bar_press_mbar, temp_degc, rh_pct, wl_mm)
                    atmos_disp_rad.append((refa + refb * tzd * tzd) * tzd)
            else:
                wl_mm = wl * self.angstrom_to_mm
                refa, refb = self._calc_atmos_refco(bar_press_mbar, temp_degc, rh_pct, wl_mm)
                atmos_disp_rad = (refa + refb * tzd * tzd) * tzd
            return atmos_disp_rad

    def _calc_radec(self):
        coord = self.body._get_coord()
        if hasattr(coord, 'ra'):
            self._ra, self._dec = coord.ra, coord.dec
            self._ra_deg, self._dec_deg = coord.ra.hours * 15.0, coord.dec.degrees
            # TODO
            self._eq = 2000.0
        else:
            # moons, planets, etc.
            # Need to calculate the apparent ra/dec from the azalt
            self._calc_altaz()
            apparent = self.observer.location.at(self.obstime).from_altaz(alt_degrees=self.alt_deg,
                                                                          az_degrees=self.az_deg)
            self._ra, self._dec, distance = apparent.radec()
            self._ra_deg, self._dec_deg = self._ra.hours * 15.0, self._dec.degrees
            # TODO
            self._eq = 2000.0

    def _calc_altaz(self):
        coord = self.body._get_coord()
        astrometric = self.observer.location.at(self.obstime).observe(coord)
        apparent = astrometric.apparent()
        alt, az, distance = apparent.altaz(temperature_C=self.observer.temp_C,
                                           pressure_mbar=self.observer.pressure_mbar)
        self._az, self._alt = az, alt

        # calculate moon separation from target(s)
        moon = ssbodies['moon']
        astrometric_m = self.observer.location.at(self.obstime).observe(moon)
        apparent_m = astrometric_m.apparent()
        sep = apparent.separation_from(apparent_m)
        self._moon_sep = sep.degrees

    def get_dict(self, columns=None):
        if columns is None:
            return dict(name=self.name, ra=self.ra, ra_deg=self.ra_deg,
                        dec=self.dec, dec_deg=self.dec_deg, az=self.az,
                        equinox=self.equinox,
                        az_deg=self.az_deg, alt=self.alt, alt_deg=self.alt_deg,
                        lt=self.lt, ut=self.ut, jd=self.jd, mjd=self.mjd,
                        gast=self.gast, gmst=self.gmst, last=self.last,
                        lmst=self.lmst, ha=self.ha, pang=self.pang,
                        pang_deg=self.pang_deg, airmass=self.airmass,
                        moon_alt=self.moon_alt, moon_pct=self.moon_pct,
                        moon_sep=self.moon_sep,
                        atmos_disp_observing=self.atmos_disp['observing'],
                        atmos_disp_guiding=self.atmos_disp['guiding'])
        else:
            return {colname: getattr(self, colname) for colname in columns}

    def __len__(self):
        if isinstance(self.az, np.ndarray):
            return len(self.az)
        return 1


Moon = SSBody('Moon', ssbodies['moon'])
Sun = SSBody('Sun', ssbodies['sun'])
Mercury = SSBody('Mercury', ssbodies['mercury'])
Venus = SSBody('Venus', ssbodies['venus'])
Mars = SSBody('Mars', ssbodies['mars'])
Jupiter = SSBody('Jupiter', ssbodies['jupiter barycenter'])
Saturn = SSBody('Saturn', ssbodies['saturn barycenter'])
Uranus = SSBody('Uranus', ssbodies['uranus barycenter'])
Neptune = SSBody('Neptune', ssbodies['neptune barycenter'])
Pluto = SSBody('Pluto', ssbodies['pluto barycenter'])


def get_ssbody(lookup_name, myname=None):
    if myname is None:
        myname = lookup_name
    return SSBody(myname, ssbodies[lookup_name.lower()])

#END
