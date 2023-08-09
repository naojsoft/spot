"""
InsFov.py -- Overlay FOV info on images

E. Jeschke

Requirements
============

naojsoft packages
-----------------
- g2cam
- ginga
"""
import numpy as np

# ginga
from ginga.gw import Widgets, GwHelp
from ginga import GingaPlugin, trcalc
from ginga.util import wcs
from ginga.canvas.coordmap import BaseMapper

from g2cam.INS import INSdata

# don't show these instruments because we have no detailed info on them yet
remove_inst = ['CSW', 'FLDMON', 'LGS', 'SUKA', 'VGW', 'WAVEPLAT',
               'SCEXAO', 'CHARIS', 'VAMPIRES', 'MEC', 'MIMIZUKU',
               'TELSIM', 'PFS', 'HSC',
               ]
class InsFov(GingaPlugin.LocalPlugin):

    def __init__(self, fv, fitsimage):
        # superclass defines some variables for us, like logger
        super().__init__(fv, fitsimage)

        # get FOV preferences
        prefs = self.fv.get_preferences()
        self.settings = prefs.create_category('plugin_InsFov')
        self.settings.add_defaults(sky_radius_arcmin=3)
        self.settings.load(onError='silent')

        # for instrument information
        self.insdata = INSdata()
        self.instruments = list(set(self.insdata.getNames(active=True)) -
                                set(remove_inst))
        self.instruments.sort()
        self.instruments.insert(0, 'None')

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

        captions = (('Instrument:', 'label', 'instrument', 'combobox',
                     'PA (deg):', 'label', 'pa', 'entryset',
                     'Flip', 'checkbox'),
                    )

        w, b = Widgets.build_info(captions)
        self.w = b

        fr.set_widget(w)
        top.add_widget(fr, stretch=0)

        for name in self.instruments:
            b.instrument.append_text(name)
        b.instrument.add_callback('activated', self.select_inst_cb)
        b.instrument.set_tooltip("Choose instrument")

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
        p_canvas = self.viewer.get_canvas()
        if self.canvas not in p_canvas:
            p_canvas.add(self.canvas)

        self.resume()
        self.redo()

    def pause(self):
        self.canvas.ui_set_active(False)

    def resume(self):
        self.canvas.ui_set_active(True, viewer=self.viewer)

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

    def select_inst_cb(self, w, idx):
        with self.viewer.suppress_redraw:
            # changing instrument: remove old FOV
            if self.cur_fov is not None:
                self.cur_fov.remove()

            insname = w.get_text()
            if insname in inst_fov:
                klass = inst_fov[insname]
                pt = self.viewer.get_pan(coord='data')
                self.cur_fov = klass(self.canvas, pt[:2])
                self.mount_offset_rot_deg = self.cur_fov.mount_offset_rot_deg

                # this should change the size setting in FindImage
                self.settings.set(sky_radius_arcmin=self.cur_fov.sky_radius_arcmin)
            else:
                # 'None' selected
                self.cur_fov = None
                self.mount_offset_rot_deg = 0.0

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


class AO188_FOV(FOV):
    def __init__(self, canvas, pt):
        super().__init__(canvas, pt)

        #self.ao_fov = 0.0166667 # 1 arcmin
        self.ao_fov = 0.0333333
        self.scale = 1.0
        self.ao_radius = 60 * 0.5
        self.rot_deg = 0.0
        self.sky_radius_arcmin = self.ao_fov * 60

        self.ao_color = 'red'

        x, y = pt
        r = self.ao_radius
        self.ao_circ = self.dc.CompoundObject(
            self.dc.Circle(x, y, r,
                           color=self.ao_color, linewidth=2),
            self.dc.Text(x, y + r,
                         text="Tip Tilt Guide Star w/LGS (1 arcmin)",
                         color=self.ao_color,
                         rot_deg=self.rot_deg))
        self.canvas.add(self.ao_circ)

    def set_scale(self, scale_x, scale_y):
        # NOTE: sign of scale val indicates orientation
        self.scale = np.mean((abs(scale_x), abs(scale_y)))

        self.ao_radius = self.ao_fov * 0.5 / self.scale
        pt = self.ao_circ.objects[0].points[0][:2]
        self.set_pos(pt)

    def set_pos(self, pt):
        x, y = pt
        r = self.ao_radius
        self.ao_circ.objects[0].x = x
        self.ao_circ.objects[0].y = y
        self.ao_circ.objects[0].radius = r
        self.ao_circ.objects[1].x = x
        self.ao_circ.objects[1].y = y + r

        self.canvas.update_canvas()

    def rotate(self, rot_deg):
        self.rot_deg = rot_deg

    def remove(self):
        self.canvas.delete_object(self.ao_circ)


class IRCS_FOV(AO188_FOV):
    def __init__(self, canvas, pt):
        super().__init__(canvas, pt)

        self.ircs_fov = 0.015   # 54 arcsec
        self.ircs_radius = 54 * 0.5
        self.ircs_color = 'red'
        self.mount_offset_rot_deg = 90.0

        x, y = pt
        r = self.ircs_radius
        self.ircs_box = self.dc.CompoundObject(
            self.dc.SquareBox(x, y, r,
                              color=self.ircs_color, linewidth=2,
                              rot_deg=self.rot_deg),
            self.dc.Text(x - r, y + r,
                         text="IRCS FOV (54x54 arcsec)",
                         color=self.ircs_color,
                         rot_deg=self.rot_deg))
        self.canvas.add(self.ircs_box)

    def set_scale(self, scale_x, scale_y):
        super().set_scale(scale_x, scale_y)

        self.ircs_radius = self.ircs_fov * 0.5 / self.scale

        pt = self.ircs_box.objects[0].points[0][:2]
        self.set_pos(pt)

    def set_pos(self, pt):
        super().set_pos(pt)
        x, y = pt
        r = self.ircs_radius
        self.ircs_box.objects[0].radius = r
        self.ircs_box.objects[0].x = x
        self.ircs_box.objects[0].y = y
        self.ircs_box.objects[1].x = x - r
        self.ircs_box.objects[1].y = y + r

        self.canvas.update_canvas()

    def rotate(self, rot_deg):
        super().rotate(rot_deg)

    def remove(self):
        super().remove()

        self.canvas.delete_object(self.ircs_box)


class IRD_FOV(AO188_FOV):
    def __init__(self, canvas, pt):
        super().__init__(canvas, pt)

        self.ird_fov = (0.00555556, 0.00277778)   # 20x10 arcsec
        self.ird_radius = (20 * 0.5, 10 * 0.5)
        self.ird_color = 'red'

        x, y = pt
        xr, yr = self.ird_radius
        self.ird_box = self.dc.CompoundObject(
            self.dc.Box(x, y, xr, yr,
                        color=self.ird_color, linewidth=2,
                        rot_deg=self.rot_deg),
            self.dc.Text(x - xr, y + yr,
                         text="IRD FOV for FIM (20x10 arcsec)",
                         color=self.ird_color,
                         rot_deg=self.rot_deg))
        self.canvas.add(self.ird_box)

    def set_scale(self, scale_x, scale_y):
        super().set_scale(scale_x, scale_y)

        xr = self.ird_fov[0] * 0.5 / self.scale
        yr = self.ird_fov[1] * 0.5 / self.scale
        self.ird_radius = (xr, yr)

        pt = self.ird_box.objects[0].points[0][:2]
        self.set_pos(pt)

    def set_pos(self, pt):
        super().set_pos(pt)
        x, y = pt
        xr, yr = self.ird_radius
        self.ird_box.objects[0].x = x
        self.ird_box.objects[0].y = y
        self.ird_box.objects[0].xradius = xr
        self.ird_box.objects[0].yradius = yr
        self.ird_box.objects[1].x = x - xr
        self.ird_box.objects[1].y = y + yr

        self.canvas.update_canvas()

    def rotate(self, rot_deg):
        super().rotate(rot_deg)

    def remove(self):
        super().remove()

        self.canvas.delete_object(self.ird_box)


class CS_FOV(FOV):
    def __init__(self, canvas, pt):
        super().__init__(canvas, pt)

        self.cs_fov = 0.1   # 6 arcmin
        self.scale = 1.0
        self.cs_radius = 6 * 0.5
        self.rot_deg = 0.0
        self.sky_radius_arcmin = self.cs_fov * 60

        self.cs_color = 'red'

        x, y = pt
        r = self.cs_radius
        self.cs_circ = self.dc.CompoundObject(
            self.dc.Circle(x, y, r,
                           color=self.cs_color, linewidth=2),
            self.dc.Text(x, y,
                         text="6 arcmin",
                         color=self.cs_color,
                         rot_deg=self.rot_deg))
        self.canvas.add(self.cs_circ)

    def set_scale(self, scale_x, scale_y):
        # NOTE: sign of scale val indicates orientation
        self.scale = np.mean((abs(scale_x), abs(scale_y)))

        self.cs_radius = self.cs_fov * 0.5 / self.scale
        pt = self.cs_circ.objects[0].points[0][:2]
        self.set_pos(pt)

    def set_pos(self, pt):
        super().set_pos(pt)
        x, y = pt
        r = self.cs_radius
        self.cs_circ.objects[0].x = x
        self.cs_circ.objects[0].y = y
        self.cs_circ.objects[0].radius = r
        self.cs_circ.objects[1].x = x
        self.cs_circ.objects[1].y = y + r

        self.canvas.update_canvas()

    def rotate(self, rot_deg):
        self.rot_deg = rot_deg

    def remove(self):
        self.canvas.delete_object(self.cs_circ)


class COMICS_FOV(CS_FOV):
    def __init__(self, canvas, pt):
        super().__init__(canvas, pt)

        self.comics_fov = (0.00833333, 0.0111111)   # 30x40 arcsec
        self.comics_radius = (30 * 0.5, 40 * 0.5)

        self.comics_color = 'red'

        x, y = pt
        xr, yr = self.comics_radius
        self.comics_box = self.dc.CompoundObject(
            self.dc.Box(x, y, xr, yr,
                        color=self.comics_color, linewidth=2,
                        rot_deg=self.rot_deg),
            self.dc.Text(x - xr, y + yr,
                         text="COMICS FOV (30x40 arcsec)",
                         color=self.comics_color,
                         rot_deg=self.rot_deg))
        self.canvas.add(self.comics_box)

    def set_scale(self, scale_x, scale_y):
        super().set_scale(scale_x, scale_y)
        xr = self.comics_fov[0] * 0.5 / self.scale
        yr = self.comics_fov[1] * 0.5 / self.scale
        self.comics_radius = (xr, yr)

        pt = self.comics_box.objects[0].points[0][:2]
        self.set_pos(pt)

    def set_pos(self, pt):
        super().set_pos(pt)
        x, y = pt
        xr, yr = self.comics_radius
        self.comics_box.objects[0].x = x
        self.comics_box.objects[0].y = y
        self.comics_box.objects[0].xradius = xr
        self.comics_box.objects[0].yradius = yr
        self.comics_box.objects[1].x = x - xr
        self.comics_box.objects[1].y = y + yr

        self.canvas.update_canvas()

    def remove(self):
        super().remove()

        self.canvas.delete_object(self.comics_box)


class MOIRCS_FOV(CS_FOV):
    def __init__(self, canvas, pt):
        super().__init__(canvas, pt)

        self.moircs_fov = (0.0666667, 0.116667)   # 4x7 arcmin
        self.moircs_radius = (4 * 0.5, 7 * 0.5)

        self.moircs_color = 'red'

        x, y = pt
        xr, yr = self.moircs_radius
        self.moircs_box = self.dc.CompoundObject(
            self.dc.Box(x, y, xr, yr,
                        color=self.moircs_color, linewidth=2,
                        rot_deg=self.rot_deg),
            self.dc.Text(x - xr, y + yr,
                         text="MOIRCS FOV (4x7 arcmin)",
                         color=self.moircs_color,
                         rot_deg=self.rot_deg),
            self.dc.Line(x - xr, y, x + xr, y,
                         color=self.moircs_color, linewidth=2))
        self.canvas.add(self.moircs_box)

    def set_scale(self, scale_x, scale_y):
        super().set_scale(scale_x, scale_y)
        xr = self.moircs_fov[0] * 0.5 / self.scale
        yr = self.moircs_fov[1] * 0.5 / self.scale
        self.moircs_radius = (xr, yr)

        pt = self.moircs_box.objects[0].points[0][:2]
        self.set_pos(pt)

    def set_pos(self, pt):
        super().set_pos(pt)
        x, y = pt
        xr, yr = self.moircs_radius
        self.moircs_box.objects[0].x = pt[0]
        self.moircs_box.objects[0].y = pt[1]
        self.moircs_box.objects[0].xradius = xr
        self.moircs_box.objects[0].yradius = yr
        self.moircs_box.objects[1].x = x - xr
        self.moircs_box.objects[1].y = y + yr
        self.moircs_box.objects[2].x1 = x - xr
        self.moircs_box.objects[2].x2 = x + xr
        self.moircs_box.objects[2].y1 = y
        self.moircs_box.objects[2].y2 = y

        self.canvas.update_canvas()

    def remove(self):
        super().remove()

        self.canvas.delete_object(self.moircs_box)


class SWIMS_FOV(CS_FOV):
    def __init__(self, canvas, pt):
        super().__init__(canvas, pt)

        self.swims_fov = (0.11, 0.055)   # 6.6x3.3 arcmin
        self.swims_radius = (6.6 * 0.5, 3.3 * 0.5)

        self.swims_color = 'red'

        x, y = pt
        xr, yr = self.swims_radius
        self.swims_box = self.dc.CompoundObject(
            self.dc.Box(x, y, xr, yr,
                        color=self.swims_color, linewidth=2,
                        rot_deg=self.rot_deg),
            self.dc.Text(x - xr, y + yr,
                         text="SWIMS FOV (6.6x3.3 arcmin)",
                         color=self.swims_color,
                         rot_deg=self.rot_deg),
            self.dc.Line(x, y - yr, x, y + yr,
                         color=self.swims_color, linewidth=2))
        self.canvas.add(self.swims_box)

    def set_scale(self, scale_x, scale_y):
        super().set_scale(scale_x, scale_y)
        xr = self.swims_fov[0] * 0.5 / self.scale
        yr = self.swims_fov[1] * 0.5 / self.scale
        self.swims_radius = (xr, yr)

        pt = self.swims_box.objects[0].points[0][:2]
        self.set_pos(pt)

    def set_pos(self, pt):
        super().set_pos(pt)
        x, y = pt
        xr, yr = self.swims_radius
        self.swims_box.objects[0].x = x
        self.swims_box.objects[0].y = y
        self.swims_box.objects[0].xradius = xr
        self.swims_box.objects[0].yradius = yr
        self.swims_box.objects[1].x = x - xr
        self.swims_box.objects[1].y = y + yr
        self.swims_box.objects[2].y1 = y - yr
        self.swims_box.objects[2].y2 = y + yr
        self.swims_box.objects[2].x1 = x
        self.swims_box.objects[2].x2 = x

        self.canvas.update_canvas()

    def rotate(self, rot_deg):
        super().rotate(rot_deg)

    def remove(self):
        super().remove()

        self.canvas.delete_object(self.swims_box)


class FOCAS_FOV(CS_FOV):
    def __init__(self, canvas, pt):
        super().__init__(canvas, pt)

        self.cs_circ.objects[1].text = "FOCAS FOV (6 arcmin)"

        x, y = self.cs_circ.objects[0].points[0][:2]
        xr = self.cs_radius
        self.focas_info = self.dc.CompoundObject(
            self.dc.Line(x - xr, y, x + xr, y,
                         color=self.cs_color, linewidth=2))
        self.canvas.add(self.focas_info)

    def set_scale(self, scale_x, scale_y):
        super().set_scale(scale_x, scale_y)

        pt = self.cs_circ.objects[0].points[0][:2]
        self.set_pos(pt)

    def set_pos(self, pt):
        super().set_pos(pt)
        x, y = pt
        xr = self.cs_radius
        self.focas_info.objects[0].x1 = x - xr
        self.focas_info.objects[0].x2 = x + xr
        self.focas_info.objects[0].y1 = y
        self.focas_info.objects[0].y2 = y

        self.canvas.update_canvas()

    def remove(self):
        super().remove()

        self.canvas.delete_object(self.focas_info)


class HDS_FOV(FOV):
    def __init__(self, canvas, pt):
        super().__init__(canvas, pt)

        self.hds_fov = 0.0166667
        self.scale = 1.0
        self.hds_radius = 1 * 0.5
        self.rot_deg = 0.0
        self.sky_radius_arcmin = self.hds_fov * 60

        self.hds_color = 'red'

        x, y = pt
        r = self.hds_radius
        self.hds_circ = self.dc.CompoundObject(
            self.dc.Circle(x, y, r,
                           color=self.hds_color, linewidth=2),
            self.dc.Text(x, y,
                         text="HDS SV FOV (1 arcmin)",
                         color=self.hds_color,
                         rot_deg=self.rot_deg),
            self.dc.Line(x, y - r, x, y + r,
                         color=self.hds_color, linewidth=2))
        self.canvas.add(self.hds_circ)

    def set_scale(self, scale_x, scale_y):
        # NOTE: sign of scale val indicates orientation
        self.scale = np.mean((abs(scale_x), abs(scale_y)))

        self.hds_radius = self.hds_fov * 0.5 / self.scale
        pt = self.hds_circ.objects[0].points[0][:2]
        self.set_pos(pt)

    def set_pos(self, pt):
        super().set_pos(pt)
        x, y = pt
        r = self.hds_radius
        self.hds_circ.objects[0].x = x
        self.hds_circ.objects[0].y = y
        self.hds_circ.objects[0].radius = r
        self.hds_circ.objects[1].x = x
        self.hds_circ.objects[1].y = y + r
        self.hds_circ.objects[2].x1 = x
        self.hds_circ.objects[2].x2 = x
        self.hds_circ.objects[2].y1 = y - r
        self.hds_circ.objects[2].y2 = y + r

        self.canvas.update_canvas()

    def rotate(self, rot_deg):
        self.rot_deg = rot_deg

    def remove(self):
        self.canvas.delete_object(self.hds_circ)


class PF_FOV(FOV):
    def __init__(self, canvas, pt):
        super().__init__(canvas, pt)

        self.pf_fov = 1.5   # 1.5 deg
        self.scale = 1.0
        self.pf_radius = self.pf_fov * 0.5
        self.rot_deg = 0.0

        self.pf_color = 'red'

        x, y = pt
        r = self.pf_radius
        self.pf_circ = self.dc.CompoundObject(
            self.dc.Circle(x, y, r,
                           color=self.pf_color, linewidth=2),
            self.dc.Text(x, y,
                         text="PF FOV (1.5 deg)",
                         color=self.pf_color,
                         rot_deg=self.rot_deg))
        self.canvas.add(self.pf_circ)

    def set_scale(self, scale_x, scale_y):
        # NOTE: sign of scale val indicates orientation
        self.scale = np.mean((abs(scale_x), abs(scale_y)))

        self.pf_radius = self.pf_fov * 0.5 / self.scale
        pt = self.pf_circ.objects[0].points[0][:2]
        self.set_pos(pt)

    def set_pos(self, pt):
        super().set_pos(pt)
        x, y = pt
        r = self.pf_radius
        self.pf_circ.objects[0].x = x
        self.pf_circ.objects[0].y = y
        self.pf_circ.objects[0].radius = r
        self.pf_circ.objects[1].x = x
        self.pf_circ.objects[1].y = y + r

        self.canvas.update_canvas()

    def rotate(self, rot_deg):
        self.rot_deg = rot_deg

    def remove(self):
        self.canvas.delete_object(self.pf_circ)


class HSC_FOV(PF_FOV):
    pass

class PFS_FOV(PF_FOV):
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



inst_fov = dict(AO188=AO188_FOV, IRCS=IRCS_FOV, IRD=IRD_FOV, COMICS=COMICS_FOV,
                MOIRCS=MOIRCS_FOV, SWIMS=SWIMS_FOV, FOCAS=FOCAS_FOV,
                HDS=HDS_FOV, HSC=HSC_FOV, PFS=PFS_FOV)
