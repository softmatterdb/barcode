#!/usr/bin/env python3
"""
Pure dataclass configurations - no tkinter dependencies.
Generate GUI wrappers by running: python _config.py
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
import yaml
from abc import ABC

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
    mode: str = "file"  # "file", "dir", "agg"
    configuration_file: str = ""
    new_param: bool = False


@dataclass
class ChannelConfig(BaseConfig):
    """Channel selection and processing configuration."""

    parse_all_channels: bool = False
    selected_channel: int = 0  # -3 to 4 range


@dataclass
class QualityConfig(BaseConfig):
    """Data quality and acceptance criteria."""

    accept_dim_images: bool = False
    accept_dim_channels: bool = False


@dataclass
class AnalysisConfig(BaseConfig):
    """Analysis module selection and coordination."""

    enable_binarization: bool = False
    enable_optical_flow: bool = False
    enable_intensity_distribution: bool = False


@dataclass
class OutputConfig(BaseConfig):
    """Output generation and format configuration."""

    verbose: bool = False
    save_graphs: bool = False
    save_intermediates: bool = False
    generate_dataset_barcode: bool = False


@dataclass
class BinarizationConfig(BaseConfig):
    """Binarization analysis parameters."""

    threshold_offset: float = 0.1  # -1.0 to 1.0
    frame_step: int = 10  # 1 to 100
    frame_start_percent: float = 0.9  # 0.5 to 0.9
    frame_stop_percent: float = 1.0  # 0.9 to 1.0
    binning_number: int = 2 # 2, 4, 8 as the default
    area_size: int = 500 #default area size TO BE ADJUSTED BY USER ONCE WE FIGURE THIS OUT!


@dataclass
class OpticalFlowConfig(BaseConfig):
    """Optical flow analysis parameters."""

    frame_step: int = 10
    window_size: int = 32
    downsample_factor: int = 8  # 1 to 1000
    nm_pixel_ratio: float = 1.0  # 1 to 1,000,000
    frame_interval_s: int = 1  # 1 to 1000
    binning_number: int = 2 # 2, 4, 8 as the default


@dataclass
class IntensityDistributionConfig(BaseConfig):
    """Intensity distribution analysis parameters."""

    first_frame: int = 1  # minimum 1
    last_frame: int = 0  # 0 means auto-detect last frame
    frames_evaluation_percent: float = 0.1  # 0.01 to 0.2


@dataclass
class PreviewConfig(BaseConfig):
    """GUI preview and visualization settings."""

    sample_file: str = ""
    enable_live_preview: bool = True


@dataclass
class AggregationConfig(BaseConfig):
    """CSV aggregation and post-processing configuration."""

    output_location: str = ""
    generate_barcode: bool = False
    sort_parameter: str = "Default"  # One of the metric headers
    normalize_barcode: bool = False
    csv_paths_list: List[str] = field(default_factory=list)


@dataclass
class BarcodeConfig:
    """Main configuration container for BARCODE application."""

    # Core workflow configs
    channels: ChannelConfig = field(default_factory=ChannelConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    # Analysis-specific configurations
    binarization: BinarizationConfig = field(default_factory=BinarizationConfig)
    optical_flow: OpticalFlowConfig = field(default_factory=OpticalFlowConfig)
    intensity_distribution: IntensityDistributionConfig = field(
        default_factory=IntensityDistributionConfig
    )

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

        reader: dict = config_data["reader"]
        writer: dict = config_data["writer"]

        int_params: dict = config_data["coarse_parameters"]
        int_eval_params: dict = int_params["evaluation_settings"]

        flow_params: dict = config_data["flow_parameters"]

        bin_params: dict = config_data["resilience_parameters"]
        bin_eval_params: dict = bin_params["evaluation_settings"]

        return BarcodeConfig(
            channels=ChannelConfig(
                parse_all_channels=reader["channel_select"] == "All",
                selected_channel=(
                    reader["channel_select"] if reader["channel_select"] != "All" else 0
                ),
            ),
            quality=QualityConfig(
                accept_dim_images=reader["accept_dim_images"],
                accept_dim_channels=reader["accept_dim_channels"],
            ),
            analysis=AnalysisConfig(
                enable_binarization=reader["resilience"],
                enable_optical_flow=reader["flow"],
                enable_intensity_distribution=reader["coarsening"],
            ),
            output=OutputConfig(
                verbose=reader["verbose"],
                save_graphs=reader["return_graphs"],
                save_intermediates=writer["return_intermediates"],
                generate_dataset_barcode=writer["stitch_barcode"],
            ),
            binarization=BinarizationConfig(
                threshold_offset=bin_params["r_offset"],
                frame_step=bin_params["frame_step"],
                frame_start_percent=bin_eval_params["f_start"],
                frame_stop_percent=bin_eval_params["f_stop"],
            ),
            optical_flow=OpticalFlowConfig(
                frame_step=flow_params["frame_step"],
                window_size=flow_params["win_size"],
                downsample_factor=flow_params["downsample"],
                nm_pixel_ratio=flow_params["nm_pixel_ratio"],
                frame_interval_s=flow_params["frame_interval"],
            ),
            intensity_distribution=IntensityDistributionConfig(
                first_frame=int_eval_params["first_frame"],
                last_frame=int_eval_params["last_frame"],
                frames_evaluation_percent=int_params["mean_mode_frames_percent"],
            ),
        )


# === CONFIG GENERATION SETUP ===
# Define which configs should get GUI wrappers (edit this list as needed)
GUI_CONFIG_CLASSES = [
    InputConfig,
    ChannelConfig,
    QualityConfig,
    AnalysisConfig,
    OutputConfig,
    BinarizationConfig,
    OpticalFlowConfig,
    IntensityDistributionConfig,
    PreviewConfig,
    AggregationConfig,
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
