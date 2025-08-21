import numpy as np
# Global verbose setting
_VERBOSE = False

def set_verbose(verbose: bool):
    """Set global verbose mode."""
    global _VERBOSE
    _VERBOSE = verbose

def vprint(*args, **kwargs):
    """Global verbose print function."""
    if _VERBOSE:
        print(*args, **kwargs, flush=True)

class MyException(Exception):
    pass

def normalize_counts(count): 
    return count / count.sum()

def inv(arr):
    ones_arr = np.ones(shape = arr.shape)
    return ones_arr - arr

def groupAvg(arr, N, bin_mask=False):
    result = np.cumsum(arr, 0)[N-1::N]/float(N)
    result = np.cumsum(result, 1)[:,N-1::N]/float(N)
    result[1:] = result[1:] - result[:-1]
    result[:,1:] = result[:,1:] - result[:,:-1]
    if bin_mask:
        result = np.where(result > 0, 1, 0)
    return result

def average_largest(lst, percent = 0.1):
    lst.sort(reverse=True)
    length = len(lst)
    top_percent = int(np.ceil(length * percent))
    return np.nanmean(lst[0:top_percent])

def flatten(xss):
    return np.array([x for xs in xss for x in xs])

def find_analysis_frames(file, step_size):
    image_length = len(file)
    while step_size >= image_length:
        step_size /= 5
        vprint(f'Step size between frames too large for analysis, new step size set to {step_size}')
    frame_indices = list(range(0, image_length, step_size))
    if frame_indices[-1] != image_length - 1:
        frame_indices.append(image_length - 1)
    return frame_indices, step_size

def check_channel_dim(image):
    min_intensity = np.min(image)
    mean_intensity = np.mean(image)
    return 2 * np.exp(-1) * mean_intensity <= min_intensity