from typing import List

import numpy as np
from scipy.stats import mode
from skimage.measure import label, regionprops

def inv(arr: np.ndarray) -> np.ndarray:
    """Invert a binary array."""
    ones_arr = np.ones(shape=arr.shape)
    return ones_arr - arr


def group_avg(arr: np.ndarray, N: int) -> np.ndarray:
    """Downsample 2D array by averaging over N x N blocks."""
    result = np.cumsum(arr, 0)[N - 1 :: N] / float(N)
    result = np.cumsum(result, 1)[:, N - 1 :: N] / float(N)
    result[1:] = result[1:] - result[:-1]
    result[:, 1:] = result[:, 1:] - result[:, :-1]
    return result


def binarize(frame: np.ndarray, offset_threshold: float) -> np.ndarray:
    """Binarize data based on an offset threshold."""
    avg_intensity = np.mean(frame)
    threshold = avg_intensity * (1 + offset_threshold)
    new_frame = np.where(frame < threshold, 0, 1)
    labeled_frame = label(new_frame, connectivity=2)
    regions = regionprops(labeled_frame)
    for region in regions:
        if region.area == 1:
            new_frame[labeled_frame == region.label] = 0
    return new_frame


def top_ten_average(values: List[float]) -> float:
    """Calculate the average of the top 10% of values."""
    values.sort(reverse=True)
    top_ten_percent = int(np.ceil(len(values) * 0.1))
    return np.mean(values[:top_ten_percent])


def check_channel_dim(image: np.ndarray) -> bool:
    """Check if the image is dim."""
    min_intensity = np.min(image)
    mean_intensity = np.mean(image)
    return 2 * np.exp(-1) * mean_intensity <= min_intensity


def calc_mode(frame: np.ndarray) -> float:
    """Calculate the mode of the pixel intensities in a frame."""
    mode_result = mode(frame.flatten(), keepdims=False)
    mode_intensity = (
        mode_result.mode
        if isinstance(mode_result.mode, np.ndarray)
        else np.array([mode_result.mode])
    )
    mode_intensity = mode_intensity[0] if mode_intensity.size > 0 else np.nan
    return mode_intensity


def calc_mode_skewness(frame: np.ndarray) -> float:
    """Calculate the skewness of the pixel intensities based on mode."""
    mean_intensity = np.mean(frame)
    mode_intensity = calc_mode(frame)
    stdev_intensity = np.std(frame)
    return (mean_intensity - mode_intensity) / stdev_intensity


def calc_median_skewness(frame: np.ndarray) -> float:
    """Calculate the skewness of the pixel intensities based on median."""
    mean_intensity = np.mean(frame)
    median_intensity = np.median(frame)
    stdev_intensity = np.std(frame)
    return 3 * (mean_intensity - median_intensity) / stdev_intensity
