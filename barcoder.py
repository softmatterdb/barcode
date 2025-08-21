from reader import read_file
import os, yaml, time, functools, builtins, nd2
from binarization import analyze_binarization
from flow import analyze_optical_flow
from intensity_distribution_comparison import analyze_intensity_dist
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import gridspec
from itertools import pairwise
from utils import check_channel_dim, MyException
from writer import write_file, gen_combined_barcode
matplotlib.use('Agg')

class MyException(Exception):
    pass

def execute_htp(filepath, config_data, fail_file_loc, count, total):
    reader_data = config_data['reader']
    _, save_rds, save_visualizations = config_data['writer'].values()
    accept_dim_channel, accept_dim_im, binarization, channel_select, optical_flow, intensity_dist, verbose = reader_data.values()
    ib_data = config_data['image_binarization_parameters']
    of_data = config_data['optical_flow_parameters']
    id_data = config_data['intensity_distribution_parameters']
    
    print = functools.partial(builtins.print, flush=True)
    vprint = print if verbose else lambda *a, **k: None

    def check(file_path, channel, binarization, optical_flow, intensity_distribution, binarization_params, optical_flow_params, intensity_dist_params, fail_file_loc):
        flag = 0
        figure_dir_name = remove_extension(filepath) + ' BARCODE Output'
        fig_channel_dir_name = os.path.join(figure_dir_name, 'Channel ' + str(channel))
        if not os.path.exists(figure_dir_name):
            os.makedirs(figure_dir_name)
        if not os.path.exists(fig_channel_dir_name):
            os.makedirs(fig_channel_dir_name)
        
        if binarization:
            thresh_offset = binarization_params['threshold_offset']
            frame_step = binarization_params['frame_step']
            pf_eval = binarization_params['percentage_frames_evaluated']
            binning_factor = 2
            try:
                rfig, binarization_outputs = analyze_binarization(file, fig_channel_dir_name, channel, thresh_offset, frame_step, pf_eval, binning_factor, save_visualizations, save_rds, verbose)
            except Exception as e:
                with open(fail_file_loc, "a", encoding="utf-8") as log_file:
                    log_file.write(f"File: {file_path}, Module: Binarization, Exception: {str(e)}\n")
                rfig = None
                binarization_outputs = [np.nan] * 7
        else:
            rfig = None
            binarization_outputs = [np.nan] * 7
        if optical_flow:
            downsample = optical_flow_params['downsample']
            frame_step = optical_flow_params['frame_step']
            win_size = optical_flow_params['win_size']
            pf_eval = optical_flow_params['percentage_frames_evaluated']
            # Automatically reads ND2 file metadata for frame interval and micron-pixel-ratio
            if nd2.is_supported_file(filepath):
                with nd2.ND2File(filepath) as ndfile:
                    times = ndfile.events(orient = 'list')['Time [s]']
                    exposure_time = np.array([y - x for x, y in pairwise(times)]).mean()
                    um_pix_ratio = 1/(ndfile.voxel_size()[0])
            else:
                exposure_time = optical_flow_params['exposure_time']
                um_pix_ratio = optical_flow_params['um_pixel_ratio']
            try:
                flow_outputs = analyze_optical_flow(file, fig_channel_dir_name, channel, frame_step, downsample, exposure_time, um_pix_ratio, pf_eval, save_visualizations, save_rds, verbose, win_size)
            except Exception as e:
                with open(fail_file_loc, "a", encoding="utf-8") as log_file:
                    log_file.write(f"File: {file_path}, Module: Optical Flow, Exception: {str(e)}\n")
                flow_outputs = [np.nan] * 4
        else:
            flow_outputs = [np.nan] * 4
        if intensity_distribution:
            noise_threshold = intensity_dist_params['noise_threshold']
            bin_size = intensity_dist_params['bin_size']
            pf_eval = intensity_dist_params['percentage_frames_evaluated']
            frame_step = intensity_dist_params['frame_step']
            try:
                cfig, id_outputs, flag = analyze_intensity_dist(file, fig_channel_dir_name, channel, pf_eval, frame_step, bin_size, noise_threshold, save_visualizations, save_rds, verbose)
            except Exception as e:
                with open(fail_file_loc, "a", encoding="utf-8") as log_file:
                    log_file.write(f"File: {file_path}, Module: Intensity Distribution, Exception: {str(e)}\n")
                cfig = np.nan
                id_outputs = [np.nan] * 6
                flag = np.nan
        else:
            cfig = None
            id_outputs = [np.nan] * 6
            flag = np.nan

        figpath = os.path.join(fig_channel_dir_name, 'Summary Graphs.png')
        if save_visualizations == True and (binarization or intensity_distribution):
            num_figs = len(list(filter(None, [rfig, cfig])))
            fig = plt.figure(figsize = (5 * num_figs, 5))
            if rfig != None:
                ax1 = rfig.axes[0]
                ax1.figure = fig
                fig.add_axes(ax1)
                if num_figs == 2:
                    ax1.set_position([1.5/10, 1/10, 4/5, 4/5])
            if cfig != None:               
                ax3 = cfig.axes[0]
                ax3.figure = fig
                fig.add_axes(ax3)
                if num_figs == 2:
                    ax3.set_position([11.5/10, 1/10, 4/5, 4/5])
            plt.savefig(figpath)
            plt.close(fig)
        plt.close('all')

        non_barcode_params = [filepath, channel, flag]
        result = non_barcode_params + binarization_outputs + id_outputs + flow_outputs        
        vprint('Channel Screening Completed')
        return result
    
    try:
        counts = [count, total]
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
    
    rfc = []
    if channel_select == 'All':
        vprint('Total Channels:', channels)
        for channel in range(channels):
            vprint('Channel:', channel)
            if check_channel_dim(file[:,:,:,channel]) and not accept_dim_channel:
                vprint('Channel too dim, not enough signal, skipping...')
                continue
            elif check_channel_dim(file[:,:,:,channel]) and accept_dim_channel:
                vprint('Warning: channel is dim. Accuracy of screening may be limited by this.')
                results = check(filepath, channel, binarization, optical_flow, intensity_dist, ib_data, of_data, id_data, fail_file_loc)
                results[2] = results[2] + 1
            else:
                results = check(filepath, channel, binarization, optical_flow, intensity_dist, ib_data, of_data, id_data, fail_file_loc)
            rfc.append(results)
    
    else:
        while channel_select < 0:
            channel_select = channels + channel_select # -1 will correspond to last channel, etc
        if channel_select >= channels:
            channel_select = channels - 1 # Sets channel to maximum channel if channel selected is out of range
        vprint('Channel: ', channel_select)
        if check_channel_dim(file[:,:,:,channel_select]):
            vprint('Warning: channel is dim. Accuracy of screening may be limited by this.')
            results = check(filepath, channel_select, binarization, optical_flow, intensity_dist, ib_data, of_data, id_data, fail_file_loc)
            results[2] = results[2] + 1 # Indicate dim channel flag present
        else:
            results = check(filepath, channel_select, binarization, optical_flow, intensity_dist, ib_data, of_data, id_data, fail_file_loc)
        rfc.append(results)

    return rfc, count

def remove_extension(filepath):
    for suffix in [".tif", ".tiff", ".nd2"]:
        if filepath.endswith(suffix):
            return filepath.removesuffix(suffix)

def reformat_time(time):
    if time / 3600 > 1:
            elapsed_hours = int(time // 3600)
            elapsed_minutes = (time - (elapsed_hours * 3600))/60
            time = f'{elapsed_hours:.2f} hours, {elapsed_minutes:.2f} minutes'
    elif time / 60 > 1:
        elapsed_minutes = time / 60
        time = f'{elapsed_minutes:.2f} minutes'
    else:
        time = f'{time:.2f} seconds'
    return time

def process_directory(root_dir, config_data):
    verbose = config_data['reader']['verbose']
    writer_data = config_data['writer']
    generate_barcode, _, _ = writer_data.values()
    print = functools.partial(builtins.print, flush=True)
    vprint = print if verbose else lambda *a, **k: None
    
    if os.path.isfile(root_dir):
        channel_select = config_data['reader']['channel_select']
        all_data = []
        file_path = root_dir
        filename = os.path.basename(file_path)
        dir_name = os.path.dirname(file_path)
        rfc_data = None
        ff_loc = os.path.join(dir_name, remove_extension(filename) + "_failed_files.txt")
        open(ff_loc, 'w').close()
        time_filepath = os.path.join(dir_name, filename + 'time.txt')
        time_file = open(time_filepath, "w", encoding="utf-8")
        time_file.write(file_path + "\n")
        start_time = time.time()
        file_count = 1
        try:
            rfc_data, file_count = execute_htp(file_path, config_data, ff_loc, file_count, total=1)
        except TypeError as e:
            print(e)
            return
        except Exception as e:
            with open(ff_loc, "a", encoding="utf-8") as log_file:
                log_file.write(f"File: {file_path}, Exception: {str(e)}\n")
        if rfc_data == None:
            print("BARCODE could not process this data. Please try with a different file.")
            return
        all_data.extend(rfc_data)
        filename = remove_extension(filename) + '_'
        end_time = time.time()
        elapsed_time = reformat_time(end_time - start_time)
        
        vprint('Time Elapsed:', elapsed_time)
        time_file.write('Time Elapsed: ' + str(elapsed_time) + "\n")
        output_filepath = os.path.join(dir_name, filename + ' Summary.csv')
        write_file(output_filepath, all_data)
        
        if generate_barcode:
            output_figpath = os.path.join(dir_name, filename + ' Summary Barcode')
            if channel_select == "All":
                gen_combined_barcode(np.array(rfc_data[:,1:]), output_figpath, separate = False)
            else:
                gen_combined_barcode(np.array(rfc_data[:,1:]), output_figpath)
        settings_loc = os.path.join(dir_name, filename + " Settings.yaml")
        with open(settings_loc, 'w+', encoding="utf-8") as ff:
            yaml.dump(config_data, ff)

        time_file.close()
        if os.stat(ff_loc).st_size == 0:
            os.remove(ff_loc)
    else: 
        all_data = []
        all_rfc_data = []
        time_filepath = os.path.join(root_dir, os.path.basename(root_dir) + ' time.txt')
        time_file = open(time_filepath, "w", encoding="utf-8")
        time_file.write(root_dir + "\n")
        
        start_folder_time = time.time()
        ff_loc = os.path.join(root_dir, "failed_files.txt")
        open(ff_loc, 'w').close()

        file_count = sum([len([file for file in files if (file.endswith(".tif") or file.endswith(".nd2"))]) for _, _, files in os.walk(root_dir)])
        file_itr = 1
        
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames]
    
            for filename in filenames:
                if filename.startswith('._'):
                    continue

                file_path = os.path.join(dirpath, filename)
                start_time = time.time()
                try:
                    rfc_data, file_itr = execute_htp(file_path, config_data, ff_loc, file_itr, file_count)
                except TypeError as e:
                    if "BARCODE" in str(e):
                        continue
                    print(e)
                    continue
                except Exception as e:
                    with open(ff_loc, "a", encoding="utf-8") as log_file:
                        log_file.write(f"File: {file_path}, Exception: {str(e)}\n")
                    continue
                if rfc_data == None:
                    continue
                all_data.extend(rfc_data)
                for result in rfc_data:
                    all_rfc_data.append(np.array(result[1:]))

                end_time = time.time()
                elapsed_time = reformat_time(end_time - start_time)
                vprint('Time Elapsed:', elapsed_time)
                time_file.write(file_path + "\n")
                time_file.write('Time Elapsed: ' + str(elapsed_time) + "\n")
        
        output_filepath = os.path.join(root_dir, os.path.basename(root_dir) + " Summary.csv")
        try:
            write_file(output_filepath, all_data)
        except:
            counter = 1
            output_filepath = os.path.join(root_dir, os.path.basename(root_dir) + f" Summary ({counter}).csv")
            while os.path.exists(output_filepath):
                counter += 1
                output_filepath = os.path.join(root_dir, os.path.basename(root_dir) + f" Summary ({counter}).csv")
            write_file(output_filepath, all_data)
        
        if generate_barcode:
            try:
                output_figpath = os.path.join(root_dir, os.path.basename(root_dir) + ' Summary Barcode')
                gen_combined_barcode(np.array(all_rfc_data), output_figpath)
            except Exception as e:
                with open(ff_loc, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Unable to generate barcode, Exception: {str(e)}\n")

        end_folder_time = time.time()
        elapsed_folder_time = reformat_time(end_folder_time - start_folder_time)
        vprint('Time Elapsed to Process Folder:', elapsed_folder_time)
        time_file.write('Time Elapsed to Process Folder: ' + str(elapsed_folder_time) + "\n")
        
        time_file.close()
        if os.stat(ff_loc).st_size == 0:
            os.remove(ff_loc)
        settings_loc = os.path.join(root_dir, os.path.basename(root_dir) + " Settings.yaml")
        with open(settings_loc, 'w+') as ff:
            yaml.dump(config_data, ff)