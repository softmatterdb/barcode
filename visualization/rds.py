import csv
import numpy as np

def write_binarization_rds(csvwriter, frame_data: np.ndarray, frame_idx: int):
    """Write binarized frame data to CSV."""
    if not csvwriter:
        return
    csvwriter.writerow([f'Frame {str(frame_idx)}'])
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

def write_correlation_rds(csvwriter, frame_pair: tuple[int, int] | int, xvalues: list[float], radial_average_lst: list[float]):
    if isinstance(frame_pair, tuple):
        frame_pair_str = f"Flow Field {frame_pair[0]}-{frame_pair[1]} Velocity Correlation"
        correlation_label = 'C(v(r))'
    else:
        frame_pair_str = f"Frame {frame_pair} Structural Correlation"
        correlation_label = 'g(r)'
    csvwriter.writerow([frame_pair_str])
    csvwriter.writerow(['r'] + xvalues)
    csvwriter.writerow([correlation_label] + radial_average_lst)
    csvwriter.writerow([])
    return

def write_divergence_curl_rds(csvwriter, frame_pair: tuple[int, int], field_data: np.ndarray):
    csvwriter.writerow([f"Flow Field ({frame_pair[0]} - {frame_pair[1]})"])
    csvwriter.writerows(field_data)
    csvwriter.writerow([])
    return