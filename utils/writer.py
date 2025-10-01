import csv
import os
import warnings
from typing import Dict, List, Optional, TypeAlias, TypeVar

from core import ResultsBase, sort_channel_results_by_metric
from utils.reader import read_csv_to_channel_results
from visualization.barcode import gen_combined_barcode, gen_extended_barcode

warnings.filterwarnings("ignore")


R = TypeVar("R", bound=ResultsBase)

ExtraColumns: TypeAlias = Dict[str, List[str]]


def results_to_csv(
    results: List[R],
    output_filepath: str,
    extra_columns: Optional[ExtraColumns] = None,
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

    # Ensure the directory exists
    assert os.path.exists(
        os.path.dirname(output_filepath)
    ), "Output directory does not exist."

    headers = results[0].get_headers(**kwargs)
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
            row.extend(result.get_data(**kwargs))
            writer.writerow(row)


def generate_aggregate_csv(
    csv_files: List[str],
    output_csv: str,
    gen_barcode: bool = False,
    sort_metric: Optional[str] = None,
    separate_channels: bool = False,
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

    # Write aggregate CSV using the clean writer
    results_to_csv(all_results, output_csv, just_metrics=False)

    # Generate barcode if requested
    if gen_barcode:

        barcode_path = output_csv.replace(".csv", "Barcode")
        gen_combined_barcode(
            all_results, barcode_path, separate_channels=separate_channels
        )
