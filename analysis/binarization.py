import os
from typing import Tuple, Optional
from itertools import pairwise, combinations
import matplotlib.pyplot as plt
import numpy as np
from numpy.fft import fft2,ifft2,fftshift
from scipy import ndimage
from skimage.measure import label, regionprops_table
from utils import average_largest, find_analysis_frames, vprint, flatten
from utils.setup import setup_csv_writer
from utils.binarization import invert_frame, binarize, sia_radial_average
from core import BinarizationConfig, ReaderConfig, WriterConfig, BinarizationResults

def check_span(frame: np.ndarray):
    def check_connected(frame: np.ndarray, axis: int = 0):
        # Ensures that either connected across left-right or up-down axis
        if not axis in [0, 1]:
            raise Exception("Axis must be 0 or 1.")
    
        struct = ndimage.generate_binary_structure(2, 2)
        frame_connections, _ = ndimage.label(input=frame, structure=struct)
    
        if axis == 0:
            labeled_first = np.unique(frame_connections[0,:])
            labeled_last = np.unique(frame_connections[-1,:])
        if axis == 1:
            labeled_first = np.unique(frame_connections[:,0])
            labeled_last = np.unique(frame_connections[:,-1])
    
        labeled_first = set(labeled_first[labeled_first != 0])
        labeled_last = set(labeled_last[labeled_last != 0])
        return 1 if labeled_first.intersection(labeled_last) else 0
    return (check_connected(frame, axis = 0) or check_connected(frame, axis = 1))

def find_largest_void(frame: np.ndarray):
    eval_frame = invert_frame(frame)
    labeled, a = label(eval_frame, connectivity= 2, return_num =True) # identify the regions of connectivity 2
    if a == 0:
        return frame.shape[0] * frame.shape[1]    
    regions = regionprops_table(labeled, properties=["area"]) # determines the region properties of the labeled
    region_areas = sorted(regions["area"], reverse = True)
    largest_void = region_areas[0]
    return largest_void # returns largest region(s) area


def find_island_properties(frame: np.ndarray, bin_config: BinarizationConfig):
    def get_nearest_neighbors(islands: list[tuple], k:float):
        k_num = int(np.ceil(k * len(islands)) - 1)
        points = np.array(islands, dtype = np.dtype([('x', 'float'), ('y', 'float')]))
        a, b = points.reshape(len(islands), 1), points.reshape(1, len(islands))
        distances = ((a['x'] - b['x'])**2 + (a['y'] - b['y'])**2) ** (1/2)
        nearest_distances = np.partition(distances, k_num + 1, axis = 1)[:, :k_num+1]
        return np.nanmean(nearest_distances)
        
    def get_anisotropy_factor(major_axis_length, minor_axis_length):
        if major_axis_length and minor_axis_length:
            return major_axis_length/minor_axis_length
        else:
            return np.nan
    labeled_frame, num_islands = label(frame, connectivity= 2, return_num =True)
    if num_islands == 0:
        return [np.nan] * 6

    regions = regionprops_table(labeled_frame, properties = ['label', 'area', 'centroid', 'axis_major_length', 'axis_minor_length'])
    region_areas = sorted(regions['area'], reverse = True)
    total_island_area = sum(region_areas)
    mean_island_area = np.nanmean(region_areas)
    if len(region_areas) >= 2:
        largest_island_area, second_largest_island_area = region_areas[:2]
    else:
        largest_island_area, second_largest_island_area = region_areas[0], 0
    region_centroids = [(cx, cy) for (cy, cx) in zip(regions['centroid-0'], regions['centroid-1'])]
    major_minor_axes = [(major, minor) for (major, minor) in zip(regions["axis_major_length"], regions["axis_minor_length"]) if minor != 0]
    mean_island_distance = get_nearest_neighbors(region_centroids, bin_config.neighbor_island_fraction)
    mean_anisotropy = np.nanmean([get_anisotropy_factor(major, minor) for (major, minor) in major_minor_axes])
    return largest_island_area, second_largest_island_area, total_island_area, mean_island_area, mean_island_distance, mean_anisotropy

def spatial_image_autocorrelation(frame: np.ndarray):
    frame = (frame - np.mean(frame))/np.std(frame)
    corr_image = np.real(fftshift(ifft2(fft2(frame)*np.conj(fft2(frame)))))/(frame.shape[0]*frame.shape[1])
    radial_avg = sia_radial_average(corr_image)
    return corr_image, radial_avg

def calculate_area_or_percentage(metric: float, img_dimensions: int, 
                                 convert_units: bool = False, um_pixel_ratio: float = None) -> Tuple[np.ndarray, float]:
    metric_physical_units, metric_percentage = np.nan, np.nan
    metric_percentage = metric / img_dimensions
    if convert_units:
        metric_physical_units = metric * um_pixel_ratio
    return metric_physical_units, metric_percentage


def analyze_binarization(video: np.ndarray, name: str, bin_config: BinarizationConfig, in_config: ReaderConfig, out_config: WriterConfig) -> Tuple[Optional[plt.Figure], BinarizationResults]:
    vprint('Beginning Binarization Analysis')
    num_frames = len(video)
    frame_step = bin_config.frame_step
    threshold_offset = bin_config.threshold_offset
    frame_eval_percent = bin_config.percentage_frames_evaluated
    um_pixel_ratio = in_config.um_pixel_ratio
    binning_factor = bin_config.bin_factor
    convert_units = bin_config.enable_physical_units
    
    frame_indices, frame_step = find_analysis_frames(video, frame_step)

    csvwriter, csvfile = None, None
    scorr_csvwriter, scorr_csvfile = None, None
    if out_config.save_rds:
        from visualization import write_binarization_rds, write_correlation_rds
        filename = os.path.join(name, 'BinarizationData.csv')
        csvwriter, csvfile = setup_csv_writer(filename)
        filename_scorr = os.path.join(name, 'StructuralImageAutocorrelation.csv')
        scorr_csvwriter, scorr_csvfile = setup_csv_writer(filename_scorr)
    if out_config.save_visualizations:
        from visualization import save_binarization_visualization
        from visualization import save_binarization_plots
        from visualization import save_correlation_visualization
        
    void_area_lst = []
    island_area_lst = []
    island_area_lst2 = []
    total_island_area_lst = []
    mean_island_area_lst = []
    mean_island_distance_lst = []
    mean_anisotropy_lst = []
    correlation_lengths = []
    connected_lst = []

    correlation_max = int(video.shape[1]/2 * binning_factor)
    mid_point = frame_indices[int((len(frame_indices) - 1)/2)]
    save_spots = np.array([0, mid_point, frame_indices[-1]])

    #Test comment

    for frame_idx in frame_indices:
        frame = video[frame_idx]
        image_autocorrelation, rad_avg = spatial_image_autocorrelation(frame)
        new_frame = binarize(frame, threshold_offset, binning_factor)
        if bin_config.invert_binarization:
            new_frame = invert_frame(new_frame)
        if frame_idx in save_spots and out_config.save_visualizations:
            save_binarization_visualization(frame, new_frame, frame_idx, name)
            save_correlation_visualization(image_autocorrelation, frame_idx, name, "Structural", 1, um_pixel_ratio)

        if out_config.save_rds:
            write_binarization_rds(csvwriter, new_frame, frame_idx)

        max_void_area = find_largest_void(new_frame)
        max_island_area, max_island_area2, total_island_area, mean_island_area, island_distance, anisotropy = find_island_properties(new_frame, bin_config)
        rad_avg = rad_avg[:correlation_max]
        xvalues = np.arange(len(rad_avg)) * um_pixel_ratio * binning_factor
        correlation_length = flatten(xvalues[np.argwhere(rad_avg <= np.exp(-1))])[0] if np.argwhere(rad_avg <= np.exp(-1)).any() else np.nan
        if out_config.save_rds:
            write_correlation_rds(scorr_csvwriter, frame_idx, xvalues.tolist(), rad_avg.tolist())

        void_area_lst.append(max_void_area)
        island_area_lst.append(max_island_area)
        island_area_lst2.append(max_island_area2)
        total_island_area_lst.append(total_island_area)
        mean_island_area_lst.append(mean_island_area)
        mean_island_distance_lst.append(island_distance)
        mean_anisotropy_lst.append(anisotropy)
        connected_lst.append(check_span(new_frame))
        correlation_lengths.append(correlation_length)

    if csvfile:
        csvfile.close()
    if scorr_csvfile:
        scorr_csvfile.close()
    
    correlation_lengths = np.array(correlation_lengths)
    structural_correlation_flag = int(np.isnan(np.sum(correlation_lengths)))
    mean_correlation_length = np.nanmean(correlation_lengths)

    start_eval_index = int(np.ceil(len(void_area_lst)*frame_eval_percent))
    final_eval_index = len(void_area_lst) - start_eval_index

    void_size_initial = np.nanmean(void_area_lst[:start_eval_index])
    void_percent_gain_list = np.array(void_area_lst)/void_size_initial
    
    island_size_initial = np.nanmean(island_area_lst[:start_eval_index])
    island_size_initial2 = np.nanmean(island_area_lst2[:start_eval_index])
    island_percent_gain_list = np.array(island_area_lst)/island_size_initial

    fig = None
    if out_config.save_visualizations:
        fig = save_binarization_plots(void_percent_gain_list, island_percent_gain_list, num_frames, frame_step)

    img_dims = video[0].shape[0] * video[0].shape[1] / (binning_factor ** 2)
    
    max_void_percent_change = np.nanmean(void_area_lst[final_eval_index:])/void_size_initial
    void_size_initial_quantity, void_size_initial_percent = calculate_area_or_percentage(void_size_initial, img_dims, convert_units, um_pixel_ratio)
    max_void_size_quantity, max_void_size_percent = calculate_area_or_percentage(average_largest(void_area_lst), img_dims, convert_units, um_pixel_ratio)
    max_island_percent_change = np.nanmean(island_area_lst[final_eval_index:])/island_size_initial
    island_size_initial_quantity, island_size_initial_percent = calculate_area_or_percentage(island_size_initial, img_dims, convert_units, um_pixel_ratio)
    island_size_initial2_quantity, island_size_initial2_percent = calculate_area_or_percentage(island_size_initial2, img_dims, convert_units, um_pixel_ratio)    
    max_island_size_quantity, max_island_size_percent = calculate_area_or_percentage(average_largest(island_area_lst), img_dims, convert_units, um_pixel_ratio)    
    connectivity = len([connected for connected in connected_lst if connected == 1])/len(connected_lst)
    mean_island_area_quantity, mean_island_area_percent = calculate_area_or_percentage(np.nanmean(mean_island_area_lst), img_dims, convert_units, um_pixel_ratio)
    total_island_area_quantity, total_island_area_percent = calculate_area_or_percentage(np.nanmean(total_island_area_lst), img_dims, convert_units, um_pixel_ratio)
    island_anisotropy = np.nanmean(mean_anisotropy_lst)
    mean_island_distance = np.nanmean(mean_island_distance_lst) * um_pixel_ratio
    results = BinarizationResults(
        connectivity = connectivity, 
        max_island_size = max_island_size_percent, 
        max_void_size = max_void_size_percent,
        max_island_percent_change = max_island_percent_change, 
        max_void_percent_change = max_void_percent_change,
        island_size_initial=island_size_initial_percent, 
        island_size_initial2=island_size_initial2_percent,
        island_anisotropy=island_anisotropy,
        mean_island_size=mean_island_area_percent,
        total_island_size=total_island_area_percent, 
        mean_island_separation=mean_island_distance, 
        island_correlation_length=mean_correlation_length,
        max_island_size_quantity=max_island_size_quantity,
        max_void_size_quantity=max_void_size_quantity,
        island_size_initial_quantity=island_size_initial_quantity,
        island_size_initial2_quantity=island_size_initial2_quantity,
        mean_island_size_quantity=mean_island_area_quantity,
        total_island_size_quantity=total_island_area_quantity,
        structural_correlation_flag=structural_correlation_flag,
    )

    return fig, results
