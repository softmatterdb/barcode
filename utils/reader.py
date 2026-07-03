import os, functools, builtins
from itertools import pairwise
import nd2, av
import imageio.v3 as iio
import numpy as np
from utils import vprint
from core import BarcodeConfig, InputConfig, ChannelResults, BinarizationResults, IntensityResults, FlowResults

def check_first_frame_dim(file):
    min_intensity = np.min(file[0])
    mean_intensity = np.mean(file[0])
    return 2 * np.exp(-1) * mean_intensity <= min_intensity

def read_file(filepath, count_list, config: BarcodeConfig = None, in_config: InputConfig = None, accept_dim: bool = False, allow_large_files = True):
    print = functools.partial(builtins.print, flush=True)
    
    if count_list[1] != 1:    
        print(f'File {count_list[0]} of {count_list[1]}')
        print(filepath)
        count_list[0] += 1

    file_size = os.path.getsize(filepath)
    file_size_gb = file_size / (1024 ** 3)
    if file_size_gb > 5 and not allow_large_files:
        print("File size is too large -- this program does not process files larger than 5 GB.")
        return None
    if filepath.endswith(('.avi', '.mp4')):
        frames = []
        container = av.open(filepath)
        for frame in container.decode(video=0):
            frames.append(frame.to_ndarray(format='gray'))
        file = np.array(frames)
        file = np.reshape(file, (file.shape + (1,))) if len(file.shape) == 3 else file
    if filepath.endswith(('.tif', '.tiff')):
        file = iio.imread(filepath)
        file = np.reshape(file, (file.shape + (1,))) if len(file.shape) == 3 else file
        if file.shape[3] != min(file.shape):
            file = np.swapaxes(np.swapaxes(file, 1, 2), 2, 3)
    elif filepath.endswith('.nd2'):
        with nd2.ND2File(filepath) as ndfile:
            if len(ndfile.sizes) >= 5:
                count_list[0] += 1
                raise TypeError("Incorrect file dimensions: file must be time series data with 1+ channels (4 dimensions total)")
            if "Z" in ndfile.sizes:
                count_list[0] += 1
                raise TypeError('Z-stack identified, skipping to next file...')
            if 'T' not in ndfile.sizes or len(ndfile.shape) <= 2 or ndfile.sizes['T'] <= 5:
                count_list[0] += 1
                raise TypeError('Too few frames, unable to capture dynamics, skipping to next file...')
            if ndfile == None:
                raise TypeError('Unable to read file, skipping to next file...')
            file = ndfile.asarray()
            if 'C' not in ndfile.sizes:
                file = np.expand_dims(file, axis=1)
            file = np.swapaxes(np.swapaxes(file, 1, 2), 2, 3)
            try:
                times = ndfile.events(orient="list")["Time [s]"]
                frame_interval = np.array([y - x for x, y in pairwise(times)]).mean()
                micron_pix_ratio = ndfile.voxel_size()[0]
                config.reader.exposure_time = float(frame_interval / in_config.time)
                config.reader.um_pixel_ratio = micron_pix_ratio / in_config.length
                vprint(f"Extracted ND2 metadata: frame_interval={frame_interval:.4f}s, micron_pixel_ratio={micron_pix_ratio:.2f}")
            except Exception as e:
                config.reader.exposure_time = 1
                config.reader.um_pixel_ratio = 1
                vprint(f"Warning: Could not extract ND2 metadata: {e}")
    if (file == 0).all():
        print('Empty file: can not process, skipping to next file...')
        return None
    
    if accept_dim == False and check_first_frame_dim(file) == True:
        print(filepath + 'is too dim, skipping to next file...')
        return None
    else:
        return file
    
def read_csv_to_channel_results(filepath: str) -> list[ChannelResults]:
    """Read results from a CSV file into a list of ChannelResults."""

    def get_value(value_str: str) -> float:
        """Convert string to float, handling empty strings as NaN."""
        if value_str == "" or value_str.lower() == "nan":
            return np.nan
        try:
            return float(value_str)
        except ValueError:
            # If conversion fails, return NaN
            return np.nan

    expected_headers = ChannelResults.get_headers(just_metrics=False)
    expected_physical_headers = ChannelResults.get_physical_headers(just_metrics=False)
    expected_v1_headers = expected_headers[:10] + expected_headers[15:-1]

    v1_header_length = 18 # Channel, 7 Image_Binarization, 6 Intensity_Distribution, 4 Optical_Flow
    v2_header_length = 26 # Channel, 12 Image_Binarization, 6 Intensity_Distribution, 7 Optical_Flow

    import csv

    results = []
    with open(filepath, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)

        assert (
            (headers == expected_headers) or (headers == expected_physical_headers) or (headers == expected_v1_headers)
        ), f"CSV headers {headers} do not match expected headers for BARCODE analysis"

        for row in reader:
            filename = row[0]
            flags = row.pop(2)
            data = [get_value(value) for value in row[1:]]
            if np.isnan(data[0]):
                raise ValueError(f"Invalid channel in row: {row}")
            if len(data) == v1_header_length:
                results.append(
                    ChannelResults(
                        filepath = filename,
                        channel=int(data[0]),
                        total_flags=flags,
                        binarization=BinarizationResults(
                            connectivity=data[1],
                            max_island_size=data[2],
                            max_void_size=data[3],
                            max_island_percent_change=data[4],
                            max_void_percent_change=data[5],
                            island_size_initial=data[6],
                            island_size_initial2=data[7],
                        ),
                        intensity=IntensityResults(
                            max_kurtosis=data[8],
                            max_median_skew=data[9],
                            max_mode_skew=data[10],
                            kurtosis_diff=data[11],
                            median_skew_diff=data[12],
                            mode_skew_diff=data[13],
                        ),
                        flow=FlowResults(
                            mean_speed=data[14],
                            delta_speed=data[15],
                            mean_theta=data[16],
                            mean_sigma_theta=data[17],
                        ),
                    )
                )
            elif len(data) == v2_header_length:
                if headers == expected_headers:
                    results.append(ChannelResults(
                        filepath = filename,
                        channel = int(data[0]),
                        total_flags=flags,
                        binarization=BinarizationResults(
                            connectivity=data[1],
                            max_island_size=data[2],
                            max_void_size=data[3],
                            max_island_percent_change=data[4],
                            max_void_percent_change=data[5],
                            island_size_initial=data[6],
                            island_size_initial2=data[7],
                            island_anisotropy = data[8],
                            mean_island_size = data[9],
                            total_island_size = data[10],
                            mean_island_separation = data[11],
                            island_correlation_length = data[12],
                        ),
                        intensity=IntensityResults(
                            max_kurtosis=data[13],
                            max_median_skew=data[14],
                            max_mode_skew=data[15],
                            kurtosis_diff=data[16],
                            median_skew_diff=data[17],
                            mode_skew_diff=data[18],
                        ),
                        flow=FlowResults(
                            mean_speed=data[19],
                            delta_speed=data[20],
                            mean_theta=data[21],
                            mean_sigma_theta=data[22],
                            velocity_correlation_length=data[23],
                            divergence=data[24],
                            curl=data[25]
                        )
                    ))
                elif headers == expected_physical_headers:
                    results.append(
                        ChannelResults(
                            filepath=filename,
                            channel=int(data[0]),
                            total_flags=flags,
                            binarization=BinarizationResults(
                                connectivity=data[1],
                                max_island_size_quantity=data[2],
                                max_void_size_quantity=data[3],
                                max_island_percent_change=data[4],
                                max_void_percent_change=data[5],
                                island_size_initial_quantity=data[6],
                                island_size_initial2_quantity=data[7],
                                island_anisotropy = data[8],
                                mean_island_size_quantity = data[9],
                                total_island_size_quantity = data[10],
                                mean_island_separation = data[11],
                                island_correlation_length = data[12],
                            ),
                            intensity=IntensityResults(
                                max_kurtosis=data[13],
                                max_median_skew=data[14],
                                max_mode_skew=data[15],
                                kurtosis_diff=data[16],
                                median_skew_diff=data[17],
                                mode_skew_diff=data[18],
                            ),
                            flow=FlowResults(
                                mean_speed=data[19],
                                delta_speed=data[20],
                                mean_theta=data[21],
                                mean_sigma_theta=data[22],
                                velocity_correlation_length=data[23],
                                divergence=data[24],
                                curl=data[25]
                            )
                        )
                    )
    return results