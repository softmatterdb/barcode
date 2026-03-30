import numpy as np
import matplotlib.pyplot as plt
import csv, os, functools, builtins
from utils import average_largest, find_analysis_frames
from utils.analysis.intensity_distribution import (
    mean, frame_mode, median_skewness, mode_skewness, kurtosis, 
    calc_frame_metric, histogram)

def analyze_intensity_dist(file: np.ndarray, name: str, channel: int, intensity_distribution_settings: dict, output_settings: dict, verbose: bool):
    step_size = intensity_distribution_settings["frame_step"]
    bin_number = intensity_distribution_settings["bin_size"]
    noise_threshold = intensity_distribution_settings["noise_threshold"]
    frame_eval_percent = intensity_distribution_settings["percentage_frames_evaluated"]
    save_visualization = output_settings["save_visualizations"]
    save_rds = output_settings["save_rds"]

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
        i_frame = image[0]
        f_frame = image[-1]
        max_px_intensity = 1.1*np.max(image)
        i_count, i_bins = histogram(i_frame, bin_number, noise_threshold)

        f_count, f_bins = histogram(f_frame, bin_number, noise_threshold)
            
        i_mean = mean(i_bins, i_count)
        f_mean = mean(f_bins, f_count)

        ax.plot(i_bins, i_count, '^-', ms=4, c='darkred', alpha=0.6, label= "Frame 0 Intensity Distribution")
        ax.plot(f_bins, f_count, 'v-', ms=4, c='purple',   alpha=0.6, label= f"Frame {len(image) - 1} Intensity Distribution")
        ax.axvline(x=i_mean, ms = 4, c = 'darkred', alpha=1, label="Frame 0 Mean")
        ax.axvline(x=f_mean, ms = 4, c = 'purple', alpha=1, label=f"Frame {len(image) - 1} Mean")
        ax.axhline(0, color='dimgray', alpha=0.6)
        ax.set_xlabel("Pixel intensity value")
        ax.set_ylabel("Probability")
        ax.set_yscale('log')
        ax.set_xlim(0,max_px_intensity)
        ax.legend()

    return fig, [max_kurt, max_median_skew, max_mode_skew, kurt_diff, median_skew_diff, mode_skew_diff], flag