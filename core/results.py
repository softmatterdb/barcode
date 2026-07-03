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
    
    def get_dict_data(self, **kwargs) -> np.ndarray:
        """Convert results to dictionary"""
        pass


@dataclass
class BinarizationResults(ResultsBase):
    """Results from binarization analysis."""

    connectivity: float = np.nan
    max_island_size: float = np.nan
    max_void_size: float = np.nan
    max_island_percent_change: float = np.nan
    max_void_percent_change: float = np.nan
    island_size_initial: float = np.nan
    island_size_initial2: float = np.nan
    island_anisotropy: float = np.nan
    mean_island_size: float = np.nan
    total_island_size: float = np.nan
    mean_island_separation: float = np.nan
    island_correlation_length: float = np.nan

    max_island_size_quantity: float = np.nan
    max_void_size_quantity: float = np.nan
    island_size_initial_quantity: float = np.nan
    island_size_initial2_quantity: float = np.nan
    mean_island_size_quantity: float = np.nan
    total_island_size_quantity: float = np.nan
    
    structural_correlation_flag: int = 0

    @classmethod
    def get_metrics(cls) -> List[Metrics]:
        return [
            Metrics.CONNECTIVITY,
            Metrics.ISLAND_MAX_AREA,
            Metrics.VOID_MAX_AREA,
            Metrics.MAX_ISLAND_AREA_CHANGE,
            Metrics.MAX_VOID_AREA_CHANGE,
            Metrics.ISLAND_MAX_AREA_INITIAL,
            Metrics.ISLAND_MAX_AREA_INITIAL2,
            Metrics.ISLAND_ANISOTROPY,
            Metrics.ISLAND_MEAN_AREA,
            Metrics.ISLAND_TOTAL_AREA,
            Metrics.ISLAND_DISTANCE,
            Metrics.ISLAND_CORRELATION,
        ]
    
    @classmethod
    def get_physical_metrics(cls) -> List[Metrics]:
        return [
            Metrics.CONNECTIVITY,
            Metrics.ISLAND_MAX_AREA_QUANTITY,
            Metrics.VOID_MAX_AREA_QUANTITY,
            Metrics.MAX_ISLAND_AREA_CHANGE,
            Metrics.MAX_VOID_AREA_CHANGE,
            Metrics.ISLAND_MAX_AREA_INITIAL_QUANTITY,
            Metrics.ISLAND_MAX_AREA_INITIAL2_QUANTITY,
            Metrics.ISLAND_ANISOTROPY,
            Metrics.ISLAND_MEAN_AREA_QUANTITY,
            Metrics.ISLAND_TOTAL_AREA_QUANTITY,
            Metrics.ISLAND_DISTANCE,
            Metrics.ISLAND_CORRELATION,
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
            Units.NONE,
            Units.PERCENT_FOV,
            Units.PERCENT_FOV,
            Units.LENGTH,
            Units.LENGTH,
        ]
    
    @classmethod
    def get_physical_units(cls) -> List[Units]:
        return [
            Units.PERCENT_FRAMES,
            Units.AREA,
            Units.AREA,
            Units.PERCENT_CHANGE,
            Units.PERCENT_CHANGE,
            Units.AREA,
            Units.AREA,
            Units.NONE,
            Units.AREA,
            Units.AREA,
            Units.LENGTH,
            Units.LENGTH,
        ]

    def get_data(self) -> List[float]:
        return [
            self.connectivity,
            self.max_island_size,
            self.max_void_size,
            self.max_island_percent_change,
            self.max_void_percent_change,
            self.island_size_initial,
            self.island_size_initial2,
            self.island_anisotropy,
            self.mean_island_size,
            self.total_island_size,
            self.mean_island_separation,
            self.island_correlation_length,
        ]
    
    def get_physical_data(self) -> List[float]:
        return [
            self.connectivity,
            self.max_island_size_quantity,
            self.max_void_size_quantity,
            self.max_island_percent_change,
            self.max_void_percent_change,
            self.island_size_initial_quantity,
            self.island_size_initial2_quantity,
            self.island_anisotropy,
            self.mean_island_size_quantity,
            self.total_island_size_quantity,
            self.mean_island_separation,
            self.island_correlation_length,
        ]
    
    def get_dict_data(self) -> dict:
        return dict(zip(self.get_metrics(), self.get_data()))
    
    def get_physical_dict_data(self) -> dict:
        return dict(zip(self.get_physical_metrics(), self.get_physical_data()))


@dataclass
class FlowResults(ResultsBase):
    """Results from optical flow analysis."""

    mean_speed: float = np.nan
    delta_speed: float = np.nan
    mean_theta: float = np.nan
    mean_sigma_theta: float = np.nan
    velocity_correlation_length: float = np.nan
    divergence: float = np.nan
    curl: float = np.nan
    velocity_correlation_flag: int = 0

    @classmethod
    def get_metrics(cls) -> List[Metrics]:
        return [
            Metrics.SPEED,
            Metrics.DELTA_SPEED,
            Metrics.MEAN_THETA,
            Metrics.MEAN_SIGMA_THETA,
            Metrics.VELOCITY_CORRELATION,
            Metrics.DIVERGENCE,
            Metrics.CURL,
        ]

    @classmethod
    def get_units(cls) -> List[Units]:
        return [
            Units.SPEED,
            Units.SPEED,
            Units.DIRECTION,
            Units.DIRECTION,
            Units.LENGTH,
            Units.NONE,
            Units.NONE,
        ]

    def get_data(self) -> List[float]:
        return [
            self.mean_speed,
            self.delta_speed,
            self.mean_theta,
            self.mean_sigma_theta,
            self.velocity_correlation_length,
            self.divergence,
            self.curl,
        ]
    
    def get_dict_data(self) -> dict:
        return dict(zip(self.get_metrics(), self.get_data()))


@dataclass
class IntensityResults(ResultsBase):
    """Results from intensity distribution analysis."""

    max_kurtosis: float = np.nan
    max_median_skew: float = np.nan
    max_mode_skew: float = np.nan
    kurtosis_diff: float = np.nan
    median_skew_diff: float = np.nan
    mode_skew_diff: float = np.nan
    saturation_flag: int = 0

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
    
    def get_dict_data(self) -> dict:
        return dict(zip(self.get_metrics(), self.get_data()))


@dataclass
class ChannelResults(ResultsBase):
    """Complete analysis results for a single channel."""

    filepath: str
    channel: int
    total_flags: str = ""
    dim_channel_flag: int = 0  # 0=normal, 1=dim channel

    binarization: BinarizationResults = field(default_factory=BinarizationResults)
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
    def get_physical_metrics(cls, just_metrics: bool = False) -> List[Metrics]:
        return (
            (
                [Metrics.FILEPATH, Metrics.CHANNEL, Metrics.FLAGS]
                if not just_metrics
                else []
            )
            + BinarizationResults.get_physical_metrics()
            + IntensityResults.get_metrics()
            + FlowResults.get_metrics()
        )
    
    @classmethod
    def get_physical_headers(cls, just_metrics: bool = False) -> List[str]:
        """Get headers for CSV output."""
        return [metric.value for metric in cls.get_physical_metrics(just_metrics)]

    @classmethod
    def get_units(cls, just_metrics: bool = False) -> List[Units]:
        return (
            ([Units.NONE, Units.NONE, Units.NONE] if not just_metrics else [])
            + BinarizationResults.get_units()
            + IntensityResults.get_units()
            + FlowResults.get_units()
        )
    
    def get_physical_units(cls, just_metrics: bool = False) -> List[Units]:
        return (
            ([Units.NONE, Units.NONE, Units.NONE] if not just_metrics else [])
            + BinarizationResults.get_physical_units()
            + IntensityResults.get_units()
            + FlowResults.get_units()
        )
    
    def convert_flags(self) -> str:
        flag_lst = []
        if self.dim_channel_flag == 1:
            flag_lst.append("Channel is dim -- accuracy of screening may be limited")
        if self.intensity.saturation_flag == 1:
            flag_lst.append("Video is saturated -- intensity distribution analysis may be limited")
        if self.binarization.structural_correlation_flag == 1:
            flag_lst.append("Some frames show correlation length greater than FOV size -- " \
            "structural correlation length may be inaccurate.")
        if self.flow.velocity_correlation_flag == 1:
            flag_lst.append("Some flow fields show correlation length greater than FOV size -- " \
            "velocity correlation length may be inaccurate.")
        return ";".join(flag_lst)
            

    def get_data(self, just_metrics: bool = False) -> List[float]:
        data = []
        self.total_flags = self.convert_flags()
        if not just_metrics:
            data = [self.filepath, self.channel, self.total_flags]
        data.extend(self.binarization.get_data())
        data.extend(self.intensity.get_data())
        data.extend(self.flow.get_data())
        return data
    
    def get_physical_data(self, just_metrics: bool = False) -> List[float]:
        data = []
        self.total_flags = self.convert_flags()
        if not just_metrics:
            data = [self.filepath, self.channel, self.total_flags]
        data.extend(self.binarization.get_physical_data())
        data.extend(self.intensity.get_data())
        data.extend(self.flow.get_data())
        return data
    
    def get_dict_data(self, just_metrics: bool = False) -> dict:
        binarization_data = self.binarization.get_dict_data()
        intensity_data = self.intensity.get_dict_data()
        flow_data = self.flow.get_dict_data()
        self.total_flags = self.convert_flags()
        if just_metrics:
            data = binarization_data | intensity_data | flow_data
        else:
            data = {Metrics.FILEPATH: self.filepath,
                    Metrics.CHANNEL: self.channel,
                    Metrics.FLAGS: self.total_flags}
            data = data | binarization_data | intensity_data | flow_data
        return data
    
    def get_physical_dict_data(self, just_metrics: bool = False) -> dict:
        binarization_data = self.binarization.get_physical_dict_data()
        intensity_data = self.intensity.get_dict_data()
        flow_data = self.flow.get_dict_data()
        if just_metrics:
            data = binarization_data | intensity_data | flow_data
        else:
            data = {Metrics.FILEPATH: self.filepath,
                    Metrics.CHANNEL: self.channel,
                    Metrics.FLAGS: self.dim_channel_flag}
            data = data | binarization_data | intensity_data | flow_data
        return data
    
    def to_physical_array(self, **kwargs) -> np.ndarray:
        """Convert results to a NumPy array for easier manipulation."""
        return np.array(self.get_physical_data(**kwargs), dtype=float)

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