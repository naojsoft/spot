.. SPOT documentation master file

++++++++++++++++++++++++++++++++++++++++
SPOT: Site Planning and Observation Tool
++++++++++++++++++++++++++++++++++++++++

.. toctree::
   :maxdepth: 2

==========
About SPOT
==========

SPOT is a tool for planning and conducting observations at a site.


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


