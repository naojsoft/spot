"""
CPanel.py -- Control Panel for SPOT tools

Plugin Type: Global
===================

``Visibility`` is a local plugin, which means it is associated with a channel.
An instance can be opened for each channel.

Usage
=====
``Visibility`` is normally used in conjunction with the plugins ``Sites``,
``PolarSky`` and ``Targets``.  Typically, ``Sites`` is started first
on a channel and then ``PolarSky``, ``Targets`` and ``Visibility`` are also
started.

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
# stdlib

# ginga
from ginga.gw import Widgets, Plot
from ginga import GingaPlugin
from ginga.misc import Bunch


class CPanel(GingaPlugin.GlobalPlugin):

    def __init__(self, fv):
        super().__init__(fv)

        # get preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_CPanel')
        #self.settings.add_defaults(targets_update_interval=60.0)
        self.settings.load(onError='silent')

        self.ws_dct = dict()
        self.count = 1
        self.gui_up = False

    def build_gui(self, container):

        top = Widgets.VBox()
        top.set_border_width(4)

        captions = (("New Workspace", 'button'),
                    ("Select Workspace:", 'label', 'sel_ws', 'combobox')
                    )

        w, b = Widgets.build_info(captions)
        self.w = b
        b.new_workspace.add_callback('activated', self.new_workspace_cb)
        b.new_workspace.set_tooltip("Create a new workspace")
        top.add_widget(w, stretch=0)

        b.sel_ws.set_tooltip("Select a workspace")
        b.sel_ws.add_callback('activated', self.select_workspace_cb)

        self.w.stk = Widgets.StackWidget()
        top.add_widget(self.w.stk, stretch=0)

        top.add_widget(Widgets.Label(''), stretch=1)

        # btns = Widgets.HBox()
        # btns.set_border_width(4)
        # btns.set_spacing(3)

        # btn = Widgets.Button("Close")
        # btn.add_callback('activated', lambda w: self.close())
        # btns.add_widget(btn, stretch=0)
        # btn = Widgets.Button("Help")
        # #btn.add_callback('activated', lambda w: self.help())
        # btns.add_widget(btn, stretch=0)
        # btns.add_widget(Widgets.Label(''), stretch=1)

        # top.add_widget(btns, stretch=0)

        container.add_widget(top, stretch=1)
        self.gui_up = True

    def close(self):
        self.fv.stop_global_plugin(str(self))
        return True

    def start(self):
        pass

    def stop(self):
        self.gui_up = False

    def new_workspace_cb(self, w):
        wsname = "WS{}".format(self.count)
        self.count += 1
        ws = self.fv.add_workspace(wsname, 'mdi', inSpace='works',
                                   use_toolbar=False)
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

        vbox = Widgets.VBox()
        vbox.set_spacing(2)
        for name, plname, chname in [
                ("Site Selector", 'SiteSelector', chname_tgts),
                ("PolarSky", 'PolarSky', chname_tgts),
                ("Target List", 'Targets', chname_tgts),
                ("Visibility Plot", 'Visibility', chname_tgts),
                ("Sky Cams", 'SkyCam', chname_tgts),
                ("Telescope Position", 'TelescopePosition', chname_tgts),
                ("Finding Chart", 'FindImage', chname_find),
                ("Instrument FOV", "InsFov", chname_find)]:
            cb = Widgets.CheckBox(name)
            cb_dct[plname] = cb
            vbox.add_widget(cb, stretch=0)
            cb.add_callback('activated', self.activate_plugin_cb,
                            wsname, plname, chname)

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

    def __str__(self):
        return 'cpanel'
