++++++++++
What's New
++++++++++


Ver 1.5.0 (2026-08-17)
======================
- The altitude / visibility plot is more robust.  The sun almanac methods
  (``sunset``/``sunrise``/the twilights/``night_center``) now truncate
  their search window to the whole second before handing it to skyfield.
  This avoids an intermittent, input-dependent failure in skyfield's
  ``find_settings`` (a NaN in its refinement loop under recent numpy) and a
  boundary case where a sub-second time landing exactly on an event made
  the scan skip to the *next day's* event; the returned time keeps full
  sub-second precision.  The altitude plot also wraps its twilight drawing
  so a failed sun calculation no longer blanks the whole plot, and target
  labels no longer render on a stray blue background box (the label
  background is transparent unless a ``textbg`` is explicitly requested).
- Require ``astropy>=7.2.1`` and ``jplephem>=2.24``: both dropped an
  in-place ``ndarray.shape`` assignment that numpy 2.5 deprecates (which
  otherwise showed up as warnings, or errors under warning-as-error test
  configs).
- Require ``ginga>=7.3.0``, and -- for the web (``pg``) backend -- bump
  the ``pg`` extra to ``pgwidgets-js>=0.4.0`` and
  ``pgwidgets-python>=0.4.0``, picking up the consistent cross-backend
  ``TreeView``/``TableView`` behaviour and the batched table-update
  protocol.

Ver 1.4.0 (2026-08-10)
======================
- Internationalization: SPOT's user interface can now be translated.  SPOT
  registers its own gettext message domain with Ginga's shared localization
  machinery; its user-facing strings (and, per plugin, its help documents)
  can be translated, and a **Language** menu plus a ``language`` general
  setting select the UI language (``None`` honors the environment locale, a
  code such as ``'ja'`` forces that language).  A full Japanese translation
  (interface strings and per-plugin help documents) is included.  See the
  "Language / Localization" section of the documentation for how to add a
  language.
- Added a ``pixi.toml`` manifest (https://pixi.sh) for a reproducible
  conda-forge based development environment: ``pixi run spot`` launches SPOT
  and ``pixi run -e dev test`` runs the test suite.
- mkapp: the standalone app icons (``SPOT.ico`` / ``SPOT.icns``) are now
  rasterized from ``spot/icons/spot.svg`` instead of ``spot_logo.png``.

Ver 1.3.0 (2026-08-04)
======================
- The ``spot`` launcher is now a ``console_scripts`` entry point
  (``spot.main:_main``) instead of a shipped ``scripts/spot`` file, so pip
  generates the platform launcher (including ``spot.exe`` on Windows).
- Added an ``mkapp`` folder for building a standalone desktop application (a
  macOS ``.app`` or Windows ``.exe``) with **PyInstaller**: a single
  ``spot.spec`` builds either platform, driven by a cross-platform
  ``build.py``.  Optional non-PyPI packages (e.g. ``oscript``) are bundled
  automatically when installed in the build environment.  See
  ``mkapp/README.rst``.
- Targets: ``add_targets()`` now also accepts a pandas ``DataFrame`` (in
  addition to an astropy ``Table``); it is converted via
  ``Table.from_pandas`` without SPOT importing pandas.

Ver 1.2.0 (2026-07-16)
======================
- NOTE: requires Ginga v7.0.0
- Consolidated position calculations onto astropy (skyfield is kept for the
  rise/set/twilight almanac); dropped pandas as a dependency
- Added proper motion support: targets with pmRA/pmDEC are propagated from
  the catalog epoch to the observation time
- Coordinates are now converted to ICRS honoring the equinox (J2000, B1950,
  FK5); previously non-J2000 coordinates were treated as ICRS (a B1950
  target could be ~0.7 deg off)
- Much faster visibility and ephemeris computation: vectorized calculation
  over all targets at once, Moon/observer geometry computed once per pass,
  and optional multiprocessing acceleration
- Ephemeris data downloads are now lazy, so plugins load without triggering
  a download
- Per-workspace configuration: each workspace stores its own plugin settings
  under ~/.spot/workspaces/<name>
- CPanel: the "Open Workspace" entry is now an editable combo box; the window
  layout and the set of running plugins are saved and restored per workspace
- Added "Save config" buttons to several plugins (FindImage, Targets, SkyCam,
  SiteSelector, TelescopePosition) to persist their settings
- Targets: .prm files can now be loaded (upload, drag-and-drop, or file
  dialog) and are saved to ~/.spot/prm for resolving OPE-referenced targets
- Targets: a PRM upload now shows a confirmation dialog and handles replacing
  a same-named file
- Fixed target color rotation after a file upload
- Added a second azimuth direction option
- SkyCam: added a monochrome toggle for color images; changed the Subaru
  all-sky camera to the public URL
- Improvements for the web (in-browser) version of SPOT: the Visibility plot
  stays responsive and replots faster; name lookup (Sesame) and JPL Horizons
  ephemerides now work in-browser; a download progress bar was added to
  FindImage
- Added a new SPOT logo, shown in the banner
- Changed the color of the moon
- Removed the Pan and Zoom plugins, as they are no longer needed
- Moved packaging to pyproject.toml, switched from flake8 to ruff, and added
  continuous integration; dropped unused dependencies (pandas, joblib,
  astroquery, requests)
- Fixed timezone abbreviations in date strings so they resolve consistently
  regardless of the host machine

Ver 1.1.0 (2026-02-25)
======================
- Added a feature to InsFov where it rotates the image by the position
  angle to keep the orientation of the FOV overlay
- Added an index column to Targets table for sorting purposes
- Added a priority column to Targets table for sorting purposes;
  can be set by including a "Priority" header and column in CSV file
- Fixed an issue with loading "funky SOSS format" coordinates from CSV files
- Allow FindImage image size to be set in fractional arcminutes in a range
  (from 1.0 to 120.0)
- Fixed "Sync integgui2" feature (available from spot-subaru package)
- Added "Browse" menu to Targets toolbar to allow a search by target
  coordinates and present the results in a web browser
- Updates to documentation

Ver 1.0.1 (2025-08-27)
======================
- updated Subaru/MOIRCS FOV dimensions
- Fixed a bug where Visibility could not be started without access to
  TelescopePosition

Ver 1.0.0 (2025-08-13)
======================
- NOTE: requires Ginga v5.4.0
- Targets plugin: added ability to color targets by file loaded, including
  a button for user to manually select a color if desired
- Targets plugin: Added ability to select and delete an entire category of
  targets--if just the header is selected in the targets tree then all
  targets under that will be deleted
- Targets plugin: Removed "Tag All" and "Untag All" buttons; replaced with
  "Select All" and "Collapse All"
- Targets plugin: the "Plot solar system objects" option is moved under the
  Settings menu
- TelescopePosition plugin: Added an option "Pan to telescope position".
  This will pan the _TGTS window to the telescope position
- Added options to plot only uncollapsed targets (targets that are showing
  in the targets tree) both in _TGTS window (using Targets plugin) and in
  the Visibility plot (using Visibility plugin)
- Targets plugin: added "DateTime" column processing--if such a column
  exists in the CSV file loaded, and the setting "Enable DateTime setting"
  is checked, then the date/time in the column will be used to set the
  date/time in the SiteSelector plugin when you select that target.
- Added CFHT Nana ao visible and IR sky cameras to the list of all sky cameras
- InsFov plugin gets a "Reset" button to reset the _FIND window to the original
  target position if it has changed (e.g. by panning)
- Subaru/HDS_NO_IMR FOV now shows the correct position angle
- Subaru/MOIRCS FOV and Subaru/FOCAS FOV now have detectors labeled
- Pan and Zoom plugins now open into workspaces below the Control panel
- Added --version option to show SPOT version
- Added non-sidereal targets loaded from JPL Horizons ephemeris files
- Now properly support epoch/equinox values in CSV and OPE files
- Now support proper motion in CSV files (columns "pmRA" and "pmDEC" specified
  in milliarcsec / year
- Added HSC and PFS overlays for Subaru instruments (InsFov plugin)
- Added HSC dithering GUI to HSC FOV
- Updated FindImage SkyView survey parameters to provide better quality images

Ver 0.4.1 (2025-03-14)
======================
- Added a Help menu with an About function--shows banner with version
- Fixed a bug with the Workspace menu items
- Documentation updates by E.M. Dailey

Ver 0.4.0 (2024-11-07)
======================
- Fixed an issue where channels could not be closed
- Fixed an issue with the TelescopePosition plugin where it could freeze
  tracking the telescope slew
- Fixed download location of skyfield ephemeris files
- Corrected a problem with the "Plot SS" checkbox and the "Plot"
  drop-down menu in the Targets plugin.
- Added "List All Targets" checkbox to Targets plugin so you can list
  only OPE file targets or list targets from both OPE and PRM files.
- Fixed an issue with PAN-STARRS downloads in the FindImage plugin
- Added more documentation to the manual

Ver 0.3.1 (2024-05-22)
======================
- Change PyPI project name due to conflict

Ver 0.3.0 (2024-05-22)
======================
- initial release to PyPI
- requires ginga>=5.1.0

