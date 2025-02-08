#! /usr/bin/env python3
#
import sys
import io
from datetime import datetime, timedelta
from dateutil import parser, tz
import random
import csv
from argparse import ArgumentParser

from ginga.util import wcs

hdr_window = 'YYYY MMM dd (DDD) HHMM SS    YYYY MMM dd (DDD) HHMM SS      MM:SS'
hdr_template = '{fyear:04d} {fmonth:03s} {fday:02d} ({fyday:03d}) {fhour:02d}{fmin:02d} {fsec:02d}    {tyear:04d} {tmonth:03s} {tday:02d} ({tyday:03d}) {thour:02d}{tmin:02d} {tsec:02d}    {durmin:04d}:{dursec:02d}'

months = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')

source_geometry_template = """
Source Geometry: ({name})
---------------
Method: Fixed Point
Latitude:  19.8255 degrees N
Longitude: 155.47602 degrees W
Altitude:  4.16409 km
"""

target_geometry_radec_template = """
Target Geometry: ({name}) {target_num}
---------------
Method: Right Ascension And Declination
Catalog Date:    J2000
Right Ascension: {ra_deg:.4f} degrees
Declination:     {dec_deg:.4f} degrees
"""

target_geometry_azel_template = """
Target Geometry: ({name}) {target_num}
---------------
Method: Fixed Azimuth/Elevation
Azimuth:   {az_deg:.1f} degrees
Elevation: {el_deg:.1f} degrees
"""

min_closed_sec = 5
max_closed_sec = 60

def write_pam_target(out_f, dt_start, dt_stop, src_dct, tgt_dct,
                     num_windows=None):
    if num_windows is None:
        num_windows = random.randint(20, 80)

    cur_sse = dt_start.timestamp()
    end_sse = dt_stop.timestamp()
    total_sec = end_sse - cur_sse
    inc_sse = int((end_sse - cur_sse) / num_windows)

    num_closures = num_windows - 1
    closures = []
    for i in range(num_closures):
        closure_delta = timedelta(0, seconds=random.randint(min_closed_sec,
                                                            max_closed_sec))
        closure_time = dt_start + timedelta(0, seconds=random.randint(100, int(total_sec - 2*100)))

        closures.append((closure_time, closure_delta))
    closures.sort(key=lambda x: x[0])

    windows = []
    total_closed = 0
    fd = dt_start
    for dt_closure, delta_closure in closures:
        if dt_closure <= fd:
            continue
        total_closed += delta_closure.seconds
        windows.append((fd, dt_closure))
        fd = dt_closure + delta_closure

    print(hdr_window, file=out_f)

    for fd, td in windows:
        duration = (td - fd).total_seconds()
        durmin = int(duration // 60)
        dursec = int(duration % 60)

        dct = dict(fyear=fd.year, fmonth=months[fd.month-1], fday=fd.day,
                   fyday=fd.timetuple().tm_yday,
                   fhour=fd.hour, fmin=fd.minute, fsec=fd.second,
                   tyear=td.year, tmonth=months[td.month-1], tday=td.day,
                   tyday = td.timetuple().tm_yday,
                   thour=td.hour, tmin=td.minute, tsec=td.second,
                   durmin=durmin, dursec=dursec)
        print(hdr_template.format(**dct), file=out_f)

    pct = (total_sec - total_closed) / total_sec
    print("", file=out_f)
    print("Percent = {:.2f}%".format(pct * 100), file=out_f)

    print(source_geometry_template.format(**src_dct), file=out_f)

    if 'ra_deg' in tgt_dct:
        print(target_geometry_radec_template.format(**tgt_dct), file=out_f)
    else:
        print(target_geometry_azel_template.format(**tgt_dct), file=out_f)


def main(options, args):

    if len(args) == 0:
        print("Please provide an input file")
        sys.exit(1)
    input_file = args[0]

    tz_local = tz.gettz(options.timezone)
    if options.date is None:
        start_time = datetime.now().replace(tzinfo=tz_local)
    else:
        start_time = parser.parse(options.date).replace(tzinfo=tz_local)
    midnight = parser.parse(start_time.strftime("%Y-%m-%d") + " 00:00:00").replace(tzinfo=tz_local)

    obs_start_time = parser.parse(options.obs_start).time()
    t_delta = timedelta(hours=obs_start_time.hour, minutes=obs_start_time.minute)
    dt_start = (midnight + t_delta).astimezone(tz.UTC)
    dt_stop = dt_start + timedelta(0, hours=10)

    with open(input_file, 'r') as in_f:
        reader = csv.reader(in_f, delimiter=',')
        hdr = reader.__next__()
        is_radec = 'RA' in hdr
        is_azel = 'AZ' in hdr
        if not (is_radec or is_azel):
            print("No RA or AZ found in header")
            sys.exit(1)

        if options.output_file is not None:
            out_f = open(options.output_file, 'w')
        else:
            out_f = io.StringIO()

        for row in reader:
            if len(row) == 0:
                continue
            if is_radec:
                name, ra, dec, eq, comment = row
                try:
                    ra_deg, dec_deg = float(ra), float(dec)

                except ValueError:
                    if ':' in ra:
                        ra_deg = wcs.hmsStrToDeg(ra)
                        dec_deg = wcs.dmsStrToDeg(dec)

                src_dct = dict(name=name)
                tgt_dct = dict(name=name, target_num=1,
                               ra_deg=ra_deg, dec_deg=dec_deg)
            elif is_azel:
                name, az, el, comment = row
                az_deg, el_deg = float(az), float(el)
                src_dct = dict(name=name)
                tgt_dct = dict(name=name, target_num=1,
                               az_deg=az_deg, el_deg=el_deg)

            write_pam_target(out_f, dt_start, dt_stop, src_dct, tgt_dct)

    if options.output_file is None:
        print(out_f.getvalue())


if __name__ == "__main__":
    argprs = ArgumentParser(description="Write simulated PAM files")
    argprs.add_argument("-d", "--date", dest="date", metavar="YYYY-MM-DD",
                        default=None,
                        help="Specify date for observation")
    argprs.add_argument("--obs-start", dest="obs_start",
                        default='18:00',
                        help="Observation window start time HH:MM",
                        metavar="OBS_START")
    argprs.add_argument("-z", "--timezone", dest="timezone", metavar="TIMEZONE",
                        default="UTC",
                        help="Specify time zone for observation")
    argprs.add_argument("-o", "--output", dest="output_file", metavar="FILE",
                        default=None,
                        help="Specify an output file")

    (options, args) = argprs.parse_known_args(sys.argv[1:])
    main(options, args)
