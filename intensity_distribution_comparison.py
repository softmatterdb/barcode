import numpy as np
import matplotlib.pyplot as plt
import csv, os, functools, builtins
from utils import average_largest, find_analysis_frames
from utils.intensity_distribution import frame_mode, median_skewness, mode_skewness, kurtosis, calc_frame_metric, histogram
from visualization.analysis import save_intensity_plots

def analyze_intensity_dist(file, name, channel, frame_eval_percent, step_size, bin_number, noise_threshold, save_visualization, save_rds, verbose):
    flag = 0 # No flags have been tripped by the module
    print = functools.partial(builtins.print, flush=True)
    vprint = print if verbose else lambda *a, **k: None
    vprint('Beginning Intensity Distribution Analysis')
    image = file[:,:,:,channel]
    if (image == 0).all(): # If image is blank, then end program early
        return None, [np.nan] * 6, 1

    frame_indices = find_analysis_frames(image, step_size)[0]
    num_frames_analysis = int(np.ceil(frame_eval_percent * len(frame_indices)))
    frames_data = [image[i] for i in frame_indices]
    i_frames_data = frames_data[:num_frames_analysis]
    f_frames_data = frames_data[-num_frames_analysis:]

    fig, ax = plt.subplots(figsize=(5,5))

    # Check for saturation, posts saturation flag (flag = 2) if mode and maximal intensity values are same
    flag == 2 if all([np.max(frame) == frame_mode(frame, bin_number, noise_threshold) for frame in frames_data]) else 0
    if save_rds:
        filename = os.path.join(name, f'IntensityDistribution.csv')
        with open(filename, "w") as myfile:
            csvwriter = csv.writer(myfile)
            for frame_idx in frame_indices:
                csvwriter.writerow([f'Frame {frame_idx}'])
                frame_data = image[frame_idx]
                frame_counts, frame_values = histogram(frame_data, bin_number, noise_threshold)
                csvwriter.writerow(frame_values)
                csvwriter.writerow(frame_counts)
                csvwriter.writerow([])

    i_kurt = calc_frame_metric(kurtosis, i_frames_data, bin_number, noise_threshold)
    f_kurt = calc_frame_metric(kurtosis, f_frames_data, bin_number, noise_threshold)
    total_kurt = calc_frame_metric(kurtosis, frames_data, bin_number, noise_threshold)

    i_median_skew = calc_frame_metric(median_skewness, i_frames_data, bin_number, noise_threshold)
    f_median_skew = calc_frame_metric(median_skewness, f_frames_data, bin_number, noise_threshold)
    total_median_skew = calc_frame_metric(median_skewness, frames_data, bin_number, noise_threshold)

    i_mode_skew = calc_frame_metric(mode_skewness, i_frames_data, bin_number, noise_threshold)
    f_mode_skew = calc_frame_metric(mode_skewness, f_frames_data, bin_number, noise_threshold)
    total_mode_skew = calc_frame_metric(mode_skewness, frames_data, bin_number, noise_threshold)

    # Take the largest ten percent of each metric and average them
    max_kurt = average_largest(total_kurt)
    max_median_skew = average_largest(total_median_skew)
    max_mode_skew = average_largest(total_mode_skew)

    # Take the difference of the average between the first and last 10% of frames
    kurt_diff = np.nanmean(np.array(f_kurt)) - np.nanmean(np.array(i_kurt))
    median_skew_diff = np.nanmean(np.array(f_median_skew)) - np.nanmean(np.array(i_median_skew))
    mode_skew_diff = np.nanmean(np.array(f_mode_skew)) - np.nanmean(np.array(i_mode_skew))

    if save_visualization:
        # Plot the intensity distributions for the first and last frame for comparison
        first_frame = image[0]
        end_frame = image[-1]
        max_px_intensity = 1.1*np.max(image)
        fig = save_intensity_plots(first_frame, end_frame, bin_number, noise_threshold, len(image), max_px_intensity)

    return fig, [max_kurt, max_median_skew, max_mode_skew, kurt_diff, median_skew_diff, mode_skew_diff], flag