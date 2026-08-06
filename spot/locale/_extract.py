#
# _extract.py -- regenerate the gettext message template (spot.pot)
#
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.md for details.
#
"""Regenerate ``spot/locale/spot.pot``, SPOT's gettext message template.

SPOT reuses Ginga's two-pass message extractor
(:func:`ginga.locale._extract.build_catalog`), which collects both the
explicit ``_tr()`` / ``N_()`` calls and the ``build_info()`` caption titles
(the latter are plain strings inside caption tuples that a normal keyword
extractor cannot see).

Run it from the top of the SPOT source tree so that file locations are
recorded relative to it::

    python -m spot.locale._extract

Then create/update the per-language catalogs from the template, e.g.::

    pybabel init   -D spot -i spot/locale/spot.pot \\
        -d spot/locale -l ja
    pybabel update -D spot -i spot/locale/spot.pot -d spot/locale

Requires Babel (a build/development dependency, not a runtime one).  The
``.pot`` itself is a regenerable artifact and is not tracked (see
.gitignore); only the ``.po`` sources are committed.
"""
import sys


def main(argv=None):
    from babel.messages.pofile import write_po
    from ginga.locale._extract import build_catalog

    argv = list(sys.argv[1:] if argv is None else argv)
    outfile = 'spot/locale/spot.pot'
    if '-o' in argv:
        i = argv.index('-o')
        outfile = argv[i + 1]
        del argv[i:i + 2]
    srcdir = argv[0] if argv else 'spot'

    catalog = build_catalog(srcdir)
    # build_catalog hardcodes the Ginga project name in the header; correct
    # it to SPOT (this is only .pot header metadata)
    catalog.project = 'spot'
    with open(outfile, 'wb') as f:
        write_po(f, catalog, width=76, sort_output=True)
    print("wrote %d messages to %s" % (len(catalog), outfile))
    return 0


if __name__ == '__main__':
    sys.exit(main())
