# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.txt for details.
"""
``SPOTToolbar`` provides a set of convenience UI controls.

**Plugin Type: Global**

``SPOTToolbar`` is a global plugin.  Only one instance can be opened.

**Usage**

Hovering over an icon on the toolbar should provide you with usage tool tip.

"""
from ginga.rv.plugins.Toolbar import Toolbar, Toolbar_Ginga_Image

__all__ = ['SPOTToolbar', 'SPOTToolbar_Ginga_Image']


class SPOTToolbar(Toolbar):

    def __init__(self, fv):
        # superclass defines some variables for us, like logger
        super().__init__(fv)

        self.opname_prefix = 'SPOTToolbar_'

    def __str__(self):
        return 'spottoolbar'


class SPOTToolbar_Ginga_Image(Toolbar_Ginga_Image):

    def __init__(self, fv, chviewer):
        # superclass defines some variables for us, like logger
        super().__init__(fv, chviewer)

        self.layout = [
            # (Name, type, icon, tooltip)
            ("FlipX", 'toggle', 'flip_x', "Flip image in X axis",
             self.flipx_cb),
            ("FlipY", 'toggle', 'flip_y', "Flip image in Y axis",
             self.flipy_cb),
            ("SwapXY", 'toggle', 'swap_xy', "Swap X and Y axes",
             self.swapxy_cb),
            ("---",),
            ("Rot90", 'button', 'rot90ccw', "Rotate image 90 deg",
             self.rot90_cb),
            ("RotN90", 'button', 'rot90cw', "Rotate image -90 deg",
             self.rotn90_cb),
            ("OrientRH", 'button', 'orient_nw', "Orient image N=Up E=Right",
             self.orient_rh_cb),
            ("OrientLH", 'button', 'orient_ne', "Orient image N=Up E=Left",
             self.orient_lh_cb),
            ("---",),
            ("Zoom In", 'button', 'zoom_in', "Zoom in",
             lambda w: self.fv.zoom_in()),
            ("Zoom Out", 'button', 'zoom_out', "Zoom out",
             lambda w: self.fv.zoom_out()),
            ("Zoom Fit", 'button', 'zoom_fit', "Zoom to fit window size",
             lambda w: self.fv.zoom_fit()),
            ("Zoom 1:1", 'button', 'zoom_100', "Zoom to 100% (1:1)",
             lambda w: self.fv.zoom_1_to_1()),
            ("---",),
            ("Pan", 'toggle', 'pan', "Pan with left, zoom with right",
             lambda w, tf: self.mode_cb(tf, 'pan')),
            ("Zoom", 'toggle', 'crosshair',
             "Left/right click zooms in/out;\n"
             "hold middle to pan freely over image",
             lambda w, tf: self.mode_cb(tf, 'zoom')),
            ("Rotate", 'toggle', 'rotate',
             "Drag left to rotate; click right to reset to 0 deg",
             lambda w, tf: self.mode_cb(tf, 'rotate')),
            ("Dist", 'toggle', 'sqrt',
             "Scroll to set color distribution algorithm",
             lambda w, tf: self.mode_cb(tf, 'dist')),
            ("CMap", 'toggle', 'palette',
             "Scroll to set color map",
             lambda w, tf: self.mode_cb(tf, 'cmap')),
            ("Cuts", 'toggle', 'cuts',
             "Left/right sets hi cut, up/down sets lo cut",
             lambda w, tf: self.mode_cb(tf, 'cuts')),
            ("Contrast", 'toggle', 'contrast',
             "Contrast/bias with left/right/up/down",
             lambda w, tf: self.mode_cb(tf, 'contrast')),
            ("ModeLock", 'toggle', 'lock',
             "Modes are oneshot or locked", self.set_locked_cb),
            ("---",),
            ("Center", 'button', 'center_image', "Center image",
             self.center_image_cb),
            ("Restore", 'button', 'reset_rotation',
             "Reset all transformations and rotations",
             self.reset_all_transforms_cb),
            ("AutoLevels", 'button', 'auto_cuts', "Auto cut levels",
             self.auto_levels_cb),
            ("ResetContrast", 'button', 'reset_contrast', "Reset contrast",
             self.reset_contrast_cb),
            ("---",),
            ("Preferences", 'button', 'settings', "Set channel preferences (in focused channel)",
             lambda w: self.start_local_plugin('Preferences')),
            # ("FBrowser", 'button', 'folder_open', "Open file (in focused channel)",
            #  lambda w: self.start_local_plugin('FBrowser')),
            # ("MultiDim", 'button', 'layers', "Select HDUs or cube slices (in focused channel)",
            #  lambda w: self.start_local_plugin('MultiDim')),
            ("Header", 'button', 'tags', "View image metadata (Header plugin)",
             lambda w: self.start_global_plugin('Header')),
            ("ZoomPlugin", 'button', 'microscope', "Magnify detail (Zoom plugin)",
             lambda w: self.start_global_plugin('Zoom'))]

    def __str__(self):
        return 'spottoolbar_ginga_image'
