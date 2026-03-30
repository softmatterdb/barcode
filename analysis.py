from utils.reader import read_file, check_channel_dim
import os, yaml, time, functools, builtins, nd2
from analysis_branches import analyze_binarization, analyze_optical_flow, analyze_intensity_dist
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from itertools import pairwise
from utils.writer import write_file, generate_aggregate_csv
matplotlib.use('Agg')

class MyException(Exception):
    pass

def analyze_video(filepath, config_data, fail_file_loc, count, total):
    reader_data = config_data['reader']
    _, save_rds, save_visualizations = config_data['writer'].values()
    accept_dim_channel, accept_dim_im = reader_data["accept_dim_channels"], reader_data["accept_dim_images"]
    channel_select = reader_data["channel_select"]
    verbose = reader_data["verbose"]
    print = functools.partial(builtins.print, flush=True)
    vprint = print if verbose else lambda *a, **k: None

    def analyze_channel(filename, channel, config_data, fail_file_loc):
        binarization = config_data["reader"]["binarization"]
        optical_flow = config_data["reader"]["optical_flow"]
        intensity_distribution = config_data["reader"]["intensity_distribution"]
        binarization_params = config_data["image_binarization_parameters"]
        optical_flow_params = config_data["optical_flow_parameters"]
        intensity_distribution_params = config_data["intensity_distribution_parameters"]
        writer_params = config_data["writer"]
        flag = 0
        figure_dir_name = remove_extension(filename) + ' BARCODE Output'
        fig_channel_dir_name = os.path.join(figure_dir_name, f'Channel {channel}')
        os.makedirs(figure_dir_name, exist_ok=True)
        os.makedirs(fig_channel_dir_name, exist_ok=True)
        
        if binarization:
            try:
                binarization_figure, binarization_outputs = analyze_binarization(file, fig_channel_dir_name, channel, binarization_params, writer_params, verbose)
            except Exception as e:  
                with open(fail_file_loc, "a", encoding="utf-8") as log_file:
                    log_file.write(f"File: {filename}, Module: Binarization, Exception: {str(e)}\n")
                binarization_figure = None
                binarization_outputs = [np.nan] * 7
        else:
            binarization_figure = None
            binarization_outputs = [np.nan] * 7
        if optical_flow:
            try:
                flow_outputs = analyze_optical_flow(file, fig_channel_dir_name, channel, optical_flow_params, writer_params, verbose)
            except Exception as e:
                with open(fail_file_loc, "a", encoding="utf-8") as log_file:
                    log_file.write(f"File: {filename}, Module: Optical Flow, Exception: {str(e)}\n")
                flow_outputs = [np.nan] * 4
        else:
            flow_outputs = [np.nan] * 4
        if intensity_distribution:
            try:
                intensity_figure, id_outputs, flag = analyze_intensity_dist(file, fig_channel_dir_name, channel, intensity_distribution_params, writer_params, verbose)
            except Exception as e:
                with open(fail_file_loc, "a", encoding="utf-8") as log_file:
                    log_file.write(f"File: {filename}, Module: Intensity Distribution, Exception: {str(e)}\n")
                intensity_figure = np.nan
                id_outputs = [np.nan] * 6
                flag = np.nan
        else:
            intensity_figure = None
            id_outputs = [np.nan] * 6
            flag = np.nan

        figpath = os.path.join(fig_channel_dir_name, 'Summary Graphs.png')
        if save_visualizations == True and (binarization or intensity_distribution):
            num_figs = len(list(filter(None, [binarization_figure, intensity_figure])))
            fig = plt.figure(figsize = (5 * num_figs, 5))
            if binarization_figure != None:
                ax1 = binarization_figure.axes[0]
                ax1.figure = fig
                fig.add_axes(ax1)
                if num_figs == 2:
                    ax1.set_position([1.5/10, 1/10, 4/5, 4/5])
            if intensity_figure != None:               
                ax3 = intensity_figure.axes[0]
                ax3.figure = fig
                fig.add_axes(ax3)
                if num_figs == 2:
                    ax3.set_position([11.5/10, 1/10, 4/5, 4/5])
            plt.savefig(figpath)
            plt.close(fig)
        plt.close('all')

        non_barcode_params = [filename, channel, flag]
        result = non_barcode_params + binarization_outputs + id_outputs + flow_outputs        
        vprint('Channel Screening Completed')
        return result
    try:
        counts = [count, total]
        # Automatically reads ND2 file metadata for frame interval and micron-pixel-ratio
        if nd2.is_supported_file(filepath):
            try:
                with nd2.ND2File(filepath) as ndfile:
                    times = ndfile.events(orient = 'list')['Time [s]']
                    exposure_time = np.array([y - x for x, y in pairwise(times)]).mean()
                    um_pix_ratio = ndfile.voxel_size()[0]
                    config_data["optical_flow_parameters"]["exposure_time"] = round(float(exposure_time), 4)
                    config_data["optical_flow_parameters"]["um_pixel_ratio"] = round(um_pix_ratio, 3)
                    vprint(f"Extracted ND2 File Metadata: Frame Interval = {exposure_time:.4f}s, Micron-Pixel Ratio = {um_pix_ratio:.3f}")
            except:
                exposure_time = config_data["optical_flow_parameters"]['exposure_time']
                um_pix_ratio = config_data["optical_flow_parameters"]['um_pixel_ratio']
        file = read_file(filepath, counts, accept_dim_im)
        count, total = counts
    except TypeError as e:
        raise TypeError(e)
    if file is None:
        raise TypeError("File not read by BARCODE.")
    print(f'File Dimensions: {file.shape}')
    if (isinstance(file, np.ndarray) == False):
        raise TypeError("File was not of the correct filetype")
    
    channels = min(file.shape)
    
    barcode = []
    if channel_select == 'All':
        vprint('Total Channels:', channels)
        for channel in range(channels):
            vprint('Channel:', channel)
            if check_channel_dim(file[:,:,:,channel]) and not accept_dim_channel:
                vprint('Channel too dim, not enough signal, skipping...')
                continue
            elif check_channel_dim(file[:,:,:,channel]) and accept_dim_channel:
                vprint('Warning: channel is dim. Accuracy of screening may be limited by this.')
                results = analyze_channel(filepath, channel, config_data, fail_file_loc)
                results[2] = results[2] + 1
            else:
                results = analyze_channel(filepath, channel, config_data, fail_file_loc)
            barcode.append(results)
    
    else:
        while channel_select < 0:
            channel_select = channels + channel_select # -1 will correspond to last channel, etc
        if channel_select >= channels:
            channel_select = channels - 1 # Sets channel to maximum channel if channel selected is out of range
        vprint('Channel: ', channel_select)
        if check_channel_dim(file[:,:,:,channel_select]):
            vprint('Warning: channel is dim. Accuracy of screening may be limited by this.')
            results = analyze_channel(filepath, channel_select, config_data, fail_file_loc)
            results[2] = results[2] + 1 # Indicate dim channel flag present
        else:
            results = analyze_channel(filepath, channel_select, config_data, fail_file_loc)
        barcode.append(results)

    return barcode, count

def remove_extension(filepath):
    for suffix in (".tif", ".tiff", ".nd2"):
        if filepath.endswith(suffix):
            return filepath.removesuffix(suffix)
    return filepath

def reformat_time(time):
    if time / 3600 > 1:
            elapsed_hours = time // 3600
            elapsed_minutes = (time - (elapsed_hours * 3600))//60
            time = f'{elapsed_hours:.2f} hours, {elapsed_minutes:.2f} minutes'
    elif time / 60 > 1:
        elapsed_minutes = time / 60
        time = f'{elapsed_minutes:.2f} minutes'
    else:
        time = f'{time:.2f} seconds'
    return time

def process_directory(root_dir, config_data):
    verbose = config_data['reader']['verbose']
    generate_barcode = config_data['writer']["generate_barcode"]
    print = functools.partial(builtins.print, flush=True)
    vprint = print if verbose else lambda *a, **k: None

    def find_files(folder):
        files = []
        file_formats = (".nd2", ".tiff", ".tif")
        for dirpath, dirnames, filenames in os.walk(folder):
            for filename in filenames:
                if filename.startswith('._'):
                    continue
                if filename.endswith(file_formats):
                    files.append(os.path.join(dirpath, filename))
        return files
    
    files = [root_dir] if os.path.isfile(root_dir) else find_files(root_dir)
    file_count = len(files)
    barcode_data = []
    filename = remove_extension(os.path.basename(root_dir))
    dirname = os.path.dirname(root_dir) if os.path.isfile(root_dir) else root_dir
    print(dirname, filename)
    time_filepath = os.path.join(dirname, filename + ' Time.txt')
    error_filepath = os.path.join(dirname, filename + ' Failed Files.txt')
    settings_filepath = os.path.join(dirname, filename + " Settings.yaml")
    csv_filepath = os.path.join(dirname, filename + " Summary.csv")

    time_file = open(time_filepath, "w", encoding="utf-8")
    time_file.write(root_dir + "\n")
        
    start_folder_time = time.time()
    open(error_filepath, 'w').close()
    file_number = 1
    for file in files:
        start_file_time = time.time()
        try:
            barcode, file_number = analyze_video(file, config_data, error_filepath, file_number, file_count)
        except TypeError as e:
            if "BARCODE" in str(e):
                continue
            print(e)
            continue
        except Exception as e:
            with open(error_filepath, "a", encoding="utf-8") as log_file:
                log_file.write(f"File: {file}, Exception: {str(e)}\n")
            continue
        if barcode == None:
            continue
        barcode_data.extend(barcode)
        end_file_time = time.time()
        elapsed_file_time = reformat_time(end_file_time - start_file_time)
        vprint('Time Elapsed:', elapsed_file_time)
        time_file.write(file + "\n")
        time_file.write('Time Elapsed: ' + str(elapsed_file_time) + "\n")
    
    try:
        write_file(csv_filepath, barcode_data)
    except:
        counter = 2
        csv_filepath = os.path.join(dirname, filename + f"Summary ({counter}).csv")
        while os.path.exists(csv_filepath):
            counter += 1
            csv_filepath = os.path.join(dirname, filename + f" Summary ({counter}).csv")
        write_file(csv_filepath, barcode_data)
    channel_select = config_data['reader']['channel_select']
    separate_channel = bool(channel_select == "All")
    generate_aggregate_csv([csv_filepath], csv_filepath, generate_barcode, separate_channel=separate_channel)
    end_folder_time = time.time()
    elapsed_folder_time = reformat_time(end_folder_time - start_folder_time)
    vprint('Time Elapsed to Process Folder:', elapsed_folder_time)
    time_file.write('Time Elapsed to Process Folder: ' + str(elapsed_folder_time) + "\n")

    time_file.close()
    if os.stat(error_filepath).st_size == 0:
        os.remove(error_filepath)
    with open(settings_filepath, 'w+') as settings:
        yaml.dump(config_data, settings)