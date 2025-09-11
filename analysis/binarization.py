import os
from dataclasses import dataclass
from typing import Tuple, List, Optional

import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage
from skimage.measure import label, regionprops_table
from skimage import io, color, filters, measure, morphology
from utils.setup import setup_csv_writer
from utils.binarization import inv, binarize
from utils import groupAvg, average_largest, find_analysis_frames
from core import BinarizationConfig, WriterConfig, BinarizationResults
from utils import vprint

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

def find_largest_void(frame: np.ndarray, find_void: bool, num=1):
    eval_frame = inv(frame) if find_void else frame
    labeled, a = label(eval_frame, connectivity= 2, return_num =True) # identify the regions of connectivity 2
    if a == 0 or not regionprops_table(labeled, properties=["area"]):
        return frame.shape[0] * frame.shape[1]
    
    regions = regionprops_table(labeled, properties=["area"]) # determines the region properties of the labeled
    region_areas = regions.get('area')
    regions_sorted = sorted(region_areas, reverse = True)
    largest_regions = regions_sorted[0:num]
    areas = [region for region in largest_regions]
    if num != len(areas):
        areas.append(0)
    return areas # returns largest region(s) area

def analyze_binarization(video: np.ndarray, name: str, bin_config: BinarizationConfig, out_config: WriterConfig) -> Tuple[Optional[plt.Figure], BinarizationResults]:
    vprint('Beginning Binarization Analysis')
    num_frames = len(video)
    frame_step = bin_config.frame_step
    threshold_offset = bin_config.threshold_offset
    frame_eval_percent = bin_config.percentage_frames_evaluated
    binning_factor = 2

    
    frame_indices, frame_step = find_analysis_frames(video, frame_step)

    csvwriter, csvfile = None, None
    if out_config.save_rds:
        from visualization import write_binarization_rds
        filename = os.path.join(name, 'BinarizationData.csv')
        csvwriter, csvfile = setup_csv_writer(filename)
    if out_config.save_visualizations:
        from visualization import save_binarization_visualization
        from visualization import save_binarization_plots

        
    void_lst = []
    island_area_lst = []
    island_area_lst2 = []
    connected_lst = []

    mid_point = frame_indices[int((len(frame_indices) - 1)/2)]
    save_spots = np.array([0, mid_point, frame_indices[-1]])

    for frame_idx in frame_indices:
        new_image = binarize(video[frame_idx], threshold_offset)
        new_frame = groupAvg(new_image, binning_factor, bin_mask = True)
        
        if frame_idx in save_spots and out_config.save_visualizations:
            save_binarization_visualization(video[frame_idx], new_frame, frame_idx, name)

        if out_config.save_rds:
            write_binarization_rds(csvwriter, new_frame, frame_idx)

        largest_islands = find_largest_void(new_frame, find_void = False, num = 2)
        largest_voids = find_largest_void(new_frame, find_void = True)
        island_area_lst.append(largest_islands[0])
        island_area_lst2.append(largest_islands[1])
        connected_lst.append(check_span(new_frame))
        void_lst.append(largest_voids[0])

    if csvfile:
        csvfile.close()
    
    start_eval_index = int(np.ceil(len(void_lst)*frame_eval_percent))
    final_eval_index = len(void_lst) - start_eval_index

    void_size_initial = np.mean(void_lst[:start_eval_index])
    void_percent_gain_list = np.array(void_lst)/void_size_initial
    
    island_size_initial = np.mean(island_area_lst[:start_eval_index])
    island_size_initial2 = np.mean(island_area_lst2[:start_eval_index])
    island_percent_gain_list = np.array(island_area_lst)/island_size_initial

    fig = None
    if out_config.save_visualizations:
        fig = save_binarization_plots(void_percent_gain_list, island_percent_gain_list, num_frames, frame_step)

    img_dims = video[0].shape[0] * video[0].shape[1] / (binning_factor ** 2)
    
    max_void_percent_change = np.mean(void_lst[final_eval_index:])/void_size_initial
    void_size_initial = void_size_initial / img_dims
    max_void_size = average_largest(void_lst)/img_dims
    max_island_percent_change = np.mean(island_area_lst[final_eval_index:])/island_size_initial
    island_size_initial = island_size_initial / img_dims
    island_size_initial2 = island_size_initial2 / img_dims
    max_island_size = average_largest(island_area_lst)/img_dims    
    connectivity = len([connected for connected in connected_lst if connected == 1])/len(connected_lst)
    results = BinarizationResults(
        spanning = connectivity, max_island_size = max_island_size, max_void_size = max_void_size,
        max_island_percent_change = max_island_percent_change, max_void_percent_change = max_void_percent_change,
        island_size_initial=island_size_initial, island_size_initial2=island_size_initial2
    )

    return fig, results