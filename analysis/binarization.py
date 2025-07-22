import os
from dataclasses import dataclass
from typing import Tuple, List, Optional

import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage
from skimage.measure import label, regionprops
from skimage import io, color, filters, measure, morphology
from utils.setup import setup_csv_writer
from utils.analysis import inv, group_avg, binarize, top_ten_average
from core import BinarizationConfig, OutputConfig, BinarizationResults
from utils import vprint


@dataclass
class FrameMetrics:
    """Metrics for a single binarized frame."""

    island_area: float
    island_area_2nd: float
    island_position: Optional[Tuple[float, float]]
    is_connected: bool
    void_area: float
    regions: List


def check_span(frame):
    def check_connected(frame, axis=0):
        # Ensures that either connected across left-right or up-down axis
        if not axis in [0, 1]:
            raise Exception("Axis must be 0 or 1.")

        struct = ndimage.generate_binary_structure(2, 2)

        frame_connections, num_features = ndimage.label(input=frame, structure=struct)

        if axis == 0:
            labeled_first = np.unique(frame_connections[0, :])
            labeled_last = np.unique(frame_connections[-1, :])

        if axis == 1:
            labeled_first = np.unique(frame_connections[:, 0])
            labeled_last = np.unique(frame_connections[:, -1])

        labeled_first = set(labeled_first[labeled_first != 0])
        labeled_last = set(labeled_last[labeled_last != 0])

        if labeled_first.intersection(labeled_last):
            return 1
        else:
            return 0

    return check_connected(frame, axis=0) or check_connected(frame, axis=1)


def find_largest_void(frame: np.ndarray, find_void: bool, num: int = 1):

    eval_frame = inv(frame) if find_void else frame

    # Identify the regions of connectivity 2
    labeled_frame, num_labels = label(eval_frame, connectivity=2, return_num=True)
    if num_labels == 0:
        return frame.shape[0] * frame.shape[1]

    # Determines the region properties of the labeled frame
    regions = regionprops(labeled_frame)

    if not regions:
        return frame.shape[0] * frame.shape[1]

    regions_sorted = sorted(regions, key=lambda r: r.area, reverse=True)
    largest_regions = regions_sorted[:num]
    areas = [region.area for region in largest_regions]
    if num != len(areas):
        areas.append(0)
    return areas  # Returns largest region(s) area


def largest_island_position(frame: np.ndarray):

    # Identify the regions of connectivity 2
    labeled_frame, num_labels = label(frame, connectivity=2, return_num=True)
    if num_labels == 0:
        return None

    # Determines the region properties of the labeled frame
    regions = regionprops(labeled_frame)

    # Determines the region with the maximum area
    largest_region = max(regions, key=lambda r: r.area)

    return largest_region.centroid  # Returns largest region centroid


def write_binarization_data(csvwriter, frame_data: np.ndarray, frame_idx: int):
    """Write binarized frame data to CSV."""
    if not csvwriter:
        return

    csvwriter.writerow([str(frame_idx)])
    csvwriter.writerows(frame_data)
    csvwriter.writerow([])

def analyze_binarized_frame(frame: np.ndarray) -> FrameMetrics:
    """Analyze a single binarized frame and return metrics."""
    # Calculate all metrics for this frame
    island_area = find_largest_void(frame, find_void=False)[0]
    island_area_2nd = find_largest_void(frame, find_void=False, num=2)[1]
    island_position = largest_island_position(frame)
    is_connected = check_span(frame)
    void_area = find_largest_void(frame, find_void=True)[0]

    # Get region data
    labeled_frame, num_labels = label(frame, connectivity=2, return_num=True)
    regions = regionprops(labeled_frame)

    return FrameMetrics(
        island_area=island_area,
        island_area_2nd=island_area_2nd,
        island_position=island_position,
        is_connected=is_connected,
        void_area=void_area,
        regions=regions,
    )


def calculate_frame_indices(num_frames: int, step: int) -> List[int]:
    """Calculate frame indices to process (matching original logic)."""
    frame_indices = list(range(0, num_frames, step))

    # Add final frame if not evenly divisible by step
    final_frame = num_frames - 1
    if final_frame % step != 0:
        frame_indices.append(final_frame)

    return frame_indices


def calculate_visualization_frames(num_frames: int, step: int) -> set:
    """Calculate which frames should have visualizations saved (matching original logic)."""
    if num_frames <= 0:
        return set()

    mid_point_arr = list(range(0, num_frames, step))
    if len(mid_point_arr) <= 1:
        return {0} if num_frames > 0 else set()

    mid_point = mid_point_arr[int((len(mid_point_arr) - 1) / 2)]
    return {0, mid_point, num_frames}


def track_void(
    image: np.ndarray,
    name: str,
    bin_config: BinarizationConfig,
    out_config: OutputConfig,
    csvwriter=None,
) -> Tuple[List[float], List[float], List[float], List[bool]]:
    """
    Track void and island metrics across video frames using modular functions.

    Returns:
        Tuple of (void_sizes, island_areas, island_areas_2nd, connectivity_flags)
    """
    num_frames = len(image)
    threshold = bin_config.threshold_offset
    area_size=bin_config.area_size
    step = bin_config.frame_step
    binning_factor = bin_config.binning_number
    # Calculate which frames to process and visualize
    frame_indices = calculate_frame_indices(num_frames, step)
    save_frames = set()
    if out_config.save_graphs:
        save_frames = calculate_visualization_frames(num_frames, step)

    # Initialize result lists
    void_lst = []
    island_area_lst = []
    island_area_lst2 = []
    connected_lst = []
    region_lst = []

#########added binning factor
    # Process each frame
    for frame_idx in frame_indices:
        # Binarize and downsample frame       
        downsampled_frame = group_avg(image[frame_idx], binning_factor)
        binarized_frame = binarize(downsampled_frame, threshold) 
        filtered_frame=morphology.remove_small_objects(binarized_frame>0, min_size=int(area_size))
        # Analyze frame metrics
        
        metrics = analyze_binarized_frame(binarized_frame>0)
        # Write CSV data if enabled
        if csvwriter:
            write_binarization_data(csvwriter, filtered_frame.astype(int), frame_idx)
          
        # Save visualization if this is a key frame
        if frame_idx in save_frames:
            from visualization import save_binarization_visualization

            save_binarization_visualization(
                image[frame_idx], filtered_frame, frame_idx, name
            )

        # Collect metrics
        void_lst.append(metrics.void_area)
        island_area_lst.append(metrics.island_area)
        island_area_lst2.append(metrics.island_area_2nd)
        connected_lst.append(metrics.is_connected)
        region_lst.append(metrics.regions)

    return void_lst, island_area_lst, island_area_lst2, connected_lst


def analyze_binarization(
    file: np.ndarray,
    name: str,
    channel: int,
    bin_config: BinarizationConfig,
    out_config: OutputConfig,
) -> Tuple[Optional[plt.Figure], BinarizationResults]:
    """
    Analyze material resilience through binarization analysis.

    Returns:
        Tuple of (matplotlib figure or None, BinarizationResults)
    """
    vprint("Beginning Binarization Analysis...")

    image = file[:, :, :, channel]
    frame_initial_percent = 0.05

    if (image == 0).all():
        return None, BinarizationResults()

    # Adjust frame step if too large for video
    frame_step = bin_config.frame_step
    while len(image) <= frame_step:
        frame_step = int(frame_step / 5)

    # Setup CSV writer if needed
    csvwriter, myfile = None, None
    if out_config.save_intermediates:
        filename = os.path.join(name, "BinarizationData.csv")
        csvwriter, myfile = setup_csv_writer(filename)

    # Process frames using modular track_void function
    largest_void_lst, island_area_lst, island_area_lst2, connected_lst = track_void(
        image, name, bin_config, out_config, csvwriter
    )

    # Clean up CSV file
    if myfile:
        myfile.close()

    # Calculate analysis windows
    start_index = int(
        np.floor(len(image) * bin_config.frame_start_percent / frame_step)
    )
    stop_index = int(
        np.ceil(len(largest_void_lst) * bin_config.frame_stop_percent)
    )
    start_initial_index = int(np.ceil(len(image) * frame_initial_percent / frame_step))

    # Calculate initial baseline metrics
    void_size_initial = np.mean(largest_void_lst[0:start_initial_index])
    void_percent_gain_list = np.array(largest_void_lst) / void_size_initial

    island_size_initial = np.mean(island_area_lst[0:start_initial_index])
    island_size_initial2 = np.mean(island_area_lst2[0:start_initial_index])
    island_percent_gain_list = np.array(island_area_lst) / island_size_initial

    # Create visualization plot using extracted function
    fig = None
    if out_config.save_graphs:
        from visualization import save_binarization_plot

        start_plot_index = 0  # Reset to 0 as in original
        fig = save_binarization_plot(
            void_percent_gain_list,
            island_percent_gain_list,
            len(image),
            frame_step,
            start_plot_index,
            stop_index,
        )

    # Calculate final metrics
    downsample = 2
    img_dims = image[0].shape[0] * image[0].shape[1] / (downsample**2)

    avg_void_percent_change = (
        np.mean(largest_void_lst[0:stop_index]) / void_size_initial
    )
    max_void_size = top_ten_average(largest_void_lst) / img_dims

    avg_island_percent_change = (
        np.mean(island_area_lst[0:stop_index]) / island_size_initial
    )
    island_size_initial_norm = island_size_initial / img_dims
    island_size_initial2_norm = island_size_initial2 / img_dims
    max_island_size = top_ten_average(island_area_lst) / img_dims

    spanning = len([con for con in connected_lst if con == 1]) / len(connected_lst)

    results = BinarizationResults(
        spanning=spanning,
        max_island_size=max_island_size,
        max_void_size=max_void_size,
        avg_island_percent_change=avg_island_percent_change,
        avg_void_percent_change=avg_void_percent_change,
        island_size_initial=island_size_initial_norm,
        island_size_initial2=island_size_initial2_norm,
    )

    return fig, results
