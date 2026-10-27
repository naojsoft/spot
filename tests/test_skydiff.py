#
# test_skydiff.py -- unit tests for the all-sky camera difference imaging
#
# The frames are synthetic: a smooth sky background plus a field of point
# "stars" placed by their HA/Dec, so that the same stars can be rendered
# at two different times as the sky rotates.  A cloud is a smooth blob
# added to (or dimming) one of the frames.
#
import numpy as np
import pytest

from spot.util import skydiff

LAT = 19.8
# exercise both hemispheres (Mauna Kea, Mt. Stromlo)
LATS = [19.8, -35.3]
SIZE = 401


def _star_field(n=600, seed=1):
    rng = np.random.default_rng(seed)
    ra = rng.uniform(0, 360, n)
    dec = np.degrees(np.arcsin(rng.uniform(-1, 1, n)))
    flux = rng.uniform(50, 200, n)
    return ra, dec, flux


def _render(stars, lst_deg, cloud=None, size=SIZE, noise=1.0, seed=0,
            lat=LAT):
    """Render a frame at local sidereal time `lst_deg`."""
    ra, dec, flux = stars
    x, y, r = skydiff.radial_coords((size, size))
    scale = (size * 0.5) / 90.0
    data = 20.0 + 0.02 * r                    # brightening toward horizon
    alt, az = skydiff.hadec_to_altaz(lst_deg - ra, dec, lat)
    up = alt > 0
    sx, sy = skydiff.altaz_to_xy(alt[up], az[up], scale)
    cx = (size - 1) * 0.5
    cols = np.round(sx + cx).astype(int)
    rows = np.round(sy + cx).astype(int)
    ok = (rows >= 0) & (rows < size) & (cols >= 0) & (cols < size)
    stars_np = np.zeros_like(data)
    np.add.at(stars_np, (rows[ok], cols[ok]), flux[up][ok])
    # give the stars a ~2 pixel PSF
    for _ in range(2):
        stars_np = (stars_np + np.roll(stars_np, 1, 0) +
                    np.roll(stars_np, -1, 0)) / 3.0
        stars_np = (stars_np + np.roll(stars_np, 1, 1) +
                    np.roll(stars_np, -1, 1)) / 3.0
    data = data + stars_np
    if cloud is not None:
        x0, y0, rad, amp = cloud
        data = data + amp * np.exp(-((x - x0) ** 2 + (y - y0) ** 2) /
                                   (2 * rad ** 2))
    rng = np.random.default_rng(seed)
    data = data + rng.normal(0, noise, data.shape)
    return data.astype(np.float32)


@pytest.mark.parametrize('lat', LATS)
def test_altaz_hadec_roundtrip(lat):
    alt = np.array([5.0, 30.0, 60.0, 89.0])
    az = np.array([10.0, 100.0, -170.0, 250.0])
    ha, dec = skydiff.altaz_to_hadec(alt, az, lat)
    alt2, az2 = skydiff.hadec_to_altaz(ha, dec, lat)
    assert np.allclose(alt, alt2)
    assert np.allclose(np.cos(np.radians(az)), np.cos(np.radians(az2)))
    assert np.allclose(np.sin(np.radians(az)), np.sin(np.radians(az2)))


def test_star_rises_in_east():
    # a star on the eastern horizon has negative hour angle
    ha, dec = skydiff.altaz_to_hadec(0.0, 90.0, 0.0)
    assert ha == pytest.approx(-90.0)
    assert dec == pytest.approx(0.0, abs=1e-9)


def test_xy_altaz_orientation():
    scale = 2.0
    # North is up (+y), East is left (-x)
    assert np.allclose(skydiff.altaz_to_xy(0.0, 0.0, scale), (0, 180))
    assert np.allclose(skydiff.altaz_to_xy(0.0, 90.0, scale), (-180, 0))
    alt, az = skydiff.xy_to_altaz(-180.0, 0.0, scale)
    assert alt == pytest.approx(0.0) and az == pytest.approx(90.0)


def test_block_median_removes_point_sources():
    data = np.full((40, 40), 10.0, dtype=np.float32)
    data[5, 5] = 1000.0
    data[22, 31] = 500.0
    res = skydiff.block_median(data, 4)
    assert res.shape == (10, 10)
    assert np.all(res == 10.0)


def test_median_filter_preserves_shape():
    data = np.arange(100, dtype=np.float32).reshape(10, 10)
    data[4, 4] = 1e4
    res = skydiff.median_filter(data, 3)
    assert res.shape == data.shape
    assert res[4, 4] < 100


def test_to_mono():
    rgb = np.zeros((4, 5, 3), dtype=np.uint8)
    rgb[..., 1] = 100
    res = skydiff.to_mono(rgb)
    assert res.shape == (4, 5) and res.dtype == np.float32
    assert np.allclose(res, 71.52)


def test_celestial_poles():
    # the visible pole is due North (up) in the north and due South
    # (down) in the south, at an altitude equal to the latitude
    alt, az = skydiff.hadec_to_altaz(0.0, 90.0, 19.8)
    assert alt == pytest.approx(19.8) and az % 360 == pytest.approx(0.0)
    alt, az = skydiff.hadec_to_altaz(0.0, -90.0, -35.3)
    assert alt == pytest.approx(35.3) and az % 360 == pytest.approx(180.0)
    x, y = skydiff.altaz_to_xy(alt, az, 1.0)
    assert x == pytest.approx(0.0, abs=1e-9) and y < 0


@pytest.mark.parametrize('lat', LATS)
def test_derotation_cancels_stars(lat):
    stars = _star_field()
    dt = 300.0
    dlst = dt * skydiff.sidereal_rate_deg_s
    old = skydiff.make_work_frame(_render(stars, 0.0, seed=1, lat=lat), 1, 1)
    cur = skydiff.make_work_frame(_render(stars, dlst, seed=2, lat=lat),
                                  1, 1)

    plain = skydiff.sky_diff(cur, old, dt_sec=dt, lat_deg=lat,
                             derotate_sky=False)
    derot = skydiff.sky_diff(cur, old, dt_sec=dt, lat_deg=lat,
                             derotate_sky=True)
    m = plain['mask'] & derot['mask']
    # star residuals dominate the tail of the distribution
    tail_plain = np.percentile(np.abs(plain['sig'][m] * plain['sigma']), 99.9)
    tail_derot = np.percentile(np.abs(derot['sig'][m] * derot['sigma']), 99.9)
    assert tail_derot < 0.5 * tail_plain
    # and what is left is close to the noise (sqrt(2) for two frames)
    rms_derot = np.sqrt(np.mean((derot['sig'][m] * derot['sigma']) ** 2))
    assert rms_derot < 1.5 * np.sqrt(2.0)


@pytest.mark.parametrize('lat', LATS)
def test_clear_sky_has_low_cloud_cover(lat):
    stars = _star_field()
    dt = 180.0
    dlst = dt * skydiff.sidereal_rate_deg_s
    old = skydiff.make_work_frame(_render(stars, 0.0, seed=1, lat=lat), 1, 3)
    cur = skydiff.make_work_frame(_render(stars, dlst, seed=2, lat=lat),
                                  1, 3)
    res = skydiff.sky_diff(cur, old, dt_sec=dt, lat_deg=lat)
    assert res['cc_pct'] < 2.0


@pytest.mark.parametrize('amp', [15.0, -15.0])
def test_cloud_is_detected(amp):
    stars = _star_field()
    dt = 180.0
    dlst = dt * skydiff.sidereal_rate_deg_s
    cloud = (40.0, -30.0, 25.0, amp)
    old = skydiff.make_work_frame(_render(stars, 0.0, seed=1), 1, 3)
    cur = skydiff.make_work_frame(_render(stars, dlst, cloud=cloud,
                                          seed=2), 1, 3)
    res = skydiff.sky_diff(cur, old, dt_sec=dt, lat_deg=LAT)
    assert res['cc_pct'] > 2.0
    # the change is at the cloud, with the right sign
    cx = (SIZE - 1) * 0.5
    val = res['sig'][int(round(cx - 30)), int(round(cx + 40))]
    assert np.sign(val) == np.sign(amp)
    assert abs(val) > 5.0


def test_gain_change_is_normalized():
    stars = _star_field()
    old = skydiff.make_work_frame(_render(stars, 0.0, seed=1), 1, 3)
    cur = skydiff.make_work_frame(_render(stars, 0.0, seed=2), 1, 3)
    res = skydiff.sky_diff(1.5 * cur, old, dt_sec=0.0, lat_deg=LAT)
    assert res['gain'] == pytest.approx(1.5, rel=0.05)
    assert res['cc_pct'] < 2.0


def test_shape_mismatch_raises():
    with pytest.raises(ValueError):
        skydiff.sky_diff(np.zeros((10, 10)), np.zeros((12, 12)))


@pytest.mark.parametrize('rot_deg', [0.0, -35.6])
def test_orient_frame_centers_zenith(rot_deg):
    # a 640x480 frame whose sky circle (r=300) runs off the top and bottom,
    # like the GTC camera; mark the zenith pixel
    frame = np.full((480, 640), 10, dtype=np.uint8)
    xc, yc, r = 327, 252, 300
    frame[yc, xc] = 255
    out, cover = skydiff.orient_frame(frame, xc, yc, r, rot_deg=rot_deg,
                                      flip_ud=True)
    assert out.shape == (2 * r + 1, 2 * r + 1)
    # the zenith stays exactly at the center, even after rotation
    assert out[r, r] == 255
    # the parts of the circle outside the camera frame are not covered
    assert cover[r, r] and not cover.all()
    assert np.all(out[~cover] == 0)
    if rot_deg == 0.0:
        # frame rows 0..479 land at rows 48..527 of the square, which
        # flip_ud turns into rows 73..552
        n = 2 * r + 1
        top, bot = n - 480 + (yc - r), n - 1 + (yc - r)
        assert top == 73 and bot == 552
        col = cover[:, r]
        assert col[top:bot + 1].all()
        assert not col[:top].any() and not col[bot + 1:].any()


def _write_gif(path, n_frames):
    from PIL import Image
    frames = []
    for i in range(n_frames):
        arr = np.zeros((20, 30, 3), dtype=np.uint8)
        arr[:5, :, 0] = 255           # mark the top rows (orientation)
        arr[10:, :, 1] = 40 * (i + 1)  # frame number in the bottom half
        frames.append(Image.fromarray(arr))
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=70, loop=0)


def test_read_multiframe(tmp_path):
    path = str(tmp_path / 'loop.gif')
    _write_gif(path, 4)
    last = skydiff.read_multiframe(path)
    assert last.shape == (20, 30, 3)
    assert last[15, 0, 1] == 160          # last frame
    assert skydiff.read_multiframe(path, frame=0)[15, 0, 1] == 40
    assert skydiff.read_multiframe(path, frame=-2)[15, 0, 1] == 120

    # single-frame image: not handled here
    one = str(tmp_path / 'one.gif')
    _write_gif(one, 1)
    assert skydiff.read_multiframe(one) is None


def test_read_multiframe_matches_ginga_orientation(tmp_path):
    # the frame must come out oriented like ginga's own loader does it,
    # since the camera geometry in skycams.yml refers to that
    import logging
    from ginga.RGBImage import RGBImage
    from PIL import Image
    path = str(tmp_path / 'loop.gif')
    _write_gif(path, 3)
    first = skydiff.read_multiframe(path, frame=0)
    # (ginga reads a palette GIF as palette indices, so compare with the
    # same frame saved as an RGB PNG)
    png = str(tmp_path / 'first.png')
    with Image.open(path) as im:
        im.convert('RGB').save(png)
    img = RGBImage(logger=logging.getLogger('test'))
    img.load_file(png)
    assert np.array_equal(img.get_data()[..., :3], first)
    assert first[0, 0, 0] == 255       # top rows stay at the top


def test_box_mean_matches_brute_force():
    rng = np.random.default_rng(3)
    data = rng.normal(size=(23, 31))
    res = skydiff.box_mean(data, 2)
    for r, c in ((0, 0), (5, 7), (22, 30), (11, 0)):
        win = data[max(0, r - 2):r + 3, max(0, c - 2):c + 3]
        assert res[r, c] == pytest.approx(win.mean())


def _cloud_texture(size, shift=(0.0, 0.0), seed=5):
    """Smooth random 'cloud' texture, shifted by `shift` = (dx, dy) pixels
    (x to the right, y up = increasing row)."""
    rng = np.random.default_rng(seed)
    big = rng.normal(size=(size + 80, size + 80))
    for _ in range(3):
        big = skydiff.box_mean(big, 3)
    yi, xi = np.indices((size, size), dtype=float)
    return skydiff.sample_bilinear(big, yi + 40 - shift[1], xi + 40 - shift[0])


@pytest.mark.parametrize('shift', [(30.0, 0.0), (-45.5, 20.0),
                                   (0.0, -12.5)])
def test_cloud_motion_recovers_shift(shift):
    size = 401
    old = _cloud_texture(size) * 50 + 100
    cur = _cloud_texture(size, shift=shift) * 50 + 100
    res = skydiff.cloud_motion(cur, old)
    assert res is not None
    dx, dy, peak = res
    assert dx == pytest.approx(shift[0], abs=0.5)
    assert dy == pytest.approx(shift[1], abs=0.5)


def test_cloud_motion_ignores_fixed_features():
    # with strong fixed features (a "dome" silhouette and a glow) in the
    # frames, the differences of three frames still give the motion
    size = 401
    x, y, r = skydiff.radial_coords((size, size))
    fixed = 80.0 * np.exp(-((x - 60) ** 2 + (y - 40) ** 2) / 800.0)
    fixed[(y < -120) & (np.abs(x) < 40)] -= 100.0
    d = (-35.0, 12.0)
    f0, f1, f2 = [_cloud_texture(size, shift=(k * d[0], k * d[1])) * 50 +
                  100 + fixed for k in range(3)]
    dx, dy, peak = skydiff.cloud_motion(f2 - f1, f1 - f0)
    assert dx == pytest.approx(d[0], abs=1.0)
    assert dy == pytest.approx(d[1], abs=1.0)


def test_cloud_motion_none_without_clouds():
    # unrelated frames (no common structure): no motion reported
    size = 401
    old = _cloud_texture(size, seed=1) * 50 + 100
    cur = _cloud_texture(size, seed=2) * 50 + 100
    assert skydiff.cloud_motion(cur, old) is None


def test_cloud_map():
    size = SIZE
    sig = np.zeros((size, size), dtype=np.float32)
    # a "cloud" of changed pixels around alt 50, az 120 (south-east)
    scale = (size * 0.5) / 90.0
    x0, y0 = skydiff.altaz_to_xy(50.0, 120.0, scale)
    x, y, r = skydiff.radial_coords(sig.shape)
    sig[np.hypot(x - x0, y - y0) < 6 * scale] = 20.0
    sig[r > size * 0.5] = np.nan
    frac = skydiff.cloud_fraction(sig, threshold_sigma=5.0, radius_deg=3.0)
    cmap = skydiff.CloudMap(frac, threshold=0.2)
    assert cmap.is_cloudy(120.0, 50.0)
    assert not cmap.is_cloudy(300.0, 50.0)     # opposite side
    assert not cmap.is_cloudy(120.0, 80.0)
    # array query
    res = cmap.is_cloudy([120.0, 300.0], [50.0, 50.0])
    assert list(res) == [True, False]
    # below the horizon is outside the map
    assert np.isnan(cmap.fraction_at(0.0, -10.0))
