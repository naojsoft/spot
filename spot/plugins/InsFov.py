"""
InsFov.py -- Overlay FOV info on images

Requirements
============

naojsoft packages
-----------------
- ginga
"""
import numpy as np

# ginga
from ginga.gw import Widgets
from ginga import GingaPlugin, trcalc
from ginga.util import wcs
from ginga.canvas.coordmap import BaseMapper

# get all overlays
from spot.instruments import inst_dict


class InsFov(GingaPlugin.LocalPlugin):
    """TODO
    """
    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super().__init__(fv, fitsimage)

        # get FOV preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_InsFov')
        self.settings.add_defaults(sky_radius_arcmin=3)
        self.settings.load(onError='silent')

        self.viewer = self.fitsimage
        self.crdmap = UnRotatedDataMapper(self.viewer)
        self.viewer.set_coordmap('insfov', self.crdmap)
        self.viewer.add_callback('redraw', self.redraw_cb)

        self.dc = fv.get_draw_classes()
        canvas = self.dc.DrawingCanvas()
        canvas.crdmap = self.crdmap
        canvas.set_surface(self.viewer)
        self.canvas = canvas

        compass = self.dc.Compass(0.15, 0.15, 0.08,
                                  fontsize=14, coord='percentage',
                                  color='orange')
        self.canvas.add(compass, redraw=False)

        self.cur_fov = None
        self.xflip = False
        self.rot_deg = 0.0
        self.mount_offset_rot_deg = 0.0
        # user's chosen flip and PA
        self.flip = False
        self.pa_deg = 0.0
        self.gui_up = False

    def build_gui(self, container):

        top = Widgets.VBox()
        top.set_border_width(4)

        fr = Widgets.Frame("Instrument")

        captions = (('Instrument:', 'label', 'instrument', 'llabel',
                     'Choose', 'button'),
                    ('PA (deg):', 'label', 'pa', 'entryset',
                     'Flip', 'checkbox'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b

        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        # populate instrument overlays menu
        self.w.insmenu = Widgets.Menu()
        child = self.w.insmenu.add_name('None')
        child.add_callback('activated', self.select_inst_cb, 'None', 'None')
        for telname, fov_dct in inst_dict.items():
            menu = self.w.insmenu.add_menu(telname)
            for insname in fov_dct:
                child = menu.add_name(insname)
                child.add_callback('activated', self.select_inst_cb,
                                   telname, insname)
        b.instrument.set_text('None')
        b.choose.add_callback('activated',
                              lambda w: self.w.insmenu.popup(widget=w))
        b.choose.set_tooltip("Choose instrument overlay")

        b.pa.set_text("0.00")
        b.pa.add_callback('activated', self.set_pa_cb)
        b.pa.set_tooltip("Set desired position angle")
        b.flip.set_state(self.flip)
        b.flip.set_tooltip("Flip orientation")
        b.flip.add_callback("activated", self.toggle_flip_cb)

        fr = Widgets.Frame("Pointing")

        captions = (('RA:', 'label', 'ra', 'entry', 'DEC:', 'label',
                     'dec', 'entry'),
                    ('Equinox:', 'label', 'equinox', 'entry'),
                    )

        w, b = Widgets.build_info(captions)
        self.w.update(b)
        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        top.add_widget(Widgets.Label(''), stretch=1)

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
        # insert canvas, if not already
        p_canvas = self.viewer.get_canvas()
        if self.canvas not in p_canvas:
            p_canvas.add(self.canvas)
        self.canvas.ui_set_active(False)

        self.redo()

    def stop(self):
        self.gui_up = False
        # remove the canvas from the image
        p_canvas = self.viewer.get_canvas()
        p_canvas.delete_object(self.canvas)

    def redo(self):
        """This is called when a new image arrives or the data in the
        existing image changes.
        """
        if not self.gui_up:
            return
        image = self.viewer.get_image()
        if image is None:
            return
        header = image.get_header()
        rot, scale = wcs.get_xy_rotation_and_scale(header)
        scale_x, scale_y = scale

        # rot_x, rot_y = rot
        # # the image rotation necessary to show 0 deg position angle
        # self.rot_deg = np.mean((rot_x, rot_y))
        xflip, rot_deg = self.calc_ang(image, righthand=self.flip)
        self.xflip = xflip
        self.rot_deg = rot_deg

        if self.flip:
            img_rot_deg = self.rot_deg - self.mount_offset_rot_deg + self.pa_deg
        else:
            img_rot_deg = self.rot_deg + self.mount_offset_rot_deg - self.pa_deg
        # adjust image flip and rotation for desired position angle
        self.viewer.transform(xflip, False, False)
        self.viewer.rotate(img_rot_deg)

        if self.cur_fov is not None:
            self.cur_fov.set_scale(scale_x, scale_y)

            self.viewer.redraw(whence=3)

    def select_inst_cb(self, w, telname, insname):
        with self.viewer.suppress_redraw:
            # changing instrument: remove old FOV
            if self.cur_fov is not None:
                self.cur_fov.remove()

            if telname == 'None':
                # 'None' selected
                self.cur_fov = None
                self.mount_offset_rot_deg = 0.0
                self.w.instrument.set_text(telname)
            else:
                klass = inst_dict[telname][insname]
                pt = self.viewer.get_pan(coord='data')
                self.cur_fov = klass(self.canvas, pt[:2])
                self.w.instrument.set_text(f"{telname}/{insname}")
                self.mount_offset_rot_deg = self.cur_fov.mount_offset_rot_deg

                # this should change the size setting in FindImage
                self.settings.set(sky_radius_arcmin=self.cur_fov.sky_radius_arcmin)

            self.redo()

    def set_pa_cb(self, w):
        self.pa_deg = float(w.get_text().strip())
        self.redo()

    def toggle_flip_cb(self, w, tf):
        self.flip = tf
        self.redo()

    def redraw_cb(self, viewer, whence):
        if not self.gui_up or whence >= 3:
            return
        # check pan location
        pos = viewer.get_pan(coord='data')[:2]
        if self.cur_fov is not None:
            self.cur_fov.set_pos(pos)

        data_x, data_y = pos[:2]
        image = viewer.get_image()
        if image is not None:
            ra_deg, dec_deg = image.pixtoradec(data_x, data_y)
            ra_str = wcs.ra_deg_to_str(ra_deg)
            dec_str = wcs.dec_deg_to_str(dec_deg)
            self.w.ra.set_text(ra_str)
            self.w.dec.set_text(dec_str)
            header = image.get_header()
            self.w.equinox.set_text(str(header.get('EQUINOX', '')))

        img_rot_deg = viewer.get_rotation()
        if not self.flip:
            pa_deg = self.rot_deg + self.mount_offset_rot_deg - img_rot_deg
        else:
            pa_deg = -self.rot_deg + self.mount_offset_rot_deg + img_rot_deg
        self.logger.info(f"PA is now {pa_deg} deg")
        self.w.pa.set_text("%.2f" % (pa_deg))
        self.pa_deg = pa_deg

    def calc_ang(self, image, righthand=False):
        data_x, data_y = self.viewer.get_pan(coord='data')[:2]
        (x, y, xn, yn, xe, ye) = wcs.calc_compass(image, data_x, data_y,
                                                  1.0, 1.0)
        degn = np.degrees(np.arctan2(xn - x, yn - y))
        self.logger.info("degn=%f xe=%f ye=%f" % (
            degn, xe, ye))
        # rotate east point also by degn
        xe2, ye2 = trcalc.rotate_pt(xe, ye, degn, xoff=x, yoff=y)
        dege = np.degrees(np.arctan2(xe2 - x, ye2 - y))
        self.logger.info("dege=%f xe2=%f ye2=%f" % (
            dege, xe2, ye2))

        # if right-hand image, flip it to make left hand
        xflip = righthand
        if dege > 0.0:
            xflip = not xflip
        if xflip:
            degn = - degn

        return (xflip, degn)

    def __str__(self):
        return 'insfov'


class FOV:
    def __init__(self, canvas, pt):
        super().__init__()

        self.canvas = canvas
        self.dc = canvas.get_draw_classes()

        self.mount_offset_rot_deg = 0.0

    def set_pos(self, pt):
        pass

    def remove(self):
        pass


class UnRotatedDataMapper(BaseMapper):
    """A coordinate mapper that maps to the viewer in data coordinates.
    """
    def __init__(self, viewer):
        super().__init__()
        trcat = viewer.trcat
        self.tr = (trcat.DataCartesianTransform(viewer) +
                   trcat.InvertedTransform(trcat.RotationFlipTransform(viewer)) +
                   trcat.InvertedTransform(trcat.DataCartesianTransform(viewer)))
        self.viewer = viewer

    def to_data(self, crt_pts, viewer=None):
        crt_arr = np.asarray(crt_pts)
        return self.tr.to_(crt_arr)

    def data_to(self, data_pts, viewer=None):
        data_arr = np.asarray(data_pts)
        return self.tr.from_(data_arr)

    def offset_pt(self, pts, offset):
        return np.add(pts, offset)

    def rotate_pt(self, pts, theta, offset):
        x, y = np.asarray(pts).T
        xoff, yoff = np.transpose(offset)
        rot_x, rot_y = trcalc.rotate_pt(x, y, theta, xoff=xoff, yoff=yoff)
        return np.asarray((rot_x, rot_y)).T
