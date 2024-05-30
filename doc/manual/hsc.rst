+++++++++++
HSC Planner
+++++++++++

HSCPlanner works according to the following steps:

1. establish the pointing of the telescope
2. create a blank field or DSS field from the established pointing
3. place one or more targets within the field
4. set the acquisition parameters and visualize
5. repeat 4. or from earlier steps as needed or desired

We will go over each of these steps in turn.

.. image:: figures/hscwind.*

=====================
Establishing Pointing
=====================

To establish pointing, you can type RA and DEC coordinates (sexigesimal)
into the corresponding boxes under the "Position" section of the GUI and
click "Set Pointing".

Another way that is fairly easy is to drag a FITS image that has a
reasonably accurate WCS with pointing for the desired field into the
main window. Click anywhere on the image to set the RA and DEC boxes,
and you can then click "Set Pointing".

You can use this image as the background image (and skip Step B) if
the FOV is wide enough to show your target of interest (HSC FOV is
approx 1.5 deg).

==========================
Create Field from Pointing
==========================

Once pointing is established, we need to create a background field with
correct WCS to do the correct overplotting to visualize the acquisition.
You can either load your own background image (already discussed),
create a blank field, or download a DSS image of the field (if available).

To create a blank image click "Create Blank". To download a DSS field
click "Get DSS". To use the DSS function you will need a functioning
internet connection.


.. note::   The default location for DSS download is from ESO's web 
            site and it may take up to a minute to download and update 
            the background image. If you experience trouble acquiring a 
            DSS image it is recommended that you download your own 
            background FITS image and load it in step A.

================================
Placing Targets within the Field
================================

To place targets within the field, you can type RA and DEC coordinates
as in step A above or simply click in the field where you want a target
(as in step A the RA and DEC boxes will be filled when you click).
Press "Add Target" to add the current RA/DEC as a target. You can fine
tune the target position by simply moving it using the cursor.
To completely clear the target list, press "Clear All".

============================================
Set the Acquisition Parameters and Visualize
============================================

Now we are finally ready to set the acquisition parameters and visualize
the field throughout the dither. In the section labeled "Acquisition"
you can set any of the parameters normally used for HSC acquisition.

The parameters are:

Dither type:
    1 for a single shot, 5 for a 5-point box pattern, and N
    for an N-point circular pattern

Dither steps: 
    Only settable for N-type dither, set it to the number
    of dither positions

INSROT_PA: 
    This parameter will set up the instrument rotator to set
    the rotation of the field on the CCD plane--see the instrument
    documentation for details

RA Offset, DEC Offset: 
    Offsets in arc seconds from the pointing
    position in the center of the field

Dith1, Dith2 (Delta RA, Delta DEC or RDITH, TDITH): 
    The names of these parameters change according to the dither type selected.
    For Dither Type 1 they are not used.  For Dither Type 5, these
    parameters specify the offsets in arc seconds for Delta RA and Delta DEC
    to accomplish the dither between positions.  For Dither Type N they
    specify the offset in arc seconds (RDITH) and the angle offset in
    degrees (TDITH) for the circular dither.  See the instrument documentation
    for more information.

Skip: 
    The number of shots to skip from the beginning of a dither.
    Leave at the default for the full dither.

Stop: 
    Used to terminate a dither early after a certain number of shots.
    Leave at the default for the full dither.

Once you have set the parameters as desired, press the "Update Image"
button to update the overlays. You can then use the "Show Step" control
to step through your dither.

.. note::   It may be helpful to view the field first with the image 
            zoomed out, and then later to pan to your target (hint: 
            use Shift+click to set pan position) and zoom in to more 
            closely watch the detailed positioning of the target(s) on 
            the detector grid.

=================
Repeat as Desired
=================

You can go back to any step and repeat from there as needed.  It may be
helpful when repositioning targets to press the "Clear Overlays" button,
which will remove the detector and dither position overlays.  Pressing
"Update Image" will bring them right back.

