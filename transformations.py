# -*- coding: utf-8 -*-
import numpy as np
from collections import Iterable

def line(x, m, b):
    return m * x + b


def scale(x, y, xsc=1.0, ysc=1.0, **kwargs):
    """Scale data. For use with Transformer."""
    return x * xsc, y * ysc


def translate(x, y, xtrans=1.0, ytrans=1.0, **kwargs):
    """Translate data. For use with Transformer."""
    return x + xtrans, y + ytrans


def invertx(x, y, **kwargs):
    """Multiply x by -1"""
    return -x, y


def inverty(x, y, **kwargs):
    """Multiply y by -1"""
    return x, -y


def medfilt(x, y, ks=3, axis='y', **kwargs):
    """Use scipy.signal.medfilt to filter either the x or y data.
    
    Args:
        ks: and odd number that represents the width of the filter. See medfilt
            for more detail.
        axis: either 'x' or 'y'. Indicates which axis medfilt should be called
            on.
    """
    from scipy.signal import medfilt
    _verify_axis(axis)
    if axis == 'x':
        x = medfilt(x, ks)
    elif axis == 'y': 
        y = medfilt(y, ks)
    return x, y


def wrapped_medfilt(x, y, ks=3, axis='y', **kwargs):
    """Use scipy.signal.medfilt to filter either the x or y data. Also loop the
    filter around to prevent edge effects.

    If the data forms a closed loop the medfilt should account for this,
    otherwise there will be artifacts introduced in points near (less than
    ks-1 / 2) the edge of the data. This version of medfilt accounts for that
    by prepending the last ks data points and appending the first data points,
    running medfilt, and then removing the pre/appended points.
    
    Args:
        ks: and odd number that represents the width of the filter. See medfilt
            for more detail.
        axis: either 'x' or 'y'. Indicates which axis medfilt should be called
            on.
    """
    from scipy.signal import medfilt
    _verify_axis(axis)
    x = np.concatenate((x[-ks:], x, x[:ks]))
    y = np.concatenate((y[-ks:], y, y[:ks]))
    if axis == 'x':
        x = medfilt(x, ks)
    elif axis == 'y': 
        y = medfilt(y, ks)
    return x[ks:-ks], y[ks:-ks]


def remove_offset(x, y, axis='y', **kwargs):
    """Center data either horizontally or vertically (default to vertically).

    This is done by the crude method of just doing y -= y.mean() (if axis='y').

    Args:
        axis: either 'x' or 'y'. Indicates which axis should be centered.
    """
    _verify_axis(axis)
    if axis == 'y':
        y -= y.mean()
    elif axis == 'x':
        x -= x.mean()
    return x, y


def center(x, y, axis='y', **kwargs):
    """Center data either horizontally or vertically (default to vertically).

    Return y - average_of(y.max(), y.min())

    Args:
        axis: either 'x' or 'y'. Indicates which axis should be centered.
    """
    _verify_axis(axis)
    if axis == 'y':
        y -= 0.5 * (y.max() + y.min())
    elif axis == 'x':
        x -= 0.5 * (x.max() + x.min())
    return x, y


def unroll(x, y, axis='y', **kwargs):
    """Replace the x (y) data with np.arange(N) where N is the number of data
    points. 

    Args:
        axis: either 'x' or 'y'. Indicates which axis should be unrolled. So if
            axis is 'y', the x data will be thrown out and replaced with 
            arange(len(y)).
    """
    _verify_axis(axis)
    if axis == 'y':
        x = np.arange(len(x))
    elif axis == 'x':
        y = np.arange(len(y))
    return x, y


def spline(x, y, axis='y', s=3.0, **kwargs):
    """Replace y (x) data with a spline fit.

    See scipy.interpolate.UnivariateSpline for spline details.

    Args:
        axis: Either 'x' or 'y'. Indicates the axis to be fit.
    """
    from scipy.interpolate import UnivariateSpline as Spline
    _verify_axis(axis)
    if axis == 'y':
        xlin = np.arange(0, len(x))
        spl = Spline(xlin, y)
        spl.set_smoothing_factor(s)
        return x, spl(xlin)
    if axis == 'x':
        ylin = np.arange(0, len(y))
        spl = Spline(ylin, x)
        spl.set_smoothing_factor(s)
        return spl(ylin), y


def flatten_saturation(x, y, threshold=200, polarity='+', **kwargs):
    """Subtract a linear term from your data based on a fit to the saturation
    region.
    """
    from scipy.optimize import curve_fit
    if polarity == '+':
        mask = x > threshold
    elif polarity == '-':
        mask = x < threshold
    popt, pcov = curve_fit(line, x[mask], y[mask])
    return x, y - line(x, *popt)


def _verify_axis(axis):
    if axis not in ('x', 'y'):
        raise ValueError('Arg "axis" must be "x" or "y", not {}'.format(axis))


def second_half(x, y, **kwargs):
    N = len(x)
    half = int((N-1)/2)
    return x[half:], y[half:]
    

def first_half(x, y, **kwargs):
    N = len(x)
    half = int((N-1)/2)
    return x[:half], y[:half]


def middle(x, y, **kwargs):
    N = len(x)
    half = int((N-1)/2)
    Nseg = 100
    return x[half-Nseg:N-1-Nseg], y[half-Nseg:N-1-Nseg]
    

def ith_cycle(x, y, i, ncyc, delta=0, **kwargs):
    N = len(x)
    cycN = N/ncyc
    start, end = i*cycN+delta, (i+1)*cycN+delta
    return x[start:end], y[start:end]
    

def vertical_offset(x, y, dy=0.1, **kwargs):
    if not hasattr(vertical_offset, 'offset'):
        vertical_offset.offset = 0.0
    vertical_offset.offset += dy
    return x, y + vertical_offset.offset


def normalize(x, y, xlim=None, ylim=None, n_avg=1, **kwargs):
    """Move the data to fit in the box defined by xlim and ylim.


    Args:
        xlim: float or (float, float). The x data will be scaled and 
            translated to fit in the specified x window. If a float x0 is
            passed, the window will by (-x0, x0). If left as None, there
            will be no change to this axis.
        ylim: Same as xlim, but for y data.
        n_avg: Number of points to average over when looking for max/min of 
            data. For example, if n_avg=10 instead of using x.max() the average
            of the 10 greatest points would be used.
    """
    res = []
    for u, lim in zip((x, y), (xlim, ylim)):
        if lim is None:
            res.append(u)
            continue
        if not isinstance(lim, Iterable):
            lim = (-lim, lim)
        center = (lim[0] + lim[1]) / 2.0
        width = lim[1] - lim[0]
        u -= u.mean()
        uwidth = 2 * (_max_n_points(np.abs(u), n_avg).mean())
        res.append(u * (width / uwidth) + center)
    return res[0], res[1]


def simple_normalize(x, y, n_avg=1, axis='y', **kwargs):
    _verify_axis(axis)
    if axis == 'y':
        return x, y/_max_n_points(np.abs(y), n_avg).mean()
    else:
        return x/_max_n_points(np.abs(x), n_avg).mean(), y


def saturation_normalize(x, y, thresh=1.0, axis='y', **kwargs):
    return x, y / _saturation_level(x, y, thresh)
    # return x[np.abs(x) > thresh], y[np.abs(x) > thresh]


def _max_n_points(arr, n=1):
    return _n_nearest_points(arr, n, arr.max())


def _min_n_points(arr, n=1):
    return _n_nearest_points(arr, n, arr.min())


def _n_nearest_points(arr, n=1, x0=0.0, other_arr=None):
    """Return the n nearest points to x0."""
    asind = np.argsort(np.abs(arr - x0))
    if other_arr is None:
        return arr[asind][:n]
    else:
        return (arr[asind][:n], other_arr[asind][:n])


def _saturation_level(x, y, thresh):
    return np.abs(y)[np.abs(x) > thresh].mean()


def threshold_crop(x, y, thresh=np.float('inf'), axis='x', **kwargs):
    """Clip of all points that are above thresh.

    Args:
        thresh: all points greater than thresh (in data coords, not an index)
            will be cut out of the data, for both axes.
        axis: Either 'x' or 'y', indicating which axis will be compared to 
            thresh
    """
    ind = np.abs(x) < thresh
    return x[ind], y[ind]
    

def Hc_of(x, y, name_gleaner, ks=2, fit_ks_multiplier=5.0, **kwargs):
    v = float(name_gleaner.glean(kwargs['target'])['v'])
    # Setup indices
    gt0idx = x >= 0
    lt0idx = x < 0
    ymgt0idx = np.argmin(np.abs(y[gt0idx]))
    ymlt0idx = np.argmin(np.abs(y[lt0idx]))
    # Compute Hc
    Hc_gt0 = x[gt0idx][ymgt0idx-ks:ymgt0idx+ks].mean()
    Hc_lt0 = x[lt0idx][ymlt0idx-ks:ymlt0idx+ks].mean()
    Hc_avg = (abs(Hc_gt0) + abs(Hc_lt0))/2.
    vals = (v, Hc_lt0, Hc_gt0, Hc_avg)
    print(('V: {}   Hc: (-) {}, (+) {}, (avg) {}'.format(*vals)))
    # Compute sigma_y and m
    s_y = sigma_y(x, y)
    fksm = fit_ks_multiplier
    fitygt0 = y[gt0idx][ymgt0idx-fksm*ks:ymgt0idx+fksm*ks]
    fitxgt0= x[gt0idx][ymgt0idx-fksm*ks:ymgt0idx+fksm*ks]
    fitylt0 = y[lt0idx][ymlt0idx-fksm*ks:ymlt0idx+fksm*ks]
    fitxlt0 = x[lt0idx][ymlt0idx-fksm*ks:ymlt0idx+fksm*ks]
    try:
        (mgt0, _), _ = curve_fit(line, fitxgt0, fitygt0)
        (mlt0, _), _ = curve_fit(line, fitxlt0, fitylt0)
        m = (mgt0 + mlt0)/2.0
        s_x = proj_sigma(s_y, m)
        print(('sigma_y: {} proj_sigma: {} m: {}\n'.format(s_y, s_x, m)))
    except TypeError:
        print('Type Error in curve fit unable to project slope')
        print(('sigma_y: {}\n'.format(s_y)))
        m = np.float('inf')
        s_x = np.float('0.0')
    # return np.array(v), np.array(s_y)
    # return np.array(v), np.array(Hc_avg)
    return np.array([v]*3), np.array([Hc_avg+x for x in (-s_x, 0, s_x)])


def Mrem_of(x, y, name_gleaner, ks=3, **kwargs):
    v = float(name_gleaner.glean(kwargs['target'])['v'])
    # Setup indices
    N = len(x)
    inds = np.arange(N).reshape(4, N//4)
    yq03 = y[inds[[0, 3]]].reshape(N//2) # yq03 = y quarters 0 and 3
    xq03 = x[inds[[0, 3]]].reshape(N//2)
    yq12 = y[inds[[1, 2]]].reshape(N//2)
    xq12 = x[inds[[1, 2]]].reshape(N//2)
    xmq03i = np.argmin(np.abs(xq03)) # xmq03i = indsof x min quarters 0 and 3
    xmq12i = np.argmin(np.abs(xq12))
    # Average over the kernel size
    yq03avg = abs(np.mean(yq03[xmq03i-ks:xmq03i+ks]))
    yq12avg = abs(np.mean(yq12[xmq12i-ks:xmq12i+ks]))
    mrem = (yq03avg + yq12avg)/2.
    s_y = sigma_y(x, y)
    return np.array([v]*3), np.array([mrem+x for x in (-s_y, 0, s_y)])
