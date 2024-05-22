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
import time
from datetime import datetime, timedelta
from dateutil import tz, parser
import math
from collections import OrderedDict
import csv

# 3rd party
import numpy as np
import pandas as pd

# ginga
from ginga.gw import Widgets, GwHelp
from ginga import GingaPlugin
from ginga.util.paths import ginga_home
from ginga.util import wcs
from ginga.misc import Bunch, Callback

# local
from spot.util import calcpos

# oscript (optional, for loading OPE files)
try:
    from oscript.parse import ope
    have_oscript = True
except ImportError:
    have_oscript = False

from spot.util.target import Target, normalize_ra_dec_equinox

# where our icons are stored
from spot import __file__
icondir = os.path.join(os.path.dirname(__file__), 'icons')


class Targets(GingaPlugin.LocalPlugin):
    """
    Targets
    =======
    ``Targets`` is normally used in conjunction with the plugins ``PolarSky``,
    and ``Visibility`` to show information about celestial objects that could
    be observed.  It allows you to load one or more files of targets and then
    plot them on the "<wsname>_TGTS" window, or show their visibility in the
    ``Visibility`` plugin UI.

    Loading targets from a CSV file
    -------------------------------
    Targets can be loaded from a CSV file that contains a column header
    containing the column titles "Name", "RA", "DEC", and "Equinox" (they
    do not need to be in that order).  Other columns may be present but will
    be ignored.  In this format, RA and DEC can be specified as decimal values
    (in which case they are interpreted as degrees) or sexigesimal notation
    (HH:MM:SS.SSS for RA, DD:MM:SS.SS for DEC).  Equinox can be specified
    as e.g. J2000 or 2000.0.

    .. note:: SPOT can also read targets from CSV files in "SOSS notation".
              See the section below on loading targets from an OPE file.

    Press the "File" button and navigate to, and select, a CSV file with the
    above format.  Or, type the path of the file in the box next to the "File"
    button and press "Set" (the latter method can also be used to quickly
    reload a file that you have edited).

    The targets should populate the table.

    Loading targets from an OPE file
    --------------------------------
    An OPE file is a special format of file used by Subaru Telescope.
    Targets in this kind of file are specified in "SOSS notation"
    (HHMMSS.SSS for RA, +|-DDMMSS.SS for DEC, NNNN.0 for Equinox).

    Follow the instructions above for loading targets from a CSV file, but
    choose an OPE file instead.

    .. note::  In order to load this format you need to have installed the
               optional "oscript" package:
               (pip install git+https://github.com/naojsoft/oscript).

    Table information
    -----------------
    The target table summarizes information about targets. There are columns
    for static information like target name, RA, DEC, as well as dynamically
    updating information for azimuth, altitude, a color-coded rise/set icon,
    hour angle, airmass, atmospheric dispersion, parallactic angle and moon
    separation.


    """
    def __init__(self, fv, fitsimage):
        super().__init__(fv, fitsimage)

        # get preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_Targets')
        self.settings.add_defaults(targets_update_interval=60.0,
                                   plot_ss_objects=True)
        self.settings.load(onError='silent')

        # these are set via callbacks from the SiteSelector plugin
        self.site = None
        self.dt_utc = None
        self.cur_tz = None
        self._last_tgt_update_dt = None
        self.home = os.path.expanduser('~')

        self.cb = Callback.Callbacks()
        for name in ['selection-changed']:
            self.cb.enable_callback(name)

        self.colors = ['red', 'blue', 'green', 'cyan', 'magenta', 'yellow']
        self.base_circ = None
        self.target_dict = {}
        self.full_tgt_list = []
        self.plot_which = 'selected'
        self.plot_ss_objects = self.settings.get('plot_ss_objects', True)
        self.selected = set([])
        self.tgt_df = None
        self.ss_df = None
        self._mbody = None


        self.columns = [('Sel', 'selected'),
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
                        #('Eq', 'equinox'),
                        #('Comment', 'comment'),
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
        canvas.set_surface(self.fitsimage)
        canvas.set_draw_mode('pick')
        canvas.register_for_cursor_drawing(self.fitsimage)
        self.canvas = canvas

        self.gui_up = False

    def build_gui(self, container):

        # initialize site and date/time/tz
        obj = self.channel.opmon.get_plugin('SiteSelector')
        self.site = obj.get_site()
        obj.cb.add_callback('site-changed', self.site_changed_cb)
        self.dt_utc, self.cur_tz = obj.get_datetime()
        obj.cb.add_callback('time-changed', self.time_changed_cb)

        top = Widgets.VBox()
        top.set_border_width(4)

        captions = (('Load File', 'button', 'File Path', 'entryset'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b

        b.load_file.set_text("File")
        self.fileselect = GwHelp.FileSelection(container.get_widget(),
                                               all_at_once=True)
        self.proc_dir_path = os.path.join(self.home, 'Procedure')
        b.file_path.set_text(self.proc_dir_path)

        top.add_widget(w, stretch=0)
        b.load_file.add_callback('activated', self.load_file_cb)
        b.load_file.set_tooltip("Select target file")
        b.file_path.add_callback('activated', self.file_setpath_cb)

        plot_update_text = "Please select file for list display"

        hbox = Widgets.HBox()
        hbox.set_spacing(5)
        self.w.update_time = Widgets.Label(plot_update_text)
        hbox.add_widget(self.w.update_time, stretch=0)
        hbox.add_widget(Widgets.Label(''), stretch=1)
        cbox = Widgets.CheckBox("Merge Targets")
        self.w.merge_targets = cbox
        cbox.set_state(False)
        hbox.add_widget(cbox, stretch=0)
        cbox = Widgets.CheckBox("List All Targets")
        cbox.set_tooltip("List only targets referenced in OPE file or list all targets in OPE and PRM files")
        self.w.list_all_targets = cbox
        cbox.set_state(False)
        cbox.add_callback('activated', self.list_all_cb)
        hbox.add_widget(cbox, stretch=0)
        top.add_widget(hbox, stretch=0)

        self.w.tgt_tbl = Widgets.TreeView(auto_expand=True,
                                          selection='multiple',
                                          sortable=True,
                                          use_alt_row_color=True)
        self.w.tgt_tbl.setup_table(self.columns, 2, 'name')
        top.add_widget(self.w.tgt_tbl, stretch=1)

        self.w.tgt_tbl.set_optimal_column_widths()
        self.w.tgt_tbl.add_callback('selected', self.target_selection_cb)
        self.w.tgt_tbl.add_callback('activated', self.target_single_cb)

        hbox = Widgets.HBox()
        btn = Widgets.Button("Select")
        btn.set_tooltip("Add highlighted items to selected targets")
        btn.add_callback('activated', self.select_cb)
        hbox.add_widget(btn, stretch=0)
        self.w.btn_select = btn
        btn = Widgets.Button("Unselect")
        btn.set_tooltip("Remove highlighted items from selected targets")
        btn.add_callback('activated', self.unselect_cb)
        hbox.add_widget(btn, stretch=0)
        self.w.btn_unselect = btn
        btn = Widgets.Button("Select All")
        btn.set_tooltip("Add all targets to selected targets")
        btn.add_callback('activated', self.select_all_cb)
        hbox.add_widget(btn, stretch=0)
        self.w.btn_select_all = btn
        btn = Widgets.Button("Unselect All")
        btn.set_tooltip("Clear all targets from selected targets")
        btn.add_callback('activated', self.unselect_all_cb)
        hbox.add_widget(btn, stretch=0)
        self.w.btn_unselect_all = btn
        btn = Widgets.Button("Delete")
        btn.set_tooltip("Delete selected target from targets")
        btn.add_callback('activated', self.delete_cb)
        hbox.add_widget(btn, stretch=0)
        self.w.btn_delete = btn

        hbox.add_widget(Widgets.Label(''), stretch=1)

        self.w.plot_ss = Widgets.CheckBox("Plot SS")
        self.w.plot_ss.set_state(self.plot_ss_objects)
        self.w.plot_ss.add_callback('activated', self.plot_ss_cb)
        hbox.add_widget(self.w.plot_ss, stretch=0)

        hbox.add_widget(Widgets.Label('Plot:'), stretch=0)
        plot = Widgets.ComboBox()
        hbox.add_widget(plot, stretch=0)
        for option in ['All', 'Selected']:
            plot.append_text(option)
        plot.set_index(1)
        plot.add_callback('activated', self.configure_plot_cb)
        plot.set_tooltip("Choose what is plotted")

        self._update_selection_buttons()
        top.add_widget(hbox, stretch=0)

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
        p_canvas = self.fitsimage.get_canvas()
        if self.canvas not in p_canvas:
            # Add our canvas
            p_canvas.add(self.canvas)

        self.canvas.delete_all_objects()

        self.initialize_plot()
        self.update_all()

        self.resume()

    def pause(self):
        self.canvas.ui_set_active(False)

    def resume(self):
        self.canvas.ui_set_active(True, viewer=self.viewer)

    def stop(self):
        self.gui_up = False
        # remove the canvas from the image
        p_canvas = self.fitsimage.get_canvas()
        if self.canvas in p_canvas:
            p_canvas.delete_object(self.canvas)

    def redo(self):
        pass

    def replot_all(self):
        self.initialize_plot()

    def initialize_plot(self):
        pass

    def clear_plot(self):
        self.canvas.delete_object_by_tag('ss')
        self.canvas.delete_object_by_tag('targets')

    def filter_targets(self, tgt_df):
        if self.plot_which == 'all':
            shown_tgt_lst = tgt_df
        elif self.plot_which == 'selected':
            shown_tgt_lst = tgt_df[tgt_df['selected'] == True]

        return shown_tgt_lst

    def select_star_cb(self, obj, canvas, event, pt, action):
        info = obj.get_data()
        if info.get('tag', None) != 'targets':
            return
        idx = info.get('index')
        # TODO
        #self.table.show_selection(info.star)
        return True

    def plot_targets(self, tgt_df, tag, start_time=None):
        """Plot targets.
        """
        if start_time is None:
            start_time = self.get_datetime()
        self.canvas.delete_object_by_tag(tag)

        # filter the subset desired to be seen
        pt_radius = 3
        cl_radius = pt_radius * 2
        radius_dct = dict(Sun=cl_radius * 8,
                          Moon=cl_radius * 8)
        if tag != 'ss':
            tgt_df = self.filter_targets(tgt_df)
            fill = False
        else:
            fill = True

        self.logger.info("plotting {} targets tag {}".format(len(tgt_df), tag))
        objs = []
        for idx, row in tgt_df.iterrows():
            is_ref = row.get('is_ref', None)
            if tag == 'ss' or self.w.list_all_targets.get_state() or is_ref:
                alpha = 1.0 if row['alt_deg'] > 0 else 0.0
                t, r = self.map_azalt(row['az_deg'], row['alt_deg'])
                x, y = self.p2r(r, t)
                point = self.dc.Point(x, y, radius=pt_radius, style='cross',
                                      color=row['color'], fillcolor=row['color'],
                                      linewidth=2, alpha=alpha,
                                      fill=True, fillalpha=alpha)
                radius = radius_dct.get(row['name'], cl_radius)
                circle = self.dc.Circle(x, y, radius, color=row['color'],
                                        linewidth=1, alpha=alpha,
                                        fill=fill, fillcolor=row['color'],
                                        fillalpha=alpha * 0.7)
                text = self.dc.Text(x, y, row['name'],
                                    #color=row['color'], alpha=alpha,
                                    fill=True, fillcolor=row['color'],
                                    fillalpha=alpha, linewidth=0,
                                    font="Roboto", fontscale=True,
                                    fontsize=None, fontsize_min=8)
                star = self.dc.CompoundObject(point, circle, text)
                star.opaque = True
                star.pickable = True
                star.set_data(tag=tag, index=idx)
                star.add_callback('pick-up', self.select_star_cb, 'select')
                #star.add_callback('pick-hover', self.select_star_cb, 'info')
                objs.append(star)

        o = self.dc.CompoundObject(*objs)
        self.canvas.add(o, tag=tag, redraw=False)

        self.canvas.update_canvas(whence=3)

        if tag == 'ss':
            # don't plot visibility of solar system objects in Visibility
            return

        tgt_list = self.full_tgt_list if self.plot_which == 'all' else self.selected
        targets = []
        for tgt in tgt_list:
            is_ref = tgt.metadata.is_ref
            if self.w.list_all_targets.get_state() or is_ref:
                targets.append(tgt)
        obj = self.channel.opmon.get_plugin('Visibility')
        self.fv.gui_do(obj.plot_targets, start_time, self.site, targets)

    def update_targets(self, tgt_df, tag, start_time=None):
        """Update targets already plotted with new positions.
        """
        self.canvas.delete_object_by_tag(tag)
        if not self.canvas.has_tag(tag):
            self.plot_targets(tgt_df, tag, start_time=start_time)
            return
        # if start_time is None:
        #     start_time = self.get_datetime()

        # if tag != 'ss':
        #     # filter the subset desired to be seen
        #     tgt_info_lst = self.filter_targets(tgt_info_lst)

        # self.logger.info("updating {} targets".format(len(tgt_info_lst)))
        # obj = self.canvas.get_object_by_tag(tag)
        # objs = obj.objects
        # i = 0
        # for res in tgt_info_lst:
        #     alpha = 1.0 if res.info.alt_deg > 0 else 0.0
        #     t, r = self.map_azalt(res.info.az_deg, res.info.alt_deg)
        #     x, y = self.p2r(r, t)
        #     point, text = objs[i], objs[i + i]
        #     point.x, point.y, point.alpha, point.fillalpha = x, y, alpha, alpha
        #     text.x, text.y, text.alpha = x, y, alpha
        #     point.color = text.color = res.color
        #     i += 2

        # self.canvas.update_canvas(whence=3)

        # if tag == 'ss':
        #     # don't plot visibility of solar system objects in Visibility
        #     return
        # targets = [res.tgt for res in tgt_info_lst]
        # obj = self.channel.opmon.get_plugin('Visibility')
        # # obj.plot_targets(start_time, self.site, targets,
        # #                  timezone=self.cur_tz)
        # obj.plot_targets(start_time, self.site, targets)

    def _create_multicoord_body(self):
        self.full_tgt_list = list(self.target_dict.values())
        if len(self.full_tgt_list) == 0:
            self._mbody = None
            return
        names = np.asarray([tgt.name for tgt in self.full_tgt_list])
        arr = np.asarray([(tgt.ra, tgt.dec, tgt.equinox)
                          for tgt in self.full_tgt_list]).T
        self._mbody = calcpos.Body(names, arr[0], arr[1], arr[2])

    def _create_addl_tgt_cols(self):
        # create columns for target color, selected and category
        self._addl_tgt_cols = np.asarray([('green2' if tgt not in
                                           self.selected else 'pink',
                                           tgt.category)
                                           for tgt in self.full_tgt_list]).T
        self._col_selected = np.array([tgt in self.selected
                                       for tgt in self.full_tgt_list],
                                      dtype=bool)
        self._is_ref =  np.array([tgt.metadata.is_ref
                                  for tgt in self.full_tgt_list],
                                 dtype=bool)

    def update_all(self, start_time=None, targets_changed=False):
        if start_time is None:
            start_time = self.get_datetime()
        self._last_tgt_update_dt = start_time
        self.logger.info("update time: {}".format(start_time.strftime(
                         "%Y-%m-%d %H:%M:%S [%z]")))
        if len(self.target_dict) == 0:
            self.w.tgt_tbl.clear()
        else:
            # create multi-coordinate body if not yet created
            if targets_changed or self._mbody is None:
                self._create_multicoord_body()
                self._create_addl_tgt_cols()

            # get full information about all targets at `start_time`
            cres = self._mbody.calc(self.site.observer, start_time)
            dct_all = cres.get_dict()
            dct_all['color'] = self._addl_tgt_cols[0]
            dct_all['category'] = self._addl_tgt_cols[1]
            dct_all['selected'] = self._col_selected
            dct_all['is_ref'] = self._is_ref

            # make pandas dataframe from result
            self.tgt_df = pd.DataFrame.from_dict(dct_all, orient='columns')

            # update the target table
            if self.gui_up:
                self.targets_to_table(self.tgt_df)

                local_time = (self._last_tgt_update_dt.astimezone(self.cur_tz))
                tzname = self.cur_tz.tzname(local_time)
                self.w.update_time.set_text("Last updated at: " +
                                            local_time.strftime("%H:%M:%S") +
                                            f" [{tzname}]")

            self.update_targets(self.tgt_df, 'targets', start_time=start_time)

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

        self.update_targets(ss_df, 'ss', start_time=start_time)

    def update_plots(self):
        """Just update plots, targets and info haven't changed."""
        if self.tgt_df is not None:
            self.update_targets(self.tgt_df, 'targets')
        if self.plot_ss_objects:
            self.update_targets(self.ss_df, 'ss')

    def change_radius_cb(self, setting, radius):
        # sky radius has changed in PolarSky
        self.update_plots()

    def time_changed_cb(self, cb, time_utc, cur_tz):
        old_dt_utc = self.dt_utc
        self.dt_utc = time_utc
        self.cur_tz = cur_tz

        if (self._last_tgt_update_dt is None or
            abs((self.dt_utc - self._last_tgt_update_dt).total_seconds()) >
            self.settings.get('targets_update_interval')):
            self.logger.info("updating targets")
            self.update_all()

    def load_file_cb(self, w):
        # Needs to be updated for multiple selections
        proc_dir = os.path.join(self.home, 'Procedure')
        self.fileselect.popup("Load File", self.file_select_cb, proc_dir)

    def file_setpath_cb(self, w):
        file_path = w.get_text().strip()
        if file_path.lower().endswith(".ope"):
            self.process_ope_file_for_targets(file_path)
        else:
            self.process_csv_file_for_targets(file_path)

    def file_select_cb(self, paths):
        if len(paths) == 0:
            return

        # Needs to be updated for multiple selections
        self.w.file_path.set_text(paths[0])
        file_path = paths[0].strip()
        if file_path.lower().endswith(".ope"):
            self.process_ope_file_for_targets(file_path)
        else:
            self.process_csv_file_for_targets(file_path)

        self.w.tgt_tbl.set_optimal_column_widths()

    def add_targets(self, category, tgt_df, merge=False):
        """Add targets from a Pandas dataframe."""
        new_targets = []
        for idx, row in tgt_df.iterrows():
            name = row.get('Name', 'none')
            try:
                ra, dec, eqx = row['RA'], row['DEC'], row['Equinox']
                ra_deg, dec_deg, eq = normalize_ra_dec_equinox(ra, dec, eqx)
                # these will check angles and force an exception if there is
                # a bad angle
                ra_str = wcs.ra_deg_to_str(ra_deg)
                dec_str = wcs.dec_deg_to_str(dec_deg)
            except Exception as e:
                errmsg = f"Bad coordinate for '{name}': RA={ra} DEC={dec} EQ={eqx}: {e}"
                self.logger.error(errmsg, exc_info=True)
                self.fv.show_error(errmsg)
                continue

            t = Target(name=name,
                       ra=ra_deg,
                       dec=dec_deg,
                       equinox=eq,
                       comment=row.get('comment', ''),
                       category=category)
            t.set_metadata(is_ref=row.get('IsRef', None))
            new_targets.append(t)

        if not merge:
            # remove old targets from this same file
            target_dict = {(tgt.category, tgt.name): tgt
                           for tgt in self.target_dict.values()
                           if tgt.category != category}
        else:
            target_dict = self.target_dict
        # add new targets
        target_dict.update({(tgt.category, tgt.name): tgt
                            for tgt in new_targets})
        self.target_dict = target_dict

        # update GUIs
        self.update_all(targets_changed=True)

    def process_csv_file_for_targets(self, csv_path):
        tgt_df = pd.read_csv(csv_path)
        merge = self.w.merge_targets.get_state()
        category = csv_path if not merge else "Targets"
        self.add_targets(category, tgt_df, merge=merge)

    def process_ope_file_for_targets(self, ope_file):
        if not have_oscript:
            self.fv.show_error("Please install the 'oscript' module to use this feature")

        proc_home = os.path.join(self.home, 'Procedure')
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
        for tgt_info in tgt_res.tgt_list_info:
            objname = tgt_info.objname
            ra_str = tgt_info.ra
            dec_str = tgt_info.dec
            eq_str = tgt_info.eq
            is_ref = tgt_info.is_referenced
            new_targets.append((objname, ra_str, dec_str, eq_str, is_ref))

        tgt_df = pd.DataFrame(new_targets,
                              columns=["Name", "RA", "DEC", "Equinox", "IsRef"])
        merge = self.w.merge_targets.get_state()
        category = ope_file if not merge else "Targets"
        self.add_targets(category, tgt_df, merge=merge)

    def targets_to_table(self, tgt_df):
        tree_dict = OrderedDict()
        for idx, row in tgt_df.iterrows():
            is_ref = row.get('is_ref', None)
            if self.w.list_all_targets.get_state() or is_ref:
                dct = tree_dict.setdefault(row.category, dict())
                selected = row['selected']
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
                    selected='*' if selected else '',
                    name=row['name'],
                    ra=wcs.ra_deg_to_str(row.ra_deg),
                    dec=wcs.dec_deg_to_str(row.dec_deg),
                    #equinox=("%6.1f" % row.equinox),
                    az_deg=("% 4d" % int(round(az_deg))),
                    alt_deg=("% 3d" % int(round(row.alt_deg))),
                    parang_deg=("% 3d" % int(row.pang_deg)),
                    ha=("% 6.2f" % (np.degrees(row.ha)/15)),
                    icon=self._get_dir_icon(row),
                    airmass=("% 5.2f" % row.airmass),
                    moon_sep=("% 3d" % int(round(row.moon_sep))),
                    # TODO
                    #comment=row.comment,
                    ad=("% .1f" % (np.degrees(calc_ad)*3600)))
        self.w.tgt_tbl.set_tree(tree_dict)

    def target_selection_update(self):
        self.clear_plot()
        # change columns with selection info
        self._create_addl_tgt_cols()
        self.update_all()

        self.cb.make_callback('selection-changed', self.selected)

    def target_selection_cb(self, w, sel_dct):
        self._update_selection_buttons()

    def target_single_cb(self, w, sel_dct):
        selected = set([self.target_dict[(category, name)]
                        for category, dct in sel_dct.items()
                        for name in dct.keys()])
        self.selected = selected
        self.target_selection_update()

    def list_all_cb(self, w, arg1):
        if self.tgt_df is not None:
            self.targets_to_table(self.tgt_df)
            self.update_targets(self.tgt_df, 'targets')
        self.update_targets(self.ss_df, 'ss')

    def select_cb(self, w):
        sel_dct = self.w.tgt_tbl.get_selected()
        selected = set([self.target_dict[(category, name)]
                        for category, dct in sel_dct.items()
                        for name in dct.keys()])
        self.selected = self.selected.union(selected)
        self.target_selection_update()
        self._update_selection_buttons()

    def unselect_cb(self, w):
        sel_dct = self.w.tgt_tbl.get_selected()
        selected = set([self.target_dict[(category, name)]
                        for category, dct in sel_dct.items()
                        for name in dct.keys()])
        self.selected = self.selected.difference(selected)
        self.target_selection_update()
        self._update_selection_buttons()

    def delete_cb(self, w):
        sel_dct = self.w.tgt_tbl.get_selected()
        selected = set([self.target_dict[(category, name)]
                        for category, dct in sel_dct.items()
                        for name in dct.keys()])
        # TODO: have confirmation dialog
        # remove any items from selection that were deleted
        self.selected = self.selected.difference(selected)
        # remove any items from target list that were deleted
        target_dict = {(tgt.category, tgt.name): tgt
                       for tgt in self.target_dict.values()
                       if tgt not in selected}
        self.target_dict = target_dict
        self._mbody = None
        self.target_selection_update()
        self._update_selection_buttons()

    def select_all_cb(self, w):
        self.selected = set(self.target_dict.values())
        self.target_selection_update()
        self._update_selection_buttons()

    def unselect_all_cb(self, w):
        self.selected = set([])
        self.target_selection_update()
        self._update_selection_buttons()

    def _update_selection_buttons(self):
        # enable or disable the selection buttons as needed
        sel_dct = self.w.tgt_tbl.get_selected()
        selected = set([self.target_dict[(category, name)]
                        for category, dct in sel_dct.items()
                        for name in dct.keys()
                        if (category, name) in self.target_dict])
        self.w.btn_select.set_enabled(len(selected - self.selected) > 0)
        self.w.btn_unselect.set_enabled(len(selected & self.selected) > 0)
        self.w.btn_delete.set_enabled(len(selected) > 0)

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

    def get_datetime(self):
        # TODO: work with self.site directly, not observer
        # return self.dt_utc.astimezone(self.site.observer.tz_local)
        # return self.dt_utc.astimezone(self.cur_tz)
        return self.dt_utc

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


def process_tgt_list(category, tgt_list):
    return res
