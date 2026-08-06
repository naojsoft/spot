.. _language:

+++++++++++++++++++++++
Language / Localization
+++++++++++++++++++++++

SPOT's user interface can be shown in languages other than English.  SPOT
reuses `Ginga <https://ginga.readthedocs.io>`_'s gettext-based localization
machinery and adds its own message catalog, so SPOT's strings are translated
alongside Ginga's.

Choosing the language
=====================

SPOT picks its language at startup from the ``language`` setting in the
``general`` configuration (``$HOME/.spot/general.cfg``):

* ``language = None`` (the default) honors the environment locale
  (``LANGUAGE`` / ``LC_ALL`` / ``LC_MESSAGES`` / ``LANG``).
* A language code such as ``language = 'ja'`` forces that language, falling
  back to English for any string that has not been translated.

The setting is applied once, before the UI is built.

Interactively, use the **Language** menu in the menubar to switch languages.
It lists only the languages SPOT actually has translations for (English is
always present).  Choosing a language records it in the ``language`` setting
and prompts you to restart SPOT for the change to take effect.

To "lock" the language for a deployment, set ``show_languages = False`` in
``general.cfg``: this hides the Language menu while still honoring the
``language`` setting.

Adding or updating a translation
================================

Translations live under ``spot/locale/`` in the source tree, one gettext
*domain* (``spot``) with a per-language catalog::

    spot/locale/<lang>/LC_MESSAGES/spot.po     # translated UI strings (tracked)
    spot/locale/<lang>/docs/plugins/*.rst      # translated plugin help (tracked)

Only the ``.po`` sources and the help ``.rst`` files are tracked in version
control; the compiled ``.mo`` catalogs and the ``.pot`` template are build
artifacts and are generated on demand.

These steps require `Babel <https://babel.pocoo.org>`_ (a development
dependency); run them from the top of the SPOT source tree.

1. Regenerate the message template.  SPOT's extractor collects both the
   strings marked with ``_tr()`` / ``N_()`` and the ``build_info()`` widget
   captions::

       python -m spot.locale._extract

   This (re)writes ``spot/locale/spot.pot``.

2. Create a catalog for a new language (e.g. Japanese)::

       pybabel init -D spot -i spot/locale/spot.pot -d spot/locale -l ja

   or, for an existing language, merge in any new/changed messages::

       pybabel update -D spot -i spot/locale/spot.pot -d spot/locale

3. Edit ``spot/locale/<lang>/LC_MESSAGES/spot.po`` and fill in the ``msgstr``
   entries with the translations.

4. Compile the catalogs to binary ``.mo`` files::

       pybabel compile -D spot -d spot/locale

   .. note:: This step is also performed automatically at build time (see
             ``setup.py``), so a wheel/sdist ships up-to-date ``.mo`` files
             without committing them.

Translating plugin help
========================

Each plugin's help text (shown by the plugin's "Help" button) is too large
for the message catalog, so it is translated as a whole document.  Create a
reStructuredText file named after the plugin's **class name**::

    spot/locale/<lang>/docs/plugins/<PluginClassName>.rst

For example, a Japanese translation of the Targets plugin help goes in
``spot/locale/ja/docs/plugins/Targets.rst``.  When that language is active the
file is shown in place of the English class docstring; if no such file exists,
the English text is used.  Author the file "flat" (mirroring the English help
without the leading indentation of the source docstring).

Notes for developers
====================

* Mark new user-facing strings with ``_tr()`` (imported from ``spot.locale``);
  use ``N_()`` for strings defined at import/class time and translate them with
  ``_tr()`` where they are displayed.  ``build_info()`` caption titles are
  extracted and translated automatically -- do **not** wrap them.
* Do not translate strings that are used as internal keys.  Selection combo
  boxes key their logic on the item *index*, not its text, so their displayed
  labels are safe to translate.
* See Ginga's developer manual ("Internationalization") for the underlying
  machinery, which SPOT shares.
