import numpy as np
from utils import normalize_counts, flatten

def mean(values: np.ndarray, probabilities: np.ndarray):
    return np.sum(values * probabilities)

def stdev(values: np.ndarray, probabilities: np.ndarray):
    mean = np.sum(values * probabilities)
    return np.sqrt(np.sum((values - mean) ** 2 * probabilities))

def mode(values: np.ndarray, probabilities: np.ndarray):
    try:
        return values[np.argmax(probabilities)]
    except:
        return values
    
def median(values: np.ndarray, probabilities: np.ndarray):
    cumulative_probabilities = np.cumsum(probabilities)
    try:
        return flatten(values[np.argwhere(cumulative_probabilities >= 0.5)])[0]
    except:
        return values    
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

def calc_frame_metric(metric, data, bin_number, noise_threshold):
    metric_outputs = []
    for i in range(len(data)):
        frame_counts, frame_values = histogram(data[i], bin_number, noise_threshold)
        metric_outputs.append(metric(frame_values, frame_counts))
    return metric_outputs

def calc_frame_metrics(metrics: list, data, bin_number, noise_threshold):
    outputs = np.zeros(shape = (len(data), len(metrics)))
    for i in range(len(data)):
        frame_counts, frame_values = histogram(data[i], bin_number, noise_threshold)
        for j in range(len(metrics)):
            outputs[i, j] = metrics[j](frame_values, frame_counts)
    return outputs

def frame_mode(frame: np.ndarray, bin_number: int, noise_threshold: float):
    counts, values = histogram(frame, bin_number, noise_threshold)
    return mode(values, counts)

def histogram(frame: np.ndarray, bin_number: int, noise_threshold: float) -> tuple[np.ndarray, np.ndarray]:
    if bin_number == 1:
        values, count = np.unique(frame, return_counts=True)
    else:
        count, values = np.histogram(frame, bins=bin_number)
        values = values[0:-1] + (values[1] - values[0])/2
    count = normalize_counts(count)
    values = flatten(values[np.argwhere(count > noise_threshold)])
    count = flatten(count[np.argwhere(count > noise_threshold)])
    count = normalize_counts(count)
    return count, values
