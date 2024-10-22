+++++++++++++
Finding Chart
+++++++++++++

The finding chart plugin is used to view a survey image of a requested 
region of the sky. This plugin is used in conjunction with 
:doc:`targetlist`, :doc:`intfov` and/or :doc:`telescopepos`.

.. image:: figures/FindingChart.*

Image contains data from the WISE 3.4 :math:`\mu`\ m survey. 
(`Wright et al (2010)`_, `Mainzer et al (2011)`_)

======================================
Display an image of a specified region
======================================

The center coordinates of the image can be set either from a target from 
the :doc:`targetlist` or from the telescope position. To set the coordinates 
from the target list, double left-click a target from the list and the
coordinates under "Pointing" will be automatically filled out. 
Alternatively, the coordinates can be set from the current telescope pointing 
by checking the checkbox by "Follow telescope" (requires the 
:doc:`telescopepos` plugin). Checking the "Lock Target" checkbox will prevent 
the coordinates from changing until the box is unchecked.

The image source can be selected from a list of optical, ultraviolet,  
infrared, and radio sky surveys. The image will be a square with the height 
and width set by the "Size (arcmin)" selection. Once the RA, DEC, and 
Equinox have been selected, the "Find Image" button will search for the 
requested survey image and will display it in the "wsname_FIND" window. The 
"Create Blank" button will create a blank image.

.. note::   Images will fail to load if the pointing position is outside
            the surveyed regions. Details about each of the surveys including 
            survey coverage can be found in the links below.
                     
            | SkyView:      https://skyview.gsfc.nasa.gov/current/cgi/survey.pl
            | PanSTARRS:    https://outerspace.stsci.edu/display/PANSTARRS/
            | STScI:        https://gsss.stsci.edu/SkySurveys/Surveys.htm
            | SDSS 17:      https://www.sdss4.org/dr17/scope/


.. _Wright et al (2010): https://ui.adsabs.harvard.edu/abs/2010AJ....140.1868W/abstract

.. _Mainzer et al (2011): https://ui.adsabs.harvard.edu/abs/2011ApJ...731...53M/abstract
