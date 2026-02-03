import os, csv
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import warnings
warnings.filterwarnings("ignore")

def write_file(output_filepath, data):
    headers = [
        'Filepath', 'Channel', 'Flags', 'Connectivity', 'Maximum Island Area', 'Maximum Void Area', 
        'Island Area Change', 'Void Area Change', 'Initial Maximum Island Area', 
        'Initial 2nd Maximum Island Area', 'Maximum Kurtosis', 'Maximum Median Skewness', 
        'Maximum Mode Skewness', 'Kurtosis Change', 'Median Skewness Change', 
        'Mode Skewness Change', 'Speed', 'Speed Change',
        'Mean Flow Direction', 'Flow Directional Spread']
    if data:
        with open(output_filepath, 'w', newline='', encoding="utf-8") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(headers) # Write headers before the first filename
            headers = [] # Ensures headers are only written once per file
            for entry in data:
                csvwriter.writerow(entry)

def generate_aggregate_csv(csv_list, csv_loc, gen_barcode, sort = None, separate_channel = False):
    headers = [
        'Filepath', 'Channel', 'Flags', 'Connectivity', 'Maximum Island Area', 'Maximum Void Area', 
        'Island Area Change', 'Void Area Change', 'Initial Maximum Island Area', 
        'Initial 2nd Maximum Island Area', 'Maximum Kurtosis', 'Maximum Median Skewness', 
        'Maximum Mode Skewness', 'Kurtosis Change', 'Median Skewness Change', 
        'Mode Skewness Change', 'Speed', 'Speed Change',
        'Mean Flow Direction', 'Flow Directional Spread']
    if gen_barcode:
        combined_barcode_loc = os.path.join(os.path.dirname(csv_loc), f"{os.path.basename(csv_loc).removesuffix('.csv')} Barcode")
        
    num_params = len(headers) - 1
    csv_data = np.zeros(shape=(num_params))
    if not csv_list:
        return None
    if len(csv_list) == 1 and csv_list[0] == csv_loc:
        with open(csv_loc, 'r', newline='\n') as fread:
                csv_reader = csv.reader(fread)
                next(csv_reader, None)
                for row in csv_reader:
                    row = [float(val) if val != '' else np.nan for val in row[1:]]
                    arr_row = np.array(row)
                    csv_data = np.vstack((csv_data, arr_row))
    else:
        with open(csv_loc, 'w', encoding="utf-8", newline="\n") as fwrite:
            csv_writer = csv.writer(fwrite)
            csv_writer.writerow(headers)
            for csv_file in csv_list:
                with open(csv_file, 'r', newline='\n') as fread:
                    csv_reader = csv.reader(fread)
                    next(csv_reader, None)
                    for row in csv_reader:
                        csv_writer.writerow(row)
                        row = [float(val) if val != '' else np.nan for val in row[1:]]
                        arr_row = np.array(row)
                        csv_data = np.vstack((csv_data, arr_row))

    csv_data = csv_data[1:]

    if gen_barcode:
        gen_combined_barcode(csv_data, combined_barcode_loc, sort, separate_channel)

def check_limits(limit, thresh):
    if thresh < limit[0]:
        limit[0] = thresh
    elif thresh > limit[1]:
        limit[1] = thresh
    return limit

def update_limits(limits, new_limits):
    for i in range(len(limits)):
        limits[i, 0] = min(limits[i, 0], new_limits[i, 0])
        limits[i, 1] = max(limits[i, 1], new_limits[i, 1])
    return limits

def add_units(metric):
    frame_percent_unit = "\n(% of Frames)"
    fov_percent_unit = "\n(% of FOV)"
    unit_less = ""
    percent_change_unit = "\n(Fractional Change)"
    directional_unit = "\n(rads)"
    speed_unit = "\n($\\mu$m/s)"
    units = {'Connectivity': frame_percent_unit, 'Maximum Island Area': fov_percent_unit, 
             'Maximum Void Area': fov_percent_unit, 'Island Area Change': percent_change_unit, 
             'Void Area Change': percent_change_unit, 'Initial Maximum Island Area': fov_percent_unit, 
             'Initial 2nd Maximum Island Area': fov_percent_unit, 'Maximum Kurtosis': unit_less, 
             'Maximum Median Skewness': unit_less, 'Maximum Mode Skewness': unit_less,
             'Kurtosis Change': unit_less, 'Median Skewness Change': unit_less, 
             'Mode Skewness Change': unit_less, 'Speed': speed_unit, 'Speed Change': speed_unit,
             'Mean Flow Direction': directional_unit, 'Flow Directional Spread': directional_unit}
    return metric + units[metric]

def generate_comparison_barcodes(csv_list):
    headers = [
        'Filepath', 'Channel', 'Flags', 'Connectivity', 'Maximum Island Area', 'Maximum Void Area', 
        'Island Area Change', 'Void Area Change', 'Initial Maximum Island Area', 
        'Initial 2nd Maximum Island Area', 'Maximum Kurtosis', 'Maximum Median Skewness', 
        'Maximum Mode Skewness', 'Kurtosis Change', 'Median Skewness Change', 
        'Mode Skewness Change', 'Speed', 'Speed Change',
        'Mean Flow Direction', 'Flow Directional Spread']
    num_params = len(headers) - 3
    norms = []
    datas = []
    figpaths = []
    # Define normalization limits of floating point values
    binarized_static_limits = [0, 1]
    direction_static_limits = [-np.pi, np.pi]
    direction_spread_static_limit = [0, np.pi]
    change_limits = {3:1, 4:1, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 14:0}
    limits = np.array([[0.0, 0.0]] * 17)
        
    for csv_file in csv_list:
        figpaths.append(csv_file.removesuffix(".csv") + " Barcode.png")
        csv_data = np.zeros(shape=(num_params))
        with open(csv_file, 'r', newline='\n') as fread:
            csv_reader = csv.reader(fread)
            next(csv_reader, None)
            for row in csv_reader:
                row = [float(val) if val != '' else np.nan for val in row[3:]]
                arr_row = np.array(row)
                csv_data = np.vstack((csv_data, arr_row))
        csv_data = csv_data[1:]
        datas.append(csv_data)
        csv_data_limits = np.transpose(np.array([np.nanmin(csv_data, axis = 0), np.nanmax(csv_data, axis = 0)]))
        limits = update_limits(limits, csv_data_limits)
    
    for i in range(num_params):
        static_indices = [0, 1, 2, 5, 6, 15, 16]
        if i in static_indices[:-2]:
            limits[i] = binarized_static_limits
        elif i == static_indices[-2]:
            limits[i] = direction_static_limits
        elif i == static_indices[-1]:
            limits[i] = direction_spread_static_limit
        elif i in change_limits.keys():
            limits[i] = check_limits(limits[i], change_limits.get(i))
        else:
            limits[i] = [0, limits[i][1]]
        norms.append(mpl.colors.Normalize(vmin = limits[i][0], vmax = limits[i][1]))
    cmap = plt.get_cmap('plasma')  # Colormap for floats
    cmap.set_bad("black")
    
    for data, figpath in zip(datas, figpaths):    
        height = 9 * int(len(data) / 40) if len(data) > 40 else 9
        fig = plt.figure(figsize = (15, height), dpi = 300)
        height_ratio = [5, 2] if height == 9 else [int(2/5 * height), 1]
        gs = fig.add_gridspec(nrows = 2, ncols = (num_params) * 8, height_ratios = height_ratio)
        
        barcode = np.repeat(np.expand_dims(np.zeros_like(data), axis=2), 4, axis=2)
        for idx in range(num_params):
            norm = norms[idx]
            barcode[:,idx] = cmap(norm(data[:,idx]))
            norm_ax = fig.add_subplot(gs[1, 8 * idx: 8 * idx + 1])
            cbar = norm_ax.figure.colorbar(mpl.cm.ScalarMappable(norm = norm, cmap = cmap), cax = norm_ax, orientation='vertical')
            cbar.set_label(add_units(headers[idx + 3]), size=7)
            cbar.formatter.set_powerlimits((-2, 2))
            cbar.ax.tick_params(labelsize=6)
            
        plt.subplots_adjust(wspace=1, hspace=0.05)
        # Create a figure and axis
        barcode_ax = fig.add_subplot(gs[0, :])
        # Repeat each barcode to make it more visible
        barcode_image = np.repeat(barcode, 5, axis=0)  # Adjust the repetition factor as needed
        
        # Plot the stitched barcodes
        barcode_ax.imshow(barcode_image, aspect='auto')
        barcode_ax.axis('off')  # Turn off the axis
        
        # Save or show the figure
        fig.savefig(figpath, bbox_inches='tight', pad_inches=0)
        
        plt.close('all')
    

def gen_combined_barcode(data, figpath, sort = None, separate = False):
    headers = [
        'Filepath', 'Channel', 'Flags', 'Connectivity', 'Maximum Island Area', 'Maximum Void Area', 
        'Island Area Change', 'Void Area Change', 'Initial Maximum Island Area', 
        'Initial 2nd Maximum Island Area', 'Maximum Kurtosis', 'Maximum Median Skewness', 
        'Maximum Mode Skewness', 'Kurtosis Change', 'Median Skewness Change', 
        'Mode Skewness Change', 'Speed', 'Speed Change',
        'Mean Flow Direction', 'Flow Directional Spread']
    num_params = len(headers) - 3
    if len(data.shape) <= 1:
        data = np.reshape(data, (1, data.shape[0]))
    if data.shape[1] == 0:
        return
    channels = data[:,0]
    unique_channels = np.unique(channels)
    unique_channels = unique_channels[~np.isnan(unique_channels)]


    flags = data[:,1]
    params = {'Connectivity': 0, 'Maximum Island Area': 1, 'Maximum Void Area': 2, 
            'Island Area Change': 3, 'Void Area Change': 4, 'Initial Maximum Island Area': 5, 
            'Initial 2nd Maximum Island Area': 6, 'Maximum Kurtosis': 7, 'Maximum Median Skewness': 8, 
            'Maximum Mode Skewness': 9, 'Kurtosis Change': 10, 'Median Skewness Change': 11, 
            'Mode Skewness Change': 12, 'Speed': 13, 'Speed Change': 14,
            'Mean Flow Direction': 15, 'Flow Directional Spread': 16}
    if sort != None:
        sort_idx = params.get(sort) + 2
        sorted_indices = np.argsort(data[:,sort_idx])
        data = data[sorted_indices]

    all_entries = np.array([data[:,i+2] for i in range(num_params)])


    limits = [_ for _ in range(num_params)]
    norms = []
    # Define normalization limits of floating point values
    binarized_static_limits = [0, 1]
    direction_static_limits = [-np.pi, np.pi]
    direction_spread_static_limit = [0, np.pi]
    change_limits = {3:1, 4:1, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 14:0}
    static_indices = [0, 1, 2, 5, 6, 15, 16]

    for i in range(num_params):
        if i in static_indices[:-2]:
            limits[i] = binarized_static_limits
        elif i == static_indices[-2]:
            limits[i] = direction_static_limits
        elif i == static_indices[-1]:
            limits[i] = direction_spread_static_limit
        elif i in change_limits.keys():
            limits[i] = [np.nanmin(all_entries[i]), np.nanmax(all_entries[i])]
            limits[i] = check_limits(limits[i], change_limits.get(i))
        else:
            limits[i] = [np.nanmin(all_entries[i]), np.nanmax(all_entries[i])]
            limits[i] = [0, limits[i][1]]
        norms.append(mpl.colors.Normalize(vmin = limits[i][0], vmax = limits[i][1]))
    cmap = plt.get_cmap('plasma')  # Colormap for floats
    cmap.set_bad("black")

    for channel in unique_channels:
        if separate:
            channel_figpath = f'{figpath} (Channel {int(channel)}).svg'
            filtered_channel_data = np.array(data[data[:,0] == channel][:,2:])
        else:
            channel_figpath = f'{figpath}.svg'
            filtered_channel_data = np.array(data[np.isin(data[:,0], unique_channels)][:,2:])

        height = 9 * int(len(filtered_channel_data) / 40) if len(filtered_channel_data) > 40 else 9
        fig = plt.figure(figsize = (15, height), dpi = 300)
        height_ratio = [5, 2] if height == 9 else [int(2/5 * height), 1]
        gs = fig.add_gridspec(nrows = 2, ncols = (num_params) * 8, height_ratios = height_ratio)

        barcode = np.repeat(np.expand_dims(np.zeros_like(filtered_channel_data), axis=2), 4, axis=2)
        for idx in range(num_params):
            norm = norms[idx]
            barcode[:,idx] = cmap(norm(filtered_channel_data[:,idx]))
            norm_ax = fig.add_subplot(gs[1, 8 * idx: 8 * idx + 1])
            cbar = norm_ax.figure.colorbar(mpl.cm.ScalarMappable(norm = norm, cmap = cmap), cax = norm_ax, orientation='vertical')
            cbar.set_label(add_units(headers[idx + 3]), size=7)
            cbar.formatter.set_powerlimits((-2, 2))
            cbar.ax.tick_params(labelsize=6)
            
        plt.subplots_adjust(wspace=1, hspace=0.05)
        # Create a figure and axis
        barcode_ax = fig.add_subplot(gs[0, :])
        # Repeat each barcode to make it more visible
        barcode_image = np.repeat(barcode, 5, axis=0)  # Adjust the repetition factor as needed

        # Plot the stitched barcodesd
        barcode_ax.imshow(barcode_image, aspect='auto')
        barcode_ax.axis('off')  # Turn off the axis
        
        # Save or show the figure
        fig.savefig(channel_figpath, bbox_inches='tight', pad_inches=0)

        plt.close('all')

        if not separate:
            break
