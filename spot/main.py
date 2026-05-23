#
# spot -- Site Planning and Observation Tool
#
import sys
import os
import threading

if 'CONFHOME' in os.environ:
    spot_home = os.path.join(os.environ['CONFHOME'], 'spot')
else:
    spot_home = os.path.join(os.path.expanduser('~'), '.spot')

from ginga.util import paths
paths.set_home(spot_home)
import ginga.rv.main as g_main
from ginga.misc.Bunch import Bunch
from ginga.misc import Settings
from ginga.misc import log

import spot.plugins
import spot.icons

icondir = os.path.split(spot.icons.__file__)[0]
paths.set_icon(os.path.join(icondir, "spot.svg"))

default_layout = ['seq', {},
                   ['vbox', dict(name='top', width=1400, height=750),  # noqa
                    dict(row=['ws', dict(name='menubar', wstype='stack',
                                         group=99)],
                         stretch=0),
                    dict(row=['hpanel', dict(name='hpnl'),
                     ['vbox', dict(name='main', width=600),
                      dict(row=['ws', dict(name='channels', wstype='tabs',
                                           group=1, use_toolbar=False,
                                           default=True),
                                 ],
                           stretch=1),
                      # dict(row=['ws', dict(name='cbar', wstype='stack',
                      #                      group=99)], stretch=0),
                      dict(row=['ws', dict(name='readout', wstype='stack',
                                           group=99)], stretch=0),
                      dict(row=['ws', dict(name='operations', wstype='stack',
                                           group=99)], stretch=0),
                      ],
                     ['ws', dict(name='right', wstype='tabs',
                                 width=400, height=-1, group=2),
                      # (tabname, layout), ...
                      [("Dialogs", ['ws', dict(name='dialogs', wstype='tabs',
                                               group=2),
                                    ]
                        ),
                       ("Control", ['vpanel', {},
                                    ['ws', dict(name='uright', wstype='stack',
                                                height=250, group=3)],
                                    ['ws', dict(name='mright', wstype='stack',
                                                height=250, group=3)],
                                    ['ws', dict(name='lright', wstype='stack',
                                                height=250, group=3)],
                                    ]
                        ),
                       ],
                      ],
                     ], stretch=1),  # noqa
                    dict(row=['ws', dict(name='toolbar', wstype='stack',
                                         height=40, group=2)],
                         stretch=0),
                    dict(row=['hbox', dict(name='status')], stretch=0),
                    ]]


class SPOT(g_main.ReferenceViewer):

    def __init__(self, layout=default_layout, plugins=None, appname='spot',
                 basedir=spot_home, channels=None):
        super().__init__(layout=layout, plugins=plugins, appname=appname,
                         basedir=basedir, channels=channels)

    def setup(self):
        from astropy.utils import iers
        # Turn off auto download
        iers.conf.auto_download = False
        # Optional: Set to None if you want to allow older IERS data without warning
        iers.conf.auto_max_age = None

        # Tweak the sys.path here if you are loading plugins from some
        # special area
        pluginHome = os.path.split(sys.modules['spot.plugins'].__file__)[0]
        sys.path.insert(0, pluginHome)

        # add SPOT plugins
        for spec in [
            Bunch(module='SPOTMenubar', ptype='global', workspace='menubar',
                  category="System", hidden=True, start=True, enabled=True),
            Bunch(module='SPOTToolbar', ptype='global', workspace='toolbar',
                  category="System", hidden=True, start=True, enabled=True),
            Bunch(module='SPOTToolbar', klass='SPOTToolbar_Ginga_Image',
                  hidden=True, category='System', ptype='local',
                  enabled=True, exclusive=False),
            Bunch(module='CPanel', ptype='global', workspace='uright',
                  category="System", tab='CPanel',
                  start=True, enabled=True, hidden=True),
            Bunch(module='SiteSelector', ptype='local', workspace='dialogs',
                  category="Planning", menu="Site Selector", tab='Site',
                  ch_sfx='_TGTS', index=0.0, enabled=True, exclusive=False),
            Bunch(module='PolarSky', ptype='local', workspace='dialogs',
                  category="Planning", menu="PolarSky", tab='PolarSky',
                  ch_sfx='_TGTS', index=1.0, enabled=True, exclusive=False),
            Bunch(module='Targets', ptype='local', workspace='channels',
                  category="Planning", menu="Target List", tab='Targets',
                  ch_sfx='_TGTS', index=2.0, enabled=True, exclusive=False),
            Bunch(module='Visibility', ptype='local', workspace='channels',
                  category="Planning", menu="Visibility Plot", tab='Visibility',
                  ch_sfx='_TGTS', index=3.0, enabled=True, exclusive=False),
            Bunch(module='SkyCam', ptype='local', workspace='dialogs',
                  category="Planning", menu="Sky Cams", tab='SkyCam',
                  ch_sfx='_TGTS', index=4.0, enabled=True, exclusive=False),
            Bunch(module='TargetGenerator', ptype='local', workspace='channels',
                  category="Planning", menu="Target Generator", tab='TargetGen',
                  ch_sfx='_TGTS', index=5.0, enabled=True, exclusive=False),
            Bunch(module='TelescopePosition', ptype='local', workspace='channels',
                  category="Planning", menu="Telescope Position", tab='TelPos',
                  ch_sfx='_TGTS', index=6.0, enabled=False, exclusive=False),
            Bunch(module='LGS', ptype='local', workspace='channels',
                  category="Planning", menu="LGS", tab='LGS',
                  ch_sfx='_TGTS', index=7.0, enabled=False, exclusive=True),
            Bunch(module='FindImage', ptype='local', workspace='dialogs',
                  category="Planning", menu="Finding Chart", tab='FindImage',
                  ch_sfx='_FIND', index=10.0, enabled=True, exclusive=False),
            Bunch(module='InsFov', ptype='local', workspace='dialogs',
                  category="Planning", menu="Instrument FOV", tab='InsFov',
                  ch_sfx='_FIND', index=11.0, enabled=True, exclusive=False),
        ]:
            self.add_plugin_spec(spec)

        # Bring in Ginga plugins that may be useful in SPOT
        for modname, remap in [('Operations', dict(workspace='operations')),
                               # ('Colorbar', dict(workspace='colorbar')),
                               ('Cursor', dict(workspace='readout')),
                               ('Errors', dict(workspace='right')),
                               ('Downloads', dict(workspace='dialogs', start=True)),
                               ('Command', dict(workspace='dialogs')),
                               ('Log', dict(workspace='right')),
                               ('ScreenShot', dict(workspace='dialogs')),
                               ('ColorMapPicker', dict(workspace='dialogs')),
                               ('Histogram', dict(workspace='dialogs')),
                               ('Ruler', dict(workspace='dialogs')),
                               ('Preferences', dict(workspace='dialogs')),
                               ('FBrowser', dict(workspace='dialogs')),
                               ('Pan', dict(workspace='mright', start=False,
                                            category='Utils', hidden=False)),
                               ('Zoom', dict(workspace='lright', start=False,
                                             category='Utils', hidden=False)),
                               ('Header', dict(workspace='dialogs')),
                               ('LoaderConfig', dict(workspace='channels')),
                               ('PluginConfig', dict(workspace='channels'))]:
            specs = g_main.get_plugin_spec(module=modname)
            spec = specs[0]
            # remap to SPOT
            spec.update(remap)
            self.add_plugin_spec(spec)

        return super().setup()

    def process_args(self, args):
        pass

    def main(self, options, args):
        logname = self.appname.lower().replace(' ', '_')

        # create a logger
        self.logger = log.get_logger(name=logname, options=options)
        self.ev_quit = threading.Event()

        if hasattr(options, 'basedir') and options.basedir is not None:
            # command line option overrules
            self.basedir = os.path.expanduser(options.basedir)
        if self.basedir is not None:
            # custom basedir
            paths.set_home(self.basedir)
        else:
            # stock ginga basedir
            self.basedir = paths.ginga_home

        # get settings (preferences)
        if not os.path.exists(self.basedir):
            try:
                os.mkdir(self.basedir)
            except OSError as e:
                self.logger.warning(
                    "Couldn't create %s settings area (%s): %s" % (
                        self.appname, self.basedir, str(e)))
                self.logger.warning("Preferences will not be able to be saved")

        # set up preferences
        self.prefs = Settings.Preferences(basefolder=self.basedir,
                                          logger=self.logger)

        # general settings control initialization of viewer
        settings = self.prefs.create_category('general')
        settings.set_defaults(appname=self.appname,
                              useMatplotlibColormaps=False,
                              widgetSet='choose',
                              # this is only used with the PG widgets
                              # backend
                              http_server=True,
                              min_threads=2,
                              num_threads=max(os.cpu_count(), 10),
                              threadpool_analyze_interval_sec=None,
                              icc_working_profile=None,
                              font_scaling_factor=None,
                              use_opengl=False,
                              plugin_file='plugins.yml',
                              channel_prefix="Image")
        settings.load(onError='silent')
        self.settings = settings

        settings.set(title="SPOT (Site Planning and Observation Tool)",
                     WCSpkg='astropy', FITSpkg='astropy',
                     suppress_fits_warnings=False,
                     recursion_limit=10000,
                     pluginmgr_allow_nonsingletons=False,
                     ignore_saved_layout=True,
                     save_layout=False,
                     channels=[])
        # ------ command line overrides for various settings -----
        #
        if hasattr(options, 'toolkit') and options.toolkit is not None:
            settings.set(widgetSet=options.toolkit)

        # did user specify a particular geometry?
        if hasattr(options, 'geometry') and options.geometry is not None:
            settings.set(geometry=options.geometry)

        if (hasattr(options, 'disable_plugins') and
            options.disable_plugins is not None):
            settings.set(disable_plugins=options.disable_plugins)

        # --------------------------------------------------------
        self.setup()

        # process non-option command line args
        self.process_args(args)

        # run the app event loop
        self.run()
