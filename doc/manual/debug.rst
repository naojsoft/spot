+++++
Debug
+++++

Contains tools for debugging. Includes four options, Command Line, 
LoaderConfig, Logger info, and PluginConfig.

============
Command Line
============
The command plugin provides a command line interface to the reference 
viewer.

.. note:: The command line is for use *within* the plugin UI.
        If you are looking for a *remote* command line interface,
        please see the ``RC`` plugin.

**Plugin Type: Global**

``Command`` is a global plugin.  Only one instance can be opened.

**Usage**
        
Get a list of commands and parameters::

        g> help

Execute a shell command::

        g> !cmd arg arg ...

**Notes**

An especially powerful tool is to use the ``reload_local`` and
``reload_global`` commands to reload a plugin when you are developing
that plugin.  This avoids having to restart the reference viewer and
laboriously reload data, etc.  Simply close the plugin, execute the
appropriate "reload" command (see the help!) and then start the plugin
again.

.. note:: If you have modifed modules *other* than the plugin itself,
        these will not be reloaded by these commands.

============
LoaderConfig
============
The ``LoaderConfig`` plugin allows you to configure the file openers that
can be used to load various content into Ginga.

Registered file openers are associated with file MIME types, and there can
be several openers for a single MIME type.  A priority associated
with a MIME type/opener pairing determines which opener will be used
for each type--the lowest priority value will determine which opener will
be used.  If there are more than one opener with the same low priority
then the user will be prompted for which opener to use, when opening a
file in Ginga.  This plugin can be used to set the opener preferences
and save it to the user's $HOME/.ginga configuration area.

**Plugin Type: Global**

``LoaderConfig`` is a global plugin.  Only one instance can be opened.

**Usage**

After starting the plugin, the display will show all the registered MIME
types and the openers registered for those types, with an associated
priority for each MIME type/opener pairing.

Select one or more lines and type a priority for them in the box labeled
"Priority:"; press "Set" (or ENTER) to set the priority of those items.

.. note:: The lower the number, the higher the priority. Negative numbers
        are fine and the default priority for a loader is usually 0.
        So, for example, if there are two loaders available for a MIME
        type and one priority is set to -1 and the other to 0, the one
        with -1 will be used without asking the user to choose.


Click "Save" to save the priorities to $HOME/.ginga/loaders.json so that
they will be reloaded and used on subsequent restarts of the program.

===========
Logger Info
===========
``Logger Info`` will show the logging output of the reference viewer.

**Plugin Type: Global**

``Log`` is a global plugin.  Only one instance can be opened.

**Usage**

The ``Log`` plugin builds a UI that includes a large scrolling text widget
showing the active output of the logger.  The latest output shows up at
the bottom.  This can be useful for troubleshooting problems.

There are four controls:

* The combo box on the lower left allows you to choose the level of
  logging desired.  The four levels, in order of verbosity are: "debug",
  "info", "warn", and "error".
* The box with the number on the lower right allows you to set how many
  lines of input to keep in the display buffer (e.g., keep only the last
  1000 lines).
* The checkbox "Auto scroll", if checked, will cause the large text
  widget to scroll to the end as new log messages are added.  Uncheck
  this if you want to peruse the older messages and study them.
* The "Clear" button is used to clear the text widget, so that only new
  logging shows up.

============
PluginConfig
============
The ``PluginConfig`` plugin allows you to configure the plugins that
are visible in your menus.

**Plugin Type: Global**

``PluginConfig`` is a global plugin.  Only one instance can be opened.

**Usage**

PluginConfig is used to configure plugins to be used in Ginga.  The items
that can be configured for each plugin include:

* whether it is enabled (and therefore whether it shows up in the menus)
* the category of the plugin (used to construct the menu hierarchy)
* the workspace in which the plugin will open
* if a global plugin, whether it starts automatically when the reference
  viewer starts
* Whether the plugin name should be hidden (not show up in plugin
  activation menus)
 
When PluginConfig starts, it will show a table of plugins.  To edit the
above attributes for plugins, click "Edit", which will bring up a dialog
for editing the table.

For each plugin you want to configure, click on an entry in the main table
and then adjust the settings in the dialog, then click "Set" in the dialog
to reflect the changes back into the table.  If you don't click "Set",
nothing is changed in the table.  When you are done editing configurations,
click "Close" on the dialog to close the editing dialog.

.. note:: It is not recommended to change the workspace for a plugin
        unless you choose a compatibly-sized workspace to the original,
        as the plugin may not display correctly.  If in doubt, leave
        the workspace unchanged.  Also, disabling plugins in the
        "Systems" category may cause some expected features to stop
        working.


.. important:: To make the changes persist across Ginga restarts, click
        "Save" to save the settings (to `$HOME/.ginga/plugins.json`).
        Restart Ginga to see changes to the menus (via "category"
        changes).  **Remove this file manually if you want to reset
        the plugin configurations to the defaults**.
