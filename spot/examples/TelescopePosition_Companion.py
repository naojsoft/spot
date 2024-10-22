"""
TelescopePosition_Companion.py -- Get status information from your telescope

This is a plugin template that can be modified to provide status information
from your telescope to be able to use the "TelescopePosition" plugin in SPOT.

Requirements
============
Be able to connect to your status system and populate some values.

Usage
=====
Put this module in your $HOME/.spot/plugins folder.  Add the appropriate
plugin_TelescopePosition_Companion.cfg file to $HOME/.spot (if needed,
see below).

Run with spot like this:

spot --loglevel=20 --stderr --modules=TelescopePosition_Companion

Once satisfied that things are working, you can add a line to your
$HOME/.spot/general.cfg like so:

    global_plugins = "TelescopePosition_Companion"

and it will be automatically started without having to specify --modules.
"""
# ginga
from ginga import GingaPlugin

# local
from spot.util import sites


class TelescopePosition_Companion(GingaPlugin.GlobalPlugin):

    def __init__(self, fv):
        super().__init__(fv)

        # get preferences from plugin configuration file
        # for example, you can put settings in there that are needed to
        # connect to a status system.  That file should be placed in
        # $HOME/.spot ("plugin_TelescopePosition_Companion.cfg")
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_TelescopePosition_Companion')
        self.settings.add_defaults(status_update_interval=5.0)
        self.settings.load(onError='silent')

        # change this to the short name for your site as known in
        # spot.util.sites--they must match!
        self.site_name = 'Yoursite'

        # These are the values you need to update!
        self.status_dict = dict(
            az_deg=0.0,               # current telescope azimuth in deg
            az_cmd_deg=0.0,           # current target azimuth in deg
            az_diff_deg=0.0,          # diff between target az and cmd az
            alt_deg=90.0,             # current telescope elevation in deg
            alt_cmd_deg=90.0,         # current target elevation in deg
            alt_diff_deg=0.0,         # diff between target el and cmd el
            ra_deg=0.0,               # current telescope RA in deg
            ra_cmd_deg=0.0,           # current target RA in deg
            equinox=2000.0,           # ref equinox for telescope coords
            dec_deg=0.0,              # current telescope DEC in deg
            dec_cmd_deg=0.0,          # current target DEC in deg
            cmd_equinox=2000.0,       # ref equinox for target coords
            slew_time_sec=0.0,        # slew time in sec to target
            rot_deg=0.0,              # current rotator position in deg
            rot_cmd_deg=0.0,          # rotator commanded position in deg
            tel_status='Pointing',    # current telescope status string
        )

        # timer that will get called periodically to update status
        # (every `status_update_interval` seconds)
        self.tmr = self.fv.make_timer()
        self.tmr.add_callback('expired', self.update_timer_cb)

    def close(self):
        self.fv.stop_global_plugin(str(self))
        return True

    def start(self):
        # Called right after build_gui()
        # Do any one-time initialization here that you need to
        # ...

        # start the timer
        self.update_timer_cb(self.tmr)

    def stop(self):
        # Called when the program exits
        # Do any necessary clean up for the plugin here
        pass

    def get_status(self):
        # IMPORTANT: Here fetch your status and update self.status_dict
        # with any changed values
        # ...

        # update the site status variables
        site_obj = None
        try:
            # NOTE: we have this in a try/except clause because this
            # timer update may be run before the sites are fully configured
            # by a SiteSelector plugin, so quietly abandon any update of
            # the site status until we get a valid site object
            site_obj = sites.get_site(self.site_name)
        except KeyError:
            return

        site_obj.update_status(self.status_dict)

    def update_timer_cb(self, timer):
        # restart the timer
        timer.start(duration=self.settings['status_update_interval'])

        self.get_status()

    def __str__(self):
        return 'telescopeposition_companion'
