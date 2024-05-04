#
# rot.py -- rotation calculations
#
from collections import namedtuple

import numpy as np


TelMove = namedtuple('TelMove', ['rot1_start_deg', 'rot1_stop_deg',
                                 'rot2_start_deg', 'rot2_stop_deg',
                                 'az1_start_deg', 'az1_stop_deg',
                                 'az2_start_deg', 'az2_stop_deg',
                                 'alt_start_deg', 'alt_stop_deg',
                                 ])


def calc_alternate_angle(ang_deg):
    """calculates the alternative usable angle to the given one."""
    _ang_deg = ang_deg - np.sign(ang_deg) * 360
    return _ang_deg


def calc_rotation_choices(cr_start, cr_stop, pa_deg):
    """cr_start and cr_stop are CalculationResult objects for the
    same target at two different times.
    """
    pang1_deg = cr_start.pang_deg
    pang2_deg = cr_stop.pang_deg

    # calculate direction of movement
    # if rotation movement is greater than 180 degrees, then switch the
    # rotation direction of movement to the smaller one with opposite sign
    rot_delta = np.fmod(pang2_deg - pang1_deg, 360.0)
    if np.abs(rot_delta) > 180.0:
        rot_delta = - np.sign(rot_delta) * (rot_delta - np.sign(rot_delta) * 360)

    # rotator_angle = parallactic_angle + position_angle
    rot1_start = np.fmod(pang1_deg + pa_deg, 360.0)
    # calculate the other possible angle for this target
    rot2_start = calc_alternate_angle(rot1_start)

    rot1_stop = rot1_start + rot_delta
    rot2_stop = rot2_start + rot_delta

    az1_start = cr_start.az_deg
    az2_start = calc_alternate_angle(az1_start)
    az1_stop = cr_stop.az_deg

    # calculate direction of movement for standard rotation
    # (see remarks above for rot_delta)
    az_delta = np.fmod(az1_stop - az1_start, 360.0)
    if np.abs(az_delta) > 180.0:
        az_delta = - np.sign(az_delta) * (az_delta - np.sign(az_delta) * 360)
    az2_stop = az2_start + az_delta

    # return both rotation moves, both azimuth moves and elevation start/stop
    return TelMove(rot1_start, rot1_stop, rot2_start, rot2_stop,
                   az1_start, az1_stop, az2_start, az2_stop,
                   cr_start.alt_deg, cr_stop.alt_deg)
