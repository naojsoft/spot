#
# config.py -- per-workspace configuration helpers for SPOT
#
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.txt for details.
#
"""
Helpers for per-workspace plugin configuration.

SPOT lays out configuration under the home directory (``~/.spot``) with one
subdirectory per workspace::

    ~/.spot/<wsname>/workspace.json     # CPanel-saved window layout
    ~/.spot/<wsname>/<PluginName>.cfg   # each plugin's settings

so that every workspace can carry its own configuration.
"""
import os

from ginga.util import paths
from ginga.misc import Settings


def get_workspace_dir(wsname):
    """Return the per-workspace config directory (``~/.spot/<wsname>``),
    creating it if necessary."""
    folder = os.path.join(paths.ginga_home, wsname)
    os.makedirs(folder, exist_ok=True)
    return folder


def get_workspace_settings(wsname, name, logger=None):
    """Return a :class:`~ginga.misc.Settings.SettingGroup` backed by the
    per-workspace config file ``~/.spot/<wsname>/<name>.cfg``.

    Parameters
    ----------
    wsname : str
        The workspace name.
    name : str
        The category/plugin name; becomes ``<name>.cfg``.
    logger : logging-compatible object, optional
        Logger for the settings group.
    """
    folder = get_workspace_dir(wsname)
    prefs = Settings.Preferences(basefolder=folder, logger=logger)
    return prefs.create_category(name)


def save_settings(settings, fv=None):
    """Save a plugin's settings to its ``.cfg`` file.

    If ``fv`` (the Ginga shell) provides a ``persist_config`` hook, also
    flush it to persistent storage -- in-situ (Pyodide) the home directory
    is backed by IndexedDB, which only persists on an explicit sync.  On
    other backends this is a no-op beyond the file write.
    """
    settings.save()
    if fv is not None:
        persist = getattr(fv, 'persist_config', None)
        if persist is not None:
            persist()
