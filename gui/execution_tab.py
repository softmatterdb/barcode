import tkinter as tk
from tkinter import ttk, filedialog

# from core import BarcodeConfig, InputConfig
from gui.config import BarcodeConfigGUI, InputConfigGUI

def create_execution_frame(parent, config: BarcodeConfigGUI, input_config: InputConfigGUI):
    """Create the execution settings tab"""
    frame = ttk.Frame(parent)

    # Access config sections directly  
    ci = input_config
    cc = config.channels
    ca = config.analysis
    cq = config.quality
    co = config.output

    row_idx = 0

    # File/Directory Selection
    def browse_file():
        chosen = filedialog.askopenfilename(
            filetypes=[("TIFF Image", "*.tif"), ("ND2 Document", "*.nd2")],
            title="Select a File",
        )
        if chosen:
            ci.file_path.set(chosen)
            ci.dir_path.set("")

    def browse_folder():
        chosen = filedialog.askdirectory(title="Select a Folder")
        if chosen:
            ci.dir_path.set(chosen)
            ci.file_path.set("")

    def on_mode_change():
        m = ci.mode.get()
        file_state = "normal" if m == "file" else "disabled"
        dir_state = "normal" if m == "dir" else "disabled"
        file_entry.config(state=file_state)
        browse_file_btn.config(state=file_state)
        dir_entry.config(state=dir_state)
        browse_folder_btn.config(state=dir_state)

    # Process File
    tk.Radiobutton(
        frame,
        text="Process File",
        variable=ci.mode,
        value="file",
        command=on_mode_change,
    ).grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)

    file_entry = tk.Entry(frame, textvariable=ci.file_path, width=35)
    file_entry.grid(row=row_idx, column=1, padx=5, pady=2)

    browse_file_btn = tk.Button(frame, text="Browse File…", command=browse_file)
    browse_file_btn.grid(row=row_idx, column=2, sticky="w", padx=5)
    row_idx += 1

    # Process Directory
    tk.Radiobutton(
        frame,
        text="Process Directory",
        variable=ci.mode,
        value="dir",
        command=on_mode_change,
    ).grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)

    dir_entry = tk.Entry(frame, textvariable=ci.dir_path, width=35)
    dir_entry.grid(row=row_idx, column=1, padx=5, pady=2)

    browse_folder_btn = tk.Button(frame, text="Browse Folder…", command=browse_folder)
    browse_folder_btn.grid(row=row_idx, sticky="w", column=2, padx=5)
    row_idx += 1

    # Combine CSVs mode
    tk.Radiobutton(
        frame,
        text="Combine CSV files / Generate Barcodes",
        variable=ci.mode,
        value="agg",
        command=on_mode_change,
    ).grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=5, pady=5)
    row_idx += 1

    # Channel selection
    tk.Label(frame, text="Choose Channel (-3 to 4):").grid(
        row=row_idx, column=0, sticky="w", padx=5, pady=5
    )
    channel_spin = tk.Spinbox(
        frame, from_=-4, to=4, textvariable=cc.selected_channel, width=5
    )
    channel_spin.grid(row=row_idx, column=0, padx=(50, 5), pady=2)
    row_idx += 1

    parse_all_chk = tk.Checkbutton(
        frame, text="Parse All Channels", variable=cc.parse_all_channels
    )
    parse_all_chk.grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)
    row_idx += 1

    # Channel selection mutual exclusion
    def on_channels_toggled(*args):
        if cc.parse_all_channels.get():
            channel_spin.config(state="disabled")
        else:
            channel_spin.config(state="normal")

    cc.parse_all_channels.trace_add("write", on_channels_toggled)

    def on_channel_selection_changed(*args):
        if cc.selected_channel.get() is not None:
            cc.parse_all_channels.set(False)

    cc.selected_channel.trace_add("write", on_channel_selection_changed)

    # Analysis modules
    _create_analysis_section(
        frame,
        row_idx,
        "Binarization",
        ca.enable_binarization,
        "Evaluate video(s) using binarization branch",
    )
    row_idx += 2

    _create_analysis_section(
        frame,
        row_idx,
        "Optical Flow",
        ca.enable_optical_flow,
        "Evaluate video(s) using optical flow branch",
    )
    row_idx += 2

    _create_analysis_section(
        frame,
        row_idx,
        "Intensity Distribution",
        ca.enable_intensity_distribution,
        "Evaluate video(s) using intensity distribution branch",
    )
    row_idx += 2

    # Options
    _create_option_section(
        frame,
        row_idx,
        "Include dim files",
        cq.accept_dim_images,
        "Click to scan files that may be too dim to accurately profile",
    )
    row_idx += 2

    _create_option_section(
        frame,
        row_idx,
        "Include dim channels",
        cq.accept_dim_channels,
        "Click to scan channels that may be too dim to accurately profile",
    )
    row_idx += 2

    _create_option_section(frame, row_idx, "Verbose", co.verbose, "Show more details")
    row_idx += 2

    _create_option_section(
        frame,
        row_idx,
        "Save Graphs",
        co.save_graphs,
        "Click to save graphs representing sample changes",
    )
    row_idx += 2

    _create_option_section(
        frame,
        row_idx,
        "Save Reduced Data Structures",
        co.save_intermediates,
        "Click to save reduced data structures (flow fields, binarized images, intensity distributions) for further analysis",
    )
    row_idx += 2

    _create_option_section(
        frame,
        row_idx,
        "Dataset Barcode",
        co.generate_dataset_barcode,
        "Generates an aggregate barcode for the dataset",
    )
    row_idx += 2

    # Configuration file
    tk.Label(frame, text="Configuration YAML File:").grid(
        row=row_idx, column=0, sticky="w", padx=5, pady=2
    )
    config_entry = tk.Entry(frame, textvariable=ci.configuration_file, width=35)
    config_entry.grid(row=row_idx, column=1, padx=5, pady=2)

    def browse_config_file():
        chosen = filedialog.askopenfilename(
            filetypes=[("YAML Files", "*.yaml"), ("YAML Files", "*.yml")],
            title="Select a Configuration YAML",
        )
        if chosen:
            ci.configuration_file.set(chosen)

    tk.Button(frame, text="Browse YAML...", command=browse_config_file).grid(
        row=row_idx, column=2, sticky="w", padx=5
    )

    return frame


def _create_analysis_section(parent, row, title, var, description):
    """Helper to create analysis module sections"""
    tk.Label(parent, text=title, font=("TkDefaultFont", 10, "bold")).grid(
        row=row, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 0)
    )

    tk.Checkbutton(parent, variable=var).grid(row=row + 1, column=0, sticky="w", padx=5)

    tk.Label(parent, text=description).grid(
        row=row + 1, column=0, sticky="w", padx=(25, 5), pady=(0, 0)
    )


def _create_option_section(parent, row, title, var, description):
    """Helper to create option sections"""
    tk.Label(parent, text=title, font=("TkDefaultFont", 10, "bold")).grid(
        row=row, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 0)
    )

    tk.Checkbutton(parent, variable=var).grid(row=row + 1, column=0, sticky="w", padx=5)

    tk.Label(parent, text=description).grid(
        row=row + 1, column=0, sticky="w", padx=(25, 5), pady=(0, 0)
    )
