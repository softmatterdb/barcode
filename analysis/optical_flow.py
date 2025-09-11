import numpy as np
import cv2 as cv
import os 
from utils import groupAvg, find_analysis_frames, vprint
from utils.setup import setup_csv_writer
from core import OpticalFlowConfig, WriterConfig, FlowResults

def analyze_optical_flow(video: np.ndarray, name: str, flow_config: OpticalFlowConfig, out_config: WriterConfig) -> FlowResults:
    # Defines print to enable printing only if verbose setting set to True
    vprint('Beginning Optical Flow Analysis')
    frame_eval_percent = flow_config.percentage_frames_evaluated
    frame_stride = flow_config.frame_step
    win_size = flow_config.win_size
    downsample = flow_config.downsample
    exposure_time = flow_config.exposure_time
    um_pix_ratio = flow_config.um_pixel_ratio
    frame_indices, frame_stride = find_analysis_frames(video, frame_stride)
    flow_field_indices = [(frame_indices[i], frame_indices[i + 1]) for i in range(len(frame_indices) - 1)]
    num_frames_analysis = int(np.ceil(frame_eval_percent * len(flow_field_indices)))

    mid_point = flow_field_indices[int((len(flow_field_indices) - 1)/2)]
    visualization_flow_fields = [flow_field_indices[0], mid_point, flow_field_indices[-1]]

    vx_list = []
    vy_list = []
    speeds = []

    # Prepares the intermediate file for saving if setting is turned on
    csvwriter, csvfile = None, None
    if out_config.save_rds:
        filename = os.path.join(name, 'OpticalFlow.csv')
        csvwriter, csvfile = setup_csv_writer(filename)

    for frame_pair in flow_field_indices:
        start, stop = frame_pair
        flow = cv.calcOpticalFlowFarneback(video[start], video[stop], None, 0.5, 3, win_size, 3, 5, 1.2, 0)
        flow_reduced = groupAvg(flow, downsample)
        downU = flow_reduced[:,:,0]
        downV = flow_reduced[:,:,1]
        downU = np.flipud(downU)* 1/(exposure_time) * 1/(stop - start) * um_pix_ratio
        downV = -1 * np.flipud(downV)* 1/(exposure_time) * 1/(stop - start) * um_pix_ratio

        if out_config.save_rds:
            from visualization import write_flow_field_rds
            write_flow_field_rds(csvwriter, downU, downV, start, stop)
        
        speed = (downU ** 2 + downV ** 2) ** (1/2)
        direction = np.arctan2(downV, downU)
        flow_field = [downU, downV, direction, speed]

        if (start, stop) in visualization_flow_fields and out_config.save_visualizations:
            from visualization import save_flow_field_visualization
            save_flow_field_visualization(flow_field, start, stop, name, downsample)
        
        # Convert speed from pixels / interval to nm/sec
        # Conversion: px/interval * interval/frame * 1/(sec/frame) * um/px
        vx_list.append(np.mean(np.cos(direction)))
        vy_list.append(np.mean(np.sin(direction)))
        speeds.append(np.mean(speed))
        
    # Close the CSV intermediate file
    if csvfile:
        csvfile.close()

    vx_list = np.array(vx_list)
    vy_list = np.array(vy_list)
    speeds = np.array(speeds)

    vector_lengths = np.sqrt(vx_list ** 2 + vy_list ** 2)
    sigma_thetas = np.sqrt(-2 * np.log(vector_lengths))

    theta = np.arctan2(np.nanmean(vy_list), np.nanmean(vx_list)) # Metric for average flow direction # "Mean Flow Direction"
    sigma_theta = np.nanmean(sigma_thetas) # Metric for st. dev of flow (-pi, pi) # "Flow Directional Spread"
    mean_speed = np.nanmean(speeds) # Metric for avg. speed (units of um/s) # Average speed
    delta_speed = np.nanmean(speeds[-num_frames_analysis:]) - np.nanmean(speeds[:num_frames_analysis]) # Metric for change in speed # "Speed Change"
    results = FlowResults(mean_speed = mean_speed, delta_speed = delta_speed, mean_theta = theta, mean_sigma_theta = sigma_theta)
    return results
