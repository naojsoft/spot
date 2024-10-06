# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.txt for details.
"""
The ``SPOTMenubar`` plugin provides a default menubar for SPOT.

**Plugin Type: Global**

``SPOTMenubar`` is a global plugin.  Only one instance can be opened.

"""
from ginga.rv.plugins import Menubar

__all__ = ['SPOTMenubar']


class SPOTMenubar(Menubar.Menubar):

    def add_menus(self):

        menubar = self.w.menubar
        # create a File pulldown menu, and add it to the menu bar
        filemenu = menubar.add_name("File")

        filemenu.add_separator()

        item = filemenu.add_name("Quit")
        item.add_callback('activated', self.fv.window_close)

        # create a Window pulldown menu, and add it to the menu bar
        wsmenu = menubar.add_name("Workspace")

        item = wsmenu.add_name("Add Workspace")
        item.add_callback('activated', self.add_workspace_cb)
        # item = wsmenu.add_name("Delete Workspace")
        # item.add_callback('activated', self.del_workspace_cb)

        # # create a Option pulldown menu, and add it to the menu bar
        # optionmenu = menubar.add_name("Option")

        # create a Plugins pulldown menu, and add it to the menu bar
        # plugmenu = menubar.add_name("Plugins")
        # self.w.menu_plug = plugmenu

        # !!TODO!!
        # # create a Help pulldown menu, and add it to the menu bar
        # helpmenu = menubar.add_name("Help")

        # item = helpmenu.add_name("About")
        # item.add_callback('activated',
        #                   lambda *args: self.fv.banner())

        # item = helpmenu.add_name("Documentation")
        # item.add_callback('activated', lambda *args: self.fv.help())

    def add_workspace_cb(self, w):
        self.fv.call_global_plugin_method('CPanel', 'new_workspace_cb',
                                          [w], {})

    def del_workspace_cb(self, w):
        ws = self.fv.get_current_workspace()
        if ws is not None:
            self.fv.workspace_closed_cb(ws)

    def __str__(self):
        return 'spotmenubar'
