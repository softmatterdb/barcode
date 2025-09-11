from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np

from analysis import analyze_optical_flow, analyze_intensity_distribution, analyze_binarization
from core import BarcodeConfig, ChannelResults
from utils import vprint

def run_analysis_pipeline(filepath: str, file: np.ndarray, channel: int, config: BarcodeConfig, output_dir: str, fail_file_loc: str) -> Tuple[ChannelResults, List[plt.Figure]]:
    results = ChannelResults(filepath=filepath, channel=channel)
    figures = []

    video = file[:,:,:,channel]
    if (video == 0).all():
        vprint('Video appears to be blank, please check channel manually.')
        return results, figures

    if config.reader.binarization:
        try:
            bfig, binarization_results = analyze_binarization(
                video, output_dir, config.image_binarization_parameters, config.writer
            )
            results.binarization = binarization_results
            if bfig and config.writer.save_visualizations:
                figures.append(bfig)
        except Exception as e:
            with open(fail_file_loc, "a", encoding="utf-8") as log_file:
                log_file.write(
                    f"Channel {channel}, Module: Binarization, Exception: {str(e)}\n"
                )

    # Run optical flow analysis
    if config.reader.flow:
        try:
            results.flow = analyze_optical_flow(
                video, output_dir, config.optical_flow_parameters, config.writer
            )
        except Exception as e:
            with open(fail_file_loc, "a", encoding="utf-8") as log_file:
                log_file.write(
                    f"Channel {channel}, Module: Optical Flow, Exception: {str(e)}\n"
                )

    # Run intensity distribution analysis
    if config.reader.intensity_distribution:
        try:
            ifig, intensity_results = analyze_intensity_distribution(
                video, output_dir, config.intensity_distribution_parameters, config.writer
            )
            results.intensity = intensity_results
            if ifig and config.writer.save_visualizations:
                figures.append(ifig)
        except Exception as e:
            with open(fail_file_loc, "a", encoding="utf-8") as log_file:
                log_file.write(
                    f"Channel {channel}, Module: Intensity Distribution, Exception: {str(e)}\n"
                )

    return results, figures