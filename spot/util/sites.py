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


class Site:
    name = 'Generic Site'

    def __init__(self):
        super().__init__()

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
        )

    def get_status(self):
        return Bunch(self.status_dict)

    def fetch_status(self, fv):
        """Site class should override this to update our status_dict
        with fresh status, if it has any.  Called by SiteSelector plugin.
        """
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
                                 timezone=timezone)

    def az_to_norm(self, az_deg):
        return az_deg

    def norm_to_az(self, az_deg):
        return az_deg

    def __str__(self):
        return self.name


class Subaru(Site):
    name = 'Subaru (Mauna Kea, Hawaii)'

    def __init__(self):
        super().__init__()

        self.status_dict.update(
            dict(longitude_deg=-155.47611111111,
                 latitude_deg=19.8285,
                 elevation_m=4163,
                 pressure_mbar=615,
                 temperature_c=0,
                 timezone_name='HST',
                 timezone_offset_min=-600,
                 azimuth_start_direction='S',
                 fov_deg=1.5))
        self.initialize()

        # maps Subaru Telescope OCS status items to local status
        self.status_map = dict(
            az_deg='STATS.AZ_DEG',
            az_cmd_deg='STATS.AZ_CMD',
            az_diff_deg='STATS.AZ_DIF',
            alt_deg='STATS.EL_DEG',
            alt_cmd_deg='STATS.EL_CMD',
            alt_diff_deg='STATS.EL_DIF',
            ra_deg='STATS.RA_DEG',
            ra_cmd_deg='STATS.RA_CMD_DEG',
            equinox='STATS.EQUINOX',
            dec_deg='STATS.DEC_DEG',
            dec_cmd_deg='STATS.DEC_CMD_DEG',
            cmd_equinox='STATS.EQUINOX',
            slew_time_sec='STATS.SLEWING_TIME',
            tel_status='STATL.TELDRIVE',
        )

        # self.status_dict['az_norm_deg'] = \
        #     subaru_normalize_az(self.status_dict['az_deg'])
        # self.status_dict['az_cmd_norm_deg'] = \
        #     subaru_normalize_az(self.status_dict['az_cmd_deg'])


    def az_to_norm(self, az_deg):
        return subaru_normalize_az(az_deg)

    def norm_to_az(self, az_deg):
        return subaru_normalize_az(az_deg)

    def put_status(self, actual_status):
        """Called from a global plugin to update the local status
        periodically.
        """
        for key, alias in self.status_map.items():
            if alias in actual_status:
                self.status_dict[key] = actual_status[alias]

        # self.status_dict['az_norm_deg'] = \
        #     subaru_normalize_az(self.status_dict['az_deg'])
        # self.status_dict['az_cmd_norm_deg'] = \
        #     subaru_normalize_az(self.status_dict['az_cmd_deg'])

    def fetch_status(self, fv):
        # get any updates to local status
        try:
            obj = fv.gpmon.get_plugin('SubaruTelescope')
            status_dict = obj.get_status()
            self.put_status(status_dict)
        except KeyError:
            # no SubaruTelescope plugin loaded
            pass
        return self.get_status()


class VLT(Site):
    name = 'VLT (Cerro Paranal, Chile)'

    def __init__(self):
        super().__init__()

        self.status_dict.update(
            dict(longitude_deg=Longitude('70d24m15.36s').deg,
                 latitude_deg=Latitude('-24d37m38.38s').deg,
                 elevation_m=2635,
                 pressure_mbar=1015,
                 temperature_c=10,
                 timezone_name='PRT',
                 timezone_offset_min=-240,
                 fov_deg=1.0))
        self.initialize()


site_list = [
    Subaru,
    VLT,
]

site_dict = {klass.name: klass for klass in site_list}
site_names = list(site_dict.keys())
site_names.sort()

def get_site_names():
    return site_names

def get_site(name):
    return site_dict[name]()
