import csv
from itertools import compress
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from typing import List
from core.results import ChannelResults
from core.metrics import Units, get_data_limits

def check_limits(limit, thresh):
    if thresh < limit[0]:
        limit[0] = thresh
    elif thresh > limit[1]:
        limit[1] = thresh
    return limit

def update_limits(limits, new_limits):
    for i in range(len(limits)):
        limits[i, 0] = min(limits[i, 0], new_limits[i, 0])
        limits[i, 1] = max(limits[i, 1], new_limits[i, 1])
    return limits

def add_units(metric):
    frame_percent_unit = "\n(% of Frames)"
    fov_percent_unit = "\n(% of FOV)"
    unit_less = ""
    percent_change_unit = "\n(Fractional Change)"
    directional_unit = "\n(rads)"
    speed_unit = "\n($\\mu$m/s)"
    units = {'Connectivity': frame_percent_unit, 'Maximum Island Area': fov_percent_unit, 
             'Maximum Void Area': fov_percent_unit, 'Island Area Change': percent_change_unit, 
             'Void Area Change': percent_change_unit, 'Initial Maximum Island Area': fov_percent_unit, 
             'Initial 2nd Maximum Island Area': fov_percent_unit, 'Maximum Kurtosis': unit_less, 
             'Maximum Median Skewness': unit_less, 'Maximum Mode Skewness': unit_less,
             'Kurtosis Change': unit_less, 'Median Skewness Change': unit_less, 
             'Mode Skewness Change': unit_less, 'Mean Speed': speed_unit, 'Speed Change': speed_unit,
             'Mean Flow Direction': directional_unit, 'Flow Directional Spread': directional_unit}
    return metric + units[metric]

def generate_comparison_barcodes(results_list: List[List[ChannelResults]], figpaths: List[str], separate_channels: bool = False):
    if not results_list:
        return

    def format_header_with_units(header: str, unit: Units) -> str:
        """Format header with unit annotation."""
        if unit == Units.NONE:
            return header
        return f"{header}\n({unit})"
    limits_list = []
    for results in results_list:
        data_arrays = [result.to_array(just_metrics=True) for result in results]

        if not data_arrays:
            return

        data = (
            np.vstack(data_arrays)
            if len(data_arrays) > 1
            else data_arrays[0].reshape(1, -1)
        )

        headers = ChannelResults.get_headers(just_metrics=True)
        metrics = ChannelResults.get_metrics(just_metrics=True)
        units = results[0].get_units(just_metrics=True)
        num_metrics = len(metrics)

        limits_list.append(get_data_limits(data, metrics, units))
    limits_list = np.array(limits_list)
    min_limits = np.min(limits_list[:,:,0], axis=0)
    max_limits = np.max(limits_list[:,:,1], axis=0)
    overall_limits = [[mini, maxi] for mini, maxi in zip(min_limits, max_limits)]

    norms = [mpl.colors.Normalize(vmin=limit[0], vmax=limit[1]) for limit in overall_limits]
    cmap = plt.get_cmap("plasma")
    cmap.set_bad("black")

    for results, figpath in zip(results_list, figpaths):
        unique_channels = np.unique([result.channel for result in results])
        unique_channels = unique_channels[~np.isnan(unique_channels)]
        channels = np.array([result.channel for result in results])
        data_arrays = [result.to_array(just_metrics=True) for result in results]
        data = (np.vstack(data_arrays) if len(data_arrays) > 1
            else data_arrays[0].reshape(1, -1))
        
        for channel in unique_channels:
            if separate_channels:
                channel_figpath = f"{figpath} (Channel {int(channel)}).png"
                channel_mask = channels == channel
                filtered_data = data[channel_mask]
            else:
                channel_figpath = f"{figpath}.png"
                channel_mask = np.isin(channels, unique_channels)
                filtered_data = data[channel_mask]

            if filtered_data.size == 0:
                continue

            # Ensure 2D array
            if len(filtered_data.shape) == 1:
                filtered_data = filtered_data.reshape(1, -1)

            # Set up figure dimensions
            height = 9 * int(len(filtered_data) / 40) if len(filtered_data) > 40 else 9
            fig = plt.figure(figsize=(15, height), dpi=300)

            if height == 9:
                height_ratio = [5, 2]
            else:
                height_ratio = [int(2 / 5 * height), 1]

            gs = fig.add_gridspec(
                nrows=2, ncols=num_metrics * 8, height_ratios=height_ratio
            )

            # Create barcode array
            barcode = np.repeat(
                np.expand_dims(np.zeros_like(filtered_data), axis=2), 4, axis=2
            )

            # Fill barcode with colors and create colorbars
            for idx in range(num_metrics):
                norm = norms[idx]
                barcode[:, idx] = cmap(norm(filtered_data[:, idx]))

                # Create colorbar
                norm_ax = fig.add_subplot(gs[1, 8 * idx : 8 * idx + 1])
                cbar = norm_ax.figure.colorbar(
                    mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                    cax=norm_ax,
                    orientation="vertical",
                )

                # Use structured units for labeling
                cbar.set_label(format_header_with_units(headers[idx], units[idx]), size=7)
                cbar.formatter.set_powerlimits((-2, 2))
                cbar.ax.tick_params(labelsize=6)

            plt.subplots_adjust(wspace=1, hspace=0.05)

            # Create main barcode visualization
            barcode_ax = fig.add_subplot(gs[0, :])
            barcode_image = np.repeat(barcode, 5, axis=0)  # Make bars more visible

            barcode_ax.imshow(barcode_image, aspect="auto")
            barcode_ax.axis("off")

            # Save figure
            fig.savefig(channel_figpath, bbox_inches="tight", pad_inches=0)
            plt.close("all")

            if not separate_channels:
                break
    return

def generate_combined_barcode(
    results: List[ChannelResults],
    figpath: str,
    separate_channels: bool = True,
    physical_units: bool = False,
    metrics_to_visualize: List[bool] = None,
) -> None:
    """
    Generate barcode visualization from structured ChannelResults.

    Args:
        results: List of ChannelResults to visualize
        figpath: Base path for output figures (without extension)
        sort_metric: Optional metric name to sort results by
        separate_channels: If True, create separate figures per channel
    """
    if not results:
        return
    
    if metrics_to_visualize is None:
        metrics_to_visualize = [True] * len(ChannelResults.get_metrics(just_metrics = True))

    def format_header_with_units(header: str, unit: Units) -> str:
        """Format header with unit annotation."""
        if unit == Units.NONE:
            return header
        return f"{header}\n({unit})"

    # Convert structured results to array format (metrics only, no channel/flags)
    data_arrays = [np.fromiter(compress(result.to_physical_array(just_metrics=True), metrics_to_visualize), float) if physical_units else 
                   np.fromiter(compress(result.to_array(just_metrics=True), metrics_to_visualize), float) for result in results]    
    if not data_arrays:
        return

    data = (
        np.vstack(data_arrays)
        if len(data_arrays) > 1
        else data_arrays[0].reshape(1, -1)
    )

    unique_channels = np.unique([result.channel for result in results])
    unique_channels = unique_channels[~np.isnan(unique_channels)]

    # Get headers and units from structured results
    if physical_units:
        headers = list(compress(ChannelResults.get_physical_headers(just_metrics=True), metrics_to_visualize))
        metrics = list(compress(ChannelResults.get_physical_metrics(just_metrics=True), metrics_to_visualize))
        units = list(compress(results[0].get_physical_units(just_metrics=True), metrics_to_visualize))
    else:
        headers = list(compress(ChannelResults.get_headers(just_metrics=True), metrics_to_visualize))
        metrics = list(compress(ChannelResults.get_metrics(just_metrics=True), metrics_to_visualize))
        units = list(compress(results[0].get_units(just_metrics=True), metrics_to_visualize))
    num_metrics = len(metrics)

    limits = get_data_limits(data, metrics, units)

    # Get channel info (needed for visualization)
    channels = np.array([result.channel for result in results])

    # Set up colormap
    norms = [mpl.colors.Normalize(vmin=limit[0], vmax=limit[1]) for limit in limits]
    cmap = plt.get_cmap("plasma")
    cmap.set_bad("black")

    # Generate visualizations
    for channel in unique_channels:
        if separate_channels:
            channel_figpath = f"{figpath} (Channel {int(channel)}).png"
            channel_mask = channels == channel
            filtered_data = data[channel_mask]
        else:
            channel_figpath = f"{figpath}.png"
            channel_mask = np.isin(channels, unique_channels)
            filtered_data = data[channel_mask]

        if filtered_data.size == 0:
            continue

        # Ensure 2D array
        if len(filtered_data.shape) == 1:
            filtered_data = filtered_data.reshape(1, -1)

        # Set up figure dimensions
        height = 9 * int(len(filtered_data) / 40) if len(filtered_data) > 40 else 9
        fig = plt.figure(figsize=(num_metrics, height), dpi=300)

        if height == 9:
            height_ratio = [5, 2]
        else:
            height_ratio = [int(2 / 5 * height), 1]

        gs = fig.add_gridspec(
            nrows=2, ncols=num_metrics * 8, height_ratios=height_ratio
        )

        # Create barcode array
        barcode = np.repeat(
            np.expand_dims(np.zeros_like(filtered_data), axis=2), 4, axis=2
        )

        # Fill barcode with colors and create colorbars
        for idx in range(num_metrics):
            norm = norms[idx]
            barcode[:, idx] = cmap(norm(filtered_data[:, idx]))

            # Create colorbar
            norm_ax = fig.add_subplot(gs[1, 8 * idx : 8 * idx + 1])
            cbar = norm_ax.figure.colorbar(
                mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                cax=norm_ax,
                orientation="vertical",
            )

            # Use structured units for labeling
            cbar.set_label(format_header_with_units(headers[idx], units[idx]), size=7)
            cbar.formatter.set_powerlimits((-2, 2))
            cbar.ax.tick_params(labelsize=6)

        plt.subplots_adjust(wspace=1, hspace=0.05)

        # Create main barcode visualization
        barcode_ax = fig.add_subplot(gs[0, :])
        barcode_image = np.repeat(barcode, 5, axis=0)  # Make bars more visible

        barcode_ax.imshow(barcode_image, aspect="auto")
        barcode_ax.axis("off")

        # Save figure
        fig.savefig(channel_figpath, bbox_inches="tight", pad_inches=0)
        plt.close("all")

        if not separate_channels:
            break