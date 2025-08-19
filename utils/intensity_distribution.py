import numpy as np
from utils import normalize_counts, flatten

def mean(values: np.ndarray, probabilities: np.ndarray):
    return np.sum(values * probabilities)

def stdev(values: np.ndarray, probabilities: np.ndarray):
    mean = np.sum(values * probabilities)
    second_moment = np.sum((values ** 2) * probabilities)
    return np.sqrt(second_moment - mean ** 2)

def mode(values: np.ndarray, probabilities: np.ndarray):
    return values[np.argmax(probabilities)]
    
def median(values: np.ndarray, probabilities: np.ndarray):
    cumulative_probabilities = np.cumsum(probabilities)
    return flatten(values[np.argwhere(cumulative_probabilities >= 0.5)])[0]

def kurtosis(values: np.ndarray, probabilities: np.ndarray):
    def fourth_moment(values: np.ndarray, probabilities: np.ndarray):
        mean = np.sum(values * probabilities)
        return np.sum((values - mean) ** 4 * probabilities)
    return fourth_moment(values, probabilities)/(stdev(values, probabilities) ** 4) - 3

def mode_skewness(values: np.ndarray, probabilities: np.ndarray):
    mean_intensity = mean(values, probabilities)
    mode_intensity = mode(values, probabilities)
    stdev_intensity = stdev(values, probabilities)
    return (mean_intensity - mode_intensity)/stdev_intensity

def median_skewness(values: np.ndarray, probabilities: np.ndarray):
    mean_intensity = mean(values, probabilities)
    median_intensity = median(values, probabilities)
    stdev_intensity = stdev(values, probabilities)
    return 3 * (mean_intensity - median_intensity)/stdev_intensity

def calc_frame_metric(metric, data, bin_number = 300, noise_floor = 10**-3):
    mets = []
    for i in range(len(data)):
        frame_counts, frame_values = histogram(data[i], bin_number)
        frame_values = flatten(frame_values[np.argwhere(frame_counts > noise_floor)])
        frame_counts = flatten(frame_counts[np.argwhere(frame_counts > noise_floor)])
        met = metric(frame_values, frame_counts)
        mets.append(met)
    return mets

def frame_mode(frame: np.ndarray, bin_number: int):
    counts, values = histogram(frame, bin_number)
    return mode(values, counts)

def histogram(frame: np.ndarray, bin_number: int) -> tuple[np.ndarray, np.ndarray]:
    if bin_number == 1:
        values, count = np.unique(frame, return_counts=True)
    else:
        count, values = np.histogram(frame, bins=bin_number)
        values = values[0:-1] + (values[1] - values[0])/2
    count = normalize_counts(count)
    return count, values
