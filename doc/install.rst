.. _ch-install:

++++++++++++
Installation
++++++++++++

============
Dependencies
============

SPOT is written entirely in Python, and only uses supporting Python
packages.  There is nothing to compile (unless you need to compile one
of the supporting packages).

In recent Linux, Mac, and Windows versions, all of the packages are
available in binary (installable) form.  It should not be necessary
to compile anything, but as always, your mileage may vary.

REQUIRED
========

* python (v. 3.10 or higher)
* setuptools-scm
* numpy  (v. 1.14 or higher)
* astropy
* jplephem
* skyfield
* pandas
* python-dateutil
* pyyaml
* requests
* matplotlib
* pillow
* PyQt (v5 or v6)
* QtPy
* ginga
* python-magic
* astroquery

RECOMMENDED
===========

Certain plugins in SPOT (or features of those plugins) will not work
without the following packages:

* scipy

For use at Subaru Telescope you may need the following packages:

* naojutils (pip install git+https://github.com/naojsoft/naojutils)
* g2cam (pip install git+https://github.com/naojsoft/g2cam)
* oscript (pip install git+https://github.com/naojsoft/oscript)
* naojutils (pip install git+https://github.com/naojsoft/naojutils

==================
Basic Installation
==================

Via Conda
=========
For most users, we recommend installing the
`Miniconda distribution <https://docs.anaconda.com/free/miniconda/index.html>`_  (Anaconda works too).

#. Use `this file <http://github.com/naojsoft/spot/blob/main/spot_conda_environment.yml>`_ to create a conda environment named "spot" like so::
 
     conda env create -f spot_conda_environment.yml
 
#. Activate this environment::
 
     conda activate spot
 
and then use `this file <http://github.com/naojsoft/spot/blob/main/spot_pip_requirements.txt>`_ to install the remaining requirements via *pip*::
 
    pip install -r spot_pip_requirements.txt
 
Assuming everything installed without error, you are now ready to run
spot.


======================
Building documentation
======================

#. Install the following packages::

    $ pip install -e .[docs]

#. Build the documentation using `make`::

   $ cd doc
   $ make html
