import nd2
try:
    import tifffile
except ImportError:
    tifffile = None
import numpy as np

def load_first_frame(file_path, channel = 0):
    ext = file_path.lower().split('.')[-1]
    if ext in ['tif', 'tiff'] and tifffile:
        img = tifffile.imread(file_path)
        if not len(img.shape) in [3, 4] or img.shape[0] <= 5:
            raise TypeError('File must be time series data with at least 5 frames...')
        img = img[0,:,:,channel] if len(img.shape) == 4 else img[0]
        return img
    elif ext == 'nd2':
        with nd2.ND2File(file_path) as ndfile:
            # ND2Reader returns an iterable over frames; grab the first frame
            # It may return a (y, x) or (c, y, x) array; handle both
            if len(ndfile.sizes) >= 5:
                    raise TypeError("Incorrect file dimensions: file must be time series data with 1+ channels (4 dimensions total)")
            if "Z" in ndfile.sizes:
                raise TypeError('Z-stack identified, skipping to next file...')
            if 'T' not in ndfile.sizes or len(ndfile.shape) <= 2 or ndfile.sizes['T'] <= 5:
                raise TypeError('Too few frames, unable to capture dynamics, skipping to next file...')
            if ndfile == None:
                raise TypeError('Unable to read file, skipping to next file...')
            file = ndfile.asarray()
            arr = np.swapaxes(np.swapaxes(file, 1, 2), 2, 3)

            # If ND2 contains channels, select channel 0 by default
            arr = arr[0,:,:,channel] if arr.ndim == 4 else arr[0]
            return arr
    raise ValueError("Only TIFF and ND2 are supported in this demo, and required libraries must be installed.")

def read_all_frames(file_path, channel):
    ext = file_path.lower().split(".")[-1]

    if ext in ["tif", "tiff"] and tifffile:
        img = tifffile.imread(file_path)
        if img.ndim == 3:
            temp = [img[i] for i in range(img.shape[0])]
            return temp
        elif img.ndim == 4:
            total_channels = img.shape[3]
            while channel < 0:
                channel += total_channels
            channel = min(channel, total_channels - 1)
            return [img[i, :, :, channel] for i in range(img.shape[0])]
        else:
            return [img]

    elif ext == "nd2":
        with nd2.ND2File(file_path) as ndfile:
            file = ndfile.asarray()
            if len(ndfile.sizes) not in [3, 4] or "T" not in ndfile.sizes or "Z" in ndfile.sizes:
                raise ValueError("Unsupported ND2 format for preview")
            img = np.swapaxes(np.swapaxes(file, 1, 2), 2, 3)
            if len(ndfile.sizes) == 3:
                return [img[i] for i in range(img.shape[0])]
            total_channels = img.shape[3]
            while channel < 0:
                channel += total_channels
            channel = min(channel, total_channels - 1)
            return [img[i, :, :, channel] for i in range(img.shape[0])]

    raise ValueError("Only TIFF and ND2 formats supported.")