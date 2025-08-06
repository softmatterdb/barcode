import os
from typing import List, Tuple, TypeAlias

import numpy as np

from core import OpticalFlowConfig, OutputConfig, FlowResults
from utils import vprint
from utils.analysis import group_avg
from utils.setup import setup_csv_writer

FramePair: TypeAlias = Tuple[int, int]
FlowOutput: TypeAlias = Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
FlowStats: TypeAlias = Tuple[float, float, float]


def calculate_frame_pairs(num_frames: int, frame_step: int) -> List[FramePair]:
    """Calculate frame pairs for optical flow analysis."""
    end_frame = (int(num_frames / frame_step) - 1) * frame_step
    while end_frame <= 0:
        frame_step = int(np.ceil(frame_step / 5))
        vprint(
            f"Flow field frame step too large for video, dynamically adjusting, new frame step: {frame_step}"
        )
        end_frame = int(num_frames / frame_step) * frame_step

    frame_pairs = []
    for start in range(0, end_frame, frame_step):
        end = start + frame_step
        end = min(end, num_frames - 1)
        frame_pairs.append((start, end))

    if end_frame != num_frames - 1:
        frame_pairs.append((end_frame, num_frames - 1))

    return frame_pairs


def calculate_visualization_frames(
    frame_pairs: List[FramePair], frame_step: int
) -> set:
    """Calculate which frames should have visualizations saved (matching original logic)."""
    if not frame_pairs:
        return set()

    end_point = frame_pairs[-1][0]  # Last start frame
    mid_point_arr = list(range(0, end_point, frame_step))

    if len(mid_point_arr) <= 1:
        return {0} if frame_pairs else set()

    mid_point = mid_point_arr[int((len(mid_point_arr) - 1) / 2)]
    return {0, mid_point, end_point}


def calculate_optical_flow(
    images: np.ndarray,
    frame_pair: FramePair,
    opt_config: OpticalFlowConfig,
) -> Tuple[FlowOutput, FlowStats]:
    """Calculate optical flow between two frames."""
    import cv2 as cv

    start_frame, end_frame = frame_pair

    frame_int = opt_config.frame_interval_s
    if frame_int == 0:
        frame_int = 1
    # Convert from pixels/interval to nm/sec
    speed_conversion_factor = opt_config.nm_pixel_ratio / (
        frame_int * (end_frame - start_frame)
    )

    params = (None, 0.5, 3, opt_config.window_size, 3, 5, 1.2, 0)
    flow = cv.calcOpticalFlowFarneback(images[start_frame], images[end_frame], *params)

    flow_reduced = group_avg(flow, opt_config.downsample_factor)
    downU = np.flipud(flow_reduced[:, :, 0])
    downV = np.flipud(flow_reduced[:, :, 1])

    directions = np.arctan2(downV, downU)
    speed = np.sqrt(downU**2 + downV**2)
    speed *= speed_conversion_factor  # Convert speed to nm/sec

    theta = np.mean(directions)
    sigma_theta = np.std(directions)
    mean_speed = np.mean(speed)

    flow: FlowOutput = (downU, downV, directions, speed)
    flow_stats: FlowStats = (theta, sigma_theta, mean_speed)

    return flow, flow_stats


def aggregate_flow_stats(
    thetas: List[float],
    sigma_thetas: List[float],
    speeds: List[float],
) -> FlowResults:
    """Aggregate flow statistics."""

    thetas = np.array(thetas)
    sigma_thetas = np.array(sigma_thetas)
    speeds = np.array(speeds)

    # Metric for average direction of flow (-pi, pi) # "Flow Direction"
    mean_theta = np.mean(thetas)
    # Metric for st. dev of flow (-pi, pi) # "Flow Directional Spread"
    mean_sigma_theta = np.mean(sigma_thetas)
    # Metric for avg. speed (units of nm/s) # Average speed
    mean_speed = np.mean(speeds)
    # Calculate delta speed as (v_f - v_i)
    delta_speed = speeds[-1] - speeds[0]

    return FlowResults(mean_speed, delta_speed, mean_theta, mean_sigma_theta)


def write_flow_data(csvwriter, flow: FlowOutput, frame_pair: Tuple[int, int]):
    """Write flow field data to CSV."""
    if not csvwriter:
        return

    start_frame, end_frame = frame_pair
    downU, downV, _, _ = flow

    csvwriter.writerow([f"Flow Field ({start_frame}-{end_frame})"])
    csvwriter.writerow(["X-Direction"])
    csvwriter.writerows(downU)
    csvwriter.writerow(["Y-Direction"])
    csvwriter.writerows(downV)


def analyze_flow(
    file: np.ndarray,
    name: str,
    channel: int,
    opt_config: OpticalFlowConfig,
    out_config: OutputConfig,
) -> FlowResults:
    vprint("Beginning Flow Analysis...")

    images = file[:, :, :, channel]
    num_frames = len(images)

    if (images == 0).all():
        return FlowResults()

    csvwriter, myfile = None, None
    if out_config.save_intermediates:
        filename = os.path.join(name, "OpticalFlow.csv")
        csvwriter, myfile = setup_csv_writer(filename)

    thetas, sigma_thetas, speeds = [], [], []
    frame_step = opt_config.frame_step
    frame_pairs = calculate_frame_pairs(num_frames, frame_step)

    # Determine which frames to save visualizations for
    save_frames = set()
    if out_config.save_graphs:
        save_frames = calculate_visualization_frames(frame_pairs, frame_step)

    for frame_pair in frame_pairs:
        start_frame, _ = frame_pair

        flow, flow_stats = calculate_optical_flow(
            images,
            frame_pair,
            opt_config,
        )

        # Save visualization for key frames
        if start_frame in save_frames:
            from visualization import save_flow_visualization

            save_flow_visualization(
                flow, start_frame, name, opt_config.downsample_factor
            )

        if csvwriter:
            write_flow_data(csvwriter, flow, frame_pair)

        theta, sigma_theta, mean_speed = flow_stats
        thetas.append(theta)
        sigma_thetas.append(sigma_theta)
        speeds.append(mean_speed)

    if myfile:
        myfile.close()

    return aggregate_flow_stats(thetas, sigma_thetas, speeds)
