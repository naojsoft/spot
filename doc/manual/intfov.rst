++++++++++++++
Instrument FOV
++++++++++++++

The Instrument FOV plugin is used to overlay the field of view of an 
instrument over a survey image in the :ref:`FindChannel`. 

.. image:: figures/FOV.*

Image contains data from the WISE 3.4 :math:`\mu`\ m survey. 
(`Wright et al (2010)`_, `Mainzer et al (2011)`_)

.. note:: It is important to have previously downloaded an image in
          the find viewer (using the "FindImage" plugin) that has an
          accurate WCS in order for this plugin to operate properly.

========================
Selecting the Instrument
========================

The instrument can be selected by pressing the "Choose" button under 
"Instrument", and then navigating the menu until you find the 
desired instrument. Once the instrument is selected the name will be 
filled in by "Instrument:" and a red outline of the instrument's 
field of view will appear in the :ref:`FindChannel`. The position 
angle can be adjusted, rotating the survey 
image relative to the instrument overlay. The image can also be 
flipped across the vertical axis by checking the "Flip" box.

The RA and DEC will be autofilled by the :doc:`findchart` channel, but 
can also be adjusted manually by entering in the coordinates. The
RA and DEC can be specified as decimal values or sexagesimal notation.


.. _Wright et al (2010): https://ui.adsabs.harvard.edu/abs/2010AJ....140.1868W/abstract

.. _Mainzer et al (2011): https://ui.adsabs.harvard.edu/abs/2011ApJ...731...53M/abstract
