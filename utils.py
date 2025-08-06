import numpy as np
from scipy.stats import mode

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
    return np.mean(lst[0:top_percent])

def calc_mode(frame):
    mode_result = mode(frame.flatten(), keepdims=False)
    mode_intensity = mode_result.mode if isinstance(mode_result.mode, np.ndarray) else np.array([mode_result.mode])
    mode_intensity = mode_intensity[0] if mode_intensity.size > 0 else np.nan
    return mode_intensity

def mode_skewness(frame):
    mean_intensity = np.mean(frame)
    mode_intensity = calc_mode(frame)
    stdev_intensity = np.std(frame)
    return (mean_intensity - mode_intensity)/stdev_intensity

def median_skewness(frame):
    mean_intensity = np.mean(frame)
    median_intensity = np.median(frame)
    stdev_intensity = np.std(frame)
    return 3 * (mean_intensity - median_intensity)/stdev_intensity

def calc_frame_metric(metric, data):
    mets = []
    for i in range(len(data)):
        met = metric(data[i].flatten())
        mets.append(met)
    return mets

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