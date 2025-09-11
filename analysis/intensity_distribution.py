import os
from typing import Tuple, List, Optional

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import kurtosis

from core import IntensityDistributionConfig, WriterConfig, IntensityResults
from utils import vprint, average_largest, find_analysis_frames
from utils.intensity_distribution import (
    frame_mode, median_skewness, mode_skewness, 
    kurtosis, calc_frame_metric, histogram
)
from utils.setup import setup_csv_writer

def analyze_intensity_distribution(video: np.ndarray, name: str, id_config: IntensityDistributionConfig, out_config: WriterConfig) -> IntensityResults:
    vprint('Beginning Intensity Distribution Analysis')
    step_size = id_config.frame_step
    frame_eval_percent = id_config.percentage_frames_evaluated
    bin_number = id_config.bin_size
    noise_threshold = id_config.noise_threshold
    frame_indices = find_analysis_frames(video, step_size)[0]
    num_frames_analysis = int(np.ceil(frame_eval_percent * len(frame_indices)))

    csvwriter, csvfile = None, None
    if out_config.save_rds:
        filename = os.path.join(name, 'IntensityDistribution.csv')
        csvwriter, csvfile = setup_csv_writer(filename)

    kurtosis_list = []
    median_skewness_list = []
    mode_skewness_list = []
    flags = []

    for frame_idx in frame_indices:
        frame_data = video[frame_idx]
        frame_counts, frame_values = histogram(frame_data, bin_number, noise_threshold)

        if out_config.save_rds:
            from visualization import write_intensity_distribution_rds
            write_intensity_distribution_rds(csvwriter, frame_values, frame_counts, frame_idx)
        
        kurtosis_list.append(kurtosis(frame_values, frame_counts))
        median_skewness_list.append(median_skewness(frame_values, frame_counts))
        mode_skewness_list.append(mode_skewness(frame_values, frame_counts))
        flag_value = bool(frame_mode(frame_data, bin_number, noise_threshold) == frame_values[-1])
        flags.append(flag_value)
    
    max_kurt = average_largest(kurtosis_list)
    max_median_skew = average_largest(median_skewness_list)
    max_mode_skew = average_largest(mode_skewness_list)

    kurt_diff = np.nanmean(kurtosis_list[-num_frames_analysis:]) - np.nanmean(kurtosis_list[:num_frames_analysis])
    median_skew_diff = np.nanmean(median_skewness_list[-num_frames_analysis:]) - np.nanmean(median_skewness_list[:num_frames_analysis])
    mode_skew_diff = np.nanmean(mode_skewness_list[-num_frames_analysis:]) - np.nanmean(mode_skewness_list[:num_frames_analysis])

    fig = None
    if out_config.save_visualizations:
        from visualization import save_intensity_plots
        # Plot the intensity distributions for the first and last frame for comparison
        first_frame = video[0]
        end_frame = video[-1]
        max_px_intensity = 1.1*np.max(video)
        fig = save_intensity_plots(first_frame, end_frame, bin_number, noise_threshold, len(video), max_px_intensity)

    flag = 2 * int(all(flags))
    results = IntensityResults(max_kurtosis=max_kurt, max_median_skew=max_median_skew, max_mode_skew=max_mode_skew,
                               kurtosis_diff=kurt_diff, median_skew_diff=median_skew_diff, mode_skew_diff=mode_skew_diff, flag=flag)
    
    return fig, results

