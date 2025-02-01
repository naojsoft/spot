"""
NOTES:
[1] Southern Hemispheres should have a negative Latitude, Northern positive
    Western Longitudes should have a negative Longitude, Eastern positive

"""
# stdlib
import os.path
from dateutil import tz
import threading

# 3rd party
import yaml
from astropy import units as u
from astropy.coordinates import Longitude, Latitude

# ginga
from ginga.misc.Bunch import Bunch

# local
from spot.util.polar import subaru_normalize_az
from spot.util.calcpos import Observer

from spot import __file__
cfg_sites_yml = os.path.join(os.path.dirname(__file__), "config", "sites.yml")

site_dict = dict()
site_names = []


class Site:
    def __init__(self, name):
        super().__init__()

        self.name = name
        self.observer = None
        self.lock = threading.RLock()
        self.status_dict = dict(
            fullname='Unnamed site',
            longitude_deg=0.0,
            latitude_deg=0.0,
            elevation_m=0.0,
            horizon_deg=0.0,          # horizon for calculating sunset/sunrise
            pressure_mbar=0.0,        # ATM pressure in millibars
            temperature_c=0.0,        # temperature at site
            timezone_name='UTC',      # name of time zone at site
            timezone_offset_min=0,    # minute offset of time zone at site
            azimuth_start_direction='N',  # where is 0 deg azimuth (N/S)
            fov_deg=1.0,              # telescope FOV in deg
            az_deg=0.0,               # current telescope azimuth in deg
            az_cmd_deg=0.0,           # current target azimuth in deg
            # az_norm_deg=0.0,          #
            # az_cmd_norm_deg=0.0,      #
            az_diff_deg=0.0,          # diff between target az and cmd az
            alt_deg=90.0,             # current telescope elevation in deg
            alt_cmd_deg=90.0,         # current target elevation in deg
            alt_diff_deg=0.0,         # diff between target el and cmd el
            ra_deg=0.0,               # current telescope RA in deg
            ra_cmd_deg=0.0,           # current target RA in deg
            equinox=2000.0,           # ref equinox for telescope coords
            dec_deg=0.0,              # current telescope DEC in deg
            dec_cmd_deg=0.0,          # current target DEC in deg
            cmd_equinox=2000.0,       # ref equinox for target coords
            slew_time_sec=0.0,        # slew time in sec to target
            rot_deg=0.0,              # current rotator position in deg
            rot_cmd_deg=0.0,          # rotator commanded position in deg
            tel_status='Pointing',    # current telescope status string
            humidity=0.0,
            wavelength={'': 0.0, '': 0.0}
        )

    def get_status(self):
        with self.lock:
            return Bunch(self.status_dict)

    def update_status(self, status_dct):
        with self.lock:
            self.status_dict.update(status_dct)

    def initialize(self):
        status = Bunch(self.get_status())
        timezone = tz.tzoffset(status.timezone_name,
                               status.timezone_offset_min * 60)
        self.observer = Observer(self.name,
                                 longitude=Longitude(status.longitude_deg * u.deg).to_string(sep=':', precision=3),
                                 latitude=Latitude(status.latitude_deg * u.deg).to_string(sep=':', precision=3),
                                 elevation=status.elevation_m,
                                 pressure=status.pressure_mbar,
                                 temperature=status.temperature_c,
                                 humidity=status.humidity,
                                 horizon_deg=status.horizon_deg,
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
        return self.status_dict.get('fullname', self.name)


def get_site_names():
    return site_names


def get_site(name):
    return site_dict[name.lower()]


def configure_sites(yml_dct):
    global site_dict, site_names

    site_dict.clear()
    site_names.clear()
    for name, dct in yml_dct.items():
        site_names.append(name)
        site = Site(name)
        site.status_dict.update(dct)
        site_dict[name.lower()] = site

    site_names.sort()


def configure_default_sites():
    with open(cfg_sites_yml, 'r') as in_f:
        yml_dct = yaml.safe_load(in_f.read())
        configure_sites(yml_dct)
