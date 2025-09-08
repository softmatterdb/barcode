import os, matplotlib
from typing import List
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.axes import Axes
from matplotlib import colors
from utils.intensity_distribution import histogram, mean

# from analysis.flow import FlowOutput

def save_binarization_visualization(original_frame: np.ndarray, binarized_frame: np.ndarray, frame_idx: int, name: str):
    compare_fig, comp_axs = plt.subplots(ncols = 2, figsize=(10, 5))
    comp_axs[0].imshow(original_frame, cmap='gray')
    comp_axs[1].imshow(binarized_frame, cmap='gray')
    ticks_adj = ticker.FuncFormatter(lambda x, _: '{0:g}'.format(x * 2))
    comp_axs[1].xaxis.set_major_formatter(ticks_adj)
    comp_axs[1].yaxis.set_major_formatter(ticks_adj)
    comp_axs[0].axis('off')  # Turn off the axis
    comp_axs[1].axis('off')  # Turn off the axis
    plt.savefig(os.path.join(name, f'Binarization Frame {frame_idx} Comparison.png'))
    plt.close('all')
    return

def save_flow_field_visualization(flow, start_frame: int, end_frame: int, name: str, downsample: int):
    downU, downV, directions, speed = flow
    img_shape_ratio = downU.shape[0] / downU.shape[1]
    fig, ax = plt.subplots(figsize=(10 * img_shape_ratio,10))
    norm = colors.Normalize(vmin = 0, vmax = np.max(speed))
    cma = matplotlib.cm.plasma
    sm = matplotlib.cm.ScalarMappable(cmap = cma, norm = norm)
    q = ax.quiver(downU, downV, norm(speed))
    plt.colorbar(sm, ax = ax)
    figname = f'Frame {start_frame} to {end_frame} Flow Field.png'
    figpath = os.path.join(name, figname)
    ticks_adj = ticker.FuncFormatter(lambda x, _: '{0:g}'.format(x * downsample))
    ax.xaxis.set_major_formatter(ticks_adj)
    ax.yaxis.set_major_formatter(ticks_adj)
    ax.set_aspect(aspect=1, adjustable='box')
    fig.savefig(figpath)
    plt.close('all')

def save_intensity_plots(first_frame, last_frame, bin_number, noise_threshold, last_frame_idx, max_intensity) -> plt.Figure:
    fig, ax = plt.subplots(figsize = (5, 5))
    i_count, i_bins = histogram(first_frame, bin_number, noise_threshold)
    f_count, f_bins = histogram(last_frame, bin_number, noise_threshold)
    i_mean = mean(i_bins, i_count)
    f_mean = mean(f_bins, f_count)
    ax.plot(i_bins, i_count, '^-', ms=4, c='darkred', alpha=0.6, label= "Frame 0 Intensity Distribution")
    ax.plot(f_bins, f_count, 'v-', ms=4, c='purple',   alpha=0.6, label= f"Frame {last_frame_idx - 1} Intensity Distribution")
    ax.axvline(x=i_mean, ms = 4, c = 'darkred', alpha=1, label="Frame 0 Mean")
    ax.axvline(x=f_mean, ms = 4, c = 'purple', alpha=1, label=f"Frame {last_frame_idx - 1} Mean")
    ax.axhline(0, color='dimgray', alpha=0.6)
    ax.set_xlabel("Pixel intensity value")
    ax.set_ylabel("Probability")
    ax.set_yscale('log')
    ax.set_xlim(0,max_intensity)
    ax.legend()
    return fig

def save_binarization_plots(void_percent_gain_list: np.ndarray, island_percent_gain_list: np.ndarray, num_frames: int, frame_step: int) -> plt.Figure:
    fig, ax = plt.subplots(figsize = (5, 5))
    stop_index = len(void_percent_gain_list)
    plot_range = np.arange(0, stop_index * frame_step, frame_step)
    plot_range[-1] = num_frames - 1 if stop_index * frame_step >= num_frames else stop_index * frame_step
    ax.plot(plot_range, 100 * void_percent_gain_list, c='b', label='Original Void Size Proportion')
    ax.plot(plot_range, 100 * island_percent_gain_list, c='r', label='Original Island Size Proportion')
    ax.set_xticks(plot_range[::10])
    if stop_index * frame_step >= num_frames != 0:
        ax.set_xlim(left=None, right=num_frames - 1)
    ax.set_xlabel("Frames")
    ax.set_ylabel("Percentage of Original Size")
    ax.legend()
    return fig

def create_summary_visualization(figures: List[plt.Figure], output_path: str) -> None:
    """Create combined summary plot from analysis figures."""
    if not figures or all(figures == None):
        return

    num_figs = len(figures)
    fig = plt.figure(figsize=(5 * num_figs, 5))

    for i, source_fig in enumerate(figures):
        ax = source_fig.axes[0]
        ax.figure = fig
        fig.add_axes(ax)
        if num_figs == 2:
            # Position axes side by side
            if i == 0:
                ax.set_position([1.5 / 10, 1 / 10, 4 / 5, 4 / 5])
            else:
                ax.set_position([11.5 / 10, 1 / 10, 4 / 5, 4 / 5])

    plt.savefig(output_path)
    plt.close(fig)
    plt.close("all")