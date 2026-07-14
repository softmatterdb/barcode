from abc import ABC
from enum import Enum
from typing import List
from core.config import WriterConfig

import numpy as np

class UnitsNum(ABC):
    def _keys(self):
        return (name for name in dir(self) if not name.startswith('_'))
    __iter__ = _keys
    def _values(self):
        return (getattr(self, name) for name in self)
    def _items(self):
        return ((name, getattr(self, name)) for name in self)
    
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError
    
    def __setattr__(self, name, val):
        if name in self:
            self.name = val
        raise AttributeError


#test

class Metrics(Enum):
    """Enum for different metrics used in analysis."""

    # Metrics for binarization analysis
    CONNECTIVITY = "Connectivity"
    ISLAND_MAX_AREA = "Maximum Island Area"
    VOID_MAX_AREA = "Maximum Void Area"
    MAX_ISLAND_AREA_CHANGE = "Maximum Island Area Change"
    MAX_VOID_AREA_CHANGE = "Maximum Void Area Change"
    ISLAND_MAX_AREA_INITIAL = "Initial Maximum Island Area"
    ISLAND_MAX_AREA_INITIAL2 = "Initial 2nd Maximum Island Area"
    ISLAND_ANISOTROPY = "Mean Island Anisotropy"
    ISLAND_MEAN_AREA = "Mean Island Area"
    ISLAND_TOTAL_AREA = "Total Island Area"
    ISLAND_DISTANCE = "Mean Island Separation"
    ISLAND_CORRELATION = "Structural Correlation Length"

    # Physical Units for Binarization Void/Island Metrics
    ISLAND_MAX_AREA_QUANTITY = "Maximum Island Area Quantity"
    VOID_MAX_AREA_QUANTITY = "Maximum Void Area Quantity"
    ISLAND_MAX_AREA_INITIAL_QUANTITY = "Initial Maximum Island Area Quantity"
    ISLAND_MAX_AREA_INITIAL2_QUANTITY = "Initial 2nd Maximum Island Area Quantity"
    ISLAND_MEAN_AREA_QUANTITY = "Mean Island Area Quantity"
    ISLAND_TOTAL_AREA_QUANTITY = "Total Island Area Quantity"

    # Metrics for optical flow analysis
    SPEED = "Speed"
    DELTA_SPEED = "Speed Change"
    MEAN_THETA = "Mean Flow Direction"
    MEAN_SIGMA_THETA = "Directional Spread"
    VELOCITY_CORRELATION = "Velocity Correlation Length"
    DIVERGENCE = "Divergence"
    CURL = "Curl"

    # Metrics for intensity distribution comparison
    MAX_KURTOSIS = "Maximum Kurtosis"
    MAX_MEDIAN_SKEW = "Maximum Median Skewness"
    MAX_MODE_SKEW = "Maximum Mode Skewness"
    KURTOSIS_DIFF = "Kurtosis Change"
    MEDIAN_SKEW_DIFF = "Median Skewness Change"
    MODE_SKEW_DIFF = "Mode Skewness Change"

    IGNORE = "Ignore this"
    FILEPATH = "File"
    CHANNEL = "Channel"
    FLAGS = "Flags"


class Units(UnitsNum):
    """Enum for units corresponding to each metric."""

    NONE: str = ""
    PERCENT_FOV: str = "% of FOV"
    PERCENT_CHANGE: str = "Fractional Change"
    SPEED: str = "μm/s"
    DIRECTION: str = "rads"
    PERCENT_FRAMES: str = "% of Frames"
    LENGTH: str = "μm"
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
        
        if _limits[0] == _limits[1]:
            if _limits[0] == 0:
                _limits[1] = 1
            elif _limits[0] > 0:
                _limits[0] = 0
            else:
                _limits[1] = 0

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
        elif unit in [Units.SPEED, Units.LENGTH, Units.AREA]:
            if metric == Metrics.DELTA_SPEED:
                limits.append(dynamic_limits(data[:, i], 0))
            else:
                limits.append([0, np.nanmax(data[:, i])])
        elif unit == Units.NONE:
            if metric == Metrics.ISLAND_ANISOTROPY:
                limits.append([1, np.nanmax(data[:, i])])
            else:
                limits.append(dynamic_limits(data[:, i], 0))
        else:
            raise ValueError(f"Unsupported unit: {unit}")
    return limits
