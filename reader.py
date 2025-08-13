import os, functools, builtins
import imageio.v3 as iio
import numpy as np
import nd2

def read_file(file_path, count_list, accept_dim = False, allow_large_files = True):
    print = functools.partial(builtins.print, flush=True)
    acceptable_formats = ('.tif', '.nd2', '.tiff')
    
    if (os.path.exists(file_path) and file_path.endswith(acceptable_formats)) == False:
        return None
    

    print(f'File {count_list[0]} of {count_list[1]}')
    print(file_path)

    file_size = os.path.getsize(file_path)
    file_size_gb = file_size / (1024 ** 3)
    if file_size_gb > 5 and not allow_large_files:
        print("File size is too large -- this program does not process files larger than 5 GB.")
        return None

    def check_first_frame_dim(file):
        min_intensity = np.min(file[0])
        mean_intensity = np.mean(file[0])
        return 2 * np.exp(-1) * mean_intensity <= min_intensity
    
    if file_path.endswith('.tif') or file_path.endswith('.tiff'):
        file = iio.imread(file_path)
        file = np.reshape(file, (file.shape + (1,))) if len(file.shape) == 3 else file
        if file.shape[3] != min(file.shape):
            file = np.swapaxes(np.swapaxes(file, 1, 2), 2, 3)
    elif file_path.endswith('.nd2'):
        try:
            with nd2.ND2File(file_path) as ndfile:
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

        except Exception as e:
            raise TypeError(e)
            
        if isinstance(file, np.ndarray) == False:
            return None
        
    if (file == 0).all():
        print('Empty file: can not process, skipping to next file...')
        return None
    
    if accept_dim == False and check_first_frame_dim(file) == True:
        print(file_path + 'is too dim, skipping to next file...')
        return None
        
    else:
        count_list[0] += 1
        return file
