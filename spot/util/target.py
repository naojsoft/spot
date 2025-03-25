from collections.abc import Mapping

from ginga.util.wcs import hmsStrToDeg, dmsStrToDeg
from ginga.misc import Bunch

from spot.util.calcpos import Body

try:
    from oscript.util import ope
    have_oscript = True
except ImportError:
    have_oscript = False


class Target(Body):

    def __init__(self, name=None, ra=None, dec=None, equinox=2000.0,
                 comment='', category=None):
        super().__init__(name, ra, dec, equinox, comment=comment)
        self.category = category
        self.metadata = None

    def set(self, **kwargs):
        if self.metadata is None:
            self.metadata = Bunch.Bunch()
        self.metadata.update(kwargs)

    def get(self, *args):
        if len(args) == 1:
            key = args[0]
            if self.metadata is None:
                raise KeyError(key)
            return self.metadata[key]
        elif len(args) == 2:
            key, default_val = args
            if self.metadata is None:
                return default_val
            return self.metadata.get(key, default_val)
        else:
            raise RuntimeError("Invalid number of parameters to get()")

    def import_record(self, rec):
        self.name = rec['Name']
        self.ra, self.dec, self.equinox = normalize_ra_dec_equinox(rec['RA'],
                                                                   rec['DEC'],
                                                                   rec['Equinox'])
        self.comment = rec.get('Comment', '').strip()

    def get(self, *args):
        if len(args) not in [1, 2]:
            raise ValueError("Wrong number of parameters to get()")
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
