++++++++++++++++++
Telescope Position
++++++++++++++++++

The telescope position plugin displays live telescope and
target positions.

.. note:: In order to successfully use this plugin, it is necessary
          to write a custom companion plugin to provide the status
          necessary to draw these positions.  If you didn't create such
          a plugin, it will look as though the telescope is parked.

.. image:: figures/telpos.*

The telescope and target positions are shown in both
Right Ascension/Declination and Azimuth/Elevation.
RA and DEC are displayed in sexagesimal notation as
HH:MM:SS.SSS for RA, and DD:MM:SS.SS for DEC.
AZ and EL are both displayed in degrees as decimal
values.
In the "Telescope" section, the telescope status, such as
pointing or slewing, is shown along with the slew time in
h:mm:ss.

The "Plot telescope position" button will show the
Target and Telescope positions on the :ref:`TargetsChannel` viewer when
the button is selected.

The "Target follow telescope" option will cause a target to be selected
in the :doc:`targetlist` plugin table when the telescope is "close" to that target
(close being defined as within approximately 10 arc minutes). The closest
actual target to the telescope's coordinate is selected.

.. note:: If a target is manually selected by the user after checking this
          box it will automatically uncheck the option.  To restore the
          target following the telescope, simply recheck the box.

The "Pan to telescope position" option will cause the :ref:`TargetsChannel`
viewer to pan to the telescope position.  This can be helpful when there are
a lot of targets plotted and you have zoomed in to show only a part of the polar
sky field.

===============
Enabling Plugin
===============

This plugin in not enabled by default. To enable it, first go to
"PluginConfig", which may be found by pressing "Operation" at the bottom left
and then going to "Debug" and then "PluginConfig".
Find "Telescope Position" from the list of plugins, then press "Edit" and then
check the checkbox next to "Enabled". Press "Set", then close the window and
press "Save". Restart SPOT and the plugin should appear on the control panel.

==========================
Writing a Companion Plugin
==========================

Download the SPOT source code and look in the "spot/examples" folder
for a plugin template called "TelescopePosition_Companion".  Modify
as described in the template.
