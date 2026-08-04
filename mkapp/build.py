#!/usr/bin/env python
#
# build.py -- freeze a standalone SPOT app with PyInstaller.
#
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.md for details.
#
"""Build a standalone SPOT application (macOS ``.app`` / Windows ``.exe``).

    python build.py            # clean previous output, then freeze the app
    python build.py --no-clean # freeze without cleaning first
    python build.py --clean    # only remove build/ and dist/, then exit
    python build.py --icon     # (re)generate SPOT.ico and SPOT.icns

Runs the same on macOS and Windows (and Linux, for a smoke build).  Unlike a
Makefile it needs no ``make`` -- only the Python already required to build --
and it drives PyInstaller through its Python API, so the ``pyinstaller``
console script does not need to be on PATH.

Prerequisites (in the build env): ``pip install spot-nik[pyinstaller]`` plus
one Qt binding (e.g. ``pip install PyQt5``).  See README.rst.
"""
import argparse
import importlib.util
import shutil
import sys
from pathlib import Path

# Optional packages to bundle *if they are installed* in the build env.
# These are NOT PyPI dependencies of SPOT (e.g. installed from GitHub), so the
# app is built either way -- they are only included when present.  Install
# them before running this script, then add their import-name to this list.
#
#   oscript -- Subaru observation-script tools; not on PyPI, install with
#              pip install git+https://github.com/naojsoft/oscript
#
# The spec (spot.spec) imports this list and collects each one that imports.
OPTIONAL_PACKAGES = ["oscript"]

HERE = Path(__file__).resolve().parent
SPEC = HERE / "spot.spec"
# square source logo shipped in the package
ICON_SRC = HERE.parent / "spot" / "icons" / "spot_logo.png"
ICO_OUT = HERE / "SPOT.ico"
ICNS_OUT = HERE / "SPOT.icns"
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48),
             (64, 64), (128, 128), (256, 256)]


def clean():
    for name in ("build", "dist", "__pycache__"):
        path = HERE / name
        if path.exists():
            print("removing", path)
            shutil.rmtree(path)


def make_icons():
    from PIL import Image
    img = Image.open(ICON_SRC).convert("RGBA")
    # Windows .ico (multi-resolution)
    print("generating %s from %s" % (ICO_OUT.name, ICON_SRC))
    img.save(ICO_OUT, sizes=ICO_SIZES)
    # macOS .icns (Pillow derives the standard sizes from a large square)
    print("generating %s from %s" % (ICNS_OUT.name, ICON_SRC))
    img.resize((1024, 1024)).save(ICNS_OUT)


def _report_optional():
    if not OPTIONAL_PACKAGES:
        return
    print("optional packages:")
    for pkg in OPTIONAL_PACKAGES:
        present = importlib.util.find_spec(pkg) is not None
        print("  %-14s %s" % (
            pkg, "found (will bundle)" if present
            else "not installed (skipping)"))


def build():
    import PyInstaller.__main__
    _report_optional()
    print("freezing app from", SPEC.name)
    PyInstaller.__main__.run(["--noconfirm", str(SPEC)])
    result = "dist/SPOT.app" if sys.platform == "darwin" else "dist/SPOT/"
    print("\nDone.  Result: %s" % result)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Build a standalone SPOT app with PyInstaller.")
    ap.add_argument("--clean", action="store_true",
                    help="remove build/ and dist/, then exit")
    ap.add_argument("--icon", action="store_true",
                    help="regenerate SPOT.ico and SPOT.icns, then exit")
    ap.add_argument("--no-clean", action="store_true",
                    help="do not clean before building")
    args = ap.parse_args(argv)

    if args.clean:
        clean()
        return
    if args.icon:
        make_icons()
        return
    if not args.no_clean:
        clean()
    build()


if __name__ == "__main__":
    main()

# END
