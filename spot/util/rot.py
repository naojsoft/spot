#
# rot.py -- rotation calculations
#
import numpy as np


def calc_alternate_angle(ang_deg):
    """Calculates the alternative usable angle to the given one.

    Parameters
    ----------
    ang_deg : float or array of float
        The input angle(s) in degrees

    Returns
    -------
    alt_deg : float or array of float
        The output angle(s) in degrees
    """
    alt_deg = ang_deg - np.sign(ang_deg) * 360.0
    return alt_deg


def normalize_angle(ang_deg, limit=None, ang_offset=0.0):
    """Normalize an angle.

    Parameters
    ----------
    az_deg: float
        A traditional azimuth value where 0 deg == North

    limit: str or None (optional, defaults to None)
        How to limit the range of the result angle

    ang_offset: float (optional, defaults to 0.0)
        Angle to add to the input angle to offset it

    Returns
    -------
    limit: None (-360, 360), 'full' (0, 360), or 'half' (-180, 180)

    To normalize to Subaru azimuth (AZ 0 == S), do
        normalize_angle(ang_deg, limit='half', ang_offset=-180)
    """
    # convert to array if just a scalar
    is_array = isinstance(ang_deg, np.ndarray)
    if not is_array:
        ang_deg = np.array([ang_deg], dtype=float)
    ang_deg = ang_deg.astype(float)

    ang_deg = ang_deg + ang_offset

    # constrain to -360, +360
    mask = np.fabs(ang_deg) >= 360.0
    ang_deg[mask] = np.remainder(ang_deg[mask], np.sign(ang_deg[mask]) * 360.0)
    if limit is not None:
        # constrain to 0, +360
        mask = ang_deg < 0.0
        ang_deg[mask] += 360.0
        if limit == 'half':
            # constrain to -180, +180
            mask = ang_deg > 180.0
            ang_deg[mask] -= 360.0

    if not is_array:
        # extract scalar
        ang_deg = ang_deg[0]

    return ang_deg
