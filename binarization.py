import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import csv, os, functools, builtins
from skimage.measure import label, regionprops
from scipy import ndimage
from utils import MyException, inv, groupAvg, average_largest, find_analysis_frames
from visualization.analysis import save_binarization_visualization, save_binarization_plots
import matplotlib
matplotlib.use('Agg')

def binarize(frame: np.ndarray, offset_threshold: float):
    avg_intensity = np.mean(frame)
    threshold = avg_intensity * (1 + offset_threshold)
    new_frame = np.where(frame < threshold, 0, 1)
    return new_frame

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
        
        if labeled_first.intersection(labeled_last):
            return 1
        else:
            return 0
    return (check_connected(frame, axis = 0) or check_connected(frame, axis = 1))

def find_largest_void(frame: np.ndarray, find_void: bool, num=1):
    eval_frame = inv(frame) if find_void else frame
    labeled, a = label(eval_frame, connectivity= 2, return_num =True) # identify the regions of connectivity 2
    if a == 0 or not regionprops(labeled):
        return frame.shape[0] * frame.shape[1]
    
    regions = regionprops(labeled) # determines the region properties of the labeled
    regions_sorted = sorted(regions, key = lambda r: r.area, reverse = True)
    largest_regions = regions_sorted[0:num]
    areas = [region.area for region in largest_regions]
    if num != len(areas):
        areas.append(0)
    return areas # returns largest region(s) area

def track_void(image, name, threshold, frame_indices, binning_number, save_visualization, save_rds):
    if save_rds:
        filename = os.path.join(name, 'BinarizationData.csv')
        f = open(filename, 'w')
        csvwriter = csv.writer(f)
        
    void_lst = []
    island_area_lst = []
    island_area_lst2 = []
    connected_lst = []

    mid_point = frame_indices[int((len(frame_indices) - 1)/2)]
    save_spots = np.array([0, mid_point, frame_indices[-1]])

    for i in frame_indices:
        new_image = binarize(image[i], threshold)
        new_frame = groupAvg(new_image, binning_number, bin_mask = True)
        
        if i in save_spots and save_visualization:
            save_binarization_visualization(image[i], new_frame, i, name)

        if save_rds:
            csvwriter.writerow([str(i)])
            csvwriter.writerows(new_frame)
            csvwriter.writerow([])

        island_area_lst.append(find_largest_void(new_frame, find_void = False)[0])
        island_area_lst2.append(find_largest_void(new_frame, find_void = False, num = 2)[1])
        connected_lst.append(check_span(new_frame))
        void_lst.append(find_largest_void(new_frame, True)[0])

    if save_rds:
        f.close()

    return void_lst, island_area_lst, island_area_lst2, connected_lst

def analyze_binarization(file, name, channel, threshold_offset = 0.1, frame_step = 10, frame_eval_percent = 0.05, binning_factor = 2, save_visualization = False, save_rds = False, verbose = True):
    print = functools.partial(builtins.print, flush=True)
    vprint = print if verbose else lambda *a, **k: None
    vprint('Beginning Binarization Analysis')
    image = file[:,:,:,channel]
    # Error Checking: Empty Image
    if (image == 0).all():
        return None, [np.nan] * 7
    num_frames = len(image)
    fig, ax = plt.subplots(figsize = (5,5))
    
    frame_indices, frame_step = find_analysis_frames(image, frame_step)
    
    largest_void_lst, island_area_lst, island_area_lst2, connected_lst = track_void(image, name, threshold_offset, frame_indices, binning_factor, save_visualization, save_rds)
    start_eval_index = int(np.ceil(len(largest_void_lst)*frame_eval_percent))
    final_eval_index = len(largest_void_lst) - start_eval_index

    void_size_initial = np.mean(largest_void_lst[:start_eval_index])
    void_percent_gain_list = np.array(largest_void_lst)/void_size_initial
    
    island_size_initial = np.mean(island_area_lst[:start_eval_index])
    island_size_initial2 = np.mean(island_area_lst2[:start_eval_index])
    island_percent_gain_list = np.array(island_area_lst)/island_size_initial

    fig = save_binarization_plots(void_percent_gain_list, island_percent_gain_list, num_frames, frame_step)

    img_dims = image[0].shape[0] * image[0].shape[1] / (binning_factor ** 2)
    
    max_void_percent_change = np.mean(largest_void_lst[final_eval_index:])/void_size_initial
    void_size_initial = void_size_initial / img_dims
    max_void_size = average_largest(largest_void_lst)/img_dims
    max_island_percent_change = np.mean(island_area_lst[final_eval_index:])/island_size_initial
    island_size_initial = island_size_initial / img_dims
    island_size_initial2 = island_size_initial2 / img_dims
    max_island_size = average_largest(island_area_lst)/img_dims    
    connectivity = len([connected for connected in connected_lst if connected == 1])/len(connected_lst)
    outputs = [connectivity, max_island_size, max_void_size, max_island_percent_change, max_void_percent_change, island_size_initial, island_size_initial2]

    return fig, outputs