import os 
import cv2 as cv
import numpy as np
from utils import groupAvg, find_analysis_frames, vprint, flatten
from utils.optical_flow import velocity_correlation, divergence, curl
from utils.setup import setup_csv_writer
from core import OpticalFlowConfig, ReaderConfig, WriterConfig, FlowResults

def analyze_optical_flow(video: np.ndarray, name: str, flow_config: OpticalFlowConfig, 
                         in_config: ReaderConfig, out_config: WriterConfig) -> FlowResults:
    # Defines print to enable printing only if verbose setting set to True
    vprint('Beginning Optical Flow Analysis')
    frame_eval_percent = flow_config.percentage_frames_evaluated
    frame_stride = flow_config.frame_step
    win_size = flow_config.win_size
    downsample = flow_config.downsample
    exposure_time = in_config.exposure_time
    um_pix_ratio = in_config.um_pixel_ratio
    frame_indices, frame_stride = find_analysis_frames(video, frame_stride)
    correlation_max = int(video.shape[1]/(2 * downsample))
    flow_field_indices = [(frame_indices[i], frame_indices[i + 1]) for i in range(len(frame_indices) - 1)]
    num_frames_analysis = int(np.ceil(frame_eval_percent * len(flow_field_indices)))

    mid_point = flow_field_indices[int((len(flow_field_indices) - 1)/2)]
    visualization_flow_fields = [flow_field_indices[0], mid_point, flow_field_indices[-1]]

    flow_field_list = []
    vx_list = []
    vy_list = []
    velocity_correlations = []
    divergences = []
    curls = []
    speeds = []

    # Prepares the intermediate file for saving if setting is turned on
    csvwriter, csvfile = None, None
    vcorr_csvwriter, vcorr_file = None, None
    divwriter, divfile = None, None
    curlwriter, curlfile = None, None
    if out_config.save_rds:
        from visualization import write_flow_field_rds, write_correlation_rds, write_divergence_curl_rds
        filename = os.path.join(name, 'OpticalFlow.csv')
        filename_vcorr = os.path.join(name, 'VelocityCorrelation.csv')
        filename_div = os.path.join(name, 'Divergence.csv')
        filename_curl = os.path.join(name, 'Curl.csv')
        csvwriter, csvfile = setup_csv_writer(filename)
        vcorr_csvwriter, vcorr_file = setup_csv_writer(filename_vcorr)
        divwriter, divfile = setup_csv_writer(filename_div)
        curlwriter, curlfile = setup_csv_writer(filename_curl)
    for frame_pair in flow_field_indices:
        start, stop = frame_pair
        flow = cv.calcOpticalFlowFarneback(video[start], video[stop], None, 0.5, 3, win_size, 3, 5, 1.2, 0)
        flow_reduced = groupAvg(flow, downsample)
        downU = flow_reduced[:,:,0]
        downV = flow_reduced[:,:,1]
        downU = np.flipud(downU)* 1/(exposure_time) * 1/(stop - start) * um_pix_ratio
        downV = -1 * np.flipud(downV)* 1/(exposure_time) * 1/(stop - start) * um_pix_ratio

        if out_config.save_rds:
            write_flow_field_rds(csvwriter, downU, downV, start, stop)
        
        speed = (downU ** 2 + downV ** 2) ** (1/2)
        direction = np.arctan2(downV, downU)
        flow_field = [downU, downV, direction, speed]
        downsampled_field = np.stack([downU, downV], axis = -1)
        flow_field_list.append(downsampled_field/np.stack([speed, speed], axis = -1))
        v_correlation, v_rad_avg = velocity_correlation(downsampled_field)
        cumulative_field = np.cumsum(flow_field_list, axis = 0)[-1]
        div_field = divergence(cumulative_field, um_pix_ratio * downsample)
        curl_field = curl(downsampled_field/np.stack([speed, speed], axis = -1), um_pix_ratio * downsample)
        mean_div = np.nanmean(div_field)
        mean_curl = np.nanmean(curl_field)
        v_rad_avg = v_rad_avg[:correlation_max]
        xvalues = np.arange(len(v_rad_avg)) * um_pix_ratio * downsample
        correlation_length = flatten(xvalues[np.argwhere(v_rad_avg <= 0.5)])[0] if np.argwhere(v_rad_avg <= 0.5).any() else np.nan
        if out_config.save_rds:
            write_correlation_rds(vcorr_csvwriter, frame_pair, xvalues.tolist(), v_rad_avg.tolist())
            write_divergence_curl_rds(divwriter, frame_pair, div_field)
            write_divergence_curl_rds(curlwriter, frame_pair, curl_field)


        if (start, stop) in visualization_flow_fields and out_config.save_visualizations:
            from visualization import save_flow_field_visualization, save_correlation_visualization
            save_flow_field_visualization(flow_field, start, stop, name, downsample, um_pix_ratio)
            save_correlation_visualization(v_correlation, (start, stop), name, "Velocity", downsample, um_pix_ratio)
        
        # Conversion: px/interval * interval/frame * 1/(sec/frame) * um/px
        vx_list.append(np.mean(np.cos(direction)))
        vy_list.append(np.mean(np.sin(direction)))
        velocity_correlations.append(correlation_length)
        divergences.append(mean_div)
        curls.append(mean_curl)
        speeds.append(np.mean(speed))
        
    # Close the CSV intermediate file
    for rds_file in [csvfile, vcorr_file, divfile, curlfile]:
        if rds_file:
            rds_file.close()
    vx_list = np.array(vx_list)
    vy_list = np.array(vy_list)
    speeds = np.array(speeds)
    correlation_lengths = np.array(velocity_correlations)
    velocity_correlation_flag = int(np.isnan(np.sum(correlation_lengths)))
    max_divergence = divergences[-1]
    mean_curl = np.mean(curls)
    mean_correlation_length = np.nanmean(correlation_lengths)

    vector_lengths = np.sqrt(vx_list ** 2 + vy_list ** 2)
    sigma_thetas = np.sqrt(-2 * np.log(vector_lengths))

    theta = np.arctan2(np.nanmean(vy_list), np.nanmean(vx_list)) # Metric for average flow direction # "Mean Flow Direction"
    sigma_theta = np.nanmean(sigma_thetas) # Metric for st. dev of flow (-pi, pi) # "Flow Directional Spread"
    mean_speed = np.nanmean(speeds) # Metric for avg. speed (units of um/s) # Average speed
    delta_speed = np.nanmean(speeds[-num_frames_analysis:]) - np.nanmean(speeds[:num_frames_analysis]) # Metric for change in speed # "Speed Change"
    results = FlowResults(mean_speed = mean_speed, delta_speed = delta_speed, mean_theta = theta, 
                          mean_sigma_theta = sigma_theta, velocity_correlation_length = mean_correlation_length,
                          divergence = max_divergence, curl = mean_curl,
                          velocity_correlation_flag=velocity_correlation_flag)
    return results