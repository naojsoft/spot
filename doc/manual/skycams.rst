++++++++
Sky Cams
++++++++

The SkyCam plugin is used to place an all sky camera image on the background
of the Targets channel to assist with monitoring sky conditions. There is a
drop-down menu with several sites to choose from.

.. image:: figures/skycam.*

=====================
Setting the Sky Image
=====================

Select the camera server you would like to use from the drop down menu
under "All Sky Camera". Then, press the checkbox next to "Show Sky Image"
to display the image in the Targets channel. It may take a few moments
before the sky image appears in the channel. When the image updates,
the time and date of the last image will be displayed at the bottom of the
window underneath "Image Download Info".

Some all-sky cameras produce color images.  Checking the "Monochrome"
checkbox converts these to a monochrome (grayscale) image; uncheck it to
show the original colors.

The sky image is drawn with the viewer's color map and cut levels, so you
can adjust its contrast and cut levels with the usual viewer controls (for
a color image only the cut levels apply).  Your settings are kept when new
images arrive.

The "Save config" button records your current selections (camera server,
"Show Sky Image", "Show Differential Image" and "Monochrome") for the
workspace, so they are restored the next time it is opened.

==================
Differential Image
==================

Select the checkbox next to "Show Differential Image" to show how the sky
changed between the last two images from the camera, instead of the image
itself.  This makes moving or developing clouds much easier to see.  With
the default "Gray" color map, areas that did not change are medium gray,
areas that became brighter are lighter and areas that became darker are
darker.  Clouds lit by the Moon or by city lights usually get brighter;
clouds that hide the stars or the Milky Way get darker.

.. image:: figures/skydif.*

To make the differential image, both images are converted to monochrome,
reduced in resolution and median filtered, which removes most stars and
noise.  The previous image is scaled to match the overall brightness of the
current one, so that changes in the camera's exposure do not look like
clouds.  The difference is then divided by an estimate of the noise in the
image, so the differential image is in units of the noise ("sigma").

The controls are:

* "Derotate Sky": the sky rotates by about a quarter of a degree per
  minute, so stars move between images.  With this checked, the previous
  image is rotated about the celestial pole to the time of the current
  image, so that the stars cancel out and only real changes remain.  This
  needs the camera orientation in skycams.yml to be correct (see `Adding
  new cameras`_).  Objects fixed in the camera view, such as domes or trees
  near the horizon, may then leave curved streaks.

* "Threshold": a change larger than this many sigma counts as cloud for
  the cloud cover (default 5).

* "Color Map": the color map for the differential image.  "Gray" and
  "Change" (which shows only the size of the change, not whether it got
  brighter or darker) keep the target overlays easy to read; "Teal/Amber"
  and "Blue/Red" show the direction of the change in color.

* "Cloud Cover": the percentage of the sky within 75 degrees of the zenith
  that changed by more than the threshold.  It measures clouds that move or
  change between images; a uniform overcast that does not change will not
  show up.  While the Sun is less than 12 degrees below the horizon at the
  camera the sky brightness changes too quickly for this to mean anything,
  so "Twilight" or "Sun up" is shown instead.

The differential image keeps its own color map and cut levels (by default
-10 to +10 sigma), separate from those of the normal image, and you can
adjust them with the usual viewer controls as well.

After selecting a camera, the differential image appears once a second
image has been received.  If a download returns the same image as the
previous one (the camera has not updated yet), it is ignored.

==================
Adding new cameras
==================

You can easily add your own all-sky camera images if you have a suitable
feed of images that can be fetched via web protocols.
If you have the SPOT source code checked out, you can find the file
"skycams.yml" in .../spot/spot/config/.  Copy this file to $HOME/.spot
and edit it to add your own camera.  You will need to provide a URL
for downloading images, a title, a center pixel (X and Y coords) in the
image representing the zenith, the radius of the circle to the horizon
in pixels, a rotation to be applied, whether to flip the image in X or
Y dimensions, and an update interval measured in seconds.  You can also
give the location of the camera in degrees as "latitude" (negative in the
southern hemisphere) and "longitude" (negative west of Greenwich).  The
latitude is used to derotate the sky for the differential image, and both
are used to tell when it is night at the camera.  Without them, the
location of the site selected in SPOT is used, which is wrong if the camera
is at a different site.

Some cameras only publish an animated image (such as a GIF loop of the last
several images).  SPOT then uses the last frame of the animation, which is
normally the most recent one; to use a different frame, give its number as
"frame" (counting from 0, or from -1 for the last frame).

The rotation and flips must turn the image so that North is up and East is
to the left, as in the polar sky plot (in both hemispheres).  A good check
is that the Moon or a bright planet in the sky image lines up with its
position in SPOT, and that stars cancel out in the differential image with
"Derotate Sky" checked.

For example::

    Canary - La Palma/GTC (Visual):
      url: "https://www.gtc.iac.es/multimedia/netcam/camaraAllSky.jpg"
      title: "Canary - La Palma/GTC (Visual)"
      ctr_x: 327
      ctr_y: 252
      radius: 300
      rot_deg: -35.6
      flip_y: False
      flip_x: False
      update_interval: 180.0
      latitude: 28.7564
      longitude: -17.8920

Restart spot and you should be able to pick your new camera from the list.
