++++++
System
++++++

==================
Spot Control Panel
==================
CPanel is the Control Panel for the SPOT application.

Use CPanel to launch a new workspace, or to open SPOT planning plugins
in a specific workspace.

**Creating a workspace**
        
Use the "New Workspace" button to create a new workspace.  If you want to
give it a specific name, put a name in the entry box to the right of the
button before pressing the button.  Workspace names must be unique.
If you don't provide a name, the workspaces will be created with a generic
name.

Select the new workspace by selecting its tab in order to see and work
with the plugins that will be opened there.

**Selecting a workspace to start a plugin**
        
Using the "Select Workspace" drop-down menu, choose a workspace in which
you want to launch one of the SPOT planning plugins.  Then use the
checkboxes below to start (check) or stop (uncheck) a plugin.

You will almost always want to start the "SiteSelector" plugin, because it
controls many of the aspects of the other plugins visible on the workspace.

**Hint: Minimizing plugins**

Sometimes you want to start a plugin to use some of its features, but
you may not be interested in looking at the plugin UI (good examples
are the "SiteSelector", "PolarSky", and "SkyCam" plugins). In such cases
you can start the plugin and then click on the UI minimization button
in the plugin UI title bar to minimize the plugin and create space for
other plugins.

**Saving the workspace layout**

By pressing the "Save <wsname> layout" button, you will save the current
position and size of the plugins that you have opened in the given
workspace.  Each workspace's layout can be saved separately under its
unique name, under $HOME/.spot

When you start up SPOT the next time and open a workspace with the same
name, it will remember the positions and sizes of the windows when you
reopen plugins.
