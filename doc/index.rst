.. SPOT documentation master file

++++++++++++++++++++++++++++++++++++++++
SPOT: Site Planning and Observation Tool
++++++++++++++++++++++++++++++++++++++++

.. image:: manual/figures/SampleWorkspace2.*

.. toctree::
   :maxdepth: 2

==========
About SPOT
==========

SPOT (Site Planning and Observation Tool) is a graphical tool for planning
and conducting astronomical observations at a site.  Here are few of the
things it can do:

- You can select a site and date/time when you plan to observe (it's also
  easy to add your own custom site).
- It can show you an astronomical almanac of information about a particular
  date (sunrise, sunset, moonrise, moonset, twilights, etc).
- It can load lists of targets and plot them on a polar plot for their
  position in the sky at the current time or any given time.
- It can show you the various targets' visibility as a plot of altitude
  vs. time.
- It can overlay fisheye-type sky camera images on the polar plot so that
  you can monitor for cloud coverage.
- With the right customization it can show you where your telescope target
  is, the current telescope position and the slew that it will take to get
  there on the polar plot.
- It can look up catalog images from various sources for a given target
  and show instrument detector overlays on top, with adjustable position
  angle.


=====================
Copyright and License
=====================

Copyright (c) 2023-2024 SPOT Maintainers. All rights reserved.

SPOT is distributed under an open-source BSD licence. Please see the
file ``LICENSE.md`` in the top-level directory for details.

====================================
Requirements and Supported Platforms
====================================

Because SPOT is written in pure Python, it can run on any platform that
has the required Python modules.

==================
Getting the Source
==================

Clone from Github::

    git clone https://github.com/naojsoft/spot.git

=============
Documentation
=============

.. toctree::
   :maxdepth: 1

   WhatsNew
   install
   FAQ
   manual/index

Be sure to also check out the
`SPOT wiki <https://github.com/naojsoft/spot/wiki>`_.

===========
Bug Reports
===========

Please file an issue with the `issue tracker
<https://github.com/naojsoft/spot/issues>`_
on Github.

SPOT has a logging facility, and it would be most helpful if you can
invoke SPOT with the logging options to capture any logged errors::

    spot --loglevel=20 --log=spot.log --stderr


