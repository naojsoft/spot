#
# calcpos.py -- module for wrapping astronomical ephemeris calculations
#
import os

# third-party imports
import numpy as np
from datetime import datetime, time, timedelta
from dateutil import tz
import dateutil.parser

import warnings

import erfa
from astropy import units as u
from astropy.utils import minversion
from astropy.time import Time
from astropy.coordinates import (EarthLocation, Longitude, Latitude,
                                 Angle, SkyCoord, AltAz, ICRS, FK4, FK5,
                                 get_body, solar_system_ephemeris)
from astropy.utils import iers as ap_iers
ap_iers_conf = ap_iers.conf
#ap_iers_conf.auto_download = False
ap_iers_conf.remote_timeout = 5.0
ap_iers_conf.iers_degraded_accuracy = 'ignore'

ASTROPY_LT_6_0_0 = not minversion("astropy", "6.0.0")

from ginga.util import paths

from skyfield import almanac
from skyfield.api import Loader, wgs84
from skyfield.earthlib import refraction

# Constants
earth_radius_m = 6378136.6
solar_radius_deg = 0.25
moon_radius_deg = 0.26


def _get_spot_home():
    """Resolve SPOT's home directory.

    Prefers an explicitly-configured location -- the ``GINGA_HOME`` env var,
    or a home set by the SPOT launcher / pyscript server via
    ``ginga.util.paths.set_home`` (which is how ``$CONFHOME`` is honored at
    startup).  Falls back to ``$CONFHOME/spot`` or ``~/.spot`` when SPOT's
    home has not been configured (e.g. calcpos imported by the test-suite or
    by qplan without going through the launcher).
    """
    if 'GINGA_HOME' in os.environ:
        return os.environ['GINGA_HOME']
    if paths.ginga_home and paths.ginga_home != os.path.join(paths.home,
                                                             '.ginga'):
        return paths.ginga_home
    confhome = os.environ.get('CONFHOME')
    if confhome:
        return os.path.join(confhome, 'spot')
    return os.path.join(paths.home, '.spot')


def get_datadir(create=False):
    """Directory where astropy and skyfield stage/cache their data files
    (the de421.bsp planetary ephemeris and the finals2000A.all IERS-A
    table).  This is ``<spot-home>/downloads`` -- the same location the
    pyscript server pre-stages files into.
    """
    datadir = os.path.join(_get_spot_home(), 'downloads')
    if create:
        os.makedirs(datadir, exist_ok=True)
    return datadir


def _configure_astropy_data():
    """Point astropy at SPOT's data directory.

    Cheap (no network, no directory creation), so it runs at import: the
    global ephemeris / IERS state must be in place before any coordinate
    transform.
    """
    datadir = get_datadir()

    # Route astropy's download cache into datadir.  astropy >= 8.0 honors
    # ASTROPY_CACHE_DIR (an absolute path that takes precedence over
    # XDG_CACHE_HOME); set it before the cache is first used.  (Earlier
    # astropy has no clean permanent setter, so its cache is left at the
    # default there.)
    if minversion("astropy", "8.0"):
        os.environ.setdefault("ASTROPY_CACHE_DIR", datadir)

    # Use a pre-staged IERS-A Earth-orientation table (finals2000A.all) if
    # present, so Earth-orientation lookups need no network (e.g. under
    # Pyodide, which has no ssl module).
    iers_path = os.path.join(datadir, 'finals2000A.all')
    if os.path.exists(iers_path):
        try:
            ap_iers.earth_orientation_table.set(
                ap_iers.IERS_A.open(iers_path))
        except Exception:
            pass

    # Solar-system ephemeris for get_body(): prefer the locally-staged
    # de421.bsp (the same kernel skyfield uses -- consistent, and already
    # present) and fall back to astropy's built-in analytic ephemeris.
    # Never use a name that would trigger a download (e.g. "jpl"): that
    # needs ssl/network, which fails under Pyodide.
    de421_path = os.path.join(datadir, 'de421.bsp')
    try:
        solar_system_ephemeris.set(de421_path if os.path.exists(de421_path)
                                   else "builtin")
    except Exception:
        solar_system_ephemeris.set("builtin")


_configure_astropy_data()


# Skyfield planetary ephemeris + timescale, loaded lazily so that merely
# importing this module performs no network I/O or directory creation.  The
# first access downloads/loads de421.bsp into get_datadir().
_sf_loader = None
_ssbodies = None
_timescale = None


def _get_loader():
    global _sf_loader
    if _sf_loader is None:
        # create the directory now that we are about to write/download into it
        _sf_loader = Loader(get_datadir(create=True))
    return _sf_loader

# used for twilight calculations
horizon_6 = -6.0
horizon_12 = -12.0
horizon_18 = -18.0


def alt2airmass(alt_deg):
    xp = 1.0 / np.sin(np.radians(alt_deg + 244.0 / (165.0 + 47 * alt_deg ** 1.1)))
    return xp


def alt_to_airmass(alt_deg):
    """Standardized airmass from altitude (degrees).

    Uses the same formula as the skyfield backend (spot.util.calcpos) so the
    'airmass' column is backend-independent regardless of whether alt/az came
    from skyfield or astropy.  (alt2airmass() above is a different formula,
    kept only for the airmass->altitude inversion in observable().)
    """
    alt_deg = np.clip(alt_deg, 3.0, None)
    sz = 1.0 / np.sin(np.radians(alt_deg)) - 1.0
    return 1.0 + sz * (0.9981833 - sz * (0.002875 + 0.0008083 * sz))


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

        self.location = EarthLocation(lat=Latitude(self.lat_deg * u.deg),
                                      lon=Longitude(self.lon_deg * u.deg),
                                      height=self.elev_m * u.m)
        # for risings/settings
        earth = get_ssbodies()['earth']
        self.skyfield_location = earth + wgs84.latlon(latitude_degrees=self.lat_deg,
                                                      longitude_degrees=self.lon_deg,
                                                      elevation_m=self.elev_m)
        # cached per-time-array geometry shared across targets (see
        # _obs_geometry): the AltAz frame + Moon position, which depend only
        # on (observer, time), not on the target
        self._geom = None
        self._geom_key = None

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
        obstime = Time(date)
        frame = AltAz(alt=alt_deg * u.deg, az=az_deg * u.deg,
                      obstime=obstime, location=self.location,
                      pressure=self.pressure_mbar * u.mbar,
                      temperature=self.temp_C * u.deg_C,
                      relative_humidity=self.rh_pct,
                      #obswl=self.wavelength
                      )
        coord = frame.transform_to(ICRS())

        ra_deg, dec_deg = coord.ra.deg, coord.dec.deg
        return ra_deg, dec_deg

    def azalt_of(self, ra_deg, dec_deg, date=None):
        if date is None:
            date = self.date
        obstime = Time(date)
        coord = SkyCoord(frame=ICRS, ra=ra_deg * u.deg, dec=dec_deg * u.deg,
                         obstime=obstime)
        frame = AltAz(obstime=obstime, location=self.location,
                      pressure=self.pressure_mbar * u.mbar,
                      temperature=self.temp_C * u.deg_C,
                      relative_humidity=self.rh_pct,
                      #obswl=self.wavelength
                      )
        altaz = coord.transform_to(frame)
        # NOTE: airmass available from frame with 'secz' attribute

        az_deg, el_deg = altaz.az.deg, altaz.alt.deg
        return az_deg, el_deg

    def calc(self, body, time_start):
        return body.calc(self, time_start)

    def get_spec(self):
        """A picklable dict describing this observer (see from_spec).  Used to
        ship an observer to worker processes (populate_periods_mp)."""
        # __init__ takes humidity as a percentage (rh_pct = humidity/100), so
        # undo that here for a clean round-trip -- astropy's AltAz uses
        # relative_humidity for refraction, so a mismatch shifts alt near the
        # horizon (worker vs parent).
        return dict(name=self.name, timezone=self.tz_local,
                    longitude=self.lon_deg, latitude=self.lat_deg,
                    elevation=self.elev_m, pressure=self.pressure_mbar,
                    temperature=self.temp_C, humidity=self.rh_pct * 100.0,
                    horizon_deg=self.horizon_deg, date=self.date,
                    wavelength=self.wavelength, description=self.description)

    @classmethod
    def from_spec(cls, spec):
        return cls(spec['name'], timezone=spec['timezone'],
                   longitude=spec['longitude'], latitude=spec['latitude'],
                   elevation=spec['elevation'], pressure=spec['pressure'],
                   temperature=spec['temperature'], humidity=spec['humidity'],
                   horizon_deg=spec['horizon_deg'], date=spec['date'],
                   wavelength=spec['wavelength'], description=spec['description'])

    def _obs_geometry(self, obstime):
        """AltAz frame + Moon geometry for `obstime`, memoized by the time
        array and shared across all targets in a pass.

        The AltAz frame and the Moon's position depend only on
        (observer, time), not on the target, so computing them once and
        reusing them across every target avoids rebuilding the frame and
        re-fetching the Moon for each target.
        """
        tt = np.asarray(obstime.jd)
        key = hash((tt.shape, tt.tobytes()))
        if self._geom is not None and self._geom_key == key:
            return self._geom
        frame = AltAz(obstime=obstime, location=self.location,
                      pressure=self.pressure_mbar * u.mbar,
                      temperature=self.temp_C * u.deg_C,
                      relative_humidity=self.rh_pct,
                      #obswl=self.wavelength
                      )
        moon = get_body('moon', obstime, location=self.location)
        moon_altaz = moon.transform_to(frame)
        self._geom = dict(frame=frame, moon=moon,
                          moon_alt_deg=moon_altaz.alt.deg)
        self._geom_key = key
        return self._geom

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

    def observable(self, target, time_start, time_stop,
                   el_min_deg, el_max_deg, time_needed,
                   airmass=None, moon_sep=None):
        """Deprecated and non-functional.

        .. deprecated::
            This method was written for the previous skyfield backend and was
            never ported to the current astropy-based ``Body``/``SSBody``
            targets (it calls ``target._get_coord()`` without the required
            ``obstime`` and treats the astropy ``EarthLocation`` as a skyfield
            observer), so it no longer works.  It is also unused within SPOT
            and qplan.  Use
            :meth:`spot.util.eph_cache.EphemerisCache.observable` -- or build
            visibility directly from :meth:`Observer.calc` -- instead.
        """
        warnings.warn(
            "Observer.observable() is deprecated and non-functional: it was "
            "written for the old skyfield backend and was never ported to the "
            "current astropy-based targets.  Use "
            "spot.util.eph_cache.EphemerisCache.observable() (or build "
            "visibility from Observer.calc()) instead.",
            DeprecationWarning, stacklevel=2)
        raise NotImplementedError(
            "Observer.observable() is deprecated; use "
            "spot.util.eph_cache.EphemerisCache.observable() instead.")

    def distance(self, tgt1, tgt2, time_start):
        c1 = self.calc(tgt1, time_start)
        c2 = self.calc(tgt2, time_start)

        d_alt = c1.alt_deg - c2.alt_deg
        d_az = c1.az_deg - c2.az_deg
        return (d_alt, d_az)

    def _find_setting(self, coord, start_dt, stop_dt, horizon_deg):
        t0 = get_timescale().from_datetime(start_dt)
        t1 = get_timescale().from_datetime(stop_dt)
        # TODO: refraction function does not appear to work as expected
        r = refraction(0.0, temperature_C=self.temp_C,
                       pressure_mbar=self.pressure_mbar)
        r = horizon_deg + r
        t, y = almanac.find_settings(self.skyfield_location, coord, t0, t1,
                                     horizon_degrees=r)
        return t, y

    def _find_rising(self, coord, start_dt, stop_dt, horizon_deg):
        t0 = get_timescale().from_datetime(start_dt)
        t1 = get_timescale().from_datetime(stop_dt)
        # TODO: refraction function does not appear to work as expected
        r = refraction(0.0, temperature_C=self.temp_C,
                       pressure_mbar=self.pressure_mbar)
        r = horizon_deg + r
        t, y = almanac.find_risings(self.skyfield_location, coord, t0, t1,
                                    horizon_degrees=r)
        return t, y

    def get_last(self, date=None):
        """Return the local apparent sidereal time."""
        if date is None:
            date = self.date
        else:
            date = self.get_date(date)
        last = Time(date).sidereal_time('apparent',
                                        longitude=self.location)
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

        horizon_deg = self.horizon_deg
        t, y = self._find_setting(get_ssbodies()['sun'], date,
                                  date + timedelta(days=1, hours=1),
                                  horizon_deg - solar_radius_deg)
        return t[0].astimezone(self.tz_local)

    def sunrise(self, date=None):
        """Returns sunrise in observer's time."""
        if date is None:
            date = self.date
        else:
            date = self.get_date(date)

        horizon_deg = self.horizon_deg
        t, y = self._find_rising(get_ssbodies()['sun'], date,
                                 date + timedelta(days=1, hours=1),
                                 horizon_deg - solar_radius_deg)
        return t[0].astimezone(self.tz_local)

    def evening_twilight_6(self, date=None):
        """Returns evening 6 degree civil twilight(civil dusk) in observer's time.
        """
        if date is None:
            date = self.date
        else:
            date = self.get_date(date)

        t, y = self._find_setting(get_ssbodies()['sun'], date,
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

        t, y = self._find_setting(get_ssbodies()['sun'], date,
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

        t, y = self._find_setting(get_ssbodies()['sun'], date,
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

        t, y = self._find_rising(get_ssbodies()['sun'], date,
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

        t, y = self._find_rising(get_ssbodies()['sun'], date,
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

        t, y = self._find_rising(get_ssbodies()['sun'], date,
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

        t, y = self._find_rising(get_ssbodies()['moon'], date,
                                 date + timedelta(days=2, hours=0),
                                 self.horizon_deg - moon_radius_deg)
        return t[0].astimezone(self.tz_local)

    def moon_set(self, date=None):
        """Returns moon set time in observer's time."""
        if date is None:
            date = self.date
        else:
            date = self.get_date(date)

        t, y = self._find_setting(get_ssbodies()['moon'], date,
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

    def get_text_almanac(self, date):
        date_s = date.strftime("%Y-%m-%d")
        text = ''
        text += 'Almanac for the night of %s\n' % date_s.split()[0]
        text += '\nEvening\n'
        text += '_' * 30 + '\n'
        rst = self.sun_set_rise_times(date=date)
        rst = [t.strftime('%H:%M') for t in rst]
        text += 'Sunset: %s\n12d: %s\n18d: %s\n' % (rst[0], rst[1], rst[2])
        text += '\nMorning\n'
        text += '_' * 30 + '\n'
        text += '18d: %s\n12d: %s\nSunrise: %s\n' % (rst[3], rst[4], rst[5])
        return text

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
        dts = []
        time_t = self.date_to_utc(time_start)
        time_e = self.date_to_utc(time_stop)
        while time_t < time_e:
            dts.append(time_t)
            time_t = time_t + timedelta(minutes=time_interval)
        dt_arr = np.array(dts)

        return target.calc(self, dt_arr)

    def __repr__(self):
        return self.name

    __str__ = __repr__


def _epoch_years(equinox):
    """Equinox spec (year float, 'J2000', or array thereof) -> Julian year(s)."""
    def one(e):
        if isinstance(e, str):
            e = e.strip()
            if e[:1].upper() == 'J':
                e = e[1:]
            return float(e)
        return float(e)
    if isinstance(equinox, np.ndarray):
        return np.array([one(e) for e in equinox], dtype=float)
    return one(equinox)


def _has_pm(pmra, pmdec):
    """True if any proper motion is actually specified (non-None, non-zero)."""
    if pmra is None or pmdec is None:
        return False
    a = np.nan_to_num(np.asarray(pmra, dtype=float))
    b = np.nan_to_num(np.asarray(pmdec, dtype=float))
    return bool(np.any(a != 0.0) or np.any(b != 0.0))


def _radec_deg(ra, dec):
    """Normalize ra/dec (float, sexagesimal-hour str, or arrays) to degrees."""
    is_str = (isinstance(ra, str) or
              (isinstance(ra, np.ndarray) and ra.size > 0 and
               isinstance(ra.flat[0], str)))
    if is_str:
        c = SkyCoord(ra, dec, unit=(u.hourangle, u.degree), frame=ICRS)
        return np.asarray(c.ra.deg), np.asarray(c.dec.deg)
    return np.asarray(ra, dtype=float), np.asarray(dec, dtype=float)


def _equinox_frame(year):
    """Map a numeric equinox year to (source frame, catalog-epoch Time).

    Convention (matches spot.plugins.FindImage): 2000 -> ICRS (J2000),
    1950 -> FK4/B1950, any other year -> FK5 at that Julian equinox.  ICRS
    needs no transform; FK4/FK5 coordinates are precessed/rotated to ICRS.
    """
    year = float(year)
    if year == 2000.0:
        return ICRS(), Time('J2000.0')
    if year == 1950.0:
        t = Time('B1950.0')
        return FK4(equinox=t), t
    t = Time('J{:.4f}'.format(year))
    return FK5(equinox=t), t


def _to_icrs_deg(ra_deg, dec_deg, equinox, pmra, pmdec, ref_time):
    """Convert catalog RA/Dec (deg) to ICRS RA/Dec (deg), honoring each
    target's equinox frame (per _equinox_frame) and applying proper motion
    (mas/yr) to ref_time.  Accepts scalars or 1-D arrays; a mix of equinoxes
    is handled by grouping.  Fast path: all-J2000 with no pm is a no-op.
    """
    ra = np.atleast_1d(np.asarray(ra_deg, dtype=float))
    dec = np.atleast_1d(np.asarray(dec_deg, dtype=float))
    n = ra.shape[0]
    yr = np.atleast_1d(_epoch_years(equinox)).astype(float)
    if yr.shape[0] == 1 and n > 1:
        yr = np.repeat(yr, n)
    pm = _has_pm(pmra, pmdec)
    if not pm and np.all(yr == 2000.0):
        return ra, dec          # already ICRS
    if pm:
        if not isinstance(ref_time, Time):
            ref_time = Time(ref_time)
        pmra_a = np.atleast_1d(np.nan_to_num(np.asarray(pmra, dtype=float)))
        pmdec_a = np.atleast_1d(np.nan_to_num(np.asarray(pmdec, dtype=float)))
        if pmra_a.shape[0] == 1 and n > 1:
            pmra_a = np.repeat(pmra_a, n)
            pmdec_a = np.repeat(pmdec_a, n)
    out_ra, out_dec = ra.copy(), dec.copy()
    for yval in np.unique(yr):
        m = (yr == yval)
        frame, epoch = _equinox_frame(yval)
        with warnings.catch_warnings():
            # pm-only (no distance) -> ERFA warns "distance overridden"; benign
            warnings.simplefilter('ignore', erfa.ErfaWarning)
            if pm:
                c = SkyCoord(ra=ra[m] * u.deg, dec=dec[m] * u.deg,
                             pm_ra_cosdec=pmra_a[m] * u.mas / u.yr,
                             pm_dec=pmdec_a[m] * u.mas / u.yr,
                             obstime=epoch, frame=frame)
                c = c.apply_space_motion(new_obstime=ref_time)
            else:
                c = SkyCoord(ra=ra[m] * u.deg, dec=dec[m] * u.deg, frame=frame)
            if not isinstance(frame, ICRS):
                c = c.transform_to(ICRS())
        out_ra[m] = np.atleast_1d(np.asarray(c.ra.deg))
        out_dec[m] = np.atleast_1d(np.asarray(c.dec.deg))
    return out_ra, out_dec


class Body(object):

    def __init__(self, name, ra, dec, equinox, comment='',
                 pmra=None, pmdec=None):
        super(Body, self).__init__()

        self.name = name
        self.ra = ra
        self.dec = dec
        self.equinox = equinox
        self.comment = comment
        # proper motion in mas/yr (pmra is dRA*cos(dec)); None = not provided
        self.pmra = pmra
        self.pmdec = pmdec

    def _get_coord(self, obstime):
        scalar_in = not isinstance(self.ra, np.ndarray)
        ra_deg, dec_deg = _radec_deg(self.ra, self.dec)
        # a single reference time is enough to propagate proper motion
        ref = obstime if getattr(obstime, 'isscalar', True) else obstime[0]
        ra_i, dec_i = _to_icrs_deg(ra_deg, dec_deg, self.equinox,
                                   self.pmra, self.pmdec, ref)
        if scalar_in:
            return SkyCoord(float(ra_i[0]) * u.deg, float(dec_i[0]) * u.deg,
                            frame=ICRS)
        return SkyCoord(ra_i * u.deg, dec_i * u.deg, frame=ICRS)

    def calc(self, observer, date):
        return CalculationResult(self, observer, date)


class SSBody(object):

    def __init__(self, name, body=None):
        super(SSBody, self).__init__()

        self.name = name
        # `body` (a skyfield ephemeris body) is accepted for API compatibility
        # with the previous backend, but ignored: astropy resolves the body by
        # name via get_body().
        self._body = body

    def _get_coord(self, obstime):
        self._body = get_body(self.name.lower(), obstime)
        return self._body

    def calc(self, observer, date):
        return CalculationResult(self, observer, date)


class CalculationResult(object):

    def __init__(self, body, observer, date):
        """
        `date` is a single or array of datetime.datetime objects.
        """
        self.observer = observer
        self.body = body
        self.obstime = Time(date)

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

    def __len__(self):
        # leading axis of the computed result: time samples for a single
        # target (1 x N), else the number of targets (N x 1 or N x M).
        # (matches the earlier skyfield-based CalculationResult)
        if isinstance(self.az, np.ndarray):
            return len(self.az)
        return 1

    @property
    def name(self):
        return self.body.name

    @property
    def ra(self):
        """Return right ascension in radians."""
        if self._ra is None:
            self._calc_radec()
        return self._ra.rad

    @property
    def ra_deg(self):
        """Return right ascension in degrees."""
        if self._ra is None:
            self._calc_radec()
        return self._ra.deg

    @property
    def dec(self):
        """Return declination in radians."""
        if self._dec is None:
            self._calc_radec()
        return self._dec.rad

    @property
    def dec_deg(self):
        """Return declination in degrees."""
        if self._dec is None:
            self._calc_radec()
        return self._dec.deg

    @property
    def equinox(self):
        return self.body.equinox

    @property
    def alt(self):
        """Return altitude in radians."""
        if self._alt is None:
            self._calc_altaz()
        return self._alt.rad

    @property
    def alt_deg(self):
        """Return altitude in degrees."""
        if self._alt is None:
            self._calc_altaz()
        return self._alt.deg

    @property
    def az(self):
        """Return azimuth in radians."""
        if self._az is None:
            self._calc_altaz()
        return self._az.rad

    @property
    def az_deg(self):
        """Return azimuth in degrees."""
        if self._az is None:
            self._calc_altaz()
        return self._az.deg

    @property
    def lt(self):
        """Return local time as a Python timzezone-aware datetime."""
        if self._lt is None:
            self._lt = self.obstime.to_datetime(timezone=self.observer.tz_local)
        return self._lt

    @property
    def ut(self):
        """Return universal time as a Python timzezone-aware datetime."""
        if self._ut is None:
            self._ut = self.obstime.to_datetime(timezone=tz.UTC)
        return self._ut

    @property
    def jd(self):
        """Return the Julian Date."""
        if self._jd is None:
            self._jd = self.obstime.jd
        return self._jd

    @property
    def mjd(self):
        """Return the Mean Julian Date."""
        if self._mjd is None:
            self._mjd = self.obstime.mjd
        return self._mjd

    @property
    def gmst(self):
        """Return Greenwich Mean Sidereal Time in radians."""
        if self._gmst is None:
            self._gmst = self.obstime.sidereal_time('mean',
                                                    longitude='greenwich')
        return self._gmst.rad

    @property
    def gast(self):
        """Return Greenwich Apparent Sidereal Time in radians."""
        if self._gast is None:
            self._gast = self.obstime.sidereal_time('apparent',
                                                    longitude='greenwich')
        return self._gast.rad

    @property
    def lmst(self):
        """Compute Local Mean Sidereal Time"""
        if self._lmst is None:
            self._lmst = self.obstime.sidereal_time('mean',
                                                    longitude=self.observer.location)
        return self._lmst.rad

    @property
    def last(self):
        """Compute Local Apparent Sidereal Time"""
        if self._last is None:
            self._last = self.obstime.sidereal_time('apparent',
                                                    longitude=self.observer.location)
        return self._last.rad

    @property
    def ha(self):
        """Return the Hour Angle in radians."""
        lmst = self.lmst   # force calc of local mean sidereal time
        if self._ha is None:
            #self._ha = self.lmst - self.ra
            _ha = self._lmst - Angle(self.ra_deg / 15.0, unit=u.hour)
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
        """Compute Airmass"""
        if self._am is None:
            self._calc_altaz()
        return self._am

    @property
    def moon_alt(self):
        if self._moon_alt is None:
            # read from the shared geometry (target-independent); avoids
            # computing the target's own alt/az just to get the Moon's
            self._moon_alt = self.observer._obs_geometry(self.obstime)['moon_alt_deg']
        return self._moon_alt

    @property
    def moon_pct(self):
        """Return the moon's percentage of illumination (range: 0-1)"""
        if self._moon_pct is None:
            location = get_ssbodies()['earth'] + \
                wgs84.latlon(latitude_degrees=self.observer.lat_deg,
                             longitude_degrees=self.observer.lon_deg,
                             elevation_m=self.observer.elev_m)
            obstime = get_timescale().from_astropy(self.obstime)
            e = location.at(obstime)
            s = e.observe(get_ssbodies()['sun']).apparent()
            m = e.observe(get_ssbodies()['moon']).apparent()
            self._moon_pct = m.fraction_illuminated(get_ssbodies()['sun'])
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

    def _calc_radec(self):
        coord = self.body._get_coord(self.obstime)
        self._ra, self._dec = coord.ra, coord.dec

    def _calc_altaz(self):
        geom = self.observer._obs_geometry(self.obstime)
        coord = self.body._get_coord(self.obstime)
        altaz = coord.transform_to(geom['frame'])
        self._az, self._alt = altaz.az, altaz.alt
        # standardized airmass (matches the skyfield backend), not secz
        self._am = alt_to_airmass(self._alt.deg)

        # moon separation from target(s): reuse the Moon position (identical
        # for all targets at these times) instead of re-fetching it per target
        moon = geom['moon']
        # NOTE: needs to be moon.separation(coord) NOT coord.separation(moon)
        # apparently (see https://docs.astropy.org/en/stable/coordinates/common_errors.html#object-separation)
        if ASTROPY_LT_6_0_0:
            # doesn't have/support use of "origin_mismatch" keyword
            sep = moon.separation(coord)
        else:
            sep = moon.separation(coord, origin_mismatch='ignore')
        self._moon_sep = sep.deg

        # moon altitude comes from the shared geometry (target-independent)
        self._moon_alt = geom['moon_alt_deg']

    def _calc_parallactic(self, dec_rad, ha_rad, lat_deg):
        """Compute parallactic angle(s)."""
        lat_rad = np.radians(lat_deg)
        pang_rad = np.arctan2(np.sin(ha_rad),
                              np.tan(lat_rad) * np.cos(dec_rad) -
                              np.sin(dec_rad) * np.cos(ha_rad))
        return pang_rad

    def calc_separation_alt_az(self, body):
        """Compute deltas for azimuth and altitude from another target"""
        cr1 = self.body.calc(self.observer, self.ut)
        cr2 = body.calc(self.observer, self.ut)

        delta_az = cr1.az_deg - cr2.az_deg
        delta_alt = cr1.alt_deg - cr2.alt_deg
        return (delta_alt, delta_az)

    def calc_separation(self, body):
        """Compute angular separation from another target, in arcseconds."""
        coord1 = self.body._get_coord(self.obstime)
        coord2 = body._get_coord(self.obstime)
        return coord1.separation(coord2).arcsec

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


def calc_targets(observer, keys, bodies, dt_arr, columns=None):
    """Vectorized ephemeris for many fixed-star targets over ``dt_arr``.

    Computes *all* targets in a single ``(N, 1) x (M,)`` astropy grid --
    one AltAz transform, with the Moon and sidereal time computed once --
    and returns ``{key: {col: array(M)}}`` for the requested columns
    (defaults to the EphemerisCache column set).  This is the fast path the
    per-target CalculationResult can't provide.

    Only fixed-star ``Body`` targets are handled here; solar-system bodies
    (``SSBody``) can't be gridded across different bodies and must be
    computed separately by the caller.
    """
    if columns is None:
        columns = ['ut', 'lt', 'alt_deg', 'az_deg', 'airmass', 'pang_deg',
                   'moon_alt', 'moon_sep']

    times = Time(np.atleast_1d(np.asarray(dt_arr)))
    M = times.size

    # Build the observer location from plain lat/lon/elev so this works with
    # either Observer backend (skyfield or astropy) -- we don't depend on the
    # observer carrying an astropy EarthLocation.
    location = EarthLocation(lat=observer.lat_deg * u.deg,
                             lon=observer.lon_deg * u.deg,
                             height=observer.elev_m * u.m)

    # target RA/Dec (deg); parse any string (hms/dms) coords, gather pm + equinox
    ra_list, dec_list, pmra_list, pmdec_list, eq_list = [], [], [], [], []
    name_list = []
    for b in bodies:
        rd_ra, rd_dec = _radec_deg(b.ra, b.dec)
        ra_list.append(float(rd_ra))
        dec_list.append(float(rd_dec))
        pmra = getattr(b, 'pmra', None)
        pmdec = getattr(b, 'pmdec', None)
        pmra_list.append(0.0 if pmra is None else float(pmra))
        pmdec_list.append(0.0 if pmdec is None else float(pmdec))
        eq_list.append(float(_epoch_years(b.equinox)))
        name_list.append(getattr(b, 'name', None))
    # convert catalog RA/Dec -> ICRS (per-target equinox frame) and apply
    # proper motion, once, to the first time (see _to_icrs_deg)
    ra_deg, dec_deg = _to_icrs_deg(np.asarray(ra_list), np.asarray(dec_list),
                                   np.asarray(eq_list), np.asarray(pmra_list),
                                   np.asarray(pmdec_list), times[0])

    # --- observer-level, target-independent: computed once ---
    frame = AltAz(obstime=times, location=location,
                  pressure=observer.pressure_mbar * u.mbar,
                  temperature=observer.temp_C * u.deg_C,
                  relative_humidity=observer.rh_pct,
                  #obswl=observer.wavelength
                  )
    moon = get_body('moon', times, location=location)
    moon_alt = moon.transform_to(frame).alt.deg          # (M,)
    lmst = times.sidereal_time('mean', longitude=location)   # (M,) hrs

    # moon illumination fraction (time-only, same for every target).  Computed
    # only when asked -- it's an extra skyfield observe().  Uses skyfield so it
    # matches CalculationResult.moon_pct exactly (per-target fallback parity).
    moon_pct = None
    if 'moon_pct' in columns:
        sf_loc = get_ssbodies()['earth'] + \
            wgs84.latlon(latitude_degrees=observer.lat_deg,
                         longitude_degrees=observer.lon_deg,
                         elevation_m=observer.elev_m)
        sf_e = sf_loc.at(get_timescale().from_astropy(times))
        sf_moon = sf_e.observe(get_ssbodies()['moon']).apparent()
        moon_pct = np.atleast_1d(sf_moon.fraction_illuminated(get_ssbodies()['sun']))

    # --- the grid: all targets at all times in one transform ---
    coord = SkyCoord(ra_deg[:, None] * u.deg, dec_deg[:, None] * u.deg,
                     frame=ICRS)                          # (N, 1)
    altaz = coord.transform_to(frame)                     # (N, M)
    alt_deg = altaz.alt.deg
    az_deg = altaz.az.deg
    airmass = alt_to_airmass(alt_deg)

    if ASTROPY_LT_6_0_0:
        moon_sep = moon.separation(coord).deg             # (N, M)
    else:
        moon_sep = moon.separation(coord, origin_mismatch='ignore').deg

    # hour angle -> parallactic angle, vectorized over (N, M)
    ha_hours = lmst.hour[None, :] - (ra_deg[:, None] / 15.0)
    ha_rad = np.radians(((ha_hours + 12.0) % 24.0 - 12.0) * 15.0)
    lat_rad = np.radians(observer.lat_deg)
    dec_rad = np.radians(dec_deg[:, None])
    pang_rad = np.arctan2(np.sin(ha_rad),
                          np.tan(lat_rad) * np.cos(dec_rad) -
                          np.sin(dec_rad) * np.cos(ha_rad))   # (N, M)

    # time columns (same for every target)
    ut = times.to_datetime(timezone=tz.UTC)
    lt = times.to_datetime(timezone=observer.tz_local)

    def col_for(col, i):
        if col == 'alt_deg':
            return alt_deg[i]
        if col == 'az_deg':
            return az_deg[i]
        if col == 'alt':
            return np.radians(alt_deg[i])
        if col == 'az':
            return np.radians(az_deg[i])
        if col == 'airmass':
            return airmass[i]
        if col == 'pang':
            return pang_rad[i]
        if col == 'pang_deg':
            return np.degrees(pang_rad[i])
        if col == 'moon_sep':
            return moon_sep[i]
        if col == 'moon_alt':
            return moon_alt
        if col == 'moon_pct':
            return moon_pct
        if col == 'name':
            return np.full(M, name_list[i])
        if col == 'ha':
            return ha_rad[i]
        if col == 'ra_deg':
            return np.full(M, ra_deg[i])
        if col == 'dec_deg':
            return np.full(M, dec_deg[i])
        if col == 'ra':
            return np.full(M, np.radians(ra_deg[i]))
        if col == 'dec':
            return np.full(M, np.radians(dec_deg[i]))
        if col == 'ut':
            return ut
        if col == 'lt':
            return lt
        raise KeyError(f"calc_targets: unsupported column {col!r}")

    return {key: {col: col_for(col, i) for col in columns}
            for i, key in enumerate(keys)}


# columns calc_targets() can produce -- lets callers decide whether the
# vectorized grid path can satisfy the requested columns
GRID_COLUMNS = frozenset({
    'ut', 'lt', 'alt_deg', 'az_deg', 'alt', 'az', 'airmass', 'pang',
    'pang_deg', 'moon_sep', 'moon_alt', 'moon_pct', 'name',
    'ha', 'ra_deg', 'dec_deg', 'ra', 'dec'})


Moon = SSBody('Moon')
Sun = SSBody('Sun')
Mercury = SSBody('Mercury')
Venus = SSBody('Venus')
Mars = SSBody('Mars')
Jupiter = SSBody('Jupiter')
Saturn = SSBody('Saturn')
Uranus = SSBody('Uranus')
Neptune = SSBody('Neptune')
Pluto = SSBody('Pluto')

_SS = dict(Moon=Moon, Sun=Sun, Mercury=Mercury, Venus=Venus, Mars=Mars,
           Jupiter=Jupiter, Saturn=Saturn, Uranus=Uranus, Neptune=Neptune,
           Pluto=Pluto)


def get_ss(name):
    """Return the solar-system SSBody for *name* (e.g. 'Moon', 'Mars')."""
    return _SS[name]


# --- skyfield-ephemeris accessors, kept for API compatibility --------------
# (the loaded de421 kernel + timescale; used by callers that still hand a
# skyfield body around, e.g. spot.util.target.get_nstarget)

def get_ssbodies():
    global _ssbodies
    if _ssbodies is None:
        _ssbodies = _get_loader()('de421.bsp')
    return _ssbodies


def get_timescale():
    global _timescale
    if _timescale is None:
        _timescale = _get_loader().timescale()
    return _timescale


def get_ssbody(lookup_name, myname=None):
    if myname is None:
        myname = lookup_name
    return SSBody(myname, get_ssbodies()[lookup_name.lower()])


#END
