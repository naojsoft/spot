++++++++++++++
Instrument FOV
++++++++++++++

The Instrument FOV plugin is used to overlay the field of view of an 
instrument over a survey image in the :ref:`FindChannel`. 

.. image:: figures/FOV.*

Image contains data from the WISE 3.4 :math:`\mu`\ m survey. 
(`Wright et al (2010)`_, `Mainzer et al (2011)`_)

.. note:: It is important to have previously downloaded an image in
          the find viewer (using the :doc:`findchart` plugin) that has an
          accurate WCS in order for this plugin to operate properly.

========================
Selecting the Instrument
========================

The instrument can be selected by pressing the "Choose" button under
"Instrument", and then navigating the menu until you find the
desired instrument. Once the instrument is selected the name will be
filled in by "Instrument:" and an outline of the instrument's
field of view will appear in the :ref:`FindChannel` window.

.. note:: The HSC intrument overlay has additional features. See
          :doc:`hsc` for more information.

The position angle can be adjusted, which will adjust the angle of
the instrument FOV overlay on the image.  If the "Rotate w/PA" box is
checked then the viewer image will be rotated so that the FOV overlay
remains in the same orientation. If "Rotate w/PA" is not selected, the
instrument overlay will rotate while the image remains static.
The image can also be flipped across the vertical axis by checking the
"Flip" box.

The RA and DEC will be autofilled by setting the pan position in the
:doc:`findchart` window (for example, by Shift-clicking), but can also
be adjusted manually by entering in the coordinates. The RA and DEC
can be specified as decimal values (degrees) or sexigesimal notation.

To center the image on the current telescope pointing, check the box
next to "Follow telescope" in the :doc:`findchart` plugin UI.  This will
allow you to watch a dither happening on an area of the sky if the WCS
is reasonably accurate in the finding image.

.. note:: To get the "Follow telescope" feature to work, you need to
          have written a companion plugin to get the status from your
          telescope as described in the documentation for the
          TelescopePosition plugin.


.. _Wright et al (2010): https://ui.adsabs.harvard.edu/abs/2010AJ....140.1868W/abstract

.. _Mainzer et al (2011): https://ui.adsabs.harvard.edu/abs/2011ApJ...731...53M/abstract
