# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.txt for details.
"""
The ``SPOTMenubar`` plugin provides a default menubar for SPOT.

**Plugin Type: Global**

``SPOTMenubar`` is a global plugin.  Only one instance can be opened.

"""
import os.path
from ginga.rv.plugins import Menubar
from ginga.gw import Widgets, GwHelp

import spot.icons
icondir = os.path.split(spot.icons.__file__)[0]
from spot import __version__

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

        item = wsmenu.add_name("Open Workspace")
        item.add_callback('activated', self.open_workspace_cb)
        item = wsmenu.add_name("Close Workspace")
        item.add_callback('activated', self.close_workspace_cb)

        # # create a Option pulldown menu, and add it to the menu bar
        # optionmenu = menubar.add_name("Option")

        # create a Plugins pulldown menu, and add it to the menu bar
        # plugmenu = menubar.add_name("Plugins")
        # self.w.menu_plug = plugmenu

        # create a Help pulldown menu, and add it to the menu bar
        helpmenu = menubar.add_name("Help")

        item = helpmenu.add_name("About")
        item.add_callback('activated', self.banner)

        # item = helpmenu.add_name("Documentation")
        # item.add_callback('activated', lambda *args: self.fv.help())

    def open_workspace_cb(self, w):
        self.fv.call_global_plugin_method('CPanel', 'open_workspace_cb',
                                          [w], {})

    def close_workspace_cb(self, w):
        ws = self.fv.get_current_workspace()
        if ws is not None:
            self.fv.workspace_closed_cb(ws)

    def banner(self, w):
        # load banner image
        banner_file = os.path.join(icondir, "spot.svg")
        img_native = GwHelp.get_image(banner_file, size=(400, 400))

        # create dialog for banner
        title = f"SPOT v{__version__}"
        top = Widgets.Dialog(title=title, parent=self.w.menubar,
                             buttons=[["Close", 0]], modal=False)

        def _close_banner(*args):
            self.fv.ds.remove_dialog(top)

        top.add_callback('activated', _close_banner)
        vbox = top.get_content_area()
        img_w = Widgets.Image(native_image=img_native)
        vbox.add_widget(img_w, stretch=1)

        self.fv.ds.show_dialog(top)

    def __str__(self):
        return 'spotmenubar'
