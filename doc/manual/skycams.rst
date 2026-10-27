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

The plugin has two tabs: the controls described below are on the "Camera"
tab, and the "History" tab plots the cloud cover over time (see `Cloud
Cover History`_).

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

* "Show Cloud Motion": show an arrow for the direction and speed of the
  clouds (see `Cloud Motion and Clouded Targets`_).

* "Flag Clouded Targets": show targets in or near clouds in the clouded
  target color in the Targets plugin (orange-red by default).

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
  so "Twilight" or "Sun up" is shown instead.  The cloud cover is measured
  whenever two images are available, even if the differential image is not
  shown.

The differential image keeps its own color map and cut levels (by default
-10 to +10 sigma), separate from those of the normal image, and you can
adjust them with the usual viewer controls as well.

After selecting a camera, the differential image appears once a second
image has been received.  If a download returns the same image as the
previous one (the camera has not updated yet), it is ignored.

================================
Cloud Motion and Clouded Targets
================================

At night, SkyCam also maps where the clouds are and follows how they move.
A spot on the sky counts as clouded when more than 20% of the sky within
about 3 degrees of it changed by more than the threshold, so targets close
to a cloud are flagged as well as those right behind one.  With "Flag
Clouded Targets" checked, the Targets plugin shows these targets in the
clouded target color (see :doc:`targetlist`).

Once three images have been received, the motion of the clouds is found by
comparing the last two differences between images, which removes domes,
vignetting and moonlight.  With "Show Cloud Motion" checked, a white arrow
from the zenith shows the direction the clouds are moving and how far they
move in about 5 minutes, labeled with their speed across the sky in degrees
per minute.  (The height of the clouds is not known, so their speed in
kilometers per hour cannot be given.)  The arrow is only shown when the
motion is clear; one layer of cloud usually moves as a whole, so a single
arrow is shown for the whole sky.

Neither is shown in twilight or daylight.  How much cloud counts as
clouded, and the length of the arrow, can be changed with the settings
below.

===================
Cloud Cover History
===================

The "History" tab plots the cloud cover over the last 12 hours, with times
in the time zone of the site selected in SPOT.  A point is added for each
new image from the camera, whether or not the differential image is shown.
Points taken in twilight or daylight are drawn hollow, and the line is
broken where images are missing.  Changing the threshold changes only the
latest point.  "Clear" empties the history, which is also cleared when you
select another camera.

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

========
Settings
========

Besides the choices in the plugin's window, SkyCam has settings that adjust
how the differential image, the cloud cover and the cloud motion are
computed.  They are stored per workspace in
``$HOME/.spot/workspaces/<workspacename>/SkyCam.cfg``, which the "Save
config" button writes (with all the settings, including these).  To change
one, press "Save config" once, quit SPOT, edit the value in the file and
start SPOT again.

``diff_threshold_sigma`` (default 5.0)
    The "Threshold" control: a change larger than this many sigma counts as
    cloud.

``diff_cloud_fraction`` (default 0.2)
    A spot on the sky counts as clouded (for "Flag Clouded Targets") when
    more than this fraction of the sky around it changed by more than the
    threshold.  Raise it to flag only targets well inside clouds.

``diff_cloud_radius_deg`` (default 3.0)
    The size, in degrees, of the area around each spot that is looked at
    for clouds.  A larger value flags targets farther from a cloud's edge.

``diff_motion_minutes`` (default 5.0)
    The cloud motion arrow shows how far the clouds move in this many
    minutes (the arrow is never longer than half the way to the horizon).

``diff_max_za_deg`` (default 75.0)
    Only the sky within this many degrees of the zenith is used for the
    cloud cover, which keeps out the horizon, domes and trees.

``diff_max_sun_alt_deg`` (default -12.0)
    While the Sun is higher than this (in degrees) at the camera, the cloud
    cover is not given ("Twilight" or "Sun up" is shown), and no clouds or
    cloud motion are shown.

``diff_history_hours`` (default 12.0)
    How many hours of cloud cover the "History" tab keeps.

``diff_display_sigma`` (default 10.0)
    The initial cut levels of the differential image, in sigma (-10 to +10
    by default); they can also be changed with the viewer controls.

``diff_work_size`` (default 700) and ``diff_median_size`` (default 3)
    The differential image is computed on a copy of the camera image
    reduced to about this many pixels across, and median filtered over this
    many pixels to remove stars and noise.
