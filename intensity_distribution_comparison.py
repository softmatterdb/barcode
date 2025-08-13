import numpy as np
import matplotlib.pyplot as plt
import csv, os, functools, builtins
from scipy.stats import kurtosis
from utils import average_largest, calc_mode, median_skewness, mode_skewness, calc_frame_metric, find_analysis_frames, normalize_counts, flatten

def analyze_intensity_dist(file, name, channel, frame_eval_percent, step_size, bin_width, noise_threshold, save_visualization, save_rds, verbose):
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
    flag == 2 if all([np.max(frame) == calc_mode(frame) for frame in frames_data]) else 0
    if save_rds:
        filename = os.path.join(name, f'{bin_width} Bin Width Noise Floor {noise_threshold} IntensityDistribution.csv')
        with open(filename, "w") as myfile:
            csvwriter = csv.writer(myfile)
            for frame_idx in frame_indices:
                csvwriter.writerow([f'Frame {frame_idx}'])
                frame_data = image[frame_idx]
                min_boundary = int(np.floor(np.min(frame_data)/bin_width) * bin_width)
                max_boundary = int(np.ceil(np.max(frame_data)/bin_width) * bin_width)
                bins = np.arange(min_boundary, max_boundary, bin_width)
                frame_counts, frame_values = np.histogram(frame_data, bins)
                frame_counts = normalize_counts(frame_counts)
                frame_values = frame_values[np.argwhere(frame_counts > noise_threshold)]
                frame_counts = frame_counts[np.argwhere(frame_counts > noise_threshold)]
                print(frame_values.min(), frame_counts[np.argmin(frame_values)])
                csvwriter.writerow(flatten(frame_values))
                csvwriter.writerow(flatten(frame_counts))
                csvwriter.writerow([])
                    
    i_kurt = calc_frame_metric(kurtosis, i_frames_data, bin_width, noise_threshold)
    f_kurt = calc_frame_metric(kurtosis, f_frames_data, bin_width, noise_threshold)
    tot_kurt = calc_frame_metric(kurtosis, frames_data, bin_width, noise_threshold)

    i_median_skew = calc_frame_metric(median_skewness, i_frames_data, bin_width, noise_threshold)
    f_median_skew = calc_frame_metric(median_skewness, f_frames_data, bin_width, noise_threshold)
    tot_median_skew = calc_frame_metric(median_skewness, frames_data, bin_width, noise_threshold)

    i_mode_skew = calc_frame_metric(mode_skewness, i_frames_data, bin_width, noise_threshold)
    f_mode_skew = calc_frame_metric(mode_skewness, f_frames_data, bin_width, noise_threshold)
    tot_mode_skew = calc_frame_metric(mode_skewness, frames_data, bin_width, noise_threshold)

    # Take the largest ten percent of each metric and average them
    max_kurt = average_largest(tot_kurt)
    max_median_skew = average_largest(tot_median_skew)
    max_mode_skew = average_largest(tot_mode_skew)

    # Take the difference of the average between the first and last 10% of frames
    kurt_diff = np.mean(np.array(f_kurt)) - np.mean(np.array(i_kurt))
    median_skew_diff = np.mean(np.array(f_median_skew)) - np.mean(np.array(i_median_skew))
    mode_skew_diff = np.mean(np.array(f_mode_skew)) - np.mean(np.array(i_mode_skew))

    if save_visualization:
        # Plot the intensity distributions for the first and last frame for comparison
        i_frame = image[0]
        f_frame = image[-1]
        max_px_intensity = 1.1*np.max(image)
        bins_width = 3        
        set_bins = np.arange(0, max_px_intensity, bins_width)
        i_count, bins = np.histogram(i_frame.flatten(), bins=set_bins, density=True)
        f_count, bins = np.histogram(f_frame.flatten(), bins=set_bins, density=True)
        center_bins = (bins[1] - bins[0])/2
        plt_bins = bins[0:-1] + center_bins
            
        i_mean = np.mean(i_frame)
        f_mean = np.mean(f_frame)

        ax.plot(plt_bins[::10], i_count[::10], '^-', ms=4, c='darkred', alpha=0.6, label= "Frame 0 Intensity Distribution")
        ax.plot(plt_bins[::10], f_count[::10], 'v-', ms=4, c='purple',   alpha=0.6, label= f"Frame {len(image) - 1} Intensity Distribution")
        ax.axvline(x=i_mean, ms = 4, c = 'darkred', alpha=1, label="Frame 0 Mean")
        ax.axvline(x=f_mean, ms = 4, c = 'purple', alpha=1, label=f"Frame {len(image) - 1} Mean")
        ax.axhline(0, color='dimgray', alpha=0.6)
        ax.set_xlabel("Pixel intensity value")
        ax.set_ylabel("Probability")
        ax.set_yscale('log')
        ax.set_xlim(0,max_px_intensity)
        ax.legend()

    return fig, [max_kurt, max_median_skew, max_mode_skew, kurt_diff, median_skew_diff, mode_skew_diff], flag