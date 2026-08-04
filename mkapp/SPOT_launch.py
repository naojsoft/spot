#!/usr/bin/env python
#
# SPOT_launch.py -- entry point for the frozen (PyInstaller) SPOT app.
#
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.md for details.
#
"""Launch the SPOT (Site Planning and Observation Tool) app from a frozen
bundle.

This is the script PyInstaller freezes into the macOS ``.app`` / Windows
``.exe`` (see ``spot.spec``).  It defers to the same entry point the ``spot``
console command uses -- ``spot.main:_main`` -- which parses ``sys.argv`` and
runs the app.
"""
import multiprocessing

from spot.main import _main

if __name__ == "__main__":
    # A frozen app may re-exec itself to spawn worker processes (the
    # Windows / macOS "spawn" start method).  freeze_support() makes those
    # children return here and run as workers instead of relaunching the
    # whole GUI; it is a harmless no-op in the parent process.
    multiprocessing.freeze_support()
    _main()

# END
