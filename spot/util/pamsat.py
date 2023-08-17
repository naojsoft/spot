import io
import calendar
from collections import namedtuple

import numpy as np
from astropy.coordinates import SkyCoord, AltAz
from astropy.time import Time
import astropy.units as u


hdr_window = 'YYYY MMM dd (DDD) HHMM SS    YYYY MMM dd (DDD) HHMM SS      MM:SS'

months = dict(Jan=1, Feb=2, Mar=3, Apr=4, May=5, Jun=6,
              Jul=7, Aug=8, Sep=9, Oct=10, Nov=11, Dec=12)

RaDec_Target = namedtuple('RaDec_Target', ['ra_deg', 'dec_deg', 'epoch'])
AzAlt_Target = namedtuple('AzAlt_Target', ['az_deg', 'alt_deg'])


def load_pam_file(pam_path, tgt_dict=None, pad_sec=0):
    """Load a PAM file.

    Parameters
    ----------
    pam_path : str (path) or open file object
        Path to the file

    tgt_dict : dict (optional, defaults to None)
        Dictionary to use for storing the result

    pad_sec : int (optional, defaults to 0)
        The number of seconds to pad the window for safety

    Returns
    -------
    tgt_dict : dict
        Dictionary whose keys are targets and whose values are lists
        of time windows, where each window is of the form:
          (open_sse, close_sse)
        where the values are in Unix seconds since the epoch
    """
    windows_list = []
    if tgt_dict is None:
        tgt_dict = dict()
    a = None

    # open the file and read contents
    if isinstance(pam_path, io.TextIOBase):
        lines = pam_path.readlines()
    else:
        with open(pam_path, 'r') as in_f:
            lines = in_f.readlines()

    # loop over the lines with data in the file
    line_num = 0
    while line_num < len(lines):
        line = lines[line_num]

        # check for window data in the current string
        if line.find(hdr_window) != -1:
            line_num += 2   # skip header to first line of data
            cs = lines[line_num]

            # parse the window data line for time / date (which is in UTC)
            # repeat until empty line
            while len(cs) > 2:
                e = cs.strip().split()
                # find the opening date / time
                year, mon, day = e[0:3]
                hr, mn, sec = e[4][:2], e[4][2:], e[5]
                open_sse = calendar.timegm((int(year), months[mon], int(day),
                                            int(hr), int(mn), int(sec), 0, 0, 0))

                # find the closing date / time
                year, mon, day = e[6:9]
                hr, mn, sec = e[10][:2], e[10][2:], e[11]
                close_sse = calendar.timegm((int(year), months[mon], int(day),
                                             int(hr), int(mn), int(sec), 0, 0, 0))

                # add this window to the list
                a = (open_sse + pad_sec, close_sse - pad_sec)
                windows_list.append(a)

                # take the next line number
                line_num += 1
                cs = lines[line_num]

        # check for target name and find object coordinates
        elif line.find('Target Geometry:') != -1:
            line_num += 2   # skip header to first line of data
            cs = lines[line_num]
            a = None

            # if Azimuth / Elevation target
            if cs.find('Method: Fixed Azimuth/Elevation') != -1:
                # get the azimuth
                line_num += 1
                s = lines[line_num]
                assert s.find('Azimuth:') >= 0
                az_deg = float(s.split(':')[1].strip().split()[0])

                # get the elevation
                line_num += 1
                s = lines[line_num]
                assert s.find('Elevation:') >= 0
                el_deg = float(s.split(':')[1].strip().split()[0])

                a = dict(coord=AzAlt_Target(az_deg, el_deg),
                         windows=np.array(windows_list))

            # if right ascension / declination target
            elif cs.find('Method: Right Ascension And Declination') != -1:
                line_num += 1
                s = lines[line_num]
                assert s.find('Catalog Date:') >= 0
                epoch = s.split(':')[1].strip()

                # get the right ascension and convert to nice printing format
                line_num += 1
                s = lines[line_num]
                assert s.find('Right Ascension:') >= 0
                ra_deg = float(s.split(':')[1].strip().split()[0])

                # get the declination and convert to nice printing format
                line_num += 1
                s = lines[line_num]
                assert s.find('Declination:') >= 0
                dec_deg = float(s.split(':')[1].strip().split()[0])

                a = dict(coord=RaDec_Target(ra_deg, dec_deg, epoch),
                         windows=np.array(windows_list))

            # append to the final list
            if a is not None:
                tgt_dict[a['coord']] = a['windows']
            windows_list = []

        line_num += 1

    return tgt_dict

def make_target_array_radec(recs):
    """Make an array of PAM targets, with coordinates in RA/DEC.

    Parameters
    ----------
    recs : sequence of RaDec_Target
        A sequence or list of RaDec_Target items (keys of a target dict)

    Returns
    -------
    coord : SkyCoord
        A astropy SkyCoord array matching the coordinates of the targets
    """
    # rec.epoch?
    data = np.array([(rec.ra_deg, rec.dec_deg)
                     for rec in recs])
    coord = SkyCoord(data.T[0] * u.degree, data.T[1] * u.degree,
                     frame='icrs')
    return coord

def make_target_array_azel(recs, time_t=None, site=None):
    """Make an array of PAM targets, with coordinates in AZ/EL.

    Parameters
    ----------
    recs : sequence of AzAlt_Target
        A sequence or list of AzAlt_Target items (keys of a target dict)

    Returns
    -------
    coord : AltAz
        A astropy AltAz array matching the coordinates of the targets
    """
    data = np.array([(rec.az_deg, rec.alt_deg)
                     for rec in recs])
    coord = AltAz(az=data.T[0] * u.degree, alt=data.T[1] * u.degree,
                  obstime=time_t, location=site)
    return coord

def get_window_status(time_sse, windows):
    time_remaining = 0
    idx = np.searchsorted(windows.T[0], time_sse, side='right')
    if idx == 0:
        # before first open window
        status, reason = False, "before first window"
        time_remaining = windows[0][0] - time_sse
    elif idx < len(windows):
        last_open, last_closed = windows[idx - 1]
        next_open, next_closed = windows[idx]
        if last_open <= time_sse < last_closed:
            status, reason = True, f"in window {idx-1}"
            time_remaining = last_closed - time_sse
        elif time_sse < next_open:
            status, reason = False, f"in between windows {idx-1} and {idx}"
            time_remaining = next_open - time_sse
        elif next_open <= time_sse < next_closed:
            status, reason = True, f"in window {idx}"
            time_remaining = last_closed - time_sse
        else:
            raise ValueError("should not reach here")
    else:
        if time_sse >= windows[-1][1]:
            # past last closure
            status, reason = False, "past last window"
            time_remaining = -1
        else:
            # in last window
            assert time_sse < windows[-1][1]
            time_remaining = windows[-1][1] - time_sse
            status, reason = True, "in last window"
    return (status, reason, time_remaining)
