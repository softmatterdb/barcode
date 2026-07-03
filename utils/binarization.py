import numpy as np
from skimage.morphology import remove_small_holes, remove_small_objects
from utils import groupAvg

def invert_frame(arr):
    ones_arr = np.ones(shape = arr.shape)
    return ones_arr - arr

def binarize(frame: np.ndarray, offset_threshold: float, binning_factor: int, min_size: int = 1):
    avg_intensity = np.mean(frame)
    threshold = avg_intensity * (1 + offset_threshold)
    frame = groupAvg(frame, binning_factor)
    new_frame = np.where(frame < threshold, 0, 1)
    new_frame = remove_small_objects(new_frame.astype(bool), min_size + 1, connectivity = 2)
    new_frame = remove_small_holes(new_frame, min_size + 1, connectivity=2).astype(int)
    return new_frame

def sia_radial_average(frame: np.ndarray):
    nx, ny = frame.shape
    mask = np.ones_like(frame)
    dists = np.sqrt(np.arange(-1*nx/2, nx/2)[:,None]**2 + np.arange(-1*ny/2, ny/2)[None,:]**2)
    bins = np.arange(max(nx,ny)/2+1)
    histo_of_bins = np.histogram(dists[mask==1], bins)[0]
    h = np.histogram(dists[mask==1], bins, weights=frame[mask==1])[0]
    return h/histo_of_bins