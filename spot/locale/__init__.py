#
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.md for details.
#
"""Localization support for SPOT.

SPOT reuses Ginga's shared gettext machinery (``ginga.locale.localize``)
rather than duplicating it.  Importing this package registers SPOT's own
message domain (``spot``) and its locale directory, so ``_tr()`` consults
SPOT's catalog in addition to Ginga's -- SPOT's catalog takes precedence for
a shared message id (app-catalog-wins).

SPOT modules should import the translation helpers from here::

    from spot.locale import _tr, N_

``_tr(msg)`` translates ``msg`` into the active language at call time; ``N_(msg)``
marks a string for extraction without translating it now (use it for strings
defined at import/class-definition time, then translate with ``_tr`` when the
string is actually displayed).

(We use ``_tr`` rather than the conventional ``_`` alias, since ``_`` is
commonly used as a throwaway variable name.)

The compiled catalogs live at ``spot/locale/<lang>/LC_MESSAGES/spot.mo`` (built
from the tracked ``spot.po`` sources); whole-document help translations live at
``spot/locale/<lang>/docs/<category>/<name>.rst``.  Until those catalogs exist,
gettext falls back to the (English) source strings, so this is safe to ship
before any translations are written.
"""
import os

from ginga.locale import localize
# re-export the shared helpers so SPOT modules import them from one place
from ginga.locale.localize import _tr, N_   # noqa: F401

# SPOT's locale directory (holds <lang>/LC_MESSAGES/spot.mo and <lang>/docs/)
localedir = os.path.abspath(os.path.dirname(__file__))

# Register SPOT's message domain with Ginga's registry.  register() is
# idempotent, so importing this package more than once is harmless.
localize.register('spot', localedir)


def get_plugin_doc(plugin):
    """Return ``(name, doc)`` for a plugin's help display.

    ``name`` is the plugin's class name (used both as the help title and as
    the key for a whole-document translation).  ``doc`` is the translated
    help document for the active language if one exists at
    ``spot/locale/<lang>/docs/plugins/<ClassName>.rst`` (in any registered
    locale directory), otherwise the plugin's English class docstring.

    Plugins render this with ``text_kind='rst'``, e.g.::

        def help(self):
            name, doc = get_plugin_doc(self)
            self.fv.help_text(name, doc, text_kind='rst', trim_pfx=4)
    """
    name = plugin.__class__.__name__
    doc = localize.get_localized_doc(name, category='plugins')
    if doc is None:
        doc = plugin.__doc__
    return name, doc


def get_available_languages():
    """Return the languages SPOT itself has a compiled catalog for, plus
    English (always available via the gettext fallback).

    Unlike ``ginga.locale.localize.get_available_languages`` -- which unions
    every registered domain and so would surface languages Ginga is
    translated into even when SPOT is not -- this is scoped to SPOT's own
    ``spot.mo`` catalogs, so the Language menu only offers languages SPOT can
    actually render.
    """
    langs = {'en'}
    try:
        for name in os.listdir(localedir):
            mo = os.path.join(localedir, name, 'LC_MESSAGES', 'spot.mo')
            if os.path.isfile(mo):
                langs.add(name)
    except OSError:
        pass
    return sorted(langs)


__all__ = ['_tr', 'N_', 'localedir', 'get_plugin_doc',
           'get_available_languages']
