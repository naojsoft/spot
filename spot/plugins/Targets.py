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

Authors
=======
E. Jeschke

Requirements
============

naojsoft packages
-----------------
- ginga
- qplan
- oscript
"""
# stdlib
import os
import time
from datetime import datetime
from dateutil import tz, parser
import math
from collections import OrderedDict
import csv

# 3rd party
import numpy as np

# ginga
from ginga.gw import Widgets, GwHelp
from ginga import GingaPlugin
from ginga.util.paths import ginga_home
from ginga.util.wcs import (ra_deg_to_str, dec_deg_to_str)
from ginga.misc import Bunch

# qplan
from qplan import common
from qplan.entity import StaticTarget

# oscript (optional, for loading OPE files)
try:
    from oscript.parse import ope
    from oscript.util.ope import funkyHMStoDeg, funkyDMStoDeg
    have_oscript = True
except ImportError:
    have_oscript = False


class Targets(GingaPlugin.LocalPlugin):

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

        self.colors = ['red', 'blue', 'green', 'cyan', 'magenta', 'yellow']
        self.base_circ = None
        self.target_list = []
        self.plot_which = 'selected'
        self.plot_ss_objects = self.settings.get('plot_ss_objects', True)
        self.selected = set([])
        self.tgt_info_lst = []
        self.ss_info_lst = []

        self.columns = [('Sel', 'selected'),
                        ('Name', 'name'),
                        ('AM', 'airmass'),
                        ('Az', 'az_deg'),
                        ('Alt', 'alt_deg'),
                        ('HA', 'ha'),
                        # ('Slew', 'slew'),
                        # ('AD', 'ad'),
                        ('Pang', 'parang_deg'),
                        ('Moon Sep', 'moon_sep'),
                        ('RA', 'ra'),
                        ('DEC', 'dec'),
                        ('Eq', 'equinox'),
                        ('Comment', 'comment'),
                        ]

        # the solar system objects
        ss = [(common.moon, 'navajowhite2'),
              (common.sun, 'darkgoldenrod1'),
              (common.mercury, 'gray'), (common.venus, 'gray80'),
              (common.mars, 'mistyrose'), (common.jupiter, 'gray90'),
              (common.saturn, 'gray70'), (common.uranus, 'gray'),
              (common.neptune, 'gray'), (common.pluto, 'gray'),
              ]
        self.ss = []
        for tup in ss:
            tgt, color = tup
            self.ss.append(tgt)
            tgt.color = color

        self.viewer = self.fitsimage
        self.dc = fv.get_draw_classes()
        canvas = self.dc.DrawingCanvas()
        canvas.set_surface(self.fitsimage)
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

        captions = (('OPE Path', 'entryset'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b
        # TEMP
        proc_dir = os.path.join(os.environ['HOME'], 'Procedure')
        b.ope_path.set_text(proc_dir)

        top.add_widget(w, stretch=0)
        b.ope_path.add_callback('activated', self.ope_set_cb)

        self.w.tgt_tbl = Widgets.TreeView(auto_expand=True,
                                          selection='multiple',
                                          sortable=True,
                                          use_alt_row_color=True)
        self.w.tgt_tbl.setup_table(self.columns, 1, 'name')
        top.add_widget(self.w.tgt_tbl, stretch=1)

        self.w.tgt_tbl.add_callback('selected', self.target_selection_cb)

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
        # btn.add_callback('activated', lambda w: self.help())
        btns.add_widget(btn, stretch=0)
        btns.add_widget(Widgets.Label(''), stretch=1)

        top.add_widget(btns, stretch=0)

        container.add_widget(top, stretch=1)
        self.gui_up = True

    def close(self):
        self.fv.stop_local_plugin(self.chname, str(self))
        return True

    def start(self):
        # insert canvas, if not already
        p_canvas = self.fitsimage.get_canvas()
        if self.canvas not in p_canvas:
            # Add our canvas
            p_canvas.add(self.canvas)

        self.canvas.delete_all_objects()

        self.initialize_plot()

        self.resume()

    def pause(self):
        self.canvas.ui_set_active(False)

    def resume(self):
        self.canvas.ui_set_active(True, viewer=self.viewer)

    def stop(self):
        self.gui_up = False
        # remove the canvas from the image
        p_canvas = self.fitsimage.get_canvas()
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

    def filter_targets(self, tgt_info_lst):
        if self.plot_which == 'all':
            shown_tgt_lst = tgt_info_lst
        elif self.plot_which == 'selected':
            shown_tgt_lst = [res for res in tgt_info_lst
                             if res.tgt.name in self.selected]

        return shown_tgt_lst

    def plot_targets(self, tgt_info_lst, tag, start_time=None):
        """Plot targets.
        """
        if start_time is None:
            start_time = self.get_datetime()
        self.canvas.delete_object_by_tag(tag)

        # filter the subset desired to be seen
        if tag != 'ss':
            tgt_info_lst = self.filter_targets(tgt_info_lst)

        objs = []
        for res in tgt_info_lst:
            alpha = 1.0 if res.info.alt_deg > 0 else 0.0
            t, r = self.map_azalt(res.info.az_deg, res.info.alt_deg)
            x, y = self.p2r(r, t)
            objs.append(self.dc.Point(x, y, radius=3, style='cross',
                                      color=res.color, fillcolor=res.color,
                                      linewidth=2, alpha=alpha,
                                      fill=True, fillalpha=alpha))
            objs.append(self.dc.Text(x, y, res.tgt.name,
                                     color=res.color, alpha=alpha,
                                     fontscale=True,
                                     fontsize=None, fontsize_min=12))

        o = self.dc.CompoundObject(*objs)
        self.canvas.add(o, tag=tag, redraw=False)

        self.canvas.update_canvas(whence=3)

        if tag == 'ss':
            # don't plot visibility of solar system objects in Visibility
            return
        targets = [res.tgt for res in tgt_info_lst]
        obj = self.channel.opmon.get_plugin('Visibility')
        #obj.plot_targets(start_time, self.site, targets,
        #                 timezone=self.cur_tz)
        obj.plot_targets(start_time, self.site, targets)

    def update_targets(self, tgt_info_lst, tag, start_time=None):
        """Update targets already plotted with new positions.
        """
        self.canvas.delete_object_by_tag(tag)
        if not self.canvas.has_tag(tag):
            self.plot_targets(tgt_info_lst, tag, start_time=start_time)
            return
        if start_time is None:
            start_time = self.get_datetime()

        if tag != 'ss':
            # filter the subset desired to be seen
            tgt_info_lst = self.filter_targets(tgt_info_lst)

        obj = self.canvas.get_object_by_tag(tag)
        objs = obj.objects
        i = 0
        for res in tgt_info_lst:
            alpha = 1.0 if res.info.alt_deg > 0 else 0.0
            t, r = self.map_azalt(res.info.az_deg, res.info.alt_deg)
            x, y = self.p2r(r, t)
            point, text = objs[i], objs[i + i]
            point.x, point.y, point.alpha, point.fillalpha = x, y, alpha, alpha
            text.x, text.y, text.alpha = x, y, alpha
            i += 2

        self.canvas.update_canvas(whence=3)

        if tag == 'ss':
            # don't plot visibility of solar system objects in Visibility
            return
        targets = [res.tgt for res in tgt_info_lst]
        obj = self.channel.opmon.get_plugin('Visibility')
        # obj.plot_targets(start_time, self.site, targets,
        #                  timezone=self.cur_tz)
        obj.plot_targets(start_time, self.site, targets)

    def update_all(self, start_time=None):
        if start_time is None:
            start_time = self.get_datetime()
        self.logger.info("update time: {}".format(start_time.strftime("%Y-%m-%d %H:%M:%S [%z]")))
        # get full information about all targets
        self.tgt_info_lst = [self.get_tgt_info(tgt, self.site, start_time,
                                               # color=self.colors[i % len(self.colors)])
                                               color='green2')
                             for i, tgt in enumerate(self.target_list)]

        # update the target table
        if self.gui_up:
            self.targets_to_table(self.tgt_info_lst)

        self.update_targets(self.tgt_info_lst, 'targets', start_time=start_time)

        if self.plot_ss_objects:
            self.ss_info_lst = [self.get_tgt_info(tgt, self.site, start_time)
                                for tgt in self.ss]
        else:
            self.ss_info_lst = []
        self.update_targets(self.ss_info_lst, 'ss', start_time=start_time)

    def update_plots(self):
        self.update_targets(self.tgt_info_lst, 'targets')
        self.update_targets(self.ss_info_lst, 'ss')

    def time_changed_cb(self, cb, time_utc, cur_tz):
        old_dt_utc = self.dt_utc
        self.dt_utc = time_utc
        self.cur_tz = cur_tz

        if (abs((self.dt_utc - old_dt_utc).total_seconds()) >
            self.settings.get('targets_update_interval')):
            self.update_all()

    def ope_set_cb(self, w):
        file_path = w.get_text().strip()
        if file_path.lower().endswith(".ope"):
            self.process_ope_file_for_targets(file_path)
        else:
            self.process_csv_file_for_targets(file_path)

    def process_ope_file_for_targets(self, ope_path):
        if not have_oscript:
            self.fv.show_error("Please install the 'oscript' module to use this feature")

        proc_home = os.path.join(os.environ['HOME'], 'Procedure')
        prm_dirs = [proc_home, os.path.join(proc_home, 'COMMON'),
                    os.path.join(ginga_home, 'prm')]

        # read OPE file
        with open(ope_path, 'r') as in_f:
            ope_buf = in_f.read()

        # gather target info from OPE
        tgt_list = ope.get_targets(ope_buf, prm_dirs)

        # process into QPlan Target object list
        self.target_list = process_tgt_list(tgt_list)

        # update GUIs
        self.update_all()

    def process_csv_file_for_targets(self, csv_path):
        # read CSV file
        tgt_list = []
        with open(csv_path, newline='') as csv_f:
            reader = csv.DictReader(csv_f, delimiter=',', quotechar='"')
            for row in reader:
                tgt_list.append(StaticTarget(name=row.get('Target Name', 'none'),
                                             # ra=hmsStrToDeg(row['RA']),
                                             # dec=dmsStrToDeg(row['DEC']),
                                             ra=row['RA'],
                                             dec=row['DEC'],
                                             equinox=float(row['Equinox']),
                                             comment=row.get('comment', '')))

        self.target_list = tgt_list

        # update GUIs
        self.update_all()

    def get_tgt_info(self, tgt, site, start_time, color='violet'):
        # TODO: work with self.site directly, not observer
        info = tgt.calc(site.observer, start_time)
        color = getattr(tgt, 'color', color)
        res = Bunch.Bunch(tgt=tgt, info=info, color=color)
        return res

    def targets_to_table(self, target_info):
        tree_dict = OrderedDict()
        for res in target_info:
            selected = res.tgt.name in self.selected
            # NOTE: AZ values are normalized to standard use
            az_deg = self.site.norm_to_az(res.info.az_deg)
            tree_dict[res.tgt.name] = Bunch.Bunch(
                selected='*' if selected else '',
                name=res.tgt.name,
                ra=res.tgt.ra,
                dec=res.tgt.dec,
                equinox=("%.1f" % res.tgt.equinox),
                az_deg=("%d" % int(round(az_deg))),
                alt_deg=("%d" % int(round(res.info.alt_deg))),
                parang_deg=("%.2f" % np.degrees(res.info.pang)),
                ha=("%.2f" % res.info.ha),
                airmass=("%.2f" % res.info.airmass),
                moon_sep=("%.2f" % res.info.moon_sep),
                comment=res.tgt.comment)
        self.w.tgt_tbl.set_tree(tree_dict)
        self.w.tgt_tbl.set_optimal_column_widths()

    def target_selection_update(self):
        self.targets_to_table(self.tgt_info_lst)
        self.clear_plot()
        self.update_plots()

    def target_selection_cb(self, w, sel_dct):
        self._update_selection_buttons()

    def select_cb(self, w):
        sel_dct = self.w.tgt_tbl.get_selected()
        self.selected = self.selected.union(set(sel_dct.keys()))
        self.target_selection_update()
        self._update_selection_buttons()

    def unselect_cb(self, w):
        sel_dct = self.w.tgt_tbl.get_selected()
        self.selected = self.selected.difference(set(sel_dct.keys()))
        self.target_selection_update()
        self._update_selection_buttons()

    def select_all_cb(self, w):
        self.selected = set([res.tgt.name for res in self.tgt_info_lst])
        self.target_selection_update()
        self._update_selection_buttons()

    def unselect_all_cb(self, w):
        self.selected = set([])
        self.target_selection_update()
        self._update_selection_buttons()

    def _update_selection_buttons(self):
        # enable or disable the selection buttons as needed
        sel_dct = self.w.tgt_tbl.get_selected()
        keys = set(sel_dct.keys())
        self.w.btn_select.set_enabled(len(keys - self.selected) > 0)
        self.w.btn_unselect.set_enabled(len(keys & self.selected) > 0)
        # all_keys = set([res.tgt.name for res in self.tgt_info_lst])
        # self.w.btn_select_all.set_enabled(len(self.selected) <
        #                                   len(self.tgt_info_lst))
        # self.w.btn_unselect_all.set_enabled(len(self.selected) > 0)

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
        #return self.dt_utc.astimezone(self.site.observer.tz_local)
        #return self.dt_utc.astimezone(self.cur_tz)
        return self.dt_utc

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


def process_tgt_list(tgt_list):
    return [StaticTarget(name=objname,
                         ra=ra_deg_to_str(funkyHMStoDeg(ra_str),
                                          format='%02d:%02d:%02d.%03d'),
                         dec=dec_deg_to_str(funkyDMStoDeg(dec_str),
                                            format='%s%02d:%02d:%02d.%02d'),
                         equinox=float(eq_str),
                         comment=tgtname)
            for (tgtname, objname, ra_str, dec_str, eq_str) in tgt_list]


def get_info_tgt_list(tgt_list, site, start_time, color='violet'):
    results = []
    for tgt in tgt_list:
        info = tgt.calc(site, start_time)
        clr = getattr(tgt, 'color', color)
        if info.alt_deg > 0:
            # NOTE: AZ values are normalized to standard use (0 deg = North)
            results.append((info.az_deg, info.alt_deg, tgt.name, clr))
    return results
