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
from ginga.locale import localize

import spot.icons
icondir = os.path.split(spot.icons.__file__)[0]
from spot import __version__
from spot.locale import _tr, get_available_languages

__all__ = ['SPOTMenubar']


class SPOTMenubar(Menubar.Menubar):

    def add_menus(self):

        menubar = self.w.menubar
        # create a File pulldown menu, and add it to the menu bar
        filemenu = menubar.add_name(_tr("File"))

        filemenu.add_separator()

        item = filemenu.add_name(_tr("Quit"))
        item.add_callback('activated', self.fv.window_close)

        # create a Window pulldown menu, and add it to the menu bar
        wsmenu = menubar.add_name(_tr("Workspace"))

        item = wsmenu.add_name(_tr("Open Workspace"))
        item.add_callback('activated', self.open_workspace_cb)
        item = wsmenu.add_name(_tr("Close Workspace"))
        item.add_callback('activated', self.close_workspace_cb)

        # # create a Option pulldown menu, and add it to the menu bar
        # optionmenu = menubar.add_name("Option")

        # create a Plugins pulldown menu, and add it to the menu bar
        # plugmenu = menubar.add_name("Plugins")
        # self.w.menu_plug = plugmenu

        # create a Language pulldown menu (kept in English so it stays
        # findable regardless of the active language), marked with Ginga's
        # generic flag icon.  Only languages SPOT itself has a catalog for are
        # offered (English until more are added).  Suppress the whole menu by
        # setting "show_languages" to False in general.cfg to lock the UI
        # language; the "language" preference is honored regardless.
        gen_settings = self.fv.get_preferences().create_category('general')
        if gen_settings.get('show_languages', True):
            lang_icon = os.path.join(self.fv.iconpath, "language.svg")
            # icon_only where the backend can render it (qt/gtk3); the
            # "Language" text is passed so backends that don't render menu
            # icons (gtk4, pg) fall back to the label
            langmenu = menubar.add_name("Language", iconpath=lang_icon,
                                        icon_only=True)
            for code in get_available_languages():
                item = langmenu.add_name(localize.get_language_name(code))
                item.add_callback('activated',
                                  lambda *args, code=code:
                                  self.fv.set_language_pref(code))

        # create a Help pulldown menu, and add it to the menu bar
        helpmenu = menubar.add_name(_tr("Help"))

        item = helpmenu.add_name(_tr("About"))
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
        wd, ht = 627, 627    # 1/2 size
        banner_file = os.path.join(icondir, "spot_logo.png")
        img_native = GwHelp.get_image(banner_file, size=(wd, ht))

        # create dialog for banner
        title = f"SPOT v{__version__}"
        top = Widgets.Dialog(title=title, parent=self.w.menubar,
                             buttons=[[_tr("Close"), 0]], autoclose=True,
                             modal=True)
        #top.resize(wd, ht)

        def _close_banner(*args):
            #w.hide()
            self.fv.ds.remove_dialog(top)

        top.add_callback('activated', _close_banner)
        vbox = top.get_content_area()
        img_w = Widgets.Image(native_image=img_native)
        vbox.add_widget(img_w, stretch=1)

        self.fv.ds.show_dialog(top)

    def __str__(self):
        return 'spotmenubar'
