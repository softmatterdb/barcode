import os
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from analysis import run_analysis_pipeline
from core import BarcodeConfig, ChannelResults
from utils import vprint, set_verbose, Timer
from utils.analysis import check_channel_dim
from utils.reader import read_file, extract_nd2_metadata
from utils.setup import (
    create_output_directories,
    create_channel_output_dir,
    discover_files,
    setup_paths,
)
from utils.writer import gen_combined_barcode, results_to_csv


def determine_channels_to_process(
    config: BarcodeConfig, total_channels: int
) -> List[int]:
    """Determine which channels to process based on config settings."""
    if config.channels.parse_all_channels:
        vprint("Total Channels:", total_channels)
        return list(range(total_channels))
    else:
        channel_select = config.channels.selected_channel
        # Handle negative indexing
        while channel_select < 0:
            channel_select = total_channels + channel_select
        # Clamp to valid range
        if channel_select >= total_channels:
            channel_select = total_channels - 1
        vprint("Channel:", channel_select)
        return [channel_select]


def save_analysis_results(
    all_results: List[ChannelResults],
    base_path: str,
    base_name: str,
    config: BarcodeConfig,
    ff_loc: str,
    is_single_file: bool = False,
) -> None:
    """Save analysis results to CSV, generate barcodes, and save config."""

    # Determine output paths
    if is_single_file:
        csv_path = os.path.join(base_path, base_name + " summary.csv")
        barcode_path = os.path.join(base_path, base_name + " summary barcode")
        settings_path = os.path.join(base_path, base_name + " settings.yaml")
    else:
        csv_path = os.path.join(base_path, base_name + " Summary.csv")
        barcode_path = os.path.join(base_path, base_name + "_Summary Barcode")
        settings_path = os.path.join(base_path, base_name + " Settings.yaml")

    # Save CSV
    if all_results:
        if is_single_file:
            # Single file: fail fast if can't write
            results_to_csv(all_results, csv_path, just_metrics=False)
        else:
            # Directory: try alternate names if file exists
            try:
                results_to_csv(all_results, csv_path, just_metrics=False)
            except:
                counter = 1
                while True:
                    csv_path = os.path.join(
                        base_path, f"{base_name} Summary ({counter}).csv"
                    )
                    if not os.path.exists(csv_path):
                        break
                    counter += 1
                results_to_csv(all_results, csv_path, just_metrics=False)
    else:
        print("Warning: No results to write - all files may have failed processing")

    # Generate barcode if enabled
    if config.output.generate_dataset_barcode and all_results:
        try:
            # Multiple files: use all channels
            if not is_single_file and config.channels.parse_all_channels:
                gen_combined_barcode(all_results, barcode_path, separate_channels=False)
            else:
                gen_combined_barcode(all_results, barcode_path)

        except Exception as e:
            with open(ff_loc, "a", encoding="utf-8") as log_file:
                log_file.write(f"Unable to generate barcode, Exception: {str(e)}\n")

    # Save config
    config.save_to_yaml(settings_path)

    # Clean up empty fail file
    if os.stat(ff_loc).st_size == 0:
        os.remove(ff_loc)


def process_single_file(
    filepath: str, config: BarcodeConfig, fail_file_loc: str, count: int, total: int
) -> Tuple[List[ChannelResults], int]:
    """Process a single file and return analysis results."""

    # Load and validate file
    try:
        counts = [count, total]
        file = read_file(filepath, counts, config.quality.accept_dim_images)
        count, total = counts
    except TypeError as e:
        raise TypeError(e)

    if file is None:
        raise TypeError("File not read by BARCODE.")

    print(f"File Dimensions: {file.shape}")
    if not isinstance(file, np.ndarray):
        raise TypeError("File was not of the correct filetype")

    # Setup output directories
    figure_dir_name = create_output_directories(filepath)

    # Determine channels to process
    total_channels = min(file.shape)
    channels_to_process = determine_channels_to_process(config, total_channels)
    channel_results = []

    for channel in channels_to_process:
        vprint(f"Processing Channel: {channel}")

        # Check for dim channels
        is_dim = check_channel_dim(file[:, :, :, channel])
        if is_dim and not config.quality.accept_dim_channels:
            vprint("Channel too dim, not enough signal, skipping...")
            continue
        elif is_dim:
            vprint("Warning: channel is dim. Accuracy of screening may be limited.")

        # Create channel output directory
        channel_output_dir = create_channel_output_dir(figure_dir_name, channel)

        # Handle ND2 metadata extraction here
        extract_nd2_metadata(filepath, config)

        # Run analysis pipeline
        results, figures = run_analysis_pipeline(
            filepath, file, channel, config, channel_output_dir, fail_file_loc
        )

        results.filepath = filepath
        results.channel = channel
        # Set dim channel flag
        results.dim_channel_flag = 1 if is_dim else 0
        results.intensity.flag += 1 if is_dim else 0

        # Create summary visualization
        if config.output.save_graphs:
            from visualization import create_summary_visualization

            summary_path = os.path.join(channel_output_dir, "Summary Graphs.png")
            create_summary_visualization(figures, summary_path)

        channel_results.append(results)
        vprint("Channel Screening Completed")

    return channel_results, count


def process_multiple_files(
    files_to_process: List[str],
    config: BarcodeConfig,
    ff_loc: str,
    timer: Timer,
) -> List[ChannelResults]:
    """
    Process a list of files and return collected results.
    """
    all_results = []
    total_files = len(files_to_process)
    file_itr = 1

    for file_path in files_to_process:

        try:
            results, file_itr = process_single_file(
                file_path, config, ff_loc, file_itr, total_files
            )
        except TypeError as e:
            if "BARCODE" in str(e):
                continue
            print(e)
            continue
        except Exception as e:
            with open(ff_loc, "a", encoding="utf-8") as log_file:
                log_file.write(f"File: {file_path}, Exception: {str(e)}\n")
            continue

        if results == None:
            continue

        for result in results:
            all_results.append(result)

        # Timing and logging
        timer.log_time_since_last_log("Time Elapsed")

    return all_results


def run_analysis(root_dir: str, config: BarcodeConfig) -> None:
    """Run analysis on a file or directory path."""

    # Set global verbose mode
    set_verbose(config.output.verbose)

    # Discover files to process
    files_to_process = discover_files(root_dir)
    is_single_file = os.path.isfile(root_dir)

    if not is_single_file:
        vprint(root_dir)

    base_path, base_name, ff_loc, time_filepath = setup_paths(root_dir, is_single_file)

    timer = Timer(time_filepath)
    timer.start()

    all_results = process_multiple_files(files_to_process, config, ff_loc, timer)

    message = "Time Elapsed" + (
        " to Process Files" if is_single_file else " to Process Folder"
    )
    timer.log_time_since_start(message)
    timer.stop()

    save_analysis_results(
        all_results, base_path, base_name, config, ff_loc, is_single_file
    )
