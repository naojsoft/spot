"""
CPanel.py -- Control Panel for SPOT tools

Plugin Type: Global
===================

``CPanel`` is a global plugin. Only one instance can be opened.

Usage
=====
``CPanel`` is the control panel for activating other SPOT plugins.

Requirements
============
python packages
---------------
matplotlib

naojsoft packages
-----------------
- ginga
- qplan
"""
import os

import json

# ginga
from ginga.gw import Widgets, Plot
from ginga import GingaPlugin
from ginga.misc import Bunch
from ginga.util.paths import ginga_home


class CPanel(GingaPlugin.GlobalPlugin):
    """
    CPanel
    ======
    CPanel is the Control Panel for the SPOT application.

    Use CPanel to launch a new workspace, or to open SPOT planning plugins
    in a specific workspace.

    Creating a workspace
    --------------------
    Use the "New Workspace" button to create a new workspace.  If you want to
    give it a specific name, put a name in the entry box to the right of the
    button before pressing the button.  Workspace names must be unique.
    If you don't provide a name, the workspaces will be created with a generic
    name.

    Select the new workspace by selecting its tab in order to see and work
    with the plugins that will be opened there.

    Selecting a workspace to start a plugin
    ---------------------------------------
    Using the "Select Workspace" drop-down menu, choose a workspace in which
    you want to launch one of the SPOT planning plugins.  Then use the
    checkboxes below to start (check) or stop (uncheck) a plugin.

    You will almost always want to start the "SiteSelector" plugin, because it
    controls many of the aspects of the other plugins visible on the workspace.

    Hint: Minimizing plugins
    ------------------------
    Sometimes you want to start a plugin to use some of its features, but
    you may not be interested in looking at the plugin UI (good examples
    are the "SiteSelector", "PolarSky", and "SkyCam" plugins). In such cases
    you can start the plugin and then click on the UI minimization button
    in the plugin UI title bar to minimize the plugin and create space for
    other plugins.

    Saving the workspace layout
    ---------------------------
    By pressing the "Save <wsname> layout" button, you will save the current
    position and size of the plugins that you have opened in the given
    workspace.  Each workspace's layout can be saved separately under its
    unique name, under $HOME/.spot

    When you start up SPOT the next time and open a workspace with the same
    name, it will remember the positions and sizes of the windows when you
    reopen plugins.
    """
    def __init__(self, fv):
        super().__init__(fv)

        # get preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_CPanel')
        #self.settings.add_defaults(targets_update_interval=60.0)
        self.settings.load(onError='silent')

        t_ = prefs.create_category('general')
        t_.set(scrollbars='auto')

        self.ws_dct = dict()
        self.count = 1
        self.gui_up = False

    def build_gui(self, container):

        top = Widgets.VBox()
        top.set_border_width(4)

        captions = (("New Workspace", 'button', "wsname", 'entry'),
                    ("Select Workspace:", 'label', 'sel_ws', 'combobox')
                    )

        w, b = Widgets.build_info(captions)
        self.w = b
        b.wsname.set_tooltip("Name for the new workspace (optional)")
        b.new_workspace.add_callback('activated', self.new_workspace_cb)
        b.new_workspace.set_tooltip("Create a new workspace")
        top.add_widget(w, stretch=0)

        b.sel_ws.set_tooltip("Select a workspace")
        b.sel_ws.add_callback('activated', self.select_workspace_cb)

        self.w.stk = Widgets.StackWidget()
        top.add_widget(self.w.stk, stretch=0)

        top.add_widget(Widgets.Label(''), stretch=1)

        btns = Widgets.HBox()
        btns.set_border_width(4)
        btns.set_spacing(3)

        #btn = Widgets.Button("Close")
        #btn.add_callback('activated', lambda w: self.close())
        #btns.add_widget(btn, stretch=0)
        btn = Widgets.Button("Help")
        btn.add_callback('activated', lambda w: self.help())
        btns.add_widget(btn, stretch=0)
        btns.add_widget(Widgets.Label(''), stretch=1)

        top.add_widget(btns, stretch=0)

        container.add_widget(top, stretch=1)
        self.gui_up = True

    def close(self):
        self.fv.stop_global_plugin(str(self))
        return True

    def help(self):
        name = str(self).capitalize()
        self.fv.help_text(name, self.__doc__, trim_pfx=4)

    def start(self):
        pass

    def stop(self):
        self.gui_up = False

    def new_workspace_cb(self, w):
        wsname = self.w.wsname.get_text().strip()
        if len(wsname) == 0:
            wsname = "WS{}".format(self.count)
            self.count += 1
        if self.fv.ds.has_ws(wsname):
            self.fv.show_error(f"'{wsname}' already exists; pick a new name")
            return
        ws = self.fv.add_workspace(wsname, 'mdi', inSpace='channels',
                                   use_toolbar=False)

        path = os.path.join(ginga_home, wsname + '.json')
        if os.path.exists(path):
            # if a saved configuration for this workspace exists, load it
            # so that windows will be created in the appropriate places
            with open(path, 'r') as in_f:
                try:
                    cfg_d = json.loads(in_f.read())
                    ws.child_catalog = cfg_d['tabs']
                except Exception as e:
                    self.logger.error("Error reading workspace '{path}': {e}",
                                      exc_info=True)

        cb_dct = dict()

        # create targets channel
        chname_tgts = f"{wsname}_TGTS"
        ch_tgts = self.fv.add_channel(chname_tgts, workspace=wsname,
                                      num_images=1)
        ch_tgts.viewer.set_enter_focus(False)
        ch_tgts.opmon.add_callback('activate-plugin', self.activate_cb, cb_dct)
        ch_tgts.opmon.add_callback('deactivate-plugin', self.deactivate_cb, cb_dct)

        # create finder channel
        chname_find = f"{wsname}_FIND"
        ch_find = self.fv.add_channel(chname_find, workspace=wsname,
                                      num_images=1)
        ch_find.viewer.set_enter_focus(False)
        ch_find.opmon.add_callback('activate-plugin', self.activate_cb, cb_dct)
        ch_find.opmon.add_callback('deactivate-plugin', self.deactivate_cb, cb_dct)
        ch_find.viewer.show_pan_mark(True, color='red')

        vbox = Widgets.VBox()
        vbox.set_spacing(2)
        for name, plname, chname in [
                ("Site Selector", 'SiteSelector', chname_tgts),
                ("PolarSky", 'PolarSky', chname_tgts),
                ("Target List", 'Targets', chname_tgts),
                ("Visibility Plot", 'Visibility', chname_tgts),
                ("Sky Cams", 'SkyCam', chname_tgts),
                ("Telescope Position", 'TelescopePosition', chname_tgts),
                #("Rotation Calculator", 'RotCalc', chname_tgts),
                ("Finding Chart", 'FindImage', chname_find),
                ("Instrument FOV", "InsFov", chname_find),
                ("HSC Planner", "HSCPlanner", chname_find)]:
            cb = Widgets.CheckBox(name)
            cb_dct[plname] = cb
            vbox.add_widget(cb, stretch=0)
            cb.add_callback('activated', self.activate_plugin_cb,
                            wsname, plname, chname)

        btn = Widgets.Button(f"Save {wsname} layout")
        btn.add_callback('activated', self.save_ws_layout_cb, wsname)
        btn.set_tooltip("Save the size and position of workspace windows")
        vbox.add_widget(btn, stretch=0)

        self.w.stk.add_widget(vbox)
        self.ws_dct[wsname] = Bunch.Bunch(ws=ws, workspace=wsname,
                                          child=vbox, cb_dct=cb_dct)

        self.w.sel_ws.append_text(wsname)
        self.w.sel_ws.set_text(wsname)
        index = self.w.stk.index_of(vbox)
        self.w.stk.set_index(index)

    def select_workspace_cb(self, w, idx):
        wsname = w.get_text()
        info = self.ws_dct[wsname]
        index = self.w.stk.index_of(info.child)
        self.w.stk.set_index(index)

    def activate_plugin_cb(self, w, tf, wsname, plname, chname):
        info = self.ws_dct[wsname]
        channel = self.fv.get_channel(chname)
        opmon = channel.opmon
        if tf:
            self.logger.info(f"activate {plname} in workspace {wsname}")
            # start plugin
            if not opmon.is_active(plname):
                opmon.start_plugin_future(chname, plname, None,
                                          wsname=info.workspace)
        else:
            self.logger.info(f"deactivate {plname} in workspace {wsname}")
            if opmon.is_active(plname):
                opmon.deactivate(plname)

    def activate_cb(self, pl_mgr, bnch, cb_dct):
        p_info = bnch['pInfo']
        if p_info.name in cb_dct:
            cb_dct[p_info.name].set_state(True)

    def deactivate_cb(self, pl_mgr, bnch, cb_dct):
        p_info = bnch['pInfo']
        if p_info.name in cb_dct:
            cb_dct[p_info.name].set_state(False)

    def save_ws_layout_cb(self, w, wsname):
        ws = self.fv.ds.get_ws(wsname)
        cfg_d = ws.get_configuration()
        path = os.path.join(ginga_home, wsname + '.json')
        with open(path, 'w') as out_f:
            out_f.write(json.dumps(cfg_d, indent=4))

    def __str__(self):
        return 'cpanel'
