"""
``Targets`` -- manage a list of astronomical targets

Plugin Type: Local
==================

``Targets`` is a local plugin, which means it is associated with a channel.
An instance can be opened for each channel.

Usage
=====
``Targets`` is normally used in conjunction with the plugins ``PolarSky``,
``SkyCam`` and ``Visibility``.  Typically, ``PolarSky`` is started first
on a channel and then ``SkyCam``, ``Targets`` and ``Visibility`` are also
started, although ``SkyCam`` and ``Visibility`` are not required to be
active to use it.

Requirements
============

naojsoft packages
-----------------
- ginga
- oscript
"""
# stdlib
import os
from collections import OrderedDict

# 3rd party
import numpy as np
import pandas as pd
from dateutil.parser import parse as parse_date
from datetime import UTC

# ginga
from ginga.gw import Widgets
from ginga import GingaPlugin, colors
from ginga.util.paths import ginga_home, home as user_home
from ginga.util import wcs
from ginga.util.syncops import Shelf
from ginga.misc import Bunch, Callback

# oscript (optional, for loading OPE files)
try:
    from oscript.parse import ope
    have_oscript = True
except ImportError:
    have_oscript = False

# local
from spot.util import calcpos
from spot.util import target as spot_target

# where our icons are stored
from spot import __file__
icondir = os.path.join(os.path.dirname(__file__), 'icons')


class Targets(GingaPlugin.LocalPlugin):
    """
    +++++++++++
    Target List
    +++++++++++

    The Targets plugin is normally used in conjunction with the
    plugins ``PolarSky`` and ``Visibility`` plugins to show information about
    celestial objects that could be observed.  It allows you to load one or
    more files of targets and then plot them on the "<wsname>_TGTS" window,
    or show their visibility in the ``Visibility`` plugin UI.

    Loading targets from a CSV file
    ===============================
    Targets can be loaded from a CSV file that contains a column header
    containing the column titles "Name", "RA", "DEC", and "Equinox" (they
    do not need to be in that order).  Other columns may be present but will
    be ignored.  In this format, RA and DEC can be specified as decimal values
    (in which case they are interpreted as degrees) or sexigesimal notation
    (HH:MM:SS.SSS for RA, DD:MM:SS.SS for DEC).  Equinox can be specified
    as e.g. J2000 or 2000.0.

    .. note:: SPOT can also read targets from CSV files in "SOSS notation".
              See the section below on loading targets from an OPE file.

    If you want to set a specific color for the targets to be plotted, click
    the "Color" button to manually select a color before proceeding to open
    a file, otherwise the targets will be colored according to the option
    (described further below) called "Rotate target colors".

    Press the "File" button and navigate to, and select, a CSV file with the
    above format.  Or, type the path of the file in the box next to the "File"
    button and press "Set" (the latter method can also be used to quickly
    reload a file that you have edited).

    The targets should populate the table.

    Loading targets from an OPE file
    ================================
    An OPE file is a special format of file used by Subaru Telescope.
    Targets in this kind of file are specified in "SOSS notation"
    (HHMMSS.SSS for RA, +|-DDMMSS.SS for DEC, NNNN.0 for Equinox).

    Follow the instructions above for loading targets from a CSV file, but
    choose an OPE file instead.

    .. note::  In order to load this format you need to have installed the
               optional "oscript" package:
               (pip install git+https://github.com/naojsoft/oscript).

    Table information
    =================
    The target table summarizes information about targets. There are columns
    for static information like target name, RA, DEC, as well as dynamically
    updating information for azimuth, altitude, a color-coded rise/set icon,
    hour angle, airmass, atmospheric dispersion, parallactic angle and moon
    separation.

    Operation
    =========
    To "tag" targets, select one or more targets on the list and press "Tag".
    A checkmark will appear on the left side under the "Tagged" column to show
    which targets have been tagged. To untag a target, select one or more
    tagged targets on the list and press "Untag".

    On the `<wsname>_TGTS` window, targets will be plotted in the position
    of the time set in the SiteSelector plugin.  The color of the target will
    be a magenta-like color if the target is tagged. If a target is selected
    it will appear in blue, and the name will have a white background with a
    red border on the `<wsname>_TGTS` window.  Otherwise the target will be
    colored according to the color that was manually or automatically selected
    when the file containing the targets was loaded.

    The "Select All" button will select all of the targets in the table.

    Selecting targets and pressing "Delete" will remove selected targets
    from the list.  If only a category row is selected (but no targets),
    pressing this button will delete all targets in the category.

    The drop down menu next to "Plot:" changes which targets are plotted on
    the `<wsname>_TGTS` window. Selecting "All" will show all of the targets,
    selecting "Uncollapsed" will show any targets that are not collapsed
    (hidden) in the table as well as tagged and selected targets, selecting
    "Tagged+Selected" will show all of the targets which have been
    tagged or are selected, and selecting "Selected" will show only the
    targets which are selected.

    Settings Menu
    =============
    Clicking the "Settings" button will invoke a pop-up menu to enable certain
    settings.

    * If you check "Merge Targets" then all targets loaded *after that*
      will be organized under a single heading of "Targets", instead of being
      grouped by file name.
    * "List Unreferenced Targets" is a setting that just affects OPE files.
      Normally, the Targets plugin will ignore targets that are not referenced
      in the commands. Checking this setting will show all targets regardless
      of whether they are referenced or not.  This can be used to show targets
      in PRM include files.
    * Checking the option for "Plot solar system objects" will plot the Sun,
      Earth's Moon, the planets, and pluto on the `<wsname>_TGTS` window.

    * The "Rotate target colors" option will mean that each file loaded will
      use a different automatically selected color for the targets (this will
      only take effect if "Merge targets" is turned off).
    * "Enable DateTime setting" is a option to enable the setting of a fixed
      date/time if the CSV file includes a "DateTime" column.  When enabled,
      selecting a single target in the table will set the date/time in the
      SiteSelector plugin to that date and time.  The format of this column
      should be: YYYY-MM-DD HH:MM:SS <TZ>
      If the timezone string is omitted, UTC is assumed.
    """
    def __init__(self, fv, fitsimage):
        super().__init__(fv, fitsimage)

        if not self.chname.endswith('_TGTS'):
            return

        # get preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_Targets')
        self.settings.add_defaults(targets_update_interval=60.0,
                                   color_selected='royalblue',
                                   color_tagged='mediumorchid1',
                                   color_normal='seagreen2',
                                   plot_ss_objects=True,
                                   load_directory=user_home,
                                   enable_datetime_setting=False,
                                   rotate_target_colors=True,
                                   merge_targets=False,
                                   load_selection_order='csv_first')
        self.settings.load(onError='silent')

        # these are set via callbacks from the SiteSelector plugin
        self.site = None
        self.dt_utc = None
        self.cur_tz = None
        self._last_tgt_update_dt = None
        self.home = self.settings.get('load_directory', user_home)

        self.cb = Callback.Callbacks()
        for name in ['targets-changed', 'tagged-changed', 'selection-changed',
                     'uncollapsed-changed']:
            self.cb.enable_callback(name)

        self._tgt_color = self.settings['color_normal']
        self.tgt_colors = [self._tgt_color, 'slateblue2',
                           'coral', 'olivedrab', 'chocolate', 'darkorange2',
                           'khaki4', 'deeppink2', 'purple']
        self._tgt_color_idx = 0
        self.base_circ = None
        self.target_dict = {}
        self.full_tgt_list = []
        self.plot_which = 'uncollapsed'
        self.plot_ss_objects = self.settings.get('plot_ss_objects', True)
        self.uncollapsed = set([])
        self.tagged = set([])
        self.selected = set([])
        self.show_unref_tgts = False
        self.tgt_df = None
        self.ss_df = None
        self.fov_dct = Bunch.Bunch(dict(Sun=6.5, Moon=6.5), caseless=True)
        self._mbody = None
        self.table_shelf = Shelf()
        self.table_stocker = self.table_shelf.get_stocker()

        self.columns = [('Tagged', 'tagged'),
                        ('Name', 'name'),
                        ('Az', 'az_deg'),
                        ('Alt', 'alt_deg'),
                        ('Dir', 'icon'),
                        ('HA', 'ha'),
                        ('AM', 'airmass'),
                        # ('Slew', 'slew'),
                        ('AD', 'ad'),
                        ('Pang', 'parang_deg'),
                        ('Moon Sep', 'moon_sep'),
                        ('RA', 'ra'),
                        ('DEC', 'dec'),
                        ('Eq', 'equinox'),
                        ('Comment', 'comment'),
                        ]

        # the solar system objects
        ss = [(calcpos.Moon, 'navajowhite2'),
              (calcpos.Sun, 'darkgoldenrod1'),
              (calcpos.Mercury, 'gray'), (calcpos.Venus, 'gray80'),
              (calcpos.Mars, 'mistyrose'), (calcpos.Jupiter, 'gray90'),
              (calcpos.Saturn, 'gray70'), (calcpos.Uranus, 'gray'),
              (calcpos.Neptune, 'gray'), (calcpos.Pluto, 'gray'),
              ]
        self.ss = []
        for tup in ss:
            tgt, color = tup
            self.ss.append(tgt)
            tgt.color = color

        self.diricon = dict()
        for name, filename in [('invisible', 'no_go.svg'),
                               ('up_ng', 'red_arr_up.svg'),
                               ('up_low', 'orange_arr_up.svg'),
                               ('up_ok', 'green_arr_up.svg'),
                               ('up_good', 'blue_arr_up.svg'),
                               ('up_high', 'purple_arr_up.svg'),
                               ('down_high', 'purple_arr_dn.svg'),
                               ('down_good', 'blue_arr_dn.svg'),
                               ('down_ok', 'green_arr_dn.svg'),
                               ('down_low', 'orange_arr_dn.svg'),
                               ('down_ng', 'red_arr_dn.svg')]:
            self.diricon[name] = self.fv.get_icon(icondir, filename)

        self.viewer = self.fitsimage
        self.dc = fv.get_draw_classes()
        canvas = self.dc.DrawingCanvas()
        canvas.enable_draw(False)
        canvas.register_for_cursor_drawing(self.fitsimage)
        canvas.set_surface(self.fitsimage)
        canvas.set_draw_mode('pick')
        self.canvas = canvas

        self.gui_up = False

    def build_gui(self, container):

        if not self.chname.endswith('_TGTS'):
            raise Exception(f"This plugin is not designed to run in channel {self.chname}")

        # initialize site and date/time/tz
        obj = self.channel.opmon.get_plugin('SiteSelector')
        self.site = obj.get_site()
        obj.cb.add_callback('site-changed', self.site_changed_cb)
        self.dt_utc, self.cur_tz = obj.get_datetime()
        obj.cb.add_callback('time-changed', self.time_changed_cb)

        top = Widgets.VBox()
        top.set_border_width(4)

        captions = (('Load File', 'button', 'File Path', 'entryset',
                     'Color', 'button'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b

        b.load_file.set_text("File")
        self.w.fileselect = Widgets.FileDialog(parent=b.load_file,
                                               title="Select target files")
        self.w.fileselect.set_mode('files')
        self.w.fileselect.set_directory(self.home)
        add_order = [("CSV", ".csv"), ("OPE", ".ope"), ("EPH", ".eph")]
        if self.settings.get('load_selection_order', 'csv_first') == 'ope_first':
            add_order = [("OPE", ".ope"), ("CSV", ".csv"), ("EPH", ".eph")]
        for name, ext in add_order:
            if name == 'OPE' and not have_oscript:
                continue
            self.w.fileselect.add_ext_filter(name, ext)

        self.w.fileselect.add_callback('activated', self.load_file_cb)
        b.file_path.set_text(self.home)

        top.add_widget(w, stretch=0)
        b.load_file.add_callback('activated',
                                 lambda w: self.w.fileselect.show())
        b.load_file.set_tooltip("Select target file")
        b.file_path.add_callback('activated', self.file_setpath_cb)

        self.w.colorselect = Widgets.ColorDialog(parent=b.color,
                                                 title="Choose target color")
        self.w.colorselect.add_callback('activated', self.color_select_cb)
        hex_color = colors.lookup_color(self._tgt_color, format='hex')
        self.w.colorselect.set_color(hex_color)
        b.color.add_callback('activated', lambda w: self.w.colorselect.popup())
        b.color.set_tooltip("Set the color of the loaded targets")
        b.color.set_color(bg=hex_color, fg='black')

        plot_update_text = "Please select file for list display"

        self.w.toolbar1 = Widgets.Toolbar(orientation='horizontal')
        # TODO: figure out a better way to handle this!!!
        if self.fv.gpmon.has_plugin('Gen2Int'):
            menu = self.w.toolbar1.add_menu("Gen2", mtype='menu')
            btn = menu.add_name("Sync integgui2")
            obj = self.fv.gpmon.get_plugin('Gen2Int')
            btn.add_callback('activated', obj.sync_targets, self.channel)
            self.w.toolbar1.add_separator()

        hbox = Widgets.HBox()
        hbox.set_spacing(5)
        self.w.update_time = Widgets.Label(plot_update_text)
        hbox.add_widget(self.w.update_time, stretch=0)
        hbox.add_widget(Widgets.Label(''), stretch=1)
        hbox.add_widget(self.w.toolbar1, stretch=0)
        top.add_widget(hbox, stretch=0)

        self.w.tgt_tbl = Widgets.TreeView(auto_expand=False,
                                          selection='multiple',
                                          sortable=True,
                                          use_alt_row_color=True)
        self.w.tgt_tbl.setup_table(self.columns, 2, 'name')
        top.add_widget(self.w.tgt_tbl, stretch=1)

        self.w.tgt_tbl.set_optimal_column_widths()
        self.w.tgt_tbl.add_callback('selected', self.target_selection_cb)
        # self.w.tgt_tbl.add_callback('activated', self.target_single_cb)
        self.w.tgt_tbl.add_callback('collapsed', self.targets_collapse_cb)
        self.w.tgt_tbl.add_callback('expanded', self.targets_collapse_cb)

        self.w.toolbar2 = Widgets.Toolbar(orientation='horizontal')
        btn = self.w.toolbar2.add_action("Tag")
        btn.set_tooltip("Add highlighted items to tagged targets")
        btn.add_callback('activated', self.tag_cb)
        self.w.btn_tag = btn
        btn = self.w.toolbar2.add_action("Untag")
        btn.set_tooltip("Remove highlighted items from tagged targets")
        btn.add_callback('activated', self.untag_cb)
        self.w.btn_untag = btn
        btn = self.w.toolbar2.add_action("Select All")
        btn.set_tooltip("Select all targets")
        btn.add_callback('activated', self.select_all_cb)
        self.w.btn_select_all = btn
        btn = self.w.toolbar2.add_action("Delete")
        btn.set_tooltip("Delete selected target from targets")
        btn.add_callback('activated', self.delete_cb)
        self.w.btn_delete = btn
        btn = self.w.toolbar2.add_action("Collapse All")
        btn.set_tooltip("Collapse all loaded files")
        btn.add_callback('activated', self.collapse_all_cb)
        self.w.btn_collapse_all = btn

        self.w.toolbar2.add_spacer()
        #self.w.toolbar2.add_separator()

        self.w.toolbar2.add_widget(Widgets.Label('Plot:'))
        plot = Widgets.ComboBox()
        for option in ['Selected', 'Tagged+selected', 'Uncollapsed', 'All']:
            plot.append_text(option)
        plot.set_text(self.plot_which.capitalize())
        plot.add_callback('activated', self.configure_plot_cb)
        plot.set_tooltip("Choose what is plotted")
        self.w.toolbar2.add_widget(plot)

        self._update_selection_buttons()

        self.w.toolbar2.add_spacer()

        m = Widgets.Menu()
        self.w.menu_config = m
        action = m.add_name("Merge Targets", checkable=True)
        action.set_tooltip("Put all targets under one category called 'Targets'")
        action.set_state(self.settings.get('merge_targets', False))
        action.add_callback('activated', self.merge_targets_cb)
        self.w.merge_targets = action

        action = m.add_name("List unreferenced targets", checkable=True)
        action.set_tooltip("Show unreferenced targets (e.g. from .prm files")
        action.set_state(self.show_unref_tgts)
        action.add_callback('activated', self.list_prm_cb)
        self.w.list_prm_targets = action

        action = m.add_name("Plot solar system objects", checkable=True)
        action.set_tooltip("Plot sun, moon and planets")
        action.set_state(self.plot_ss_objects)
        action.add_callback('activated', self.plot_ss_cb)
        self.w.plot_ss_setting = action

        action = m.add_name("Rotate target colors", checkable=True)
        action.set_tooltip("Rotate target colors for each file loaded")
        action.set_state(self.settings.get('rotate_target_colors', True))
        action.add_callback('activated', self.rotate_target_colors_cb)
        self.w.rotate_target_colors = action

        action = m.add_name("Enable DateTime setting", checkable=True)
        action.set_tooltip("Allow DateTime column in target CSV to set fixed time")
        action.set_state(self.settings.get('enable_datetime_setting', False))
        action.add_callback('activated', self.enable_datetime_cb)
        self.w.enable_datetime_setting = action

        self.w.settings = self.w.toolbar2.add_menu("Settings", menu=m,
                                                   mtype='menu')
        self.w.settings.set_tooltip("Configure some settings for this plugin")

        top.add_widget(self.w.toolbar2, stretch=0)

        btns = Widgets.HBox()
        btns.set_border_width(4)
        btns.set_spacing(3)

        btn = Widgets.Button("Close")
        btn.add_callback('activated', lambda w: self.close())
        btns.add_widget(btn, stretch=0)
        btn = Widgets.Button("Help")
        btn.add_callback('activated', lambda w: self.help())
        btns.add_widget(btn, stretch=0)
        btns.add_widget(Widgets.Label(''), stretch=1)

        top.add_widget(btns, stretch=0)

        container.add_widget(top, stretch=1)
        self.gui_up = True

    def close(self):
        self.fv.stop_local_plugin(self.chname, str(self))
        return True

    def help(self):
        name = str(self).capitalize()
        self.fv.help_text(name, self.__doc__, trim_pfx=4)

    def start(self):
        skycam = self.channel.opmon.get_plugin('SkyCam')
        skycam.settings.get_setting('image_radius').add_callback(
            'set', self.change_radius_cb)

        # insert canvas, if not already
        p_canvas = self.viewer.get_canvas()
        if self.canvas not in p_canvas:
            # Add our canvas
            p_canvas.add(self.canvas)

        self.canvas.delete_all_objects()

        self.update_all()

        self.resume()

    def pause(self):
        self.canvas.ui_set_active(False)

    def resume(self):
        self.canvas.ui_set_active(True, viewer=self.viewer)
        self.canvas.set_draw_mode('pick')

    def stop(self):
        self.gui_up = False
        # remove the canvas from the image
        p_canvas = self.fitsimage.get_canvas()
        if self.canvas in p_canvas:
            p_canvas.delete_object(self.canvas)

    def redo(self):
        pass

    def clear_plot(self):
        self.canvas.delete_object_by_tag('ss')
        self.canvas.delete_object_by_tag('targets')

    def filter_targets(self, tgt_df):
        if self.plot_which == 'all':
            shown_tgt_lst = tgt_df
        elif self.plot_which == 'uncollapsed':
            tgts = self.uncollapsed.union(self.selected.union(self.tagged))
            mask = np.array([tgt in tgts
                             for tgt in self.full_tgt_list], dtype=bool)
            shown_tgt_lst = tgt_df[mask]
        elif self.plot_which == 'tagged+selected':
            tagged_and_selected = self.selected.union(self.tagged)
            mask = np.array([tgt in tagged_and_selected
                             for tgt in self.full_tgt_list], dtype=bool)
            shown_tgt_lst = tgt_df[mask]
        elif self.plot_which == 'selected':
            mask = np.array([tgt in self.selected
                             for tgt in self.full_tgt_list], dtype=bool)
            shown_tgt_lst = tgt_df[mask]

        return shown_tgt_lst

    def select_star_cb(self, obj, canvas, event, pt, action):
        info = obj.get_data()
        if info.get('tag', None) != 'targets':
            return
        idx = info.get('index')
        # TODO
        path = [info.get('category', None), info.get('name', None)]
        if None in path or not self.gui_up:
            return
        if action == 'select':
            self.w.tgt_tbl.clear_selection()
            self.w.tgt_tbl.select_path(path)
            self.w.tgt_tbl.scroll_to_path(path)
            # NOTE: Ginga TreeWidget doesn't call the callback for
            # selection changed if it is done programatically.  So
            # we need to manually call the callback here to get the
            # same effect
            sel_dct = self.w.tgt_tbl.get_selected()
            self.target_selection_cb(self.w.tgt_tbl, sel_dct)
        return True

    def select_targets(self, targets):
        self.w.tgt_tbl.clear_selection()
        for tgt in targets:
            path = [tgt.category, tgt.name]
            self.w.tgt_tbl.select_path(path)
            self.w.tgt_tbl.scroll_to_path(path)

        sel_dct = self.w.tgt_tbl.get_selected()
        self.target_selection_cb(self.w.tgt_tbl, sel_dct)

    def plot_targets(self, tgt_df, tag):
        """Plot targets.
        """
        start_time = self.get_datetime()
        self.canvas.delete_object_by_tag(tag)

        # filter the subset desired to be seen
        scale = self.get_scale()
        pt_radius = np.log(scale)
        cl_radius = pt_radius * 2
        radius_dct = dict(Sun=cl_radius * pt_radius * 2,
                          Moon=cl_radius * pt_radius * 2)
        if tag != 'ss':
            tgt_df = self.filter_targets(tgt_df)
            fill = False
        else:
            fill = True

        self.logger.info("plotting {} targets tag {}".format(len(tgt_df), tag))
        to_be_raised = []
        objs = []
        for idx, row in tgt_df.iterrows():
            category = row.get('category', None)
            name = row.get('name', None)
            tgt = self.target_dict.get((category, name), None)
            is_ref = row.get('is_ref', None)
            if tag == 'ss' or self.show_unref_tgts or is_ref:
                alpha = 1.0 if row['alt_deg'] > 0 else 0.0
                if tgt is None:
                    color = row['color']
                else:
                    color = self._get_target_color(tgt)
                selected = tgt in self.selected
                t, r = self.map_azalt(row['az_deg'], row['alt_deg'])
                x, y = self.p2r(r, t)
                point = self.dc.Point(x, y, radius=pt_radius, style='cross',
                                      color=color, fillcolor=color,
                                      linewidth=2, alpha=alpha,
                                      fill=True, fillalpha=alpha)
                radius = radius_dct.get(row['name'], cl_radius)
                circle = self.dc.Circle(x, y, radius, color=color,
                                        linewidth=1, alpha=alpha,
                                        fill=fill, fillcolor=color,
                                        fillalpha=alpha * 0.7)
                bg_alpha = alpha if selected else 0.0
                text = self.dc.Text(x, y, row['name'],
                                    color=color, alpha=alpha,
                                    fill=True, fillcolor=color,
                                    fillalpha=alpha, linewidth=0,
                                    font="Roboto condensed bold",
                                    fontscale=True,
                                    fontsize=None, fontsize_min=12,
                                    fontsize_max=16,
                                    bgcolor='floralwhite', bgalpha=bg_alpha,
                                    bordercolor='orangered1', borderlinewidth=2,
                                    borderalpha=bg_alpha)
                star = self.dc.CompoundObject(point, circle, text)
                star.opaque = True
                star.pickable = True
                star.set_data(tag=tag, index=idx, name=name,
                              category=category)
                star.add_callback('pick-up', self.select_star_cb, 'select')
                #star.add_callback('pick-hover', self.select_star_cb, 'info')
                objs.append(star)

                if selected:
                    to_be_raised.append(star)

                if tag == 'targets':
                    self.target_dict[(category, name)].set(plotted=star)

        o = self.dc.CompoundObject(*objs)
        for obj in to_be_raised:
            o.raise_object(obj)
        self.canvas.add(o, tag=tag, redraw=False)

        self.canvas.update_canvas(whence=3)

    def update_targets(self, tgt_df, tag):
        """Update targets already plotted with new positions.
        """
        self.canvas.delete_object_by_tag(tag)
        if not self.canvas.has_tag(tag):
            self.plot_targets(tgt_df, tag)

    def _create_multicoord_body(self):
        if len(self.full_tgt_list) == 0:
            self._mbody = None
            return
        names = np.asarray([tgt.name for tgt in self.full_tgt_list])
        arr = np.asarray([(tgt.ra, tgt.dec, tgt.equinox)
                          for tgt in self.full_tgt_list]).T
        self._mbody = calcpos.Body(names, arr[0], arr[1], arr[2])

    def update_all(self, targets_changed=False):
        # Run target calculations and table building in a separate thread
        # (seems to keep GUI responsive)
        self.fv.nongui_do(self._update_calc, targets_changed=targets_changed)

    def _update_calc(self, targets_changed=False):
        self.fv.assert_nongui_thread()
        start_time = self.get_datetime()
        self._last_tgt_update_dt = start_time
        self.logger.info("update time: {}".format(start_time.strftime(
                         "%Y-%m-%d %H:%M:%S [%z]")))
        if len(self.target_dict) > 0:
            # update non-sidereal targets
            non_sd = [tgt for tgt in self.full_tgt_list
                      if tgt.get('nonsidereal', False)]
            non_sd_changed = spot_target.update_nonsidereal_targets(non_sd,
                                                                    start_time)
            targets_changed = targets_changed or non_sd_changed

            # create multi-coordinate body if not yet created
            if targets_changed or self._mbody is None:
                self._create_multicoord_body()

            # get full information about all targets at `start_time`
            cres = self._mbody.calc(self.site.observer, start_time)
            dct_all = cres.get_dict()

            # add additional columns
            _addl_str_cols = np.asarray([(tgt.get('color', self._tgt_color),
                                          tgt.category, tgt.get('comment', ''))
                                         for tgt in self.full_tgt_list]).T
            _addl_bool_cols = np.array([(tgt in self.tagged,
                                         tgt.metadata.get('is_ref', True))
                                        for tgt in self.full_tgt_list],
                                       dtype=bool).T
            dct_all['color'] = _addl_str_cols[0]
            dct_all['category'] = _addl_str_cols[1]
            dct_all['comment'] = _addl_str_cols[2]
            dct_all['tagged'] = _addl_bool_cols[0]
            dct_all['is_ref'] = _addl_bool_cols[1]

            # make pandas dataframe from result
            self.tgt_df = pd.DataFrame.from_dict(dct_all, orient='columns')

        ss_df = pd.DataFrame(columns=['az_deg', 'alt_deg', 'name', 'color'])
        if self.plot_ss_objects:
            # TODO: until we learn how to do vector calculations for SS bodies
            for tgt in self.ss:
                cres = tgt.calc(self.site.observer, start_time)
                dct = cres.get_dict(columns=['az_deg', 'alt_deg', 'name'])
                dct['color'] = tgt.color
                # this is the strange way to do an append in pandas df
                ss_df.loc[len(ss_df)] = dct
            self.ss_df = ss_df

        if self.gui_up:
            self.fv.gui_do(self._update_gui, self.tgt_df, self.ss_df)

    def _update_gui(self, tgt_df, ss_df):
        self.fv.assert_gui_thread()
        if len(self.target_dict) == 0:
            self.w.tgt_tbl.clear()
        else:
            # update the target table
            self.targets_to_table(tgt_df)

            local_time = (self._last_tgt_update_dt.astimezone(self.cur_tz))
            tzname = self.cur_tz.tzname(local_time)
            self.w.update_time.set_text("Last updated at: " +
                                        local_time.strftime("%H:%M:%S") +
                                        f" [{tzname}]")

            self.update_targets(tgt_df, 'targets')

        if self.plot_ss_objects:
            self.update_targets(ss_df, 'ss')

    def update_plots(self):
        """Just update plots, targets and info haven't changed."""
        if self.tgt_df is not None:
            self.update_targets(self.tgt_df, 'targets')
        if self.plot_ss_objects:
            self.update_targets(self.ss_df, 'ss')

    def get_target_by_separation(self, tgt, dt=None, min_delta_sep_arcsec=600):
        """Select a target by angular distance from another target.

        Parameters
        ----------
        tgt : `~spot.util.target.Target`
            A target to search against

        dt : datetime.datetime (optional, defaults to current time)
            The time of checking

        min_delta_sep_arcsec : float (optional, defaults to 600 asec)
            Separation must be less than this value

        Returns
        -------
        tgt : `~spot.util.target.Target`
            Target matching parameter or None
        """
        if self._mbody is None:
            return None
        if dt is None:
            dt = self.dt_utc

        cr = self.site.observer.calc(self._mbody, dt)
        # calculate separation from the supplied target
        sep_radec = cr.calc_separation(tgt)

        idx = np.argmin(sep_radec)
        tgt_radec, sep_radec = self.full_tgt_list[idx], sep_radec[idx]
        if sep_radec >= min_delta_sep_arcsec:
            # no target meets the minimum acceptable separation
            tgt_radec = None
        return tgt_radec

    def change_radius_cb(self, setting, radius):
        # sky radius has changed in PolarSky
        self.update_plots()

    def time_changed_cb(self, cb, time_utc, cur_tz):
        self.dt_utc = time_utc
        self.cur_tz = cur_tz
        if not self.gui_up:
            return

        if (self._last_tgt_update_dt is None or
            abs((self.dt_utc - self._last_tgt_update_dt).total_seconds()) >
            self.settings.get('targets_update_interval')):
            self.logger.info("updating targets")
            #self._last_tgt_update_dt = time_utc
            self.update_all()

    def load_file_cb(self, w, paths):
        self.load_files(paths)

    def file_setpath_cb(self, w):
        file_path = w.get_text().strip()
        self.load_files([file_path])

    def load_files(self, paths):
        if len(paths) == 0:
            return

        for file_path in paths:
            file_path = file_path.strip()
            _pfx, ext = os.path.splitext(file_path.lower())
            if ext == ".ope":
                self.process_ope_file_for_targets(file_path)
            elif ext == ".csv":
                self.process_csv_file_for_targets(file_path)
            elif ext == ".eph":
                self.process_eph_file_for_target(file_path)
            else:
                self.fv.show_error(f"I don't know how to load files of type '{ext}'")
                return

            if (not self.settings.get('merge_targets', False) and
                self.settings.get('rotate_target_colors', False)):
                self._tgt_color_idx = (self._tgt_color_idx + 1) % len(self.tgt_colors)
                self._tgt_color = self.tgt_colors[self._tgt_color_idx]

        self.w.file_path.set_text(file_path)
        hex_color = colors.lookup_color(self._tgt_color, format='hex')
        self.w.colorselect.set_color(hex_color)
        self.w.color.set_color(bg=hex_color, fg='black')
        #self.w.tgt_tbl.set_optimal_column_widths()

    def add_targets(self, category, tgt_df, merge=False):
        """Add targets from a Pandas dataframe."""
        new_targets = []
        for idx, row in tgt_df.iterrows():
            name = row.get('Name', 'none')
            try:
                ra, dec, eqx = row['RA'], row['DEC'], row['Equinox']
                ra_deg, dec_deg, eq = spot_target.normalize_ra_dec_equinox(ra, dec, eqx)
                # these will check angles and force an exception if there is
                # a bad angle
                ra_str = wcs.ra_deg_to_str(ra_deg)
                dec_str = wcs.dec_deg_to_str(dec_deg)
            except Exception as e:
                errmsg = f"Bad coordinate for '{name}': RA={ra} DEC={dec} EQ={eqx}: {e}"
                self.logger.error(errmsg, exc_info=True)
                self.fv.show_error(errmsg)
                continue

            comment = row.get('Comment', '')
            pmra = row.get('pmRA', None)
            pmdec = row.get('pmDEC', None)

            tgt = spot_target.Target(name=name,
                                     ra=ra_deg,
                                     dec=dec_deg,
                                     equinox=eq,
                                     pmra=pmra,
                                     pmdec=pmdec,
                                     comment=comment,
                                     category=category)
            tgt.set(is_ref=row.get('IsRef', True),
                    color=row.get('color', self._tgt_color))
            # get all column values as metadata
            tgt.set(**row.to_dict())
            new_targets.append(tgt)

        self.add_target_list(category, new_targets, merge=merge)

    def add_target_list(self, category, targets, merge=False):
        if not merge:
            # remove old targets from this same category
            target_dict = {(tgt.category, tgt.name): tgt
                           for tgt in self.target_dict.values()
                           if tgt.category != category}
        else:
            target_dict = self.target_dict
        # add new targets
        target_dict.update({(tgt.category, tgt.name): tgt
                            for tgt in targets})
        self.target_dict = target_dict

        self.full_tgt_list = list(self.target_dict.values())
        # update PolarSky plot
        self.fv.gui_call(self.update_all, targets_changed=True)

        self.issue_targets_changed()

    def process_csv_file_for_targets(self, csv_path):
        tgt_df = pd.read_csv(csv_path)
        if 'Equinox' not in tgt_df:
            tgt_df['Equinox'] = [2000.0] * len(tgt_df)
        if 'IsRef' not in tgt_df:
            tgt_df['IsRef'] = [True] * len(tgt_df)
        if 'Comment' not in tgt_df:
            tgt_df['Comment'] = [os.path.basename(csv_path)] * len(tgt_df)

        merge = self.settings.get('merge_targets', False)
        category = csv_path if not merge else "Targets"
        self.add_targets(category, tgt_df, merge=merge)
        self.w.tgt_tbl.set_optimal_column_widths()

    def process_eph_file_for_target(self, eph_path):
        merge = self.settings.get('merge_targets', False)
        category = eph_path if not merge else "Targets"
        target = spot_target.load_jplephem_target(eph_path, dt=self.dt_utc)
        target.set(IsRef=True)

        self.add_target_list(category, [target], merge=merge)
        self.w.tgt_tbl.set_optimal_column_widths()

    def process_eph_table_for_target(self, name, eph_tbl):
        merge = self.settings.get('merge_targets', False)
        # TODO: category
        category = "Non-sidereal"
        target = spot_target.make_jplhorizons_target(name, eph_tbl,
                                                     category=category,
                                                     dt=self.dt_utc)
        target.set(IsRef=True)

        self.add_target_list(category, [target], merge=merge)
        self.w.tgt_tbl.set_optimal_column_widths()

    def process_ope_file_for_targets(self, ope_file):
        if not have_oscript:
            self.fv.show_error("Please install the 'oscript' module to use this feature")

        proc_home = os.path.join(self.home, 'Procedure')
        if not os.path.isdir(proc_home):
            proc_home = self.home
        prm_dirs = [proc_home, os.path.join(proc_home, 'COMMON'),
                    os.path.join(proc_home, 'COMMON', 'prm'),
                    os.path.join(ginga_home, 'prm')]

        # read OPE file
        with open(ope_file, 'r') as in_f:
            ope_buf = in_f.read()

        # gather target info from OPE
        tgt_res = ope.get_targets(ope_buf, prm_dirs)

        # Report errors, if any, from reading in the OPE file.
        if len(tgt_res.prm_errmsg_list) > 0:
            # pop up the error in the GUI under "Errors" tab
            self.fv.gui_do(self.fv.show_error, '\n'.join(tgt_res.prm_errmsg_list))
            for errmsg in tgt_res.prm_errmsg_list:
                self.logger.error(errmsg)

        # process into Target object list
        new_targets = []
        comment = os.path.basename(ope_file)
        for tgt_info in tgt_res.tgt_list_info:
            objname = tgt_info.objname
            ra_str = tgt_info.ra
            dec_str = tgt_info.dec
            eq_str = tgt_info.eq
            is_ref = tgt_info.is_referenced
            new_targets.append((objname, ra_str, dec_str, eq_str,
                                comment, is_ref))

        tgt_df = pd.DataFrame(new_targets,
                              columns=["Name", "RA", "DEC", "Equinox",
                                       "Comment", "IsRef"])
        merge = self.settings.get('merge_targets', False)
        category = ope_file if not merge else "Targets"
        self.add_targets(category, tgt_df, merge=merge)
        self.w.tgt_tbl.set_optimal_column_widths()

    def targets_to_table(self, tgt_df):
        tree_dict = OrderedDict()
        for idx, row in tgt_df.iterrows():
            is_ref = row.get('is_ref', True)
            if self.show_unref_tgts or is_ref:
                dct = tree_dict.setdefault(row.category, dict())
                tagged = row['tagged']
                # NOTE: AZ values are normalized to standard use
                az_deg = self.site.norm_to_az(row.az_deg)
                # find shorter of the two azimuth choices
                az2_deg = (az_deg % 360) - 360
                if abs(az2_deg) < abs(az_deg):
                    az_deg = az2_deg
                ad_observe, ad_guide = (row.atmos_disp_observing,
                                        row.atmos_disp_guiding)
                calc_ad = max(ad_observe, ad_guide) - min(ad_observe, ad_guide)
                dct[row['name']] = Bunch.Bunch(
                    tagged=chr(0x2714) if tagged else '',
                    name=row['name'],
                    ra=wcs.ra_deg_to_str(row.ra_deg),
                    dec=wcs.dec_deg_to_str(row.dec_deg),
                    equinox="{:>6.1f}".format(row.equinox),
                    az_deg="{:>+4d}".format(int(round(az_deg))),
                    alt_deg="{:>3d}".format(int(round(row.alt_deg))),
                    parang_deg="{:>3d}".format(int(row.pang_deg)),
                    ha="{:>+6.2f}".format(np.degrees(row.ha) / 15),
                    ad="{:>3.1f}".format(np.degrees(calc_ad) * 3600),
                    icon=self._get_dir_icon(row),
                    airmass="{:>5.2f}".format(row.airmass),
                    moon_sep="{:>3d}".format(int(round(row.moon_sep))),
                    comment=row.comment)

        # save and restore selection after update
        # NOTE: calling set_tree() will trigger the target_selection_cb,
        # clearing the selected targets, etc.  So we use this context
        # manager to prevent that from happening and restore the selections.
        with self.table_stocker:
            self.w.tgt_tbl.update_tree(tree_dict, expand_new=True)

        # NOTE: seems not to be necessary any more, since selected items
        # remain selected after the update
        # paths = [[tgt.category, tgt.name] for tgt in self.selected]
        # self.w.tgt_tbl.select_paths(paths)

        self._update_uncollapsed_targets()
        self._update_selection_buttons()

    def target_tagged_update(self):
        self.clear_plot()
        self.update_all()

        self.cb.make_callback('tagged-changed', self.tagged)

    def _get_target_color(self, tgt):
        if tgt in self.selected:
            color = self.settings['color_selected']
        elif tgt in self.tagged:
            color = self.settings['color_tagged']
        else:
            color = tgt.get('color', self._tgt_color)
        return color

    def _update_target_colors(self, targets):
        try:
            tgt_obj = self.canvas.get_object_by_tag('targets')
        except KeyError:
            self.update_all(targets_changed=False)
            return

        for tgt in targets:
            obj = tgt.get('plotted', None)
            if obj is not None:
                color = self._get_target_color(tgt)
                point, circle, text = obj.objects[:3]
                point.color = point.fillcolor = color
                circle.color = color
                text.color = color
                if tgt in self.selected:
                    # object selected
                    text.fillcolor = color
                    text.bgalpha = text.borderalpha = text.alpha
                    if obj in tgt_obj:
                        tgt_obj.raise_object(obj)
                else:
                    text.fillcolor = color
                    text.bgalpha = text.borderalpha = 0.0

        self.fitsimage.redraw(whence=3)

    def target_selection_cb(self, w, sel_dct):
        """Called when a selection is made in the targets table."""
        if self.table_shelf.is_blocked():
            # see NOTE in targets_to_table()
            return

        new_highlighted = set([self.target_dict[(category, name)]
                               for category, dct in sel_dct.items()
                               for name in dct.keys()])
        updated_tgts = (self.selected - new_highlighted).union(
            new_highlighted - self.selected)
        self.selected = new_highlighted
        if self.plot_which in ['selected', 'tagged+selected', 'uncollapsed']:
            self.update_all(targets_changed=False)
        else:
            self._update_target_colors(updated_tgts)

        self._update_selection_buttons()

        if len(self.selected) == 1:
            if self.settings.get('enable_datetime_setting', False):
                tgt = list(self.selected)[0]
                dt_str = tgt.get('DateTime', None)
                if dt_str is not None:
                    dt = parse_date(dt_str)
                    if dt.tzinfo is None:
                        # assume UTC if no timezone specified
                        dt = dt.replace(tzinfo=UTC)
                    self.logger.info(f"setting date to {dt}")
                    obj = self.channel.opmon.get_plugin('SiteSelector')
                    obj.set_datetime(dt)

        self.cb.make_callback('selection-changed', self.selected)

    # def target_single_cb(self, w, sel_dct):
    #     selected = set([self.target_dict[(category, name)]
    #                     for category, dct in sel_dct.items()
    #                     for name in dct.keys()])
    #     self.tagged = selected
    #     self.target_tagged_update()

    def _update_uncollapsed_targets(self):
        res_dct = self.w.tgt_tbl.get_children(status='expanded')
        self.uncollapsed = set([self.target_dict[(category, name)]
                                for category, dct in res_dct.items()
                                for name in dct.keys()])

        if self.tgt_df is not None:
            self.update_targets(self.tgt_df, 'targets')

        self.cb.make_callback('uncollapsed-changed', self.uncollapsed)

    def targets_collapse_cb(self, w, path):
        self._update_uncollapsed_targets()

    def list_prm_cb(self, w, tf):
        self.show_unref_tgts = tf
        if self.tgt_df is not None:
            self.targets_to_table(self.tgt_df)
            self.update_targets(self.tgt_df, 'targets')
        self.update_targets(self.ss_df, 'ss')

        self.issue_targets_changed()

    def get_targets(self):
        if self.show_unref_tgts:
            targets = self.full_tgt_list
        else:
            targets = [tgt for tgt in self.full_tgt_list
                       if tgt.get('is_ref', True)]
        return targets

    def get_tagged_targets(self):
        return self.tagged

    def get_selected_targets(self):
        return self.selected

    def get_uncollapsed_targets(self):
        return self.uncollapsed

    def issue_targets_changed(self):
        self.cb.make_callback('targets-changed', self.get_targets())

    def tag_cb(self, w):
        sel_dct = self.w.tgt_tbl.get_selected()
        selected = set([self.target_dict[(category, name)]
                        for category, dct in sel_dct.items()
                        for name in dct.keys()])
        self.tagged = self.tagged.union(selected)
        self.target_tagged_update()
        self._update_selection_buttons()

    def untag_cb(self, w):
        sel_dct = self.w.tgt_tbl.get_selected()
        selected = set([self.target_dict[(category, name)]
                        for category, dct in sel_dct.items()
                        for name in dct.keys()])
        self.tagged = self.tagged.difference(selected)
        self.target_tagged_update()
        self._update_selection_buttons()

    def delete_cb(self, w):
        sel_dct = self.w.tgt_tbl.get_selected()
        selected = [self.target_dict[(category, name)]
                    for category, dct in sel_dct.items()
                    for name in dct.keys()]
        if len(selected) > 0:
            self.delete_targets(selected)
            return
        # <-- no leaf items selected. check for selected branches
        paths = self.w.tgt_tbl.get_selected_paths()
        if len(paths) > 0:
            categories = [path[0] for path in paths]
            self.delete_categories(categories)

    def delete_targets(self, targets):
        selected = set(targets)
        # TODO: have confirmation dialog
        # remove any items from tagged that were deleted
        self.tagged = self.tagged.difference(selected)
        # remove any items from uncollapsed that were deleted
        self.uncollapsed = self.tagged.difference(selected)
        # remove any items from selection that were deleted
        _selected = self.selected
        self.selected = self.selected.difference(selected)
        # remove any items from target list that were deleted
        target_dict = {(tgt.category, tgt.name): tgt
                       for tgt in self.target_dict.values()
                       if tgt not in selected}
        self.target_dict = target_dict
        self._mbody = None
        self.full_tgt_list = list(self.target_dict.values())

        self.issue_targets_changed()

        self.target_tagged_update()
        self._update_selection_buttons()

        if _selected != self.selected:
            self.cb.make_callback('selection-changed', self.selected)

    def delete_categories(self, categories):
        selected = [self.target_dict[(category, name)]
                    for category, name in self.target_dict.keys()
                    if category in categories]
        self.delete_targets(selected)

    def select_all_cb(self, w):
        self.w.tgt_tbl.select_all(True)
        # NOTE: have to do this because programatically selecting items
        # doesn't invoke callback
        sel_dct = self.w.tgt_tbl.get_selected()
        self.target_selection_cb(self.w.tgt_tbl, sel_dct)

    def collapse_all_cb(self, w):
        self.w.tgt_tbl.expand_all(False)
        # NOTE: have to do this because programatically selecting items
        # doesn't invoke callback
        self._update_uncollapsed_targets()

    def _update_selection_buttons(self):
        # enable or disable the selection buttons as needed
        sel_dct = self.w.tgt_tbl.get_selected()
        selected = set([self.target_dict[(category, name)]
                        for category, dct in sel_dct.items()
                        for name in dct.keys()
                        if (category, name) in self.target_dict])
        self.w.btn_tag.set_enabled(len(selected - self.tagged) > 0)
        self.w.btn_untag.set_enabled(len(selected & self.tagged) > 0)
        sel_lst = self.w.tgt_tbl.get_selected_paths()
        self.w.btn_delete.set_enabled(len(selected) > 0 or len(sel_lst) > 0)

    def plot_ss_cb(self, w, tf):
        self.plot_ss_objects = tf
        self.clear_plot()
        self.update_all()

    def configure_plot_cb(self, w, idx):
        option = w.get_text()
        self.plot_which = option.lower()
        self.clear_plot()
        self.update_plots()

    def site_changed_cb(self, cb, site_obj):
        self.logger.debug("site has changed")
        self.site = site_obj

        self.clear_plot()
        self.update_all()

    def enable_datetime_cb(self, w, tf):
        self.settings.set(enable_datetime_setting=tf)

    def rotate_target_colors_cb(self, w, tf):
        self.settings.set(rotate_target_colors=tf)

    def merge_targets_cb(self, w, tf):
        self.settings.set(merge_targets=tf)

    def color_select_cb(self, w, color):
        hex_color = w.get_color(format='hex')
        self._tgt_color = hex_color
        self.w.color.set_color(bg=hex_color, fg='black')

    def get_datetime(self):
        # TODO: work with self.site directly, not observer
        # return self.dt_utc.astimezone(self.site.observer.tz_local)
        # return self.dt_utc.astimezone(self.cur_tz)
        return self.dt_utc

    def update_targets_fov(self, dct):
        self.fov_dct.update(dct)

    def _get_dir_icon(self, row):
        if True:  # TBD?  row.will_be_visible']:
            ha, alt_deg = row.ha, row.alt_deg
            if int(round(alt_deg)) <= 15:
                if ha < 0:
                    icon = self.diricon['up_ng']
                elif 0 < ha:
                    icon = self.diricon['down_ng']
            elif 15 < int(round(alt_deg)) <= 30:
                if ha < 0:
                    icon = self.diricon['up_low']
                elif 0 < ha:
                    icon = self.diricon['down_low']
            elif 30 < int(round(alt_deg)) <= 60:
                if ha < 0:
                    icon = self.diricon['up_ok']
                elif 0 < ha:
                    icon = self.diricon['down_ok']
            elif 60 < int(round(alt_deg)) <= 85:
                if ha < 0:
                    icon = self.diricon['up_good']
                elif 0 < ha:
                    icon = self.diricon['down_good']
            elif 85 < int(round(alt_deg)) <= 90:
                if ha < 0:
                    icon = self.diricon['up_high']
                elif 0 < ha:
                    icon = self.diricon['down_high']
        else:
            icon = self.diricon['invisible']
        return icon

    def p2r(self, r, t):
        obj = self.channel.opmon.get_plugin('PolarSky')
        return obj.p2r(r, t)

    def get_scale(self):
        obj = self.channel.opmon.get_plugin('PolarSky')
        return obj.get_scale()

    def map_azalt(self, az, alt):
        obj = self.channel.opmon.get_plugin('PolarSky')
        return obj.map_azalt(az, alt)

    def __str__(self):
        return 'targets'
