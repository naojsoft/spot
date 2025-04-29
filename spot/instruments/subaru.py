"""
subaru.py -- Subaru instrument overlays

"""
import numpy as np
from astropy.coordinates import Angle
from astropy import units as u

from spot.plugins.InsFov import FOV


class AO188_FOV(FOV):
    def __init__(self, pl_obj, canvas, pt):
        super().__init__(pl_obj, canvas, pt)

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
        self.text_off = 0.75

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
            self.dc.Text(x, y - (yr * self.text_off), text='Det 1',
                         color=self.cs_color,
                         bgcolor='white', bgalpha=0.75),
            self.dc.Text(x, y + (yr * self.text_off), text='Det 2',
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
        self.moircs_box.objects[3].x = x
        self.moircs_box.objects[3].y = y - (yr * self.text_off)
        self.moircs_box.objects[4].x = x
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
        self.text_off = 0.90

        x, y = self.cs_circ.objects[0].points[0][:2]
        xr = self.cs_radius
        self.focas_info = self.dc.CompoundObject(
            self.dc.Line(x - xr, y, x + xr, y,
                         color=self.cs_color, linewidth=2),
            self.dc.Text(x, y - (xr * self.text_off), text='Chip 1',
                         color=self.cs_color,
                         bgcolor='white', bgalpha=0.75),
            self.dc.Text(x, y + (xr * self.text_off),
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
        self.focas_info.objects[1].x = x
        self.focas_info.objects[1].y = y - (xr * self.text_off)
        self.focas_info.objects[2].x = x
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
        self.sky_radius_arcmin = self.pf_radius * 60
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


# see spot/instruments/__init__.py
#
subaru_fov_dict = dict(AO188=AO188_FOV, IRCS=IRCS_FOV, IRD=IRD_FOV,
                       #COMICS=COMICS_FOV, SWIMS=SWIMS_FOV,
                       MOIRCS=MOIRCS_FOV, FOCAS=FOCAS_FOV,
                       HDS=HDS_FOV, HDS_NO_IMR=HDS_FOV_no_IMR,
                       HSC=HSC_FOV, PFS=PFS_FOV)
