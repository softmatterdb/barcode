from enum import Enum
from typing import List

import numpy as np


class Metrics(Enum):
    """Enum for different metrics used in analysis."""

    # Metrics for binarization analysis
    SPANNING = "Connectivity"
    ISLAND_MAX_AREA = "Maximum Island Area"
    VOID_MAX_AREA = "Maximum Void Area"
    AVG_ISLAND_AREA_CHANGE = "Average Island Area Change"
    AVG_VOID_AREA_CHANGE = "Average Void Area Change"
    ISLAND_MAX_AREA_INITIAL = "Initial Maximum Island Area"
    ISLAND_MAX_AREA_INITIAL2 = "Initial 2nd Maximum Island Area"
    ISLAND_MAX_AREA_QUANTITY = "Maximum Island Area Quantity"
    VOID_MAX_AREA_QUANTITY = "Maximum Void Area Quantity"
    ISLAND_MAX_AREA_INITIAL_QUANTITY = "Initial Maximum Island Area Quantity"
    ISLAND_MAX_AREA_INITIAL2_QUANTITY = "Initial 2nd Maximum Island Area Quantity"

    # Metrics for optical flow analysis
    MEAN_SPEED = "Mean Speed"
    DELTA_SPEED = "Speed Change"
    MEAN_THETA = "Mean Direction"
    MEAN_SIGMA_THETA = "Mean Direction Standard Deviation"

    # Metrics for intensity distribution comparison
    MAX_KURTOSIS = "Max Kurtosis"
    MAX_MEDIAN_SKEW = "Max Median Skewness"
    MAX_MODE_SKEW = "Max Mode Skewness"
    KURTOSIS_DIFF = "Kurtosis Change"
    MEDIAN_SKEW_DIFF = "Median Skewness Change"
    MODE_SKEW_DIFF = "Mode Skewness Change"

    IGNORE = "Ignore this"
    FILEPATH = "File"
    CHANNEL = "Channel"
    FLAGS = "Flags"


class Units(Enum):
    """Enum for units corresponding to each metric."""

    NONE: str = ""
    PERCENT_FOV: str = "% of FOV"
    PERCENT_CHANGE: str = "Fractional Change"
    SPEED: str = "nm/s"
    ACCELERATION: str = "nm/s"
    DIRECTION: str = "rads"
    PERCENT_FRAMES: str = "% of Frames"
    AREA: str = "μm^2"


def get_data_limits(
    data: np.ndarray, metrics: List[Metrics], units: List[Units]
) -> List[List[float]]:
    """
    Get limits for each metric in the data array based on the provided metrics and units.

    Args:
        data: 2D numpy array with shape (n_samples, n_metrics)
        metrics: List of Metrics to consider
        units: Corresponding list of Units for each metric

    Returns:
        List of limits for each metric
    """
    binarized_static_limits = [0, 1]
    direction_static_limits = [-np.pi, np.pi]
    direction_spread_static_limit = [0, np.pi]

    limits = []

    def dynamic_limits(_data: np.ndarray, threshold: float) -> List[float]:
        """Calculate dynamic limits based on the data and a threshold."""
        _limits = [np.nanmin(_data), np.nanmax(_data)]
        
        if threshold < _limits[0]:
            _limits[0] = threshold
        elif threshold > _limits[1]:
            _limits[1] = threshold
        return _limits

    # Assign limits based on metrics and units
    for i, (metric, unit) in enumerate(zip(metrics, units)):

        if unit == Units.PERCENT_FRAMES or unit == Units.PERCENT_FOV:
            limits.append(binarized_static_limits)
        elif unit == Units.DIRECTION:
            if metric == Metrics.MEAN_SIGMA_THETA:
                limits.append(direction_spread_static_limit)
            else:
                limits.append(direction_static_limits)
        elif unit == Units.PERCENT_CHANGE:
            limits.append(dynamic_limits(data[:, i], 1))
        elif unit in [Units.SPEED, Units.ACCELERATION, Units.AREA]:
            limits.append([0, np.nanmax(data[:, i])])
        elif unit == Units.NONE:
            limits.append(dynamic_limits(data[:, i], 0))
        else:
            raise ValueError(f"Unsupported unit: {unit}")

    return limits
