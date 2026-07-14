import matplotlib.pyplot as plt
plt.style.use('utils/presentation.mplstyle')
from matplotlib import ticker, colors
import numpy as np
from typing import Tuple
from utils import groupAvg

def save_ib_preview(ax: plt.Axes | Tuple[plt.Axes, plt.Axes], 
                    frame: np.ndarray | Tuple[np.ndarray, np.ndarray], frame_num: int, include_title: bool):
    if isinstance(ax, plt.Axes):
        if include_title:
            title = ax.annotate(text=f'Frame Number {frame_num}', xy=(0.5, 1.03), xycoords = "axes fraction", ha="center")
        ax.axis('off')
        artist = ax.imshow(frame, cmap = "gray", aspect = 'auto')
        plt.tight_layout()
        if include_title:
            return [artist, title]
        return [artist]
    else:
        ax[0].axis('off')
        ax[1].axis('off')
        artist1 = ax[0].imshow(frame[0], cmap='gray')
        artist2 = ax[1].imshow(frame[1], cmap = 'gray')
        plt.tight_layout()
        return [artist1, artist2]


def save_of_preview(ax: plt.Axes, frame: np.ndarray, frame_num: int, limits: tuple, include_title: bool, **kwargs):
    downsample, um_px_ratio, flow_scale = kwargs["downsample"], kwargs["um_pixel_ratio"], kwargs["flow_scale"]
    ax.axis('on')
    frame = groupAvg(frame, downsample)
    rows, cols = frame.shape[:2]
    x = np.arange(cols)
    y = np.arange(rows)
    X, Y = np.meshgrid(x, y)
    vx, vy, speed = frame[:,:,0], frame[:,:,1], np.linalg.norm(frame, axis = 2)
    norm = colors.Normalize(0, limits[1])
    artist = ax.quiver(X, Y, vx, vy, norm(speed), cmap = 'plasma', scale = limits[1] / flow_scale, scale_units = 'x')
    ticks_adj = ticker.FuncFormatter(lambda x, _: '{0:g}'.format(x * downsample * um_px_ratio))
    ax.xaxis.set_major_formatter(ticks_adj)
    ax.yaxis.set_major_formatter(ticks_adj)
    ax.set_aspect(aspect=1, adjustable='box')
    if include_title:
        title = ax.annotate(text=f'Frame Number {frame_num}', xy=(0.5, 1.03), xycoords = "axes fraction", ha="center")
    plt.tight_layout()
    if include_title:
        return [artist, title]
    return [artist]

def save_id_preview(ax: plt.Axes, frame: np.ndarray, limits: tuple, frame_num: int, include_title: bool):
    ax.axis('on')
    print(limits)
    plt.setp(ax, xlabel = 'Pixel Intensity Value', ylabel = 'Probability', 
             xlim = (0, limits[0]), ylim = (limits[1], 1), yscale='log')
    i, p_i = frame[:,0], frame[:,1]
    artist = ax.scatter(i, p_i, marker = "o", s=4, color = 'purple')
    if include_title:
        title = ax.annotate(text=f'Frame Number {frame_num}', xy=(0.5, 1.03), xycoords = "axes fraction", ha="center")
    plt.tight_layout()
    if include_title:
        return [artist, title]
    return [artist]

def save_correlation_preview(ax: plt.Axes, frame: np.ndarray, limits: tuple, frame_num: int, include_title: bool, color = 'purple', c_type = "Spatial_Autocorrelation", use_lines = True):
    from core.metrics import Units
    ax.axis('on')
    ylabel = "$g(r)$" if c_type == "Spatial_Autocorrelation" else "$\\frac{\\langle v(r) \\cdot v(0)\\rangle}{\\langle||v(0)^2||\\rangle}$"
    plt.setp(ax, xlabel = f'$r$ ({Units.LENGTH})', ylabel = ylabel, 
                xlim = (0, 1.05 * limits[0]), ylim = (limits[1], 1.05 * limits[2]))
    r, c_r = frame[:,0], frame[:,1]
    artist = ax.scatter(r, c_r, marker = "o", s=4, color = color)
    if use_lines:
        cutoff = np.exp(-1) if c_type == "Spatial_Autocorrelation" else 0.5
        ax.hlines(cutoff, xmin = 0, xmax = 1.05 * limits[0], colors = "gray", linestyles="dashed")
    if include_title:
        title = ax.annotate(text=f'Frame Number {frame_num}', xy=(0.5, 1.03), xycoords = "axes fraction", ha="center")
    plt.tight_layout()
    if include_title:
        return [artist, title]
    return [artist]


def save_vector_field_preview(ax: plt.Axes, frame: np.ndarray, limits: tuple, frame_num: int, include_title: bool):
    if include_title:
        title = ax.annotate(text=f'Frame Number {frame_num}', xy=(0.5, 1.03), xycoords = "axes fraction", ha="center")
    ax.axis('off')
    norm = colors.Normalize(limits[0], limits[1])
    artist = ax.imshow(frame, cmap = "plasma", norm = norm, aspect = 'auto')
    plt.tight_layout()
    if include_title:
        return [artist, title]
    return [artist]

def save_rds_visualization(ax: plt.Axes, frame_num: int, frame: np.ndarray, rds_type: str, limits: tuple = None, include_title: bool = True, **kwargs) -> plt.Artist:
    if rds_type == "Image_Binarization":
        artists = save_ib_preview(ax, frame, frame_num, include_title)
    elif rds_type == "Optical_Flow":
        artists = save_of_preview(ax, frame, frame_num, limits, include_title, **kwargs)
    elif rds_type == "Intensity_Distribution":
        artists = save_id_preview(ax, frame, limits, frame_num, include_title)
    elif rds_type == "Vector_Fields":
        artists = save_vector_field_preview(ax, frame, limits, frame_num, include_title)
    elif rds_type in ["Spatial_Autocorrelation", "Velocity_Correlation"]:
        artists = save_correlation_preview(ax, frame, limits, frame_num, include_title, c_type = rds_type)
    return artists
