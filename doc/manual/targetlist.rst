+++++++++++
Target List
+++++++++++

``Target List``, or ``Targets``, is normally used in conjunction with the 
plugins ``PolarSky`` and ``Visibility`` to show information about celestial 
objects that could be observed.  It allows you to load one or more files 
of targets and then plot them on the "<wsname>_TGTS" window, or show their 
visibility in the ``Visibility`` plugin UI.

===============================
Loading targets from a CSV file
===============================
Targets can be loaded from a CSV file that contains a column header
containing the column titles "Name", "RA", "DEC", and "Equinox" (they
do not need to be in that order).  Other columns may be present but will
be ignored.  In this format, RA and DEC can be specified as decimal values
(in which case they are interpreted as degrees) or sexigesimal notation
(HH:MM:SS.SSS for RA, DD:MM:SS.SS for DEC).  Equinox can be specified
as e.g. J2000 or 2000.0.

.. note:: SPOT can also read targets from CSV files in "SOSS notation".
          See the section below on loading targets from an OPE file.

Press the "File" button and navigate to, and select, a CSV file with the
above format.  Or, type the path of the file in the box next to the "File"
button and press "Set" (the latter method can also be used to quickly
reload a file that you have edited).

The targets should populate the table.

================================
Loading targets from an OPE file
================================
An OPE file is a special format of file used by Subaru Telescope.
Targets in this kind of file are specified in "SOSS notation"
(HHMMSS.SSS for RA, +|-DDMMSS.SS for DEC, NNNN.0 for Equinox).

Follow the instructions above for loading targets from a CSV file, but
choose an OPE file instead.

.. note::  In order to load this format you need to have installed the
           optional "oscript" package:
           (pip install git+https://github.com/naojsoft/oscript).

=================
Table information
=================
The target table summarizes information about targets. There are columns
for static information like target name, RA, DEC, as well as dynamically
updating information for azimuth, altitude, a color-coded rise/set icon,
hour angle, airmass, atmospheric dispersion, parallactic angle and moon
separation.
