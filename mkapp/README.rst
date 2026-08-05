======================================
Building a standalone SPOT application
======================================

This folder builds a self-contained SPOT desktop application -- a macOS
``.app`` bundle or a Windows ``.exe`` -- with `PyInstaller
<https://pyinstaller.org/>`_, so end users can run SPOT without installing
Python or any packages.

A single spec (``spot.spec``) drives both platforms.  **Build on the OS you
are targeting** -- PyInstaller does not cross-compile, so a macOS ``.app`` must
be built on macOS and a Windows ``.exe`` on Windows.

Files
=====

``SPOT_launch.py``
    The entry script that is frozen into the app.  It simply calls SPOT's
    normal command-line entry point (``spot.main:_main``).

``spot.spec``
    The PyInstaller build recipe (collects SPOT's and Ginga's data files and
    dynamically loaded plugins/backends, the scientific stack, and one Qt
    binding; sets the app icon, version, and -- on macOS -- the ``Info.plist``).

``SPOT.icns`` / ``SPOT.ico``
    Application icons for macOS and Windows, rasterized from
    ``spot/icons/spot.svg`` (see "Regenerating the icons").

``build.py``
    Cross-platform build driver (``python build.py``).  No ``make`` required,
    so it works the same on macOS and Windows.

Prerequisites
=============

In the build environment (a virtualenv or conda env is recommended):

1. Install SPOT plus the PyInstaller tooling::

       pip install -e ..[pyinstaller]      # or: pip install spot-nik[pyinstaller]

   This pulls in Ginga and the rest of SPOT's dependencies as well.

2. Install **exactly one** Qt binding -- whichever is importable is the one
   bundled into the app::

       pip install PyQt5           # or PyQt6 / PySide2 / PySide6

   Having more than one installed can bundle conflicting Qt libraries; keep a
   single binding in the build env.

Bundling optional (non-PyPI) packages
=====================================

Some packages SPOT can use are not on PyPI and are installed from source
(e.g. GitHub).  ``build.py`` keeps a list, ``OPTIONAL_PACKAGES``, of such
packages to fold into the app **if they are installed in the build env** --
the app builds either way; a listed package is simply included when present.

The list ships with ``oscript`` (Subaru observation-script tools).  To include
it, install it before building::

    pip install git+https://github.com/naojsoft/oscript

To bundle additional optional packages, add their import-name to
``OPTIONAL_PACKAGES`` near the top of ``build.py``.  ``build.py`` prints which
optional packages it found before freezing.

Building
========

From this directory::

    python build.py

(equivalently ``pyinstaller --noconfirm spot.spec``).  Useful options::

    python build.py --clean     # remove build/ and dist/, then exit
    python build.py --icon      # regenerate SPOT.ico and SPOT.icns
    python build.py --no-clean  # build without cleaning first

Output:

- **macOS:** ``dist/SPOT.app`` -- double-click to run, or drag into
  ``/Applications``.
- **Windows:** ``dist/SPOT/`` -- a one-folder build; run ``dist/SPOT/SPOT.exe``.
  Zip the ``dist/SPOT`` folder to distribute.

``python build.py --clean`` removes the ``build/`` and ``dist/`` directories.

Notes and caveats
=================

- **Qt binding:** the app uses whatever binding was bundled.  You can override
  the toolkit at runtime as usual (e.g. ``SPOT.app/Contents/MacOS/SPOT -t
  qt6``) as long as that binding was the one built in.

- **Size:** the scientific stack (numpy/scipy/astropy/matplotlib/skyfield)
  makes the bundle large (hundreds of MB).  To slim it, drop unused packages
  from the ``_collect(...)`` calls in ``spot.spec`` and add them to
  ``excludes``.

- **Ephemeris / IERS data:** SPOT downloads ephemeris (e.g. ``de421.bsp``) and
  Earth-orientation data at runtime into the user's ``~/.spot`` on first use;
  these are *not* bundled into the app.

- **First launch on macOS:** an unsigned/unnotarized ``.app`` triggers
  Gatekeeper.  For personal use, right-click -> Open once; for distribution,
  code-sign and notarize the bundle (outside the scope of this spec).

- **Missing modules at runtime:** because SPOT and Ginga load plugins and
  GUI/renderer backends dynamically, the spec bundles *all* ``spot`` and
  ``ginga`` submodules.  If you add a new optional dependency that is imported
  dynamically and it is missing from the frozen app, add it to
  ``hiddenimports`` in ``spot.spec``.

Building in a conda environment
===============================

``build.py`` works fine from an activated conda environment -- it drives
PyInstaller in-process, so it uses the interpreter and libraries of whatever
env you run ``python build.py`` in.  However, conda's scientific stack causes
two well-known PyInstaller issues, so a **clean pip virtualenv is the more
reliable choice** (pip's numpy/scipy wheels use a statically-linked OpenBLAS
that freezes cleanly):

- **MKL bloat.** Conda's numpy/scipy are typically linked against Intel MKL,
  which pulls dozens of large shared libraries (hundreds of MB) into the
  bundle.

- **Missing MKL/OpenMP libraries at runtime.** PyInstaller can miss MKL
  libraries that numpy/scipy load lazily, so the *build* succeeds but the
  frozen app fails on launch with a ``cannot load mkl_...`` error.  This only
  shows up when the app is actually run, so always test the frozen app, not
  just the build.

If you must build in conda, drop MKL first::

    conda install nomkl        # switches numpy/scipy to OpenBLAS

or install numpy/scipy from pip into the env.  Also keep a single Qt binding
in the env: mixing a conda-forge Qt with a pip Qt binding can bundle
conflicting Qt libraries.

Regenerating the icons
======================

``SPOT.ico`` (Windows) and ``SPOT.icns`` (macOS) are rasterized from
``spot/icons/spot.svg`` in the source tree (via cairosvg).  Regenerate them
with::

    python build.py --icon
