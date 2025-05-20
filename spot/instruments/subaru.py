"""
subaru.py -- Subaru instrument overlays

"""
import os.path
import numpy as np
from astropy.coordinates import Angle
from astropy import units as u
from astropy.io import fits

from ginga.util import wcs
from ginga.gw import Widgets

from spot.plugins.InsFov import FOV
from spot.util.rot import normalize_angle

# where our config files are stored
from spot import __file__
cfgdir = os.path.join(os.path.dirname(__file__), 'config')


class AO188_FOV(FOV):
    def __init__(self, pl_obj, canvas, pt):
        super().__init__(pl_obj, canvas, pt)

        #self.ao_fov = 0.0166667 # 1 arcmin
        self.ao_fov = 0.0333333
        self.scale = 1.0
        self.ao_radius = 60 * 0.5
        self.rot_deg = 0.0
        self.sky_radius_arcmin = 1.5

        self.ao_color = 'red'

        x, y = pt
        r = self.ao_radius
        self.ao_circ = self.dc.CompoundObject(
            self.dc.Circle(x, y, r,
                           color=self.ao_color, linewidth=2),
            self.dc.Text(x, y + r,
                         text="Tip Tilt Guide Star w/LGS (1 arcmin)",
                         color=self.ao_color,
                         bgcolor='floralwhite', bgalpha=0.8,
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
    def __init__(self, pl_obj, canvas, pt):
        super().__init__(pl_obj, canvas, pt)

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
    def __init__(self, pl_obj, canvas, pt):
        super().__init__(pl_obj, canvas, pt)

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
    def __init__(self, pl_obj, canvas, pt):
        super().__init__(pl_obj, canvas, pt)

        self.cs_fov = 0.1   # 6 arcmin
        self.scale = 1.0
        self.cs_radius = 6 * 0.5
        self.rot_deg = 0.0
        self.sky_radius_arcmin = 5.0

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
    def __init__(self, pl_obj, canvas, pt):
        super().__init__(pl_obj, canvas, pt)

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
    def __init__(self, pl_obj, canvas, pt):
        super().__init__(pl_obj, canvas, pt)

        self.moircs_fov = (0.0666667, 0.116667)   # 4x7 arcmin
        self.moircs_radius = (4 * 0.5, 7 * 0.5)
        self.text_off = 0.90

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
                         color=self.moircs_color, linewidth=2),
            self.dc.Text(x + xr, y - (yr * self.text_off), text='Det 1',
                         color=self.cs_color,
                         bgcolor='white', bgalpha=0.75),
            self.dc.Text(x + xr, y + (yr * self.text_off), text='Det 2',
                         color=self.cs_color,
                         bgcolor='white', bgalpha=0.75),
        )
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
        self.moircs_box.objects[3].x = x + xr
        self.moircs_box.objects[3].y = y - (yr * self.text_off)
        self.moircs_box.objects[4].x = x + xr
        self.moircs_box.objects[4].y = y + (yr * self.text_off)

        self.canvas.update_canvas()

    def remove(self):
        super().remove()

        self.canvas.delete_object(self.moircs_box)


class SWIMS_FOV(CS_FOV):
    def __init__(self, pl_obj, canvas, pt):
        super().__init__(pl_obj, canvas, pt)

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
    def __init__(self, pl_obj, canvas, pt):
        super().__init__(pl_obj, canvas, pt)

        self.cs_circ.objects[1].text = "FOCAS FOV (6 arcmin)"
        self.text_off = 0.50

        # center of FOV circle
        x, y = self.cs_circ.objects[0].points[0][:2]
        xr = self.cs_radius
        self.focas_info = self.dc.CompoundObject(
            self.dc.Line(x - xr, y, x + xr, y,
                         color=self.cs_color, linewidth=2),
            self.dc.Text(x + xr, y - (xr * self.text_off), text='Chip 1',
                         color=self.cs_color,
                         bgcolor='white', bgalpha=0.75),
            self.dc.Text(x + xr, y + (xr * self.text_off),
                         text='Chip 2', color=self.cs_color,
                         bgcolor='white', bgalpha=0.75),
        )
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
        self.focas_info.objects[1].x = x + xr
        self.focas_info.objects[1].y = y - (xr * self.text_off)
        self.focas_info.objects[2].x = x + xr
        self.focas_info.objects[2].y = y + (xr * self.text_off)

        self.canvas.update_canvas()

    def remove(self):
        super().remove()

        self.canvas.delete_object(self.focas_info)


class HDS_FOV(FOV):
    def __init__(self, pl_obj, canvas, pt):
        super().__init__(pl_obj, canvas, pt)

        self.hds_fov = 0.0166667
        self.scale = 1.0
        self.hds_radius = 1 * 0.5
        self.rot_deg = 0.0
        self.sky_radius_arcmin = 1.5

        self.hds_color = 'red'

        x, y = pt
        r = self.hds_radius
        self.hds_circ = self.dc.CompoundObject(
            self.dc.Circle(x, y, r,
                           color=self.hds_color, linewidth=2),
            self.dc.Text(x, y,
                         text="HDS SV FOV (1 arcmin)",
                         color=self.hds_color,
                         bgcolor='floralwhite', bgalpha=0.8,
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


class HDS_FOV_no_IMR(HDS_FOV):
    def __init__(self, pl_obj, canvas, pt):
        super().__init__(pl_obj, canvas, pt)

    def set_pa(self, pa_deg):
        # HDS without the image rotator cannot set the position angle
        site = self.pl_obj.get_site()
        status = site.get_status()
        lat_deg = status['latitude_deg']

        cres = self.pl_obj.get_cres()
        ha_hrs = np.degrees(cres.ha) / 15
        pa_deg = self.calc_pa_hds_noimr(cres.dec_deg, ha_hrs, lat_deg)

        super().set_pa(pa_deg)

    def update_pa_from_rotation(self, rot_deg):
        # HDS without the image rotator cannot set the position angle
        return self.pa_deg

    def calc_pa_hds_noimr(self, dec_deg, ha_hr, lat_deg):
        lat_rad = np.radians(lat_deg)
        dec_rad = np.radians(dec_deg)
        ha_rad = np.radians(ha_hr * 15.0)
        hds_pa_offset = -58.4

        p_deg = np.degrees(np.arctan2((np.tan(lat_rad) * np.cos(dec_rad) -
                                       np.sin(dec_rad) * np.cos(ha_rad)),
                                      np.sin(ha_rad)))
        z_deg = np.degrees(np.arccos(np.sin(lat_rad) * np.sin(dec_rad) +
                                     np.cos(lat_rad) * np.cos(dec_rad) *
                                     np.cos(ha_rad)))
        hds_pa_ang = Angle((-(p_deg - z_deg) + hds_pa_offset) * u.deg)
        return hds_pa_ang.wrap_at(180 * u.deg).value


class PF_FOV(FOV):
    def __init__(self, pl_obj, canvas, pt):
        super().__init__(pl_obj, canvas, pt)

        self.pf_fov = 1.5   # 1.5 deg
        self.scale = 1.0
        self.pf_radius = self.pf_fov * 0.5
        self.sky_radius_arcmin = 55
        self.rot_deg = 0.0
        self.pf_color = 'red'
        self.pt_ctr = pt

    def set_scale(self, scale_x, scale_y):
        # NOTE: sign of scale val indicates orientation
        self.scale = np.mean((abs(scale_x), abs(scale_y)))

        self.pf_radius = self.pf_fov * 0.5 / self.scale
        self.set_pos(self.pt_ctr)

    def set_pos(self, pt):
        super().set_pos(pt)
        self.pt_ctr = pt

    def rotate(self, rot_deg):
        self.rot_deg = rot_deg


class HSC_FOV(PF_FOV):

    hsc_info = None

    @classmethod
    def read_hsc_info(cls):
        # read in HSC detector info
        hsc_info_fits = os.path.join(cfgdir, 'hsc_info.fits')
        with fits.open(hsc_info_fits, 'readonly') as hsc_f:
            info_dct = dict()
            sdo = hsc_f['SDO'].data
            poly = hsc_f['DET_POLY'].data
            for row in sdo:
                det_num = row['DET_INDEX']
                bad_ch_str = row['BAD_CHANNELS'].strip()
                if len(bad_ch_str) == 0:
                    bad_channels = []
                else:
                    bad_channels = list(map(int, bad_ch_str.split(',')))
                if len(bad_channels) > 0:
                    color = 'red'
                elif row['BEES_UNIT'] == 0:
                    color = 'skyblue'
                else:
                    color = 'violet'
                offsets = np.array((poly['{}_OFFSET_RA'.format(det_num)],
                                    poly['{}_OFFSET_DEC'.format(det_num)]),
                                   dtype=float).T
                det_dct = dict(bees=row['BEES_UNIT'],
                               bees_det_id=row['BEES_ID'],
                               color=color,
                               bad_channels=bad_channels,
                               polygon=offsets)
                info_dct[det_num] = det_dct

        HSC_FOV.hsc_info = info_dct

    def __init__(self, pl_obj, canvas, pt):
        super().__init__(pl_obj, canvas, pt)

        self.det_poly_paths = []

        # for the dithering GUI
        self.dither_types = ['1', '5', 'N']
        self.dither_type = '1'
        self.dither_steps = 5

        # default dra/ddec is 120"
        self.dra = 120.0
        self.ddec = 120.0
        self.tdith = 15.0
        self.rdith = 120.0

        self.target_radius = 20

        x, y = pt
        r = self.pf_radius
        self.pf_circ = self.dc.CompoundObject(
            self.dc.Circle(x, y, r,
                           color=self.pf_color, linewidth=2),
            self.dc.Text(x, y,
                         text=f"HSC FOV ({self.pf_fov:.2f} deg)",
                         color=self.pf_color,
                         rot_deg=self.rot_deg))
        self.canvas.add(self.pf_circ)

        if HSC_FOV.hsc_info is None:
            self.read_hsc_info()

    def calc_detector_positions(self):
        """Computes paths for all the detector polygons."""
        viewer = self.pl_obj.viewer
        image = viewer.get_image()
        if image is None:
            return

        ctr_ra, ctr_dec = self.pl_obj.coord
        info = HSC_FOV.hsc_info

        paths = []
        keys = list(info.keys())
        keys.sort()
        for key in keys:
            poly_coords = np.array([wcs.add_offset_radec(ctr_ra, ctr_dec,
                                                         dra, ddec)
                                    for dra, ddec in info[key]['polygon']],
                                   dtype=float)
            path_points = image.wcs.wcspt_to_datapt(poly_coords)
            paths.append((key, path_points))

        self.det_poly_paths = paths

    def draw_detectors(self):
        l = []
        info = HSC_FOV.hsc_info

        for key, points in self.det_poly_paths:

            showfill = False
            if 'color' in info[key]:
                color = info[key]['color']
            else:
                color = 'lightgreen'
            if color == 'red':
                showfill = True
            p = self.dc.Polygon(points, color=color, fill=showfill,
                                fillcolor='red', fillalpha=0.4,
                                showcap=False, coord='insfov')

            # annotate with the detector name
            # find center, which is geometric average of points
            xs, ys = points.T
            pcx, pcy = np.sum(xs) / len(xs), np.sum(ys) / len(ys)
            name = "{:1d}_{:02d}".format(info[key]['bees'],
                                         info[key]['bees_det_id'])
            t = self.dc.Text(pcx, pcy, text=name, color=color, fontsize=12,
                             coord='insfov')

            l.append(self.dc.CompoundObject(p, t))

        obj = self.dc.CompoundObject(*l)
        obj.opaque = True
        obj.editable = False

        self.canvas.add(obj, tag='detector_overlay')

    def build_gui(self, container):
        fr = Widgets.Frame("Dithering")

        vbox2 = Widgets.VBox()
        captions = (('Dither Type:', 'label', 'Dither Type', 'combobox',
                     'Dither Steps:', 'label', 'Dither Steps', 'spinbutton'),
                    ('RA Offset:', 'label', 'RA Offset', 'entry',
                     'DEC Offset:', 'label', 'DEC Offset', 'entry',),
                    ('Dith1:', 'label', 'Dith1', 'entry',
                     'Dith2:', 'label', 'Dith2', 'entry',),
                    ('Skip:', 'label', 'Skip', 'spinbutton',
                     'Stop:', 'label', 'Stop', 'spinbutton'),
                    ('Update View', 'button'),
                    )
        w, b = Widgets.build_info(captions, orientation='vertical')
        self.w.update(b)

        combobox = b.dither_type
        for name in self.dither_types:
            combobox.append_text(name)
        index = self.dither_types.index(self.dither_type)
        combobox.set_index(index)
        combobox.add_callback('activated', lambda w, idx: self.set_dither_type_cb())
        combobox.set_tooltip("Set dither type")
        b.dither_steps.set_limits(1, 20)
        b.dither_steps.add_callback('value-changed',
                                    lambda w, idx: self.set_dither_steps_cb(idx))
        b.dither_steps.set_tooltip("Number of dither steps")

        b.ra_offset.set_text(str(0.0))
        b.dec_offset.set_text(str(0.0))
        b.ra_offset.set_tooltip("RA offset from center of field in arcsec")
        b.dec_offset.set_tooltip("DEC offset from center of field in arcsec")
        b.skip.set_value(0)
        b.skip.set_tooltip("Skip over some dither steps")
        b.stop.set_value(1)
        b.stop.set_tooltip("Stop at a particular dither step")
        b.update_view.add_callback('activated', lambda w: self.update_info_cb())
        b.update_view.set_tooltip("Update the overlays after changing acquisition parameters")

        vbox2.add_widget(w)
        self.set_dither_type_cb()

        fr.set_widget(vbox2)
        container.add_widget(fr, stretch=0)

        captions = (("Dither Pos:", 'label', 'Show Step', 'spinbutton'),
                    )
        w, b = Widgets.build_info(captions, orientation='vertical')
        self.w.update(b)

        b.show_step.add_callback('value-changed',
                                 lambda w, idx: self.show_step_cb(idx))
        b.show_step.set_tooltip("Show position of detectors at dither step")

        container.add_widget(w, stretch=0)

    def draw_dither_positions(self):
        self.canvas.delete_object_by_tag('dither_positions')
        image = self.pl_obj.viewer.get_image()

        l = []
        start, stop, posns = self.get_dither_positions()
        i = start
        for ra_deg, dec_deg in posns:
            x, y = image.radectopix(ra_deg, dec_deg)
            l.append(self.dc.Text(x, y, text="%d" % i, color='yellow',
                                  fontscale=True, fontsize_min=14,
                                  fontsize_max=18))
            l.append(self.dc.Point(x, y, self.target_radius, color='yellow',
                                   linewidth=2, style='plus'))
            i += 1
        obj = self.dc.CompoundObject(*l)
        obj.opaque = True
        obj.editable = False

        self.canvas.add(obj, tag='dither_positions')

    def set_dither_type_cb(self):
        index = self.w.dither_type.get_index()
        self.dither_type = self.dither_types[index]

        if self.dither_type == '1':
            self.w.dither_steps.set_value(1)
            self.w.dither_steps.set_enabled(False)
            ## self.w.show_step.set_limits(1, 1)
            self.w.dith1.set_enabled(False)
            self.w.dith2.set_enabled(False)
            self.w.dith1.set_text('')
            self.w.dith2.set_text('')
            self.w.skip.set_enabled(False)
            self.w.stop.set_enabled(False)

        elif self.dither_type == '5':
            self.w.dith1.set_text(str(self.dra))
            self.w.dith2.set_text(str(self.ddec))
            self.w.dither_steps.set_value(5)
            self.w.dither_steps.set_enabled(False)
            ## self.w.show_step.set_limits(1, 5)
            self.w.dith1.set_enabled(True)
            self.w.dith2.set_enabled(True)
            self.w.lbl_dith1.set_text("Delta RA:")
            self.w.lbl_dith2.set_text("Delta DEC:")
            self.w.skip.set_enabled(True)
            self.w.skip.set_limits(0, 4)
            self.w.skip.set_value(0)
            self.w.stop.set_enabled(True)
            self.w.stop.set_limits(1, 5)
            self.w.stop.set_value(5)

        else:
            N = self.dither_steps
            self.w.dith1.set_text(str(self.rdith))
            self.w.dith2.set_text(str(self.tdith))
            self.w.dither_steps.set_value(N)
            self.w.dither_steps.set_enabled(True)
            ## self.w.show_step.set_limits(1, N)
            self.w.dith1.set_enabled(True)
            self.w.dith2.set_enabled(True)
            self.w.lbl_dith1.set_text("RDITH:")
            self.w.lbl_dith2.set_text("TDITH:")
            self.w.skip.set_enabled(True)
            self.w.skip.set_limits(0, N - 1)
            self.w.skip.set_value(0)
            self.w.stop.set_enabled(True)
            self.w.stop.set_limits(1, N)
            self.w.stop.set_value(N)

        return True

    def update_info_cb(self):
        try:
            # calculate center and target coordinates
            ra_off_deg = float(self.w.ra_offset.get_text()) / 3600.0
            dec_off_deg = float(self.w.dec_offset.get_text()) / 3600.0
            self.ra_off_deg = ra_off_deg
            self.dec_off_deg = dec_off_deg

            # save dither params
            if self.dither_type == '5':
                self.dra = float(self.w.dith1.get_text())
                self.ddec = float(self.w.dith2.get_text())

            elif self.dither_type == 'N':
                self.rdith = float(self.w.dith1.get_text())
                self.tdith = float(self.w.dith2.get_text())

            self.draw_dither_positions()

            start = int(self.w.skip.get_value()) + 1
            stop = int(self.w.stop.get_value())
            self.w.show_step.set_limits(start, stop)
            self.w.show_step.set_value(start)

            self.show_step(start)

        except Exception as e:
            self.pl_obj.fv.show_error(str(e))
        return True

    def calc_dither1(self, n):
        ctr_ra_deg, ctr_dec_deg = self.pl_obj.coord
        ctr_ra, ctr_dec = wcs.add_offset_radec(
            ctr_ra_deg, ctr_dec_deg,
            self.ra_off_deg, self.dec_off_deg)
        return (ctr_ra, ctr_dec)

    def calc_dither5(self, n):
        idx = n - 1
        l = ((0.0, 0.0), (1.0, -2.0), (2.0, 1.0), (-1.0, 2.0), (-2.0, -1.0))
        mra, mdec = l[idx]

        dra = float(self.w.dith1.get_text()) / 3600.0
        ddec = float(self.w.dith2.get_text()) / 3600.0

        ctr_ra_deg, ctr_dec_deg = self.pl_obj.coord
        ctr_ra, ctr_dec = wcs.add_offset_radec(
            ctr_ra_deg, ctr_dec_deg,
            mra * dra + self.ra_off_deg, mdec * ddec + self.dec_off_deg)
        return (ctr_ra, ctr_dec)

    def calc_ditherN(self, n):
        n = n - 1
        rdith = float(self.w.dith1.get_text()) / 3600.0
        tdith = float(self.w.dith2.get_text())
        ndith = float(self.dither_steps)

        sin_res = np.sin(np.radians(n * 360.0 / ndith + tdith))
        cos_res = np.cos(np.radians(n * 360.0 / ndith + tdith))

        ctr_ra_deg, ctr_dec_deg = self.pl_obj.coord
        ctr_ra, ctr_dec = wcs.add_offset_radec(
            ctr_ra_deg, ctr_dec_deg,
            cos_res * rdith + self.ra_off_deg,
            sin_res * rdith + self.dec_off_deg)
        return (ctr_ra, ctr_dec)

    def calc_dither(self, n):
        dith_type = self.dither_type
        if dith_type == '1':
            ra, dec = self.calc_dither1(n)
        elif dith_type == '5':
            ra, dec = self.calc_dither5(n)
        elif dith_type == 'N':
            ra, dec = self.calc_ditherN(n)
        return (ra, dec)

    def get_dither_positions(self):
        dith_type = self.dither_type
        skip = self.w.skip.get_value()
        stop = self.w.stop.get_value()

        if dith_type == '1':
            return 1, 1, [self.calc_dither1(n) for n in range(1, 2)]
        elif dith_type == '5':
            return skip + 1, stop, [self.calc_dither5(n)
                                    for n in range(skip + 1, stop + 1)]
        elif dith_type == 'N':
            #N = self.dither_steps
            return skip + 1, stop, [self.calc_ditherN(n)
                                    for n in range(skip + 1, stop + 1)]

    def set_dither_steps_cb(self, n):
        self.dither_steps = n
        ## self.w.show_step.set_limits(1, n)
        self.w.skip.set_limits(0, n - 1)
        self.w.skip.set_value(0)
        self.w.stop.set_limits(1, n)
        self.w.stop.set_value(n)
        #self.pl_obj.fv.error_wrap(self.draw_dither_positions)
        return True

    def _show_step(self, n):
        ra, dec = self.calc_dither(n)
        viewer = self.pl_obj.viewer
        image = viewer.get_image()
        data_x, data_y = image.radectopix(ra, dec)
        viewer.set_pan(data_x, data_y)
        return True

    def show_step(self, n):
        #self.w.show_step.set_text(str(n))
        self.w.show_step.set_value(n)
        self._show_step(n)

    def show_step_cb(self, n):
        #n = int(strip(self.w.show_step.get_text()))
        self.pl_obj.fv.error_wrap(self._show_step, n)
        return True

    def set_pos(self, pt):
        super().set_pos(pt)
        x, y = pt
        r = self.pf_radius
        self.pf_circ.objects[0].x = x
        self.pf_circ.objects[0].y = y
        self.pf_circ.objects[0].radius = r
        self.pf_circ.objects[1].x = x
        self.pf_circ.objects[1].y = y + r

        self.canvas.delete_object_by_tag('detector_overlay')

        self.calc_detector_positions()
        self.draw_detectors()

        self.canvas.update_canvas()

    def set_pa(self, pa_deg):
        # *** NOTE ***: opposite of base class because camera at Prime focus
        if self.flip_tf:
            self.pa_rot_deg = self.img_rot_deg + self.mount_offset_rot_deg - pa_deg
        else:
            self.pa_rot_deg = self.img_rot_deg - self.mount_offset_rot_deg + pa_deg

        self.pa_deg = normalize_angle(pa_deg, limit='half')

    def update_pa_from_rotation(self, rot_deg):
        self.pa_rot_deg = rot_deg

        # *** NOTE ***: opposite of base class because camera at Prime focus
        if not self.flip_tf:
            pa_deg = - self.img_rot_deg + self.mount_offset_rot_deg + rot_deg
        else:
            pa_deg = self.img_rot_deg + self.mount_offset_rot_deg - rot_deg

        self.pa_deg = normalize_angle(pa_deg, limit='half')
        return self.pa_deg

    def remove(self):
        super().remove()
        self.canvas.delete_object(self.pf_circ)
        self.canvas.delete_object_by_tag('detector_overlay')
        self.canvas.delete_object_by_tag('dither_positions')


class PFS_FOV(PF_FOV):

    pfs_info = None

    def __init__(self, pl_obj, canvas, pt):
        super().__init__(pl_obj, canvas, pt)

        self.pf_fov = 1.38   # deg
        self.pf_radius = self.pf_fov * 0.5
        self.cam_poly_paths = []
        self.fov_poly_path = []
        self.mount_offset_rot_deg = 180.0

        ang_inc = 360.0 / 6
        self.phis = np.array([np.radians(ang_inc * i) for i in range(6)])

        points = self.calc_fov_hexagon()
        self.pf_fov_hex = self.dc.CompoundObject(
            self.dc.Polygon(points, color=self.pf_color, linewidth=2),
            self.dc.Text(points[1][0], points[1][1],
                         text=f"PFS FOV ({self.pf_fov:.2f} deg)",
                         color=self.pf_color,
                         rot_deg=self.rot_deg))
        self.canvas.add(self.pf_fov_hex)

        if PFS_FOV.pfs_info is None:
            # read in PFS guide camera positions
            pfs_info_fits = os.path.join(cfgdir, 'pfs_info.fits')
            with fits.open(pfs_info_fits, 'readonly') as pfs_f:
                PFS_FOV.pfs_info = pfs_f['CAM_POLY'].copy()

    def calc_fov_hexagon(self):
        points = []
        for t_rad in self.phis:
            # polar to cartesian
            x = self.pt_ctr[0] + self.pf_radius * np.cos(t_rad)
            y = self.pt_ctr[1] + self.pf_radius * np.sin(t_rad)
            points.append((x, y))
        return np.array(points)

    def calc_guide_camera_positions(self):
        """Computes paths for all the detector polygons."""
        viewer = self.pl_obj.viewer
        image = viewer.get_image()
        if image is None:
            return

        ctr_ra, ctr_dec = self.pl_obj.coord
        info = PFS_FOV.pfs_info

        paths = []
        cam_pfx = ['CAM{}'.format(i + 1) for i in range(0, 6)]
        for pfx in cam_pfx:
            dra, ddec = (info.data[pfx + '_RA_OFF_DEG'],
                         info.data[pfx + '_DEC_OFF_DEG'])
            poly_coords = np.array([wcs.add_offset_radec(ctr_ra, ctr_dec,
                                                         dra[i], ddec[i])
                                    for i in range(len(dra))])
            path_points = image.wcs.wcspt_to_datapt(poly_coords)
            paths.append((pfx, path_points))

        self.cam_poly_paths = paths

    def draw_guide_cameras(self):
        l = []
        for name, points in self.cam_poly_paths:

            # TODO: skip some points to improve rendering performance
            showfill = False
            color = self.pf_color
            p = self.dc.Polygon(points, color=color, fill=showfill,
                                fillcolor='red', fillalpha=0.4,
                                linewidth=2,
                                showcap=False, coord='insfov')

            # annotate with the detector name
            # find center, which is geometric average of points
            xs, ys = points.T
            pcx, pcy = np.sum(xs) / len(xs), np.sum(ys) / len(ys)
            t = self.dc.Text(pcx, pcy, text=name, color=color, fontsize=12,
                             coord='insfov')

            l.append(self.dc.CompoundObject(p, t))

        obj = self.dc.CompoundObject(*l)
        obj.opaque = True
        obj.editable = False

        self.canvas.add(obj, tag='guide_camera_overlay')

    def set_pos(self, pt):
        super().set_pos(pt)

        points = self.calc_fov_hexagon()
        self.pf_fov_hex.objects[0].points = points
        self.pf_fov_hex.objects[1].x = points[1][0]
        self.pf_fov_hex.objects[1].y = points[1][1]

        self.canvas.delete_object_by_tag('guide_camera_overlay')

        self.calc_guide_camera_positions()
        self.draw_guide_cameras()

        self.canvas.update_canvas()

    def remove(self):
        super().remove()
        self.canvas.delete_object(self.pf_fov_hex)
        self.canvas.delete_object_by_tag('guide_camera_overlay')


# see spot/instruments/__init__.py
#
subaru_fov_dict = dict(AO188=AO188_FOV, IRCS=IRCS_FOV, IRD=IRD_FOV,
                       #COMICS=COMICS_FOV, SWIMS=SWIMS_FOV,
                       MOIRCS=MOIRCS_FOV, FOCAS=FOCAS_FOV,
                       HDS=HDS_FOV, HDS_NO_IMR=HDS_FOV_no_IMR,
                       HSC=HSC_FOV, PFS=PFS_FOV)
