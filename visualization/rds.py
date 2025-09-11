import csv
import numpy as np

def write_binarization_rds(csvwriter, frame_data: np.ndarray, frame_idx: int):
    """Write binarized frame data to CSV."""
    if not csvwriter:
        return
    csvwriter.writerow([str(frame_idx)])
    csvwriter.writerows(frame_data)
    csvwriter.writerow([])
    return

def write_flow_field_rds(csvwriter, vx_data: np.ndarray, vy_data: np.ndarray, start_index: int, stop_index: int):
    csvwriter.writerow([f"Flow Field ({start_index} - {stop_index})"])
    csvwriter.writerow(["X-Direction"])
    csvwriter.writerows(vx_data)
    csvwriter.writerow(["Y-Direction"])
    csvwriter.writerows(vy_data)
    return

def write_intensity_distribution_rds(csvwriter, frame_intensities: np.ndarray, frame_probabilities: np.ndarray, frame_idx: int):
    csvwriter.writerow([f'Frame {frame_idx}'])
    csvwriter.writerow(frame_intensities)
    csvwriter.writerow(frame_probabilities)
    csvwriter.writerow([])
    return