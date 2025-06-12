++++++++++
Find Image
++++++++++

The FindImage plugin is used to download and display images from
image catalogs for known coordinates.  It uses the :ref:`FindChannel` 
viewer to show the images found. It is usually used in conjunction with
the :doc:`targetlist`, :doc:`intfov` and/or :doc:`telescopepos` plugins.

.. image:: figures/FindingChart.*

Image contains data from the WISE 3.4 :math:`\mu`\ m survey. 
(`Wright et al (2010)`_, `Mainzer et al (2011)`_)

==================
Selecting a Target
==================

In the :doc:`targetlist` plugin, select a single target to uniquely select it.
Then click the "Get Selected" button in the "Pointing" area of FindImage.
This should populate the "RA", "DEC", "Equinox" and "Name" fields.

.. note:: If you have working telescope status integration, you can
          click the "Follow telescope" checkbox to have the "Pointing"
          area updated by the telescope's actual position.  The image in the
          finding viewer will be panned according to the telescope's
          current position, allowing you to follow a dithering pattern
          (for example).

.. note:: The "Mark target" option will circle and label the target.

=====================================
Loading an image from an image source
=====================================

Once RA/DEC coordinates are displayed in the "Pointing" area, an image
can be downloaded using the controls in the "Image Source" area.
Choose an image source from the drop-down control labeled "Source",
select a size (in arcminutes) using the "Size" control and click the
"Find Image" button.  It may take a little while for the image to be
downloaded and displayed in the finder viewer.

.. note:: Alternatively, you can click "Create Blank" to create a blank
          image with a WCS set to the desired location.  This may
          possibly be useful if an image source is not available.

.. note::   Images will fail to load if the pointing position is outside
            the surveyed regions. Details about each of the surveys including 
            survey coverage can be found in the links below.
                     
            | SkyView:      https://skyview.gsfc.nasa.gov/current/cgi/survey.pl
            | PanSTARRS:    https://outerspace.stsci.edu/display/PANSTARRS/
            | STScI:        https://gsss.stsci.edu/SkySurveys/Surveys.htm
            | SDSS 17:      https://www.sdss4.org/dr17/scope/


.. _Wright et al (2010): https://ui.adsabs.harvard.edu/abs/2010AJ....140.1868W/abstract

.. _Mainzer et al (2011): https://ui.adsabs.harvard.edu/abs/2011ApJ...731...53M/abstract

