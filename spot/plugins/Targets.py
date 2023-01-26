"""
Targets.py -- Overlay objects on all sky camera

E. Jeschke

Requirements
============
python packages
---------------

naojsoft packages
-----------------
- g2cam
- ginga
- qplan
- oscript
"""
# stdlib
import sys
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
from qplan.util.calcpos import Observer
from qplan.entity import StaticTarget

# oscript
from oscript.parse import ope
from oscript.util.ope import funkyHMStoDeg, funkyDMStoDeg


class Targets(GingaPlugin.LocalPlugin):

    def __init__(self, fv, fitsimage):
        super().__init__(fv, fitsimage)

        # get preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_Targets')
        self.settings.add_defaults(targets_update_interval=60.0)
        self.settings.load(onError='silent')

        self.site = Observer('Subaru',
                             longitude='-155:28:48.900',
                             latitude='+19:49:42.600',
                             elevation=4163,
                             pressure=615,
                             temperature=0,
                             timezone=tz.gettz('US/Hawaii'))

        self.colors = ['red', 'blue', 'green', 'cyan', 'magenta', 'yellow']
        self.base_circ = None
        self.target_list = []
        self.plot_which = 'all'
        self.selected = []
        self.cur_tz = tz.gettz('US/Hawaii')
        self.dt_utc = datetime.utcnow().replace(tzinfo=tz.UTC)

        self.columns = [('Name', 'name'),
                        ('AM', 'airmass'),
                        ('Az', 'az_deg'),
                        ('Alt', 'alt_deg'),
                        ('HA', 'ha'),
                        #('Slew', 'slew'),
                        #('AD', 'ad'),
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

        top = Widgets.VBox()
        top.set_border_width(4)

        captions = (('OPE Path', 'entryset'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b
        # TEMP
        b.ope_path.set_text("/home/eric/Procedure/stafftime_20220914.ope")

        top.add_widget(w, stretch=0)
        b.ope_path.add_callback('activated', self.ope_set_cb)

        #top.add_widget(Widgets.Label(''), stretch=1)
        self.w.tgt_tbl = Widgets.TreeView(auto_expand=True,
                                          selection='multiple',
                                          sortable=True,
                                          use_alt_row_color=True)
        self.w.tgt_tbl.setup_table(self.columns, 1, 'name')
        top.add_widget(self.w.tgt_tbl, stretch=1)

        self.w.tgt_tbl.add_callback('selected', self.target_selection_cb)
        #self.w.tgt_tbl.add_callback('activated', self.target_activated_cb)

        captions = (("Time mode:", 'llabel', "mode", 'combobox',
                     "Time zone:", 'llabel', 'timezone', 'entryset',
                     "Date time:", 'llabel', 'datetime', 'entryset'),
                    ("Plot:", 'label', 'plot', 'combobox'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)

        for name in 'Now', 'Fixed':
            b.mode.append_text(name)
        b.mode.set_index(0)
        b.mode.set_tooltip("Now or fixed time for visibility calculations")
        b.mode.add_callback('activated', self.set_datetime_cb)
        b.timezone.set_text('HST')
        b.timezone.set_tooltip("Time zone to be used for visibility plot")
        b.timezone.add_callback('activated', self.set_timezone_cb)
        b.datetime.set_tooltip("Set date time for visibility calculations")
        b.datetime.add_callback('activated', self.set_datetime_cb)
        b.datetime.set_enabled(False)
        self.set_datetime_cb()

        for option in ['All', 'Selected']:
            b.plot.append_text(option)
        b.plot.add_callback('activated', self.configure_plot_cb)
        b.plot.set_tooltip("Choose what is plotted")

        top.add_widget(w, stretch=0)

        btns = Widgets.HBox()
        btns.set_border_width(4)
        btns.set_spacing(3)

        btn = Widgets.Button("Close")
        btn.add_callback('activated', lambda w: self.close())
        btns.add_widget(btn, stretch=0)
        btn = Widgets.Button("Help")
        #btn.add_callback('activated', lambda w: self.help())
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
        obj.plot_targets(start_time, self.site, targets,
                         timezone=self.cur_tz)


    def update_targets(self, tgt_info_lst, tag, start_time=None):
        """Update targets already plotted with new positions.
        """
        self.canvas.delete_object_by_tag(tag)
        if not self.canvas.has_tag(tag):
            self.plot_targets(tgt_info_lst, tag, start_time=start_time)
            return
        if start_time is None:
            start_time = self.get_datetime()

        # filter the subset desired to be seen
        tgt_info_lst = self.filter_targets(tgt_info_lst)

        obj = self.canvas.get_object_by_tag(tag)
        objs = obj.objects
        i = 0
        for res in tgt_info_lst:
            alpha = 1.0 if res.info.alt_deg > 0 else 0.0
            t, r = self.map_azalt(res.info.az_deg, res.info.alt_deg)
            x, y = self.p2r(r, t)
            #print(res.tgt.name, res.info.az_deg, res.info.alt_deg, r, t, x, y)
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
        obj.plot_targets(start_time, self.site, targets,
                         timezone=self.cur_tz)

    def update_all(self, start_time=None):
        if start_time is None:
            start_time = self.get_datetime()
        print("update time", start_time.strftime("%Y-%m-%d %H:%M:%S"))
        # get full information about all targets
        self.tgt_info_lst = [self.get_tgt_info(tgt, self.site, start_time,
                                               #color=self.colors[i % len(self.colors)])
                                               color='darkgreen')
                             for i, tgt in enumerate(self.target_list)]

        # update the target table
        if self.gui_up:
            self.targets_to_table(self.tgt_info_lst)

        self.update_targets(self.tgt_info_lst, 'targets', start_time=start_time)

        ss_info_lst = [self.get_tgt_info(tgt, self.site, start_time)
                       for tgt in self.ss]
        self.update_targets(ss_info_lst, 'ss', start_time=start_time)

    def update_plots(self):
        self.update_targets(self.tgt_info_lst, 'targets')

    # def update_tgt_timer_cb(self, timer, *args):
    #     timer.start()

    #     self.update_all()
    #     # restore selection in table, if any
    #     for name in self.selected:
    #         self.table.select_path([name])

    def ope_set_cb(self, w):
        file_path = w.get_text().strip()
        if file_path.lower().endswith(".ope"):
            self.process_ope_file_for_targets(file_path)
        else:
            self.process_csv_file_for_targets(file_path)

    def set_timezone_cb(self, *args):
        zone_str = self.w.timezone.get_text().strip()
        self.cur_tz = tz.gettz(zone_str)

        self.set_datetime_cb()

    def set_datetime_cb(self, *args):
        mode = self.w.mode.get_text().lower()
        if mode == 'now':
            self.dt_utc = datetime.utcnow().replace(tzinfo=tz.UTC)
            dt = self.dt_utc.astimezone(self.cur_tz)
            self.w.datetime.set_text(dt.strftime("%Y-%m-%d %H:%M:%S"))
            self.w.datetime.set_enabled(False)
        else:
            self.w.datetime.set_enabled(True)
            dt_str = self.w.datetime.get_text().strip()
            dt = parser.parse(dt_str).replace(tzinfo=self.cur_tz)
            self.dt_utc = dt.astimezone(tz.UTC)

        self.update_all()

    def process_ope_file_for_targets(self, ope_path):
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
        info = tgt.calc(site, start_time)
        clr = getattr(tgt, 'color', color)
        res = Bunch.Bunch(tgt=tgt, info=info, color=color)
        return res

    def targets_to_table(self, target_info):
        tree_dict = OrderedDict()
        for res in target_info:
            # NOTE: AZ values are normalized to standard use, NOT Subaru
            # so need to adjust putting into table
            az_deg = res.info.az_deg - 180.0
            tree_dict[res.tgt.name] = Bunch.Bunch(name=res.tgt.name,
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

    def target_selection_cb(self, tbl_w, sel_dct):
        self.selected = list(sel_dct.keys())
        self.clear_plot()
        self.update_plots()

    def configure_plot_cb(self, w, idx):
        option = w.get_text()
        self.plot_which = option.lower()
        self.clear_plot()
        self.update_plots()

    def get_datetime(self):
        #obj = self.channel.opmon.get_plugin('Settings')
        #return obj.get_datetime()
        return self.dt_utc.astimezone(self.site.timezone)

    def p2r(self, r, t):
        # TODO: take into account fisheye distortion
        t_rad = np.radians(t)

        #cx, cy = self.settings['image_center']
        cx, cy = 0.0, 0.0
        scale = self.get_scale()

        x = cx + r * np.cos(t_rad) * scale
        y = cy + r * np.sin(t_rad) * scale

        return (x, y)

    def r2xyr(self, r):
        # TODO: take into account fisheye distortion
        #cx, cy = self.settings['image_center']
        cx, cy = 0.0, 0.0
        r = r * self.get_scale()
        return (cx, cy, r)

    def get_scale(self):
        obj = self.channel.opmon.get_plugin('PolarSky')
        scale = obj.get_scale()
        return scale

    def map_azalt(self, az, alt):
        #az = subaru_normalize_az(az)
        return az + 90.0, 90.0 - alt

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
            # NOTE: AZ values are normalized to standard use, NOT Subaru
            results.append((info.az_deg, info.alt_deg, tgt.name, clr))
    return results

def subaru_normalize_az(az_deg):
    az_deg = az_deg + 180.0
    #az_deg = az_deg % 360.0
    if math.fabs(az_deg) >= 360.0:
        az_deg = math.fmod(az_deg, 360.0)
    if az_deg < 0.0:
        az_deg += 360.0

    return az_deg
