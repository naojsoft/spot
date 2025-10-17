+++++++++++
Target List
+++++++++++

Target List, or Targets (Not to be confused with the Targets channel), is 
normally used in conjunction with other plugins to select targets and to 
show information about celestial 
objects that could be observed.  It allows you to load one or more files 
of targets and then plot them on the :ref:`TargetsChannel`, or show their 
visibility in the :doc:`visplot` plugin UI.

.. image:: figures/targetlist.*

===============================
Loading targets from a CSV file
===============================
Targets can be loaded from a CSV file that contains a column header
containing the column titles "Name", "RA", "DEC", and "Equinox" (they
do not need to be in that order).  Optional columns "Priority" and 
"Comment" may also be added, but are not required.  Other columns may be 
present but will be ignored.  In this format, RA and DEC can be specified as 
decimal values
(in which case they are interpreted as degrees) or sexigesimal notation
(HH:MM:SS.SSS for RA, DD:MM:SS.SS for DEC).  Equinox can be specified
as e.g. J2000 or 2000.0.

.. note:: SPOT can also read targets from CSV files in "SOSS notation".
          See the section in :doc:`targetlistg2` on loading targets from an 
          OPE file.

If you want to set a specific color for the targets to be plotted, click
the "Color" button to manually select a color before proceeding to open
a file, otherwise the targets will be colored according to the option
(described further below) called "Rotate target colors".

Press the "File" button and navigate to, and select, a CSV file with the
above format.  Or, type the path of the file in the box next to the "File"
button and press "Set" (the latter method can also be used to quickly
reload a file that you have edited).

The targets should populate the table.

=================
Table information
=================
The target table summarizes information about targets. There are columns
for static information like target name, RA, DEC, as well as dynamically
updating information for azimuth, altitude, a color-coded rise/set icon,
hour angle, airmass, atmospheric dispersion, parallactic angle and moon
separation. 
Index, Priority, and Comment columns display information from the source file.
Index shows the order that the targets appear in the file, and 
Priority shows the target priority if the file has a priority column.

=========
Operation
=========
To "tag" a target, select a target on the list by left-clicking on it 
and press "Tag". A checkmark will appear on the left side under the 
"Tagged" column to show which targets have been tagged. To untag a target, 
select a tagged target on the list and press "Untag". 

On the :ref:`TargetsChannel` and the :doc:`visplot`, untagged targets will 
appear in the color assigned to the target file and tagged targets will appear 
in magenta. If a target is selected it will appear in blue, and the name 
will have a white background with a red border on the :ref:`TargetsChannel`. 

The "Select All" button will select every loaded target in collapsed and 
uncollapsed files. Pressing "Delete" will delete every selected target from 
the target list. If the target was added from a file, reloading the file by 
pressing "Set" will restore all of the deleted targets. "Collapse All" will 
collapse every target file.

The "Browse" button will open a browser window to run a coordinate search 
based on the coordinates of the selected target. When selecting "Browse", 
a menu will appear with the options `SIMBAD`_ and `NED`_. Choose one of the 
options using left-click and a browser will open and run a search. 

The drop down menu next to "Plot:" changes which targets are plotted on 
the :ref:`TargetsChannel`. Selecting "All" will show all of the targets, 
selecting "Tagged+Selected" will show all of the targets which have been 
tagged or are selected, and selecting "Selected" will show only the 
target which is selected. Selecting "Uncollapsed" will show all of the 
targets from files which have not been collapsed in the target list.

=============
Settings Menu
=============

Clicking the "Settings" button will invoke a pop-up menu to enable certain
settings.

* If you check "Merge Targets" then all targets loaded *after that*
  will be organized under a single heading of "Targets", instead of being
  grouped by file name.
* "List Unreferenced Targets" is a setting that just affects OPE files.
  Normally, the Targets plugin will ignore targets that are not referenced
  in the commands. Checking this setting will show all targets regardless
  of whether they are referenced or not.  This can be used to show targets
  in PRM include files.
* Checking the option for "Plot solar system objects" will plot the Sun,
  Earth's Moon, the planets, and pluto on the `<wsname>_TGTS` window.

* The "Rotate target colors" option will mean that each file loaded will
  use a different automatically selected color for the targets (this will
  only take effect if "Merge targets" is turned off).
* "Enable DateTime setting" is a option to enable the setting of a fixed
  date/time if the CSV file includes a "DateTime" column.  When enabled,
  selecting a single target in the table will set the date/time in the
  SiteSelector plugin to that date and time.  The format of this column
  should be: YYYY-MM-DD HH:MM:SS <TZ>
  If the timezone string is omitted, UTC is assumed.

.. _NED: https://ned.ipac.caltech.edu/

.. _SIMBAD: http://simbad.cds.unistra.fr/simbad/