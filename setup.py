#! /usr/bin/env python
#
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.md for details.
#
# Project metadata lives in pyproject.toml; this shim exists only to compile
# the gettext translation catalogs (.po -> .mo) at build time.
from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    """Compile the gettext translation catalogs (.po -> .mo) before building.

    The compiled .mo files are not stored in version control (only the .po
    sources are; see .gitignore); they are generated here so that they get
    picked up by package_data and shipped in the wheel/sdist.  Requires Babel,
    which is declared in ``[build-system] requires`` (see pyproject.toml) and
    configured in setup.cfg ([compile_catalog]).
    """
    def run(self):
        try:
            self.run_command('compile_catalog')
        except Exception as exc:
            # Don't hard-fail the build if catalogs can't be compiled;
            # translations simply fall back to English at runtime.
            self.warn("could not compile translation catalogs: %s" % (exc,))
        super().run()


setup(cmdclass={'build_py': build_py})
