from datetime import UTC

import numpy as np
from astropy.time import Time
from astropy.table import Table

from ginga.util.wcs import hmsStrToDeg, dmsStrToDeg
from ginga.misc import Bunch

from spot.util.calcpos import Body, SSBody

try:
    from oscript.util import ope
    have_oscript = True
except ImportError:
    have_oscript = False


class TargetMixin:

    def __init__(self, category=None):
        self.category = category
        self.metadata = None

    def set(self, **kwargs):
        if self.metadata is None:
            self.metadata = Bunch.Bunch()
        self.metadata.update(kwargs)

    def get(self, *args):
        if len(args) not in [1, 2]:
            raise RuntimeError("Wrong number of parameters to get()")
        elif len(args) == 1:
            key = args[0]
            if self.metadata is None:
                return KeyError(key)
            return self.metadata[key]

        key, val = args
        if self.metadata is None:
            return val
        return self.metadata.get(key, val)

    def __getitem__(self, key):
        if self.metadata is None:
            raise KeyError(key)
        return self.metadata[key]

    def __setitem__(self, key, value):
        if self.metadata is None:
            self.metadata = Bunch.Bunch()
        self.metadata[key] = value

    def __delitem__(self, key):
        if self.metadata is None or key not in self.metadata:
            raise KeyError(key)
        del self.metadata[key]


class Target(TargetMixin, Body):

    def __init__(self, name=None, ra=None, dec=None, equinox=2000.0,
                 comment='', category=None, pmra=None, pmdec=None):
        TargetMixin.__init__(self, category=category)
        Body.__init__(self, name, ra, dec, equinox, comment=comment,
                      pmra=pmra, pmdec=pmdec)

    def import_record(self, rec):
        self.name = rec['Name']
        self.ra, self.dec, self.equinox = normalize_ra_dec_equinox(rec['RA'],
                                                                   rec['DEC'],
                                                                   rec['Equinox'])
        if 'pmRA' in rec:
            self.pmra = rec['pmRA']
        if 'pmDEC' in rec:
            self.pmdec = rec['pmDEC']
        self.comment = rec.get('Comment', '').strip()


class NSTarget(TargetMixin, SSBody):

    def __init__(self, name=None, body=None, comment='', category=None):
        TargetMixin.__init__(self, category=category)
        # TODO: take care of comment
        SSBody.__init__(self, name, body)


def normalize_ra_dec_equinox(ra, dec, eq):
    if ra is None:
        ra_deg = None
    elif isinstance(ra, float):
        ra_deg = ra
    elif isinstance(ra, str):
        ra = ra.strip()
        if len(ra) == 0:
            ra_deg = None
        elif ':' in ra:
            # read as sexigesimal hours
            ra_deg = hmsStrToDeg(ra)
        else:
            if '.' in ra:
                l, r = ra.split('.')
            else:
                l = ra
            if len(l) > 4:
                if not have_oscript:
                    raise ValueError("RA appears to be in funky SOSS format; please install 'oscript' to parse these values")
                ra_deg = ope.funkyHMStoDeg(ra)
            else:
                ra_deg = float(ra)
    else:
        raise ValueError(f"don't understand format/type of 'RA': {ra}")

    if dec is None:
        dec_deg = None
    elif isinstance(dec, float):
        dec_deg = dec
    elif isinstance(dec, str):
        dec = dec.strip()
        if len(dec) == 0:
            dec_deg = None
        elif ':' in dec:
            # read as sexigesimal hours
            dec_deg = dmsStrToDeg(dec)
        else:
            if '.' in dec:
                l, r = dec.split('.')
            else:
                l = dec
            if len(l) > 4:
                if not have_oscript:
                    raise ValueError("DEC appears to be in funky SOSS format; please install 'oscript' to parse these values")
                dec_deg = ope.funkyDMStoDeg(dec)
            else:
                dec_deg = float(dec)
    else:
        raise ValueError(f"don't understand format/type of 'DEC': {dec}")

    if eq is None:
        equinox = 2000.0
    elif isinstance(eq, (float, int)):
        equinox = float(eq)
    elif isinstance(eq, str):
        eq = eq.strip().upper()
        if len(eq) == 0:
            equinox = 2000.0
        elif eq[0] in ('B', 'J'):
            equinox = float(eq[1:])
        else:
            equinox = float(eq)
    else:
        raise ValueError(f"don't understand format/type of 'EQ': {eq}")

    return (ra_deg, dec_deg, equinox)


def get_closest_ra_dec(dt, track_tbl):

    # find closest time to current one. `idx` will be the index of the value
    # just greater than the value we are passing
    dt_jd = Time(dt).jd
    idx = np.searchsorted(track_tbl['datetime_jd'], dt_jd, side='left')
    if idx == 0:
        # time is before our non-sidereal track starts
        return (False, track_tbl['RA'][0], track_tbl['DEC'][0])
    if idx == len(track_tbl):
        # time is after our non-sidereal track stops
        return (False, track_tbl['RA'][-1], track_tbl['DEC'][-1])

    # interpolate between the two closest dates to find the percentage
    # difference
    jd = track_tbl['datetime_jd']
    pct = (dt_jd - jd[idx - 1]) / (jd[idx] - jd[idx - 1])

    ra, dec = track_tbl['RA'], track_tbl['DEC']
    ra_deg = ra[idx - 1] + (ra[idx] - ra[idx - 1]) * pct
    dec_deg = dec[idx - 1] + (dec[idx] - dec[idx - 1]) * pct
    return (True, ra_deg, dec_deg)


def update_nonsidereal_targets(targets, dt):
    changed = False
    dt_utc = dt.astimezone(UTC)
    for target in targets:
        track_tbl = target.get('track', None)
        if track_tbl is None:
            raise ValueError("nonsidereal target does not contain a tracking table")

        valid, ra_deg, dec_deg = get_closest_ra_dec(dt_utc, track_tbl)
        if (not np.isclose(ra_deg, target.ra, rtol=1e-10) or
            not np.isclose(dec_deg, target.dec, rtol=1e-10)):
            changed = True
            target.ra, target.dec = ra_deg, dec_deg
        if not valid:
            # Time is outside of our tracking range. Indicate this by
            # changing the color of the target
            target.set(color='orangered')
        else:
            target.set(color='cyan')
    return changed


def load_jplephem_target(eph_path, dt=None):
    from Gen2.astro.jplHorizonsIF import JPLHorizonsEphem
    with open(eph_path, 'r') as eph_f:
        buf = eph_f.read()
        eph = JPLHorizonsEphem(buf)

    hist = eph.trackInfo['timeHistory']
    dts = np.array([tup[0].replace(tzinfo=UTC) for tup in hist])
    dt_jds = Time(dts).jd
    ras = np.array([tup[1] for tup in hist])
    decs = np.array([tup[2] for tup in hist])
    tbl = Table(data=[dt_jds, dts, ras, decs],
                names=['datetime_jd', 'DateTime', 'RA', 'DEC'])

    # TODO: proper name
    name = "Target"
    target = Target(name=name, ra=ras[0], dec=decs[0], equinox=2000.0,
                    category=eph_path)
    target.set(color='cyan', nonsidereal=True, track=tbl)

    if dt is not None:
        update_nonsidereal_targets([target], dt)
    return target


def make_jplhorizons_target(name, eph_table, dt=None, category='Non-sidereal'):
    """Make a non-sidereal target from a JPL Horizons ephemeris from
    astroquery.
    """

    dt_jds = Time(eph_table['datetime_jd'], format='jd', scale='utc')
    dts = np.array([t_jd.datetime.replace(tzinfo=UTC) for t_jd in dt_jds])
    dt_jds = dt_jds.value
    ras = eph_table['RA']
    decs = eph_table['DEC']
    deltas = eph_table['delta']
    tbl = Table(data=[dt_jds, dts, ras, decs, deltas],
                names=['datetime_jd', 'DateTime', 'RA', 'DEC', 'delta'])

    target = Target(name=name, ra=ras[0], dec=decs[0], equinox=2000.0,
                    category=category)
    target.set(color='cyan', nonsidereal=True, track=tbl)

    if dt is not None:
        update_nonsidereal_targets([target], dt)
    return target
