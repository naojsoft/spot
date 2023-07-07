"""
Visibility.py -- Overlay objects on all sky camera

E. Jeschke

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
from datetime import timedelta

# ginga
from ginga.gw import Widgets, Plot
from ginga.misc import Bunch
from ginga import GingaPlugin

from qplan.plots.airmass import AirMassPlot


class Visibility(GingaPlugin.LocalPlugin):

    def __init__(self, fv, fitsimage):
        super().__init__(fv, fitsimage)

        # get preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_Visibility')
        self.settings.add_defaults(targets_update_interval=60.0)
        self.settings.load(onError='silent')

        self.gui_up = False

    def build_gui(self, container):

        top = Widgets.VBox()
        top.set_border_width(4)

        self.plot = AirMassPlot(700, 500, logger=self.logger)
        #obj = self.channel.opmon.get_plugin('Targets')
        #self.plot.colors = obj.colors

        plot_w = Plot.PlotWidget(self.plot, width=700, height=500)

        top.add_widget(plot_w, stretch=1)

        #top.add_widget(Widgets.Label(''), stretch=1)

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
        self.initialize_plot()

        # update our own plot by pinging Targets plugin
        obj = self.channel.opmon.get_plugin('Targets')
        if obj.gui_up:
            obj.update_plots()

    def stop(self):
        self.gui_up = False

    def redo(self):
        pass

    def initialize_plot(self):
        self.plot.setup()

    def clear_plot(self):
        self.plot.clear()

    def plot_targets(self, start_time, site, targets, timezone=None):
        """Plot targets.
        """
        if not self.gui_up:
            return
        # TODO: work with site object directly, not observer
        site = site.observer

        # calc noon on the day of observation in desired time zone
        if timezone is None:
            timezone = site.timezone
        ndate = start_time.astimezone(timezone).strftime("%Y-%m-%d") + " 12:00:00"
        noon_time = site.get_date(ndate, timezone=timezone)

        # plot period 15 minutes before sunset to 15 minutes after sunrise
        delta = 60*15
        start_time = site.sunset(noon_time) - timedelta(0, delta)
        stop_time = site.sunrise(start_time) + timedelta(0, delta)

        site.set_date(start_time)

        # make airmass plot
        num_tgts = len(targets)
        target_data = []
        lengths = []
        if num_tgts > 0:
            for tgt in targets:
                info_list = site.get_target_info(tgt)
                target_data.append(Bunch.Bunch(history=info_list,
                                               target=tgt))
                lengths.append(len(info_list))

        # clip all arrays to same length
        min_len = 0
        if len(lengths) > 0:
            min_len = min(lengths)
        for il in target_data:
            il.history = il.history[:min_len]

        self.clear_plot()

        if num_tgts == 0:
            self.logger.debug("no targets for plotting airmass")
        else:
            self.logger.debug("plotting airmass")

            # Plot a subset of the targets
            #idx = int((self.controller.idx_tgt_plots / 100.0) * len(target_data))
            #num_tgts = self.controller.num_tgt_plots
            #target_data = target_data[idx:idx+num_tgts]

            self.fv.error_wrap(self.plot.plot_altitude, site,
                               target_data, timezone,
                               plot_moon_distance=True,
                               show_target_legend=False)
        self.fv.error_wrap(self.plot.draw)

    def __str__(self):
        return 'visibility'
