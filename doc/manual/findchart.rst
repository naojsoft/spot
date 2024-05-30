+++++++++++++
Finding Chart
+++++++++++++

The finding chart plugin is used to view a sky survey image of a requested 
region of the sky. This plugin is also used in conjuction with 
``Instrument FOV`` and should be opened first.

.. image:: figures/FindingChart.*

======================================
Display an image of a specified region
======================================

The center coordinates of the image can be set by entering the RA, DEC, and 
Equinox under "Pointing". The RA and DEC can be 
specified as decimal values (in which case they are interpreted as degrees) 
or sexigesimal notation (HH:MM:SS.SSS for RA, DD:MM:SS.SS for DEC).  
Equinoxcan be specified as e.g. J2000 or 2000.0.

.. note:: SPOT can also read targets from CSV files in "SOSS notation".
          See the section below on loading targets from an OPE file.

The image source can be selected from a list of optical, ultraviolet,  
infrared, and radio sky surveys. The image will be a square with the height 
and width set by the ``Size (arcmin)`` selection. Once the RA, DEC, and 
Equinox have been selected, the ``Find Image`` button will search for the 
requested survey image and will display it in the ``WS1_FIND`` window. The 
``Create Blank`` button will create an blank image.

.. note::   Images will fail to load if the pointing position is outside
            the surveyed regions. Details about each of the surveys including 
            survey coverage can be found in the links below.
                     
            | SkyView:      https://skyview.gsfc.nasa.gov/current/cgi/survey.pl
            | PanSTARRS:    https://outerspace.stsci.edu/display/PANSTARRS/
            | STScI:        https://gsss.stsci.edu/SkySurveys/Surveys.htm
            | SDSS 17:      https://www.sdss4.org/dr17/scope/

========================
Finding a target by name
========================

An object can be selected by name using the ``Search name`` function under 
"Name Server". SPOT will check either the NASA/IPAC Extragalactic Database 
(NED) (https://ned.ipac.caltech.edu/) or the SIMBAD Astronomical Database 
(http://simbad.cds.unistra.fr/simbad/), and if the object is found the pointing 
information for the target will be automatically filled in. 
