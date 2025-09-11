import os, csv
from typing import List, Tuple

def remove_extension(path: str) -> str:
    return os.path.splitext(path)[0]


def create_output_directories(filepath: str) -> Tuple[str, str]:
    """Create output directories for analysis results."""
    figure_dir_name = remove_extension(filepath) + " BARCODE Output"
    if not os.path.exists(figure_dir_name):
        os.makedirs(figure_dir_name)
    return figure_dir_name

def create_channel_output_dir(figure_dir_name: str, channel: int) -> str:
    """Create channel-specific output directory."""
    fig_channel_dir_name = os.path.join(figure_dir_name, f"Channel {channel}")
    if not os.path.exists(fig_channel_dir_name):
        os.makedirs(fig_channel_dir_name)
    return fig_channel_dir_name

def find_files(path: str) -> List[str]:
    if os.path.isfile(path):
        return [path]
    files = []
    file_formats = (".nd2", ".tiff", ".tif")
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames]
        for filename in filenames:
            if filename.startswith('._'):
                continue
            if filename.endswith(file_formats):
                files.append(os.path.join(dirpath, filename))
    return files

def setup_csv_writer(filename: str):
    """Setup CSV writer and file handle."""
    myfile = open(filename, "w")
    csvwriter = csv.writer(myfile)
    return csvwriter, myfile

def setup_paths(root_dir: str, is_single_file: bool):
    """Setup filepaths for data and output files."""

    base_path = root_dir if not is_single_file else os.path.dirname(root_dir)
    base_name = remove_extension(os.path.basename(root_dir))
    ff_name = "Error Log.txt" if not is_single_file else f"{base_name} Error Log.txt"
    time_name = "Time.txt" if not is_single_file else f"{base_name} Time.txt"
    ff_filepath = os.path.join(base_path, ff_name)
    time_filepath = os.path.join(base_path, time_name)
    open(ff_filepath, "w").close()

    return base_path, base_name, ff_filepath, time_filepath