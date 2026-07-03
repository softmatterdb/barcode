import tkinter as tk
from tkinter import ttk, filedialog
from utils.gui import create_option_section, create_popup

# from core import BarcodeConfig, InputConfig
from gui.config import BarcodeConfigGUI, InputConfigGUI

def create_execution_frame(parent, config: BarcodeConfigGUI, input_config: InputConfigGUI):
    """Create the execution settings tab"""
    frame = ttk.Frame(parent)

    # Access config sections directly  
    ci = input_config
    cc = config.channels
    cr = config.reader
    co = config.writer
    cm = config.modules

    row_idx = 0
    header = ("TkDefaultFont", 15, "bold")
    frame.option_add("*font", "TkDefaultFont 13")


    # File/Directory Selection
    def browse_file():
        chosen = filedialog.askopenfilename(
            filetypes=[("TIFF Image", "*.tif *.tiff"), ("ND2 Document", "*.nd2"), ("MP4 File", "*.mp4"), ("AVI File", "*.avi")],
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

    tk.Label(frame, text="Select Data", font=header).grid(
        row=row_idx, column=0, columnspan=3, sticky="w", padx=(5, 5), pady=(10, 5)
    )
    row_idx += 1
    
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

    tk.Label(frame, text="Select Channels", font=header).grid(
        row=row_idx, column=0, columnspan=3, sticky="w", padx=(5, 5), pady=(10, 5)
    )
    row_idx += 1

    # Channel selection
    tk.Label(frame, text="Choose Channel (-3 to 4):").grid(
        row=row_idx, column=0, sticky="w", padx=5, pady=5
    )
    channel_spin = tk.Spinbox(
        frame, from_=-4, to=4, textvariable=cc.selected_channel, width=5
    )
    channel_spin.grid(row=row_idx, column=1, padx=(50, 5), pady=2)
    row_idx += 1

    create_option_section(
       frame,
       row_idx,
       cc.parse_all_channels,
       "Parse All Channels",
       "Scan either a specific channel or every video channel. Selecting a channel less than 0 will result in reverse indexing of channels (i.e. selecting -1 " \
       "will analyze the last channel of every file scanned, rather than the first).",
    )
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

    tk.Label(frame, text="Specify Metadata", font=header).grid(
        row=row_idx, column=0, columnspan=3, sticky="w", padx=(5, 5), pady=(10, 5)
    )
    row_idx += 1

    micron_pixel_label = tk.Label(frame, text="Micron to Pixel Ratio (1 nm – 1 mm)")
    micron_pixel_label.grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
    um_pixel_spin = ttk.Spinbox(
        frame, from_=10**-3, to=10**3,
        increment=10**-3,
        textvariable=cr.um_pixel_ratio,
        width=9
    )
    um_pixel_spin.grid(row=row_idx, column=1, padx=5, pady=5)
    create_popup(frame, "Set ratio of physical units (in microns) to pixels in image. Automatically read for ND2 files.", row_idx, micron_pixel_label)
    row_idx += 1

    exp_time_label = tk.Label(frame, text="Exposure Time [seconds] (1 ms - 1 hour)")
    exp_time_label.grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
    frame_interval_spin = ttk.Spinbox(
        frame, from_=10**-3, to=3.6 * 10**3,
        increment=10**-3,
        textvariable=cr.exposure_time,
        width=7
    )
    frame_interval_spin.grid(row=row_idx, column=1, padx=5, pady=5)
    create_popup(frame, "Control interval (in seconds) between frames. Automatically read for ND2 files.", row_idx, exp_time_label)
    row_idx += 1

    length_units_label = tk.Label(frame, text="BARCODE Output Length Units")
    length_units_label.grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
    length_units_menu = ttk.Combobox(
        frame,
        textvariable=ci.length_units,
        values=["nm", "μm", "mm"],
        width=5,
        state="readonly"  # force selection from list
    )
    length_units_menu.grid(row=row_idx, column=1, sticky="w", padx=5, pady=5)
    row_idx += 1

    time_units_label = tk.Label(frame, text="BARCODE Output Time Units")
    time_units_label.grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
    time_units_menu = ttk.Combobox(
        frame,
        textvariable=ci.time_units,
        values=["s", "min", "hr"],
        width=5,
        state="readonly"  # force selection from list
    )
    time_units_menu.grid(row=row_idx, column=1, sticky="w", padx=5, pady=5)
    row_idx += 1

    tk.Label(frame, text="Select Branches", font=header).grid(
        row=row_idx, column=0, columnspan=3, sticky="w", padx=(5, 5), pady=(10, 5)
    )
    row_idx += 1
    
    # Analysis modules
    create_option_section(
        frame,
        row_idx,
        cm.image_binarization,
        "Image Binarization",
        "Evaluate file(s) using Binarization branch (will generate a .CSV reduced data structure (RDS) for further analysis).",
    )
    row_idx += 2

    create_option_section(
        frame,
        row_idx,
        cm.optical_flow,
        "Optical Flow",
        "Evaluate file(s) using Optical Flow branch (will generate a .CSV reduced data structure (RDS) for further analysis).",
    )
    row_idx += 2

    create_option_section(
        frame,
        row_idx,
        cm.intensity_distribution,
        "Intensity Distribution",
        "Evaluate file(s) using Intensity Distribution branch (will generate a .CSV reduced data structure (RDS) for further analysis).",
    )
    row_idx += 2

    tk.Label(frame, text="Handling Dim Data", font=header).grid(
        row=row_idx, column=0, columnspan=3, sticky="w", padx=(5, 5), pady=(10, 5)
    )
    row_idx += 1

    # Options
    create_option_section(
        frame,
        row_idx,
        cr.accept_dim_images,
        "Scan dim files",
        "Include files that may be too dim to accurately profile (e.g. low light conditions, poor contrast).",
    )
    row_idx += 2

    create_option_section(
        frame,
        row_idx,
        cr.accept_dim_channels,
        "Scan dim channels",
        "Include channels that may be too dim to accurately profile (e.g. one channel is dim while others are better defined).",
    )
    row_idx += 2

    tk.Label(frame, text="Output Settings", font=header).grid(
        row=row_idx, column=0, columnspan=3, sticky="w", padx=(5, 5), pady=(10, 5)
    )
    row_idx += 1

    create_option_section(
        frame,
        row_idx,
        cr.verbose,
        "Verbose Output",
        "Provide additional information in the run-time Processing Log while the data is being processed (e.g. time step updates, total processing time, image dimness).",
    )
    row_idx += 2

    create_option_section(
        frame,
        row_idx,
        co.save_visualizations,
        "Save Graphs",
        "Save .PNG graphs representing chosen data structures (binarized images, optical flow fields, intensity distributions).",
    )
    row_idx += 2

    create_option_section(
        frame,
        row_idx,
        co.save_rds,
        "Save Reduced Data Structures",
        "Save .CSV reduced data structures for chosen branches (binarized images, optical flow fields, intensity distributions) for further analysis.",
    )
    row_idx += 2

    create_option_section(
        frame,
        row_idx,
        co.generate_barcode,
        "Generate Dataset Barcode",
        "Save an .PNG BARCODE matrix for the dataset, plotting the 23 BARCODE metrics for each channel in the dataset on a color-coded scale.",
    )
    row_idx += 2

    tk.Label(frame, text="Configuration Settings", font=header).grid(
        row=row_idx, column=0, columnspan=3, sticky="w", padx=(5, 5), pady=(10, 5)
    )
    row_idx += 1

    # Configuration file
    config_label = tk.Label(frame, text="Configuration YAML File:")
    config_label.grid(
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

    create_popup(frame, "If desired, choose branch settings from a prior .YAML file.", row_idx, config_label)

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