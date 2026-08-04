# -*- mode: python ; coding: utf-8 -*-
#
# spot.spec -- PyInstaller build spec for a standalone SPOT application.
#
# Builds a macOS ``.app`` or a Windows ``.exe`` from the same spec; run it on
# the target OS:
#
#     pyinstaller spot.spec
#         macOS   -> dist/SPOT.app
#         Windows -> dist/SPOT/SPOT.exe   (one-folder build)
#
# The build environment must have SPOT and its dependencies installed (which
# pulls in Ginga), plus PyInstaller and *exactly one* Qt binding (PyQt5,
# PyQt6, PySide2, or PySide6) -- whichever is importable is the one bundled.
# See README.rst for the full recipe.
#
# Targets PyInstaller >= 6 (the 5.x ``cipher=`` / ``block_cipher`` arguments
# were removed and are intentionally not used here).

import re
import sys

from PyInstaller.utils.hooks import collect_all, collect_submodules

# The list of optional (non-PyPI) packages to bundle lives in build.py so it
# is easy to extend; import it whether we are launched via build.py or via a
# bare ``pyinstaller spot.spec``.  Fall back to a sensible default if build.py
# is not importable for some reason.
sys.path.insert(0, SPECPATH)
try:
    from build import OPTIONAL_PACKAGES
except Exception:
    OPTIONAL_PACKAGES = ['oscript']

# --- version -----------------------------------------------------------------
# CFBundleVersion (macOS) and the Windows product version want a clean numeric
# X.Y.Z; strip any PEP 440 dev/local suffix, e.g.
# '1.3.0.dev3+gb9dd639d9' -> '1.3.0'.
from spot import __version__ as _spot_version   # noqa: E402
_m = re.match(r'\d+(?:\.\d+){0,2}', _spot_version)
version = _m.group(0) if _m else '0.0.0'

# --- collect dependencies ----------------------------------------------------
datas, binaries, hiddenimports = [], [], []


def _collect(pkg, required=False):
    global datas, binaries, hiddenimports
    try:
        d, b, h = collect_all(pkg)
    except Exception as e:
        if required:
            raise
        print("spot.spec: skipping optional package %r (%s)" % (pkg, e))
        return
    datas += d
    binaries += b
    hiddenimports += h


# SPOT and Ginga: grab their data files (icons, config, help docs, examples,
# fonts, cursors, ...) AND every submodule -- both load plugins / GUI backends
# dynamically, so PyInstaller's import follower cannot see them on its own.
for _pkg in ('spot', 'ginga'):
    _collect(_pkg, required=True)
    hiddenimports += collect_submodules(_pkg)

# Scientific / astronomy stack that ships data files or has dynamic pieces.
for _pkg in ('astropy', 'matplotlib', 'scipy', 'skyfield', 'jplephem',
             'dateutil', 'PIL'):
    _collect(_pkg)

# Optional, non-PyPI packages (see build.py's OPTIONAL_PACKAGES): bundle each
# one only when it is importable in the build env.
for _pkg in OPTIONAL_PACKAGES:
    try:
        __import__(_pkg)
    except ImportError:
        print("spot.spec: optional package %r not installed; not bundling"
              % _pkg)
        continue
    _collect(_pkg, required=True)
    hiddenimports += collect_submodules(_pkg)
    print("spot.spec: bundling optional package %r" % _pkg)

# Bundle whichever single Qt binding is installed in the build env; qtpy then
# selects it at runtime.
_qt_binding = None
for _binding in ('PyQt5', 'PyQt6', 'PySide2', 'PySide6'):
    try:
        __import__(_binding)
    except ImportError:
        continue
    _qt_binding = _binding
    _collect(_binding, required=True)
    hiddenimports += ['qtpy']
    break
if _qt_binding is None:
    raise SystemExit("spot.spec: no Qt binding found in the build env; "
                     "install one of PyQt5/PyQt6/PySide2/PySide6")
print("spot.spec: bundling Qt binding %r, version %s" % (_qt_binding, version))

# --- analysis / build --------------------------------------------------------
a = Analysis(
    ['SPOT_launch.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Keep the bundle lean and avoid Qt-binding clashes: drop the dead PyQt4,
    # the other GUI toolkits Ginga can use but we are not shipping here, and
    # OpenCV (large, optional accel only).
    excludes=['PyQt4', 'tkinter', 'gi', 'cv2'],
    noarchive=False,
)
pyz = PYZ(a.pure)

icon = 'SPOT.ico' if sys.platform == 'win32' else 'SPOT.icns'

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SPOT',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # windowed GUI app (no console window on Windows)
    disable_windowed_traceback=False,
    icon=icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SPOT',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='SPOT.app',
        icon='SPOT.icns',
        bundle_identifier='org.naoj.SPOT',
        version=version,
        info_plist={
            'CFBundleName': 'SPOT',
            'CFBundleDisplayName': 'SPOT',
            'CFBundleExecutable': 'SPOT',
            'CFBundleIdentifier': 'org.naoj.SPOT',
            'CFBundleShortVersionString': version,
            'CFBundleVersion': version,
            'CFBundleDevelopmentRegion': 'English',
            'NSHumanReadableCopyright':
                'Copyright © 2020-2026, SPOT Maintainers (ocs@naoj.org)',
            # Retina / HiDPI rendering
            'NSHighResolutionCapable': True,
        },
    )

# END
