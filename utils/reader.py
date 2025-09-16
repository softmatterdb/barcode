import os, nd2
import imageio.v3 as iio
import numpy as np
import functools, builtins

def check_channel_dim(file):
    f1_min_intensity = np.min(file[0])
    f1_mean_intensity = np.mean(file[0])
    f2_min_intensity = np.min(file[-1])
    f2_mean_intensity = np.mean(file[-1])
    return (2 * np.exp(-1) * f1_mean_intensity <= f1_min_intensity) and (2 * np.exp(-1) * f2_mean_intensity <= f2_min_intensity)

def read_file(filepath, count_list, accept_dim = False, allow_large_files = True, frames = None):
    print = functools.partial(builtins.print, flush=True)
    
    if count_list[1] != 1:    
        print(f'File {count_list[0]} of {count_list[1]}')
        print(filepath)
        count_list[0] += 1

    file_size = os.path.getsize(filepath)
    file_size_gb = file_size / (1024 ** 3)
    if file_size_gb > 5 and not allow_large_files:
        print("File size is too large -- this program does not process files larger than 5 GB.")
        return None
    
    if filepath.endswith(('.tif', '.tiff')):
        file = iio.imread(filepath)
        file = np.reshape(file, (file.shape + (1,))) if len(file.shape) == 3 else file
        if file.shape[3] != min(file.shape):
            file = np.swapaxes(np.swapaxes(file, 1, 2), 2, 3)
    elif filepath.endswith('.nd2'):
        with nd2.ND2File(filepath) as ndfile:
            if len(ndfile.sizes) >= 5:
                count_list[0] += 1
                raise TypeError("Incorrect file dimensions: file must be time series data with 1+ channels (4 dimensions total)")
            if "Z" in ndfile.sizes:
                count_list[0] += 1
                raise TypeError('Z-stack identified, skipping to next file...')
            if 'T' not in ndfile.sizes or len(ndfile.shape) <= 2 or ndfile.sizes['T'] <= 5:
                count_list[0] += 1
                raise TypeError('Too few frames, unable to capture dynamics, skipping to next file...')
            if ndfile == None:
                raise TypeError('Unable to read file, skipping to next file...')
            file = ndfile.asarray()
            file = np.swapaxes(np.swapaxes(file, 1, 2), 2, 3)
    
    if (file == 0).all():
        print('Empty file: can not process, skipping to next file...')
        return None
    
    if accept_dim == False and check_channel_dim(file) == True:
        print(filepath + 'is too dim, skipping to next file...')
        return None
    
    if frames:
        return file[frames]
    else:
        return file    

def load_binarization_frame(file_path, channel = 0):
    frame = read_file(file_path, count_list = (1, 1), frames = [0])
    return frame[0,:,:,channel]