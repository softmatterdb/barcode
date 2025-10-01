from typing import List

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from core import ChannelResults, Units, get_data_limits


def gen_combined_barcode(
    results: List[ChannelResults],
    figpath: str,
    separate_channels: bool = True,
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

    def format_header_with_units(header: str, unit: Units) -> str:
        """Format header with unit annotation."""
        if unit == Units.NONE:
            return header
        return f"{header}\n({unit.value})"

    # Convert structured results to array format (metrics only, no channel/flags)
    data_arrays = [result.to_array(just_metrics=True) for result in results]

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
    headers = ChannelResults.get_headers(just_metrics=True)
    metrics = ChannelResults.get_metrics(just_metrics=True)
    units = results[0].get_units(just_metrics=True)
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

def gen_extended_barcode(
    results: List[ChannelResults],
    figpath: str,
    separate_channels: bool = True,
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

    def format_header_with_units(header: str, unit: Units) -> str:
        """Format header with unit annotation."""
        if unit == Units.NONE:
            return header
        return f"{header}\n({unit.value})"

    # Convert structured results to array format (metrics only, no channel/flags)
    print("Checkpoint 0")
    data_arrays = [result.to_extended_array(just_metrics=True) for result in results]

    print("Checkpoint 1")

    if not data_arrays:
        return

    data = (
        np.vstack(data_arrays)
        if len(data_arrays) > 1
        else data_arrays[0].reshape(1, -1)
    )

    print(data)

    unique_channels = np.unique([result.channel for result in results])
    unique_channels = unique_channels[~np.isnan(unique_channels)]

    # Get headers and units from structured results
    headers = ChannelResults.get_extended_headers(just_metrics=True)
    metrics = ChannelResults.get_extended_metrics(just_metrics=True)
    units = results[0].get_extended_units(just_metrics=True)
    num_metrics = len(metrics)

    print("Checkpoint 2")

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

        print("Checkpoint 3")
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

        print("Checkpoint 4")

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

        print("Checkpoint 5")
        plt.subplots_adjust(wspace=1, hspace=0.05)

        # Create main barcode visualization
        barcode_ax = fig.add_subplot(gs[0, :])
        barcode_image = np.repeat(barcode, 5, axis=0)  # Make bars more visible

        barcode_ax.imshow(barcode_image, aspect="auto")
        barcode_ax.axis("off")

        print("Checkpoint 6")

        # Save figure
        fig.savefig(channel_figpath, bbox_inches="tight", pad_inches=0)
        plt.close("all")

        print("Final Checkpoint")

        if not separate_channels:
            break
