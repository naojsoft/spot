"""
NOTES:
[1] Southern Hemispheres should have a negative Latitude, Northern positive
    Western Longitudes should have a negative Longitude, Eastern positive

"""
# stdlib
from dateutil import tz

# astropy
from astropy import units as u
from astropy.coordinates import Longitude, Latitude

# ginga
from ginga.misc.Bunch import Bunch

# qplan
from qplan.util.calcpos import Observer

# local
from spot.util.polar import subaru_normalize_az

_external_status_dct = {}
site_dict = {}
site_names = []


class Site:
    def __init__(self, name):
        super().__init__()

        self.name = name
        self.observer = None
        self.status_dict = dict(
            longitude_deg=0.0,
            latitude_deg=0.0,
            elevation_m=0.0,
            pressure_mbar=0.0,        # ATM pressure in millibars
            temperature_c=0.0,        # temperature at site
            timezone_name='UTC',      # name of time zone at site
            timezone_offset_min=0,    # minute offset of time zone at site
            azimuth_start_direction='N',
            fov_deg=1.0,              # telescope FOV in deg
            az_deg=0.0,               # cur tel azimuth in deg
            az_cmd_deg=0.0,           # target azimuth in deg
            # az_norm_deg=0.0,          #
            # az_cmd_norm_deg=0.0,      #
            az_diff_deg=0.0,          # diff between target az and cmd az
            az_direction=1,           # -1: moving CCW, 0: not moving, 1: CW
            alt_deg=90.0,             # cur tel elevation in deg
            alt_cmd_deg=90.0,         # target elevation in deg
            alt_diff_deg=0.0,         # diff between target el and cmd el
            ra_deg=0.0,               # cur tel RA in deg
            ra_cmd_deg=0.0,           # target RA in deg
            equinox=2000.0,           # ref equinox for telescope coords
            dec_deg=0.0,              # cur tel DEC in deg
            dec_cmd_deg=0.0,          # target DEC in deg
            cmd_equinox=2000.0,       # ref equinox for target coords
            slew_time_sec=0.0,        # slew time in sec to target
            tel_status='Pointing',    # current telescope status string
            humidity=0.0,
            wavelength={'': 0.0, '': 0.0}
        )

    def get_status(self):
        return Bunch(self.status_dict)

    def fetch_status(self):
        global _external_status_dct
        self.status_dict.update(_external_status_dct)
        return self.get_status()

    def initialize(self):
        status = Bunch(self.get_status())
        timezone = tz.tzoffset(status.timezone_name,
                               status.timezone_offset_min * 60)
        self.observer = Observer(str(self),
                                 longitude=Longitude(status.longitude_deg * u.deg).to_string(sep=':', precision=3),
                                 latitude=Latitude(status.latitude_deg * u.deg).to_string(sep=':', precision=3),
                                 #elevation=status.elevation_m * u.m,
                                 #pressure=status.pressure_mbar / 1000 * u.bar,
                                 #temperature=status.temperature_c * u.deg_C,
                                 elevation=status.elevation_m,
                                 pressure=status.pressure_mbar,
                                 temperature=status.temperature_c,
                                 humidity=status.humidity,
                                 wavelength=status.wavelength,
                                 timezone=timezone)

    def az_to_norm(self, az_deg):
        if self.status_dict['azimuth_start_direction'] == 'S':
            return subaru_normalize_az(az_deg)
        return az_deg

    def norm_to_az(self, az_deg):
        if self.status_dict['azimuth_start_direction'] == 'S':
            return subaru_normalize_az(az_deg)
        return az_deg

    def __str__(self):
        return self.name


def update_status(dct):
    global _external_status_dct
    _external_status_dct.update(dct)

def get_site_names():
    return site_names

def get_site(name):
    return site_dict[name]

def configure_sites(yml_dct):
    global site_dict, site_names

    site_dict = dict()
    for name, dct in yml_dct.items():
        site = Site(name)
        site.status_dict.update(dct)
        site_dict[name] = site

    site_names = list(site_dict.keys())
    site_names.sort()
