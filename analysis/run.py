from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np

from analysis import analyze_flow, analyze_intensity_distribution, analyze_binarization
from core import BarcodeConfig, ChannelResults


def run_analysis_pipeline(
    filepath: str,
    file: np.ndarray,
    channel: int,
    config: BarcodeConfig,
    output_dir: str,
    fail_file_loc: str,
) -> Tuple[ChannelResults, List[plt.Figure]]:
    """Run all enabled analysis modules for a single channel."""
    results = ChannelResults(filepath=filepath, channel=channel)
    figures = []

    # Run binarization analysis
    if config.analysis.enable_binarization:
        try:
            bfig, binarization_results = analyze_binarization(
                file, output_dir, channel, config.binarization, config.output
            )
            results.binarization = binarization_results
            if bfig and config.output.save_graphs:
                figures.append(bfig)
        except Exception as e:
            with open(fail_file_loc, "a", encoding="utf-8") as log_file:
                log_file.write(
                    f"Channel {channel}, Module: Binarization, Exception: {str(e)}\n"
                )

    # Run optical flow analysis
    if config.analysis.enable_optical_flow:
        try:
            results.flow = analyze_flow(
                file, output_dir, channel, config.optical_flow, config.output
            )
        except Exception as e:
            with open(fail_file_loc, "a", encoding="utf-8") as log_file:
                log_file.write(
                    f"Channel {channel}, Module: Optical Flow, Exception: {str(e)}\n"
                )

    # Run intensity distribution analysis
    if config.analysis.enable_intensity_distribution:
        try:
            ifig, intensity_results = analyze_intensity_distribution(
                file, output_dir, channel, config.intensity_distribution, config.output
            )
            results.intensity = intensity_results
            if ifig and config.output.save_graphs:
                figures.append(ifig)
        except Exception as e:
            with open(fail_file_loc, "a", encoding="utf-8") as log_file:
                log_file.write(
                    f"Channel {channel}, Module: Intensity Distribution, Exception: {str(e)}\n"
                )

    return results, figures
