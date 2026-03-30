import numpy as np

def binarize(frame: np.ndarray, offset_threshold: float) -> np.ndarray:
    avg_intensity = np.mean(frame)
    threshold = avg_intensity * (1 + offset_threshold)
    new_frame = np.where(frame < threshold, 0, 1)
    return new_frame

def inv(arr):
    ones_arr = np.ones(shape = arr.shape)
    return ones_arr - arr