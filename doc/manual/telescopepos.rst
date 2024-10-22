++++++++++++++++++
Telescope Position
++++++++++++++++++

The telescope position plugin displays live telescope and 
target positions.

.. note:: In order to successfully use this plugin, it is necessary
          to write a custom companion plugin to provide the status
          necessary to draw these positions.  If you didn't create such
          a plugin, it will look as though the telescope is parked.

.. image:: figures/telpos2.*

The telescope and target positions are shown in both
Right Ascension/Declination and Azimuth/Elevation.
RA and DEC are displayed in sexigesimal notation as 
HH:MM:SS.SSS for RA, and DD:MM:SS.SS for DEC. 
AZ and EL are both displayed in degrees as decimal 
values. 
In the "Telescope" section, the telescope status, such as 
pointing or slewing, is shown along with the slew time in 
h:mm:ss.

The "Plot telescope position" button will show the 
Target and Telescope positions on the Targets window when 
the button is selected. 

The "Rotate view to azimuth" button will orient the Targets 
window so the telescope azimuth is always facing towards the 
top of the screen.

==========================
Writing a Companion Plugin
==========================

Download the SPOT source code and look in the "spot/examples" folder
for a plugin template called "TelescopePosition_Companion".  Modify
as described in the template.


