#!/usr/bin/env python3
"""
Pure dataclass configurations - no tkinter dependencies.
Generate GUI wrappers by running: python _config.py
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
import yaml
from abc import ABC

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
class PreviewConfig(BaseConfig):
    """GUI preview and visualization settings."""

    sample_file: str = ""
    enable_live_preview: bool = True

@dataclass
class AggregationConfig(BaseConfig):
    """CSV aggregation and post-processing configuration."""

    output_location: str = ""
    generate_single_barcode: bool = False
    generate_comparison_barcodes: bool = False
    sort_parameter: str = "Default"  # One of the metric headers
    csv_paths_list: List[str] = field(default_factory=list)

@dataclass
class ChannelConfig(BaseConfig):
    """Channel selection and processing configuration."""
    parse_all_channels: bool = False
    selected_channel: int = 0  # -3 to 4 range
    
@dataclass
class ReaderConfig(BaseConfig):
    accept_dim_channels: bool = False
    accept_dim_images: bool = False
    binarization: bool = False
    flow: bool = False
    intensity_distribution: bool = False
    verbose: bool = False

@dataclass
class WriterConfig(BaseConfig):
    generate_barcode: bool = False
    save_rds: bool = False
    save_visualizations: bool = False

@dataclass
class BinarizationConfig(BaseConfig):
    threshold_offset: float = 0.1 # --thresh_offset
    frame_step: int = 10 # --ib_f_step
    percentage_frames_evaluated: float = 0.05   # --ib_pf_eval

@dataclass
class OpticalFlowConfig(BaseConfig):
    frame_step: int = 10    # --of_f_step
    win_size: int = 32    # --win_size
    downsample: int = 8    # --downsample
    um_pixel_ratio: float = 1.0     # --um_pixel_ratio
    exposure_time: float = 1.0     # --exposure_time
    percentage_frames_evaluated: float = 0.05 # --of_pf_evaluation

@dataclass
class IntensityDistributionConfig(BaseConfig):
    bin_size: int = 300 # --hist_bin_size
    frame_step: int = 10    # --id_f_step
    noise_threshold: float = 5e-4 # --noise_threshold
    percentage_frames_evaluated: float = 0.05 # --id_pf_evaluation

@dataclass
class BarcodeConfig(BaseConfig):
    channels: ChannelConfig = field(default_factory=ChannelConfig)
    image_binarization_parameters: BinarizationConfig = field(default_factory=BinarizationConfig)
    intensity_distribution_parameters: IntensityDistributionConfig = field(default_factory=IntensityDistributionConfig)
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
            reader=ReaderConfig(
                accept_dim_images=read["accept_dim_images"],
                accept_dim_channels=read["accept_dim_channels"],
                binarization=read["binarization"],
                flow=read["flow"],
                intensity_distribution=read["intensity_distribution"],
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
                exposure_time=flow_params["exposure_time"],
                frame_step=flow_params["frame_step"],
                percentage_frames_evaluated=flow_params["percentage_frames_evaluated"],
                um_pixel_ratio=flow_params["um_pixel_ratio"],
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