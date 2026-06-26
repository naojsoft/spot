#
# config.py -- per-workspace configuration helpers for SPOT
#
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.txt for details.
#
"""
Helpers for per-workspace plugin configuration.

SPOT keeps all per-workspace configuration under ``~/.spot/workspaces``,
with one subdirectory per workspace::

    ~/.spot/workspaces/<wsname>/workspace.json     # CPanel-saved layout
    ~/.spot/workspaces/<wsname>/<PluginName>.cfg   # each plugin's settings

so that every workspace can carry its own configuration, and the set of
workspaces is simply the set of subdirectories there.  Files shared by all
workspaces (e.g. ``sites.yml``, ``skycams.yml``, the ``prm/`` and
``downloads/`` directories) continue to live directly under ``~/.spot``.
"""
import os

from ginga.util import paths
from ginga.misc import Settings


def get_workspaces_root():
    """Return the directory holding all per-workspace config directories
    (``~/.spot/workspaces``), creating it if necessary."""
    folder = os.path.join(paths.ginga_home, 'workspaces')
    os.makedirs(folder, exist_ok=True)
    return folder


def get_workspace_dir(wsname):
    """Return the per-workspace config directory
    (``~/.spot/workspaces/<wsname>``), creating it if necessary."""
    folder = os.path.join(get_workspaces_root(), wsname)
    os.makedirs(folder, exist_ok=True)
    return folder


def list_workspaces():
    """Return the sorted names of existing workspaces -- i.e. the
    subdirectories of ``~/.spot/workspaces``."""
    root = get_workspaces_root()
    try:
        return sorted(name for name in os.listdir(root)
                      if os.path.isdir(os.path.join(root, name)))
    except OSError:
        return []


def get_workspace_layout_path(wsname):
    """Return the path to a workspace's saved layout file
    (``~/.spot/workspaces/<wsname>/workspace.json``).

    Does not create the per-workspace directory (so it is safe to use for an
    existence check); callers that write should ``makedirs`` the parent.
    """
    return os.path.join(get_workspaces_root(), wsname, 'workspace.json')


def get_workspace_settings(wsname, name, logger=None):
    """Return a :class:`~ginga.misc.Settings.SettingGroup` backed by the
    per-workspace config file ``~/.spot/workspaces/<wsname>/<name>.cfg``.

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
