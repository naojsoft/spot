"""
skydiff.py -- difference imaging for all-sky camera frames

Numpy routines used by the SkyCam plugin to build a differential
sky image that is useful for spotting clouds and other changes:

  * frames are reduced to a monochrome working image, downsampled by a
    block median and median filtered, which suppresses stars and noise
    while keeping the large-scale structure of clouds
  * the previous frame can be "derotated" to the time of the current
    frame (the sky rotates about the celestial pole by ~0.25 deg/min),
    so that stars and the Milky Way cancel in the difference
  * the previous frame is scaled to the current one to remove changes
    in camera exposure/gain or overall sky level
  * the difference is expressed in units of a robust estimate of the
    noise, so a single threshold works across cameras, and the fraction
    of the sky above that threshold is reported as a cloud cover (CC)

All frames are expected to be oriented as they are displayed in SPOT's
polar sky plot: zenith at the center, the horizon at the edge of the
array (radius = half the width), North up (+y, increasing row index)
and East to the left (-x), with an equidistant (r ~ zenith angle)
fisheye projection.
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from ginga import trcalc

# sky rotation rate, deg of hour angle per second of time
sidereal_rate_deg_s = 15.041068640 / 3600.0

# luminance weights for converting RGB to monochrome
lum_weights = np.array([0.2126, 0.7152, 0.0722])


def orient_frame(data_np, ctr_x, ctr_y, radius, rot_deg=0.0,
                 flip_x=False, flip_y=False, swap_xy=False, flip_ud=False):
    """Cut the sky circle out of a camera frame and orient it.

    The result is a square array of side 2 * radius + 1 with the zenith
    exactly at its center, even if the circle runs off the edge of the
    camera frame (that part is padded with zeros).  The frame is rotated
    about the zenith by `rot_deg`, then flipped as requested.

    Returns the oriented frame and a boolean coverage array that is True
    where the frame has real camera data.
    """
    ht, wd = data_np.shape[:2]
    xc, yc, r = int(round(ctr_x)), int(round(ctr_y)), int(round(radius))
    n = 2 * r + 1
    out = np.zeros((n, n) + data_np.shape[2:], dtype=data_np.dtype)
    cover = np.zeros((n, n), dtype=np.uint8)
    x0, y0 = xc - r, yc - r
    sx1, sy1 = max(0, x0), max(0, y0)
    sx2, sy2 = min(wd, xc + r + 1), min(ht, yc + r + 1)
    if sx2 > sx1 and sy2 > sy1:
        out[sy1 - y0:sy2 - y0, sx1 - x0:sx2 - x0] = data_np[sy1:sy2, sx1:sx2]
        cover[sy1 - y0:sy2 - y0, sx1 - x0:sx2 - x0] = 255

    if not np.isclose(rot_deg, 0.0):
        out = trcalc.rotate_clip(out, rot_deg, rotctr_x=r, rotctr_y=r)
        cover = trcalc.rotate_clip(cover, rot_deg, rotctr_x=r, rotctr_y=r)

    out = trcalc.transform(out, flip_x=flip_x, flip_y=flip_y,
                           swap_xy=swap_xy)
    cover = trcalc.transform(cover, flip_x=flip_x, flip_y=flip_y,
                             swap_xy=swap_xy)
    if flip_ud:
        out, cover = np.flipud(out), np.flipud(cover)
    return out, cover > 127


def to_mono(data_np):
    """Return a 2D float32 luminance image from a 2D or RGB(A) array."""
    data_np = np.asarray(data_np)
    if data_np.ndim == 3:
        if data_np.shape[2] >= 3:
            data_np = data_np[:, :, :3] @ lum_weights
        else:
            data_np = data_np[:, :, 0]
    return data_np.astype(np.float32)


def block_median(data_np, factor):
    """Downsample a 2D array by taking the median of `factor` x `factor`
    blocks.  Trailing rows/columns that don't fill a block are dropped.
    """
    factor = int(factor)
    if factor <= 1:
        return data_np
    ht, wd = data_np.shape
    ht_b, wd_b = ht // factor, wd // factor
    arr = data_np[:ht_b * factor, :wd_b * factor]
    arr = arr.reshape(ht_b, factor, wd_b, factor).swapaxes(1, 2)
    arr = arr.reshape(ht_b, wd_b, factor * factor)
    return np.median(arr, axis=2).astype(data_np.dtype, copy=False)


def median_filter(data_np, size):
    """Square median filter of a 2D array (edges are reflected)."""
    size = int(size)
    if size <= 1:
        return data_np
    pad = size // 2
    arr = np.pad(data_np, pad, mode='reflect')
    win = sliding_window_view(arr, (size, size))
    return np.median(win, axis=(2, 3)).astype(data_np.dtype, copy=False)


def get_bin_factor(width, work_size):
    """Integer binning factor that brings `width` to about `work_size`."""
    if work_size is None or work_size <= 0:
        return 1
    return max(1, int(round(width / work_size)))


def make_work_frame(data_np, bin_factor=1, median_size=3, coverage=None):
    """Reduce a camera frame to a working frame for differencing.
    Pixels outside `coverage` (if given), and any binned or filtered
    pixel that touches one, are NaN.
    """
    arr = to_mono(data_np)
    if coverage is not None:
        arr[~coverage] = np.nan
    arr = block_median(arr, bin_factor)
    arr = median_filter(arr, median_size)
    return arr


def radial_coords(shape):
    """Return x, y (pixels, relative to the image center, y up) and
    radius for each pixel of an array of `shape`.
    """
    ht, wd = shape[:2]
    cx, cy = (wd - 1) * 0.5, (ht - 1) * 0.5
    yi, xi = np.indices((ht, wd), dtype=np.float64)
    x, y = xi - cx, yi - cy
    return x, y, np.hypot(x, y)


def xy_to_altaz(x, y, scale):
    """Convert plot x, y (pixels) to alt, az (deg); scale is pix/deg."""
    alt = 90.0 - np.hypot(x, y) / scale
    az = np.degrees(np.arctan2(-x, y))
    return alt, az


def altaz_to_xy(alt, az, scale):
    """Convert alt, az (deg) to plot x, y (pixels); scale is pix/deg."""
    r = (90.0 - alt) * scale
    az_r = np.radians(az)
    return -r * np.sin(az_r), r * np.cos(az_r)


def altaz_to_hadec(alt, az, lat):
    """Horizontal to equatorial coordinates (all deg, az from N via E,
    hour angle positive to the West).
    """
    a, A, phi = np.radians(alt), np.radians(az), np.radians(lat)
    sin_dec = np.sin(a) * np.sin(phi) + np.cos(a) * np.cos(phi) * np.cos(A)
    dec = np.arcsin(np.clip(sin_dec, -1.0, 1.0))
    ha = np.arctan2(-np.cos(a) * np.sin(A),
                    np.sin(a) * np.cos(phi) -
                    np.cos(a) * np.sin(phi) * np.cos(A))
    return np.degrees(ha), np.degrees(dec)


def hadec_to_altaz(ha, dec, lat):
    """Equatorial to horizontal coordinates (inverse of altaz_to_hadec)."""
    H, d, phi = np.radians(ha), np.radians(dec), np.radians(lat)
    sin_alt = np.sin(d) * np.sin(phi) + np.cos(d) * np.cos(phi) * np.cos(H)
    alt = np.arcsin(np.clip(sin_alt, -1.0, 1.0))
    az = np.arctan2(-np.cos(d) * np.sin(H),
                    np.sin(d) * np.cos(phi) -
                    np.cos(d) * np.sin(phi) * np.cos(H))
    return np.degrees(alt), np.degrees(az)


def sample_bilinear(data_np, rows, cols):
    """Sample a 2D array at fractional (rows, cols) with bilinear
    interpolation.  Points outside the array are returned as NaN.
    """
    ht, wd = data_np.shape
    outside = (rows < 0) | (rows > ht - 1) | (cols < 0) | (cols > wd - 1)
    r = np.clip(rows, 0, ht - 1)
    c = np.clip(cols, 0, wd - 1)
    r0 = np.minimum(np.floor(r).astype(np.intp), ht - 2)
    c0 = np.minimum(np.floor(c).astype(np.intp), wd - 2)
    fr, fc = r - r0, c - c0
    res = (data_np[r0, c0] * (1 - fr) * (1 - fc) +
           data_np[r0, c0 + 1] * (1 - fr) * fc +
           data_np[r0 + 1, c0] * fr * (1 - fc) +
           data_np[r0 + 1, c0 + 1] * fr * fc)
    res = res.astype(np.float32)
    res[outside] = np.nan
    return res


def derotate(data_np, dt_sec, lat_deg):
    """Resample a frame taken `dt_sec` seconds earlier so that the sky in
    it lines up with a frame taken now.  Pixels whose sky position was
    below the horizon at the earlier time are NaN.
    """
    ht, wd = data_np.shape
    scale = (wd * 0.5) / 90.0
    x, y, _r = radial_coords(data_np.shape)
    alt, az = xy_to_altaz(x, y, scale)
    ha, dec = altaz_to_hadec(alt, az, lat_deg)
    # hour angle of the same sky position at the earlier time
    ha_old = ha - dt_sec * sidereal_rate_deg_s
    alt_old, az_old = hadec_to_altaz(ha_old, dec, lat_deg)
    x_old, y_old = altaz_to_xy(alt_old, az_old, scale)
    cx, cy = (wd - 1) * 0.5, (ht - 1) * 0.5
    res = sample_bilinear(data_np, y_old + cy, x_old + cx)
    res[(alt_old < 0) | (alt < 0)] = np.nan
    return res


def robust_sigma(arr):
    """Gaussian-equivalent standard deviation from the MAD."""
    if arr.size == 0:
        return np.nan
    med = np.median(arr)
    return 1.4826 * np.median(np.abs(arr - med))


def noise_sigma(diff_np, valid, step=1):
    """Estimate the pixel noise of a difference image from differences
    between pixels `step` apart.  Large smooth structures like clouds
    mostly cancel in these, so the estimate is not inflated by a
    genuinely changing sky.
    """
    ok = valid[:, step:] & valid[:, :-step]
    dd = (diff_np[:, step:] - diff_np[:, :-step])[ok]
    return robust_sigma(dd) / np.sqrt(2.0)


def sky_diff(cur, old, dt_sec=0.0, lat_deg=None, derotate_sky=True,
             threshold_sigma=5.0, max_za_deg=75.0, noise_step=3):
    """Compute a differential sky image between two working frames.

    Parameters
    ----------
    cur, old : 2D float arrays
        Current and previous working frames (see `make_work_frame`)

    dt_sec : float
        Time elapsed between the two frames

    lat_deg : float or None
        Site latitude; needed to derotate the previous frame

    derotate_sky : bool
        If True (and `lat_deg` is given), align the previous frame with
        the sky rotation before differencing

    threshold_sigma : float
        Pixels whose change exceeds this many sigma count as changed

    max_za_deg : float
        Only pixels within this zenith angle are used for statistics,
        to avoid the horizon, trees, domes, etc.

    noise_step : int
        Pixel spacing used to estimate noise (use at least the median
        filter size, since filtered neighbors are correlated)

    Returns
    -------
    res : dict
        sig : 2D float32 array of the change in units of sigma; NaN
              where there is no valid data
        cc_pct : percentage of the sky (within max_za_deg) that changed
        sigma : noise estimate, in data units
        gain : scale factor that was applied to the previous frame
        mask : boolean array of pixels used for the statistics
    """
    if cur.shape != old.shape:
        raise ValueError("frames differ in shape: {} vs {}".format(
            cur.shape, old.shape))

    if derotate_sky and lat_deg is not None and dt_sec > 0:
        old = derotate(old, dt_sec, lat_deg)

    _x, _y, r = radial_coords(cur.shape)
    scale = (cur.shape[1] * 0.5) / 90.0
    in_sky = r <= 90.0 * scale
    valid = in_sky & np.isfinite(old) & np.isfinite(cur)
    mask = valid & (r <= max_za_deg * scale)

    # match the overall level of the previous frame to the current one
    gain = 1.0
    if mask.any():
        med_old = np.median(old[mask])
        if med_old > 0:
            gain = float(np.median(cur[mask]) / med_old)
    diff = cur - gain * old

    sigma = noise_sigma(np.where(valid, diff, 0.0), valid, step=noise_step)
    if not np.isfinite(sigma) or sigma <= 0:
        # e.g. identical or flat frames; avoid dividing by zero
        sigma = 1.0
    sig = (diff / sigma).astype(np.float32)
    sig[~valid] = np.nan

    n = int(mask.sum())
    cc_pct = 0.0
    if n > 0:
        cc_pct = 100.0 * float(np.count_nonzero(
            np.abs(sig[mask]) > threshold_sigma)) / n

    return dict(sig=sig, cc_pct=cc_pct, sigma=float(sigma), gain=gain,
                mask=mask)
