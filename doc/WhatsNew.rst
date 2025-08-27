++++++++++
What's New
++++++++++

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

