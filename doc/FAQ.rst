.. _spot-faq:

++++
FAQs
++++

This section contains some frequently asked questions (FAQs) regarding
SPOT.

-------
General
-------

Why is it installed as "spot-nik" if the name of the program is "spot"?
-----------------------------------------------------------------------
Because on the Python Package Index (PyPI), "spot" was already taken
and we needed a fun name.

---------
Platforms
---------

Does SPOT run on Mac/Windows/Linux/XYZ?
----------------------------------------
SPOT is written entirely in the Python programming language, and uses only
supporting Python packages.  As long as a platform supports Python
and the necessary packages, it can run SPOT.

Is there a web version of SPOT?
-------------------------------
Not yet, but keep an eye out for that.

-----
Usage
-----

SPOT seems to stall when opening the PolarSky plugin?
-----------------------------------------------------
When first running up SPOT, some of the third-party astronomy packages need
to download some ephemeris files.  They will do this in the background,
without any warning to the SPOT user except on the terminal you started
spot (we realize this is not ideal, and are working on a solution for it).
Just please be patient and eventually the
plugin should start

-----------
Customizing
-----------

How can I add my telescope privately to SPOT?
---------------------------------------------
If your desired location is not available, you can easily add your own.
If you have the SPOT source code checked out, you can find the file
_`sites.yml`: https://github.com/naojsoft/spot/blob/main/spot/config/sites.yml
at SPOT's github home, or (if you have downloaded the source code) in
"sites.yml" in .../spot/spot/config/.  Copy this file to $HOME/.spot
and edit it to add your own site.  Be sure to set all of the keywords
for your site (latitude, longitude, elevation, etc).  Restart spot and
you should be able to pick your new location from the list.

How can I get my telescope added to the official list?
------------------------------------------------------
See the sites file (referred to in the question directly above) for the
necessary information to provide to us.  Submit a
_`github issue`: https://github.com/naojsoft/spot/issues with the
request to add your site.

How can I get my telescope to work with the TelescopePosition plugin?
---------------------------------------------------------------------
In order to successfully use this plugin, it is necessary to write a custom
companion plugin to provide the status necessary to draw these positions.
If you didn't create such a plugin, it will look as though the telescope
is parked.

Download the SPOT source code and look in the "spot/examples" folder
for a plugin template called "TelescopePosition_Companion".  Modify
as described in the template.

How can I get my instrument FOV overlay to work with the InsFov plugin?
-----------------------------------------------------------------------
This is a little more complicated, but not too hard.  See the examples
in .../spot/spot/instruments (as well as the {\tt __init__.py} file there.
We can advise you in
_`github discussions`: https://github.com/naojsoft/spot/discussions
