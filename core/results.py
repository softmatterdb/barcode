from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

import numpy as np

from core import Metrics, Units
from core.config import BinarizationConfig


@dataclass
class ResultsBase(ABC):
    """Base class for all analysis results."""

    @classmethod
    @abstractmethod
    def get_metrics(cls, **kwargs) -> List[Metrics]:
        """Get the metrics associated with this results class."""
        pass

    @classmethod
    @abstractmethod
    def get_units(cls, **kwargs) -> List[Units]:
        """Get the units associated with this results class."""
        pass

    @classmethod
    def get_headers(cls, **kwargs) -> List[str]:
        """Get headers for CSV output."""
        return [metric.value for metric in cls.get_metrics(**kwargs)]

    @abstractmethod
    def get_data(self, **kwargs) -> List[float]:
        """Return the results as a list for CSV writing."""
        pass

    def to_array(self, **kwargs) -> np.ndarray:
        """Convert results to a NumPy array for easier manipulation."""
        return np.array(self.get_data(**kwargs), dtype=float)


@dataclass
class BinarizationResults(ResultsBase):
    """Results from binarization analysis."""

    spanning: float = np.nan
    max_island_size: float = np.nan
    max_void_size: float = np.nan
    avg_island_percent_change: float = np.nan
    avg_void_percent_change: float = np.nan
    island_size_initial: float = np.nan
    island_size_initial2: float = np.nan

    @classmethod
    def get_metrics(cls) -> List[Metrics]:
        return [
            Metrics.SPANNING,
            Metrics.ISLAND_MAX_AREA,
            Metrics.VOID_MAX_AREA,
            Metrics.AVG_ISLAND_AREA_CHANGE,
            Metrics.AVG_VOID_AREA_CHANGE,
            Metrics.ISLAND_MAX_AREA_INITIAL,
            Metrics.ISLAND_MAX_AREA_INITIAL2,
        ]

    @classmethod
    def get_units(cls) -> List[Units]:
        return [
            Units.PERCENT_FRAMES,
            Units.PERCENT_FOV,
            Units.PERCENT_FOV,
            Units.PERCENT_CHANGE,
            Units.PERCENT_CHANGE,
            Units.PERCENT_FOV,
            Units.PERCENT_FOV,
        ] 
    
    def get_data(self) -> List[float]:
        return [
            self.spanning,
            self.max_island_size,
            self.max_void_size,
            self.avg_island_percent_change,
            self.avg_void_percent_change,
            self.island_size_initial,
            self.island_size_initial2,
        ]
    
@dataclass
class BinarizationQuantityResults(ResultsBase):
    """Results from binarization analysis which includes absolute quantities"""

    max_island_size_quantity: float = np.nan
    max_void_size_quantity: float = np.nan
    island_size_initial_quantity: float = np.nan
    island_size_initial2_quantity: float = np.nan

    @classmethod
    def get_metrics(cls) -> List[Metrics]:
        return [
            Metrics.ISLAND_MAX_AREA_QUANTITY,
            Metrics.VOID_MAX_AREA_QUANTITY,
            Metrics.ISLAND_MAX_AREA_INITIAL_QUANTITY,
            Metrics.ISLAND_MAX_AREA_INITIAL2_QUANTITY
        ]

    @classmethod
    def get_units(cls) -> List[Units]:
        return [
            Units.AREA,
            Units.AREA,
            Units.AREA,
            Units.AREA
        ] 
    
    def get_data(self) -> List[float]:
        return [
            self.max_island_size_quantity,
            self.max_void_size_quantity,
            self.island_size_initial_quantity,
            self.island_size_initial2_quantity
        ]



@dataclass
class FlowResults(ResultsBase):
    """Results from optical flow analysis."""

    mean_speed: float = np.nan
    delta_speed: float = np.nan
    mean_theta: float = np.nan
    mean_sigma_theta: float = np.nan

    @classmethod
    def get_metrics(cls) -> List[Metrics]:
        return [
            Metrics.MEAN_SPEED,
            Metrics.DELTA_SPEED,
            Metrics.MEAN_THETA,
            Metrics.MEAN_SIGMA_THETA,
        ]

    @classmethod
    def get_units(cls) -> List[Units]:
        return [
            Units.SPEED,
            Units.ACCELERATION,
            Units.DIRECTION,
            Units.DIRECTION,
        ]

    def get_data(self) -> List[float]:
        return [
            self.mean_speed,
            self.delta_speed,
            self.mean_theta,
            self.mean_sigma_theta,
        ]


@dataclass
class IntensityResults(ResultsBase):
    """Results from intensity distribution analysis."""

    max_kurtosis: float = np.nan
    max_median_skew: float = np.nan
    max_mode_skew: float = np.nan
    kurtosis_diff: float = np.nan
    median_skew_diff: float = np.nan
    mode_skew_diff: float = np.nan
    flag: int = 0

    @classmethod
    def get_metrics(cls) -> List[Metrics]:
        return [
            Metrics.MAX_KURTOSIS,
            Metrics.MAX_MEDIAN_SKEW,
            Metrics.MAX_MODE_SKEW,
            Metrics.KURTOSIS_DIFF,
            Metrics.MEDIAN_SKEW_DIFF,
            Metrics.MODE_SKEW_DIFF,
        ]

    @classmethod
    def get_units(cls) -> List[Units]:
        return [
            Units.NONE,
            Units.NONE,
            Units.NONE,
            Units.NONE,
            Units.NONE,
            Units.NONE,
        ]

    def get_data(self) -> List[float]:
        return [
            self.max_kurtosis,
            self.max_median_skew,
            self.max_mode_skew,
            self.kurtosis_diff,
            self.median_skew_diff,
            self.mode_skew_diff,
        ]


@dataclass
class ChannelResults(ResultsBase):
    """Complete analysis results for a single channel."""

    filepath: str
    channel: int
    dim_channel_flag: int = 0  # 0=normal, 1=dim channel

    binarization: BinarizationResults = field(default_factory=BinarizationResults)
    binarization_quantity: BinarizationQuantityResults = field(default_factory=BinarizationQuantityResults)
    intensity: IntensityResults = field(default_factory=IntensityResults)
    flow: FlowResults = field(default_factory=FlowResults)

    @classmethod
    def _get_base_headers(cls) -> List[str]:
        return ["Filepath", "Channel", "Flags"]

    @classmethod
    def get_metrics(cls, just_metrics: bool = False) -> List[Metrics]:
        return (
            (
                [Metrics.FILEPATH, Metrics.CHANNEL, Metrics.FLAGS]
                if not just_metrics
                else []
            )
            + BinarizationResults.get_metrics()
            + IntensityResults.get_metrics()
            + FlowResults.get_metrics()
        )
    
    @classmethod
    def get_extended_metrics(cls, just_metrics: bool = False) -> List[Metrics]:
        return (
            (
                [Metrics.FILEPATH, Metrics.CHANNEL, Metrics.FLAGS]
                if not just_metrics
                else []
            )
            + BinarizationResults.get_metrics()
            + BinarizationQuantityResults.get_metrics()
            + IntensityResults.get_metrics()
            + FlowResults.get_metrics()
        )
    
    @classmethod
    def get_extended_headers(cls, just_metrics: bool = False) -> List[str]:
        """Get headers for CSV output."""
        return [metric.value for metric in cls.get_extended_metrics(just_metrics)]

    @classmethod
    def get_units(cls, just_metrics: bool = False) -> List[Units]:
        return (
            ([Units.NONE, Units.NONE, Units.NONE] if not just_metrics else [])
            + BinarizationResults.get_units()
            + IntensityResults.get_units()
            + FlowResults.get_units()
        )
    
    def get_extended_units(cls, just_metrics: bool = False) -> List[Units]:
        return (
            ([Units.NONE, Units.NONE, Units.NONE] if not just_metrics else [])
            + BinarizationResults.get_units()
            + BinarizationQuantityResults.get_units()
            + IntensityResults.get_units()
            + FlowResults.get_units()
        )

    def get_data(self, just_metrics: bool = False) -> List[float]:
        data = []
        if not just_metrics:
            data = [self.filepath, self.channel, self.dim_channel_flag]
        data.extend(self.binarization.get_data())
        data.extend(self.intensity.get_data())
        data.extend(self.flow.get_data())
        return data
    
    def get_extended_data(self, just_metrics: bool = False) -> List[float]:
        data = []
        if not just_metrics:
            data = [self.filepath, self.channel, self.dim_channel_flag]
        data.extend(self.binarization.get_data())
        data.extend(self.binarization_quantity.get_data())
        data.extend(self.intensity.get_data())
        data.extend(self.flow.get_data())
        return data
    
    def to_extended_array(self, **kwargs) -> np.ndarray:
        """Convert results to a NumPy array for easier manipulation."""
        return np.array(self.get_extended_data(**kwargs), dtype=float)


def sort_channel_results_by_metric(
    results: List[ChannelResults], sort_metric: str
) -> None:
    def get_metric_value(result: ChannelResults, metric_name: str) -> float:
        """Get metric value by header name."""
        headers = ChannelResults.get_headers(just_metrics=False)
        data = result.get_data(just_metrics=False)

        try:
            idx = headers.index(metric_name)
            return data[idx]
        except (ValueError, IndexError):
            return 0.0  # Default for sorting if metric not found

    results.sort(key=lambda r: get_metric_value(r, sort_metric))
