import csv
import os
import warnings
import numpy as np
from typing import Dict, List, Optional, TypeAlias, TypeVar

from core import ChannelResults, ResultsBase, Metrics, sort_channel_results_by_metric
from utils.reader import read_csv_to_channel_results
from visualization.barcode import generate_combined_barcode, generate_comparison_barcodes
from core.config import ComparisonConfig

warnings.filterwarnings("ignore")


R = TypeVar("R", bound=ResultsBase)

ExtraColumns: TypeAlias = Dict[str, List[str]]


def results_to_csv(
    results: List[R],
    output_filepath: str,
    extra_columns: Optional[ExtraColumns] = None,
    physical_units: bool = False,
    **kwargs,
) -> None:
    """Write homogeneous results to a CSV file."""
    assert len(results) > 0, "Results list cannot be empty."

    if extra_columns:
        for col_name, values in extra_columns.items():
            assert len(values) == len(
                results
            ), f"Extra column '{col_name}' length ({len(values)}) must match results length ({len(results)})."

    # All results must be the same type
    expected_type = type(results[0])
    for i, result in enumerate(results[1:], 1):
        assert (
            type(result) == expected_type
        ), f"All results must be the same type. Result {i} is {type(result).__name__}, expected {expected_type.__name__}"

    # All results must have the same headers
    quantified = physical_units

    for i, result in enumerate(results[1:], 1):
        assert (
            (np.isnan(result.binarization.get_data()[2]) and (not 
                      np.isnan(result.binarization.get_physical_data()[2]))) == quantified
        ), f"All results must have the same headers. Result {i} headers do not match."

    # Ensure the directory exists
    assert os.path.exists(
        os.path.dirname(output_filepath)
    ), "Output directory does not exist."

    headers = results[0].get_physical_headers(**kwargs) if quantified else results[0].get_headers(**kwargs)
    if extra_columns:
        headers = list(extra_columns.keys()) + headers

    with open(output_filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        for i, result in enumerate(results):
            row = []
            if extra_columns:
                for col_name in extra_columns.keys():
                    row.append(extra_columns[col_name][i])
            new_row = result.get_physical_data(**kwargs) if quantified else result.get_data(**kwargs)
            row.extend(new_row)
            writer.writerow(row)
    return quantified


def generate_aggregate_csv(
    csv_files: List[str],
    output_csv: str,
    gen_barcode: bool = False,
    sort_metric: Optional[str] = None,
    separate_channels: bool = True,
    metrics_to_visualize: List[bool] = None,
) -> None:
    """
    Clean version of aggregate CSV generation using structured data.

    Args:
        csv_files: List of CSV file paths to aggregate
        output_csv: Output path for the aggregate CSV
        gen_barcode: Whether to generate barcode visualization
        sort_metric: Optional metric name to sort by (e.g. "Mean Speed")
        separate_channels: Whether to create separate barcode figures per channel
    """

    if not csv_files:
        return

    all_results = []

    # Read each CSV file back into ChannelResults
    for csv_file in csv_files:
        try:
            results = read_csv_to_channel_results(csv_file)
            all_results.extend(results)
        except Exception as e:
            print(f"Warning: Could not read {csv_file}: {e}")
            continue

    if not all_results:
        print("No valid data found in CSV files")
        return

    # Sort if requested
    if sort_metric:
        sort_channel_results_by_metric(all_results, sort_metric)

    if not (len(csv_files) == 1 and csv_files[0] == output_csv):
        # Write aggregate CSV using the clean writer
        quantified = results_to_csv(all_results, output_csv, just_metrics=False)
    else:
        quantified = bool(np.isnan(all_results[0].binarization.get_data()[2]) and (not 
                      np.isnan(all_results[0].binarization.get_physical_data()[2])))

    # Generate barcode if requested
    if gen_barcode:
        barcode_path = output_csv.replace(".csv", " Barcode")
        generate_combined_barcode(
            all_results, barcode_path, 
            separate_channels=separate_channels,
            physical_units = quantified,
            metrics_to_visualize= metrics_to_visualize,
        )

def compare_multiple_csvs(
    csv_files: List[str],
    sort_metric: Optional[str] = None,
    separate_channels: bool = False,
) -> None:
    """
    Clean version of aggregate CSV generation using structured data.

    Args:
        csv_files: List of CSV file paths to aggregate
        sort_metric: Optional metric name to sort by (e.g. "Mean Speed")
        separate_channels: Whether to create separate barcode figures per channel
    """

    if not csv_files:
        return

    all_results = []

    # Read each CSV file back into ChannelResults
    for csv_file in csv_files:
        try:
            results = read_csv_to_channel_results(csv_file)
            if sort_metric:
                sort_channel_results_by_metric(results, sort_metric)
            all_results.append(results)
            quantified = bool(np.isnan(all_results[0][0].binarization.get_data()[2]) and (not 
                      np.isnan(all_results[0][0].binarization.get_physical_data()[2])))
            assert ((np.isnan(results[0].binarization.get_data()[2]) and (not 
                      np.isnan(results[0].binarization.get_physical_data()[2]))) == quantified
        ), f"All results must have the same headers. Result headers do not match."
        except Exception as e:
            print(f"Warning: Could not read {csv_file}: {e}")
            continue

    if not all_results:
        print("No valid data found in CSV files")
        return
    
    barcode_list = [csv_path.replace(".csv", " Barcode") for csv_path in csv_files]
    
    generate_comparison_barcodes(all_results, barcode_list, separate_channels)

def create_metric_comparison(
    compare_config: ComparisonConfig
) -> None:
    csv_file = compare_config.csv_location
    output_file = compare_config.output_location
    first_metric = compare_config.first_comparison_metric
    second_metric = compare_config.second_comparison_metric
    if not (csv_file and output_file):
        return
    results = read_csv_to_channel_results(csv_file)
    metrics = ChannelResults.get_metrics()
    file_metric = metrics[0]
    first_metric = [metric for metric in metrics if metric.value == first_metric][0]
    second_metric = [metric for metric in metrics if metric.value == second_metric][0]
    files = [result.get_dict_data()[file_metric] for result in results]
    param1 = [result.get_dict_data()[first_metric] for result in results]
    param2 = [result.get_dict_data()[second_metric] for result in results]
    headers = ["File", first_metric.value, second_metric.value]
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for file, p1, p2 in zip(files, param1, param2):
            if p1 == np.nan or p2 == np.nan:
                continue
            writer.writerow([file, p1, p2])
