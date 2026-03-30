import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import csv, os, functools, builtins
from skimage.measure import label, regionprops
from scipy import ndimage
from utils import groupAvg, average_largest, find_analysis_frames
from utils.analysis.image_binarization import binarize, inv
import matplotlib
matplotlib.use('Agg')

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
            compare_fig, comp_axs = plt.subplots(ncols = 2, figsize=(10, 5))
            comp_axs[0].imshow(image[i], cmap='gray')
            comp_axs[1].imshow(new_frame, cmap='gray')
            ticks_adj = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x * 2))
            comp_axs[1].xaxis.set_major_formatter(ticks_adj)
            comp_axs[1].yaxis.set_major_formatter(ticks_adj)
            comp_axs[0].axis('off')  # Turn off the axis
            comp_axs[1].axis('off')  # Turn off the axis
            plt.savefig(os.path.join(name, f'Binarization Frame {i} Comparison.png'))
            plt.close('all')
            
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

def analyze_binarization(file: np.ndarray, name: str, channel: int, binarization_settings: dict, output_settings: dict, verbose: bool):
    threshold_offset = binarization_settings["threshold_offset"]
    frame_step = binarization_settings["frame_step"]
    frame_eval_percent = binarization_settings["percentage_frames_evaluated"]
    binning_factor = 2
    save_visualization = output_settings["save_visualizations"]
    save_rds = output_settings["save_rds"]

    print = functools.partial(builtins.print, flush=True)
    vprint = print if verbose else lambda *a, **k: None
    vprint('Beginning Binarization Analysis')
    image = file[:,:,:,channel]

    fig, ax = plt.subplots(figsize = (5,5))

    # Error Checking: Empty Image
    if (image == 0).all():
        return None, [np.nan] * 7
    
    frame_indices, frame_step = find_analysis_frames(image, frame_step)
    
    largest_void_lst, island_area_lst, island_area_lst2, connected_lst = track_void(image, name, threshold_offset, frame_indices, binning_factor, save_visualization, save_rds)
    start_eval_index = int(np.ceil(len(largest_void_lst)*frame_eval_percent))
    final_eval_index = len(largest_void_lst) - start_eval_index

    void_size_initial = np.mean(largest_void_lst[:start_eval_index])
    void_percent_gain_list = np.array(largest_void_lst)/void_size_initial
    
    island_size_initial = np.mean(island_area_lst[:start_eval_index])
    island_size_initial2 = np.mean(island_area_lst2[:start_eval_index])
    island_percent_gain_list = np.array(island_area_lst)/island_size_initial
    
    start_index = 0
    stop_index = len(largest_void_lst)
    plot_range = np.arange(start_index * frame_step, stop_index * frame_step, frame_step)
    plot_range[-1] = len(image) - 1 if stop_index * frame_step >= len(image) else stop_index * frame_step
    ax.plot(plot_range, 100 * void_percent_gain_list[start_index:stop_index], c='b', label='Original Void Size Proportion')
    ax.plot(plot_range, 100 * island_percent_gain_list[start_index:stop_index], c='r', label='Original Island Size Proportion')
    ax.set_xticks(plot_range[::10])
    if stop_index * frame_step >= len(image) != 0:
        ax.set_xlim(left=None, right=len(image) - 1)
    ax.set_xlabel("Frames")
    ax.set_ylabel("Percentage of Original Size")
    ax.legend()

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