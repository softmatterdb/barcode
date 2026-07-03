#!/usr/bin/env python3
"""
Pure dataclass configurations - no tkinter dependencies.
Generate GUI wrappers by running: python _config.py
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
import yaml, csv, os
from abc import ABC
import numpy as np
import imageio.v3 as iio
import av, nd2

"""
DEVELOPING GUIDE:

1. Define your configuration options here.

2. Add them to the __init__.py file in the core module to export them.

3. Add them to the `GUI_CONFIG_CLASSES` list at the bottom.

4. Run this file to generate GUI wrappers in the `gui` module.

    python core/_config.py
    
5. Use the generated GUI classes in your application.

    `from gui.config import BarcodeConfigGUI as BarcodeGUI`

"""

@dataclass
class BaseConfig(ABC):
    """Base class for all configuration sections."""

    @classmethod
    def from_dict(cls, data: dict) -> "BaseConfig":
        """Create config instance from dictionary."""
        return cls(**data)

    def to_dict(self) -> dict:
        """Convert config to dictionary for serialization."""
        return {
            field_name: getattr(self, field_name)
            for field_name in self.__dataclass_fields__
        }
    
@dataclass
class InputConfig(BaseConfig):
    """File and data input configuration."""

    file_path: str = ""
    dir_path: str = ""
    mode: str = "file"  # "file", "dir", "agg", "comp"
    configuration_file: str = ""
    length_units: str = "μm"
    time_units: str = "s"

    @property
    def length(self):
        from core.metrics import Units
        Units.LENGTH = self.length_units
        Units.AREA = f"{self.length_units}^2"
        Units.SPEED = f"{self.length_units}/{self.time_units}"
        _length = {"nm": 1e-3, "μm": 1, "mm": 1e3}
        return _length[self.length_units]
    
    @property
    def time(self):
        from core.metrics import Units
        Units.LENGTH = self.length_units
        Units.AREA = f"{self.length_units}^2"
        Units.SPEED = f"{self.length_units}/{self.time_units}"
        _time = {"s": 1, "min": 60, "hr":3600}
        return _time[self.time_units]

@dataclass
class ChannelConfig(BaseConfig):
    """Channel selection and processing configuration."""
    parse_all_channels: bool = False
    selected_channel: int = 0  # -3 to 4 range

@dataclass
class PreviewConfig(BaseConfig):
    """GUI preview and visualization settings."""

    sample_file: str = ""
    enable_live_preview: bool = True
    _sample_file: str = ""
    _sample_preview: np.ndarray = None
    preview_frame_number: int = 0

@dataclass
class AggregationConfig(BaseConfig):
    """CSV aggregation and post-processing configuration."""

    output_location: str = ""
    generate_single_barcode: bool = False
    generate_comparison_barcodes: bool = False
    separate_channels: bool = False
    sort_parameter: str = "Default"  # One of the metric headers
    csv_paths_list: List[str] = field(default_factory=list)
    metrics_list: List[bool] = field(default_factory=list)

@dataclass
class ComparisonConfig(BaseConfig):
    """BARCODE CSV post-processing parameter comparison configuration"""

    csv_location: str = ""
    first_comparison_metric: str = "Connectivity"
    second_comparison_metric: str = "Connectivity"
    output_location: str = ""

@dataclass
class VisualizationConfig(BaseConfig):
    file_path: str = ""
    rds_type: str = ""
    scale: float = 1.0
    preview_frame_number: int = 0
    video_framerate: float = 1.0
    _file_path: str = ""
    _frames: List[np.ndarray] = field(default_factory=list)
    _indices: List[int] = field(default_factory=list)

@dataclass
class ModuleConfig(BaseConfig):
    """Analysis module selection and coordination"""
    
    image_binarization: bool = False
    optical_flow: bool = False
    intensity_distribution: bool = False
    
@dataclass
class ReaderConfig(BaseConfig):
    accept_dim_channels: bool = False
    accept_dim_images: bool = False
    exposure_time: float = 1.0
    um_pixel_ratio: float = 1.0
    verbose: bool = False

@dataclass
class WriterConfig(BaseConfig):
    generate_barcode: bool = False
    save_rds: bool = False
    save_visualizations: bool = False

@dataclass
class BinarizationConfig(BaseConfig):
    threshold_offset: float = 0.1
    frame_step: int = 10
    percentage_frames_evaluated: float = 0.05
    bin_factor: int = 2
    neighbor_island_fraction: float = 0.1
    minimum_island_size: int = 1
    enable_physical_units: bool = False
    invert_binarization: bool = False


@dataclass
class OpticalFlowConfig(BaseConfig):
    frame_step: int = 10
    win_size: int = 32
    downsample: int = 8
    percentage_frames_evaluated: float = 0.05

@dataclass
class IntensityDistributionConfig(BaseConfig):
    bin_size: int = 300
    frame_step: int = 10
    noise_threshold: float = 5e-4
    percentage_frames_evaluated: float = 0.05

@dataclass
class AnalysisConfig(BaseConfig):
    aggregation: AggregationConfig = field(default_factory=AggregationConfig)
    comparison: ComparisonConfig = field(default_factory=ComparisonConfig)
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)

@dataclass
class BarcodeConfig(BaseConfig):
    channels: ChannelConfig = field(default_factory=ChannelConfig)
    image_binarization_parameters: BinarizationConfig = field(default_factory=BinarizationConfig)
    intensity_distribution_parameters: IntensityDistributionConfig = field(default_factory=IntensityDistributionConfig)
    modules: ModuleConfig = field(default_factory=ModuleConfig)
    optical_flow_parameters: OpticalFlowConfig = field(default_factory=OpticalFlowConfig)
    reader: ReaderConfig = field(default_factory=ReaderConfig)
    writer: WriterConfig = field(default_factory=WriterConfig)
    
    def save_to_yaml(self, filepath: str) -> None:
        """Save configuration to YAML file."""
        config_data = {}
        for field_name in self.__dataclass_fields__:
            subconfig = getattr(self, field_name)
            config_data[field_name] = subconfig.to_dict()

        with open(filepath, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
    
    @classmethod
    def load_from_yaml(cls, filepath: str) -> "BarcodeConfig":
        """Load configuration from YAML file."""
        with open(filepath, "r") as f:
            config_data = yaml.safe_load(f)

        if not isinstance(config_data, dict):
            raise ValueError("Error loading YAML: expected a dictionary structure")

        try:
            return cls._load_from_yaml(config_data)
        except (KeyError, AssertionError) as e:
            print(f"Error loading YAML: {e}")
            pass

        print(f"Attempting to load legacy YAML format from {filepath}")
        try:
            return cls._load_from_legacy_yaml(config_data)
        except (KeyError, AssertionError) as e:
            print(f"Error loading legacy YAML: {e}")
            pass

        raise ValueError(f"Unknown YAML format in {filepath}")

    @classmethod
    def _load_from_yaml(cls, config_data: Dict[str, Any]) -> "BarcodeConfig":
        """Load configuration from YAML data."""

        kwargs = {}
        for subconfig_class_name, subconfig_data in config_data.items():

            assert (
                subconfig_class_name in cls.__dataclass_fields__
            ), f"Unknown configuration section: {subconfig_class_name}"

            field_info = cls.__dataclass_fields__[subconfig_class_name]
            subconfig_class = field_info.default_factory

            assert callable(
                subconfig_class
            ), f"Expected {subconfig_class_name} to be a callable class, got {subconfig_class}"
            assert issubclass(
                subconfig_class, BaseConfig
            ), f"Expected {subconfig_class_name} to be a subclass of BaseConfig"

            # Get the config class and create new instance from dict
            kwargs[subconfig_class_name] = subconfig_class.from_dict(subconfig_data)

        return cls(**kwargs)

    @classmethod
    def _load_from_legacy_yaml(cls, config_data: Dict[str, Any]) -> "BarcodeConfig":
        """Load configuration from legacy YAML format."""

        read: dict = config_data["reader"]
        write: dict = config_data["writer"]

        int_params: dict = config_data["intensity_distribution_parameters"]
        flow_params: dict = config_data["optical_flow_parameters"]
        bin_params: dict = config_data["image_binarization_parameters"]

        return BarcodeConfig(
            channels=ChannelConfig(
                parse_all_channels=read["channel_select"] == "All",
                selected_channel=(
                    read["channel_select"] if read["channel_select"] != "All" else 0
                ),
            ),
            modules=ModuleConfig(
                image_binarization=read["binarization"],
                optical_flow=read["flow"],
                intensity_distribution=read["intensity_distribution"],
            ),
            reader=ReaderConfig(
                accept_dim_images=read["accept_dim_images"],
                accept_dim_channels=read["accept_dim_channels"],
                exposure_time=flow_params["exposure_time"],
                um_pixel_ratio=flow_params["um_pixel_ratio"],
                verbose=read["verbose"],
            ),
            writer=WriterConfig(
                save_visualizations=write["save_visualizations"],
                save_rds=write["save_rds"],
                generate_barcode=write["generate_barcode"],
            ),
            image_binarization_parameters=BinarizationConfig(
                frame_step=bin_params["frame_step"],
                percentage_frame_evaluated=bin_params["percentage_frames_evaluated"],
                threshold_offset=bin_params["threshold_offset"],
            ),
            optical_flow_parameters=OpticalFlowConfig(
                downsample=flow_params["downsample"],
                frame_step=flow_params["frame_step"],
                percentage_frames_evaluated=flow_params["percentage_frames_evaluated"],
                win_size=flow_params["win_size"],
            ),
            intensity_distribution_parameters=IntensityDistributionConfig(
                bin_size=int_params["bin_size"],
                frame_step=int_params["frame_step"],
                noise_threshold=int_params["noise_threshold"],
                percentage_frames_evaluated=int_params["percentage_frames_evaluated"],            
            ),
        )

# === CONFIG GENERATION SETUP ===
# Define which configs should get GUI wrappers (edit this list as needed)
GUI_CONFIG_CLASSES = [
    InputConfig,
    ReaderConfig,
    WriterConfig,
    ChannelConfig,
    BinarizationConfig,
    OpticalFlowConfig,
    IntensityDistributionConfig,
    PreviewConfig,
    AggregationConfig,
    ComparisonConfig,
    ModuleConfig,
    VisualizationConfig,
]


if __name__ == "__main__":
    import sys, os

    # Add the parent directory to sys.path to import core.config
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from gui.core import create_gui_configs

    # Generate GUI configs
    num_generated = create_gui_configs(GUI_CONFIG_CLASSES)

    print("\n📋 Usage:")
    print("  from gui import BarcodeConfigGUI")
    print("  from gui import BinarizationConfigGUI as BinGUI  # Optional short names")
    print("  gui_config = BarcodeConfigGUI(core_config)")
    print(
        "  threshold_slider = ttk.Scale(textvariable=gui_config.binarization.threshold_offset)"
    )