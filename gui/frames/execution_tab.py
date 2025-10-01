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
        browse_dir_btn.config(state=dir_state)

    header = ("TkDefaultFont", 15, "bold")

    tk.Label(frame, text="Select Data", font=header).grid(
        row=row_idx, column=0, columnspan=3, sticky="w", padx=(5, 5), pady=(10, 5)
    )
    row_idx += 1

    file_frame = tk.Frame(frame)
    file_frame.grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=2)

    process_file_radio = tk.Radiobutton(
        file_frame,
        text="Process File",
        variable=ci.mode,
        value="file",
        command=on_mode_change,
    )
    process_file_radio.pack(side="left", padx=(0, 400))

    file_entry = tk.Entry(file_frame, textvariable=ci.file_path, width=25)
    file_entry.pack(side="left", padx=(0, 5))

    browse_file_btn = tk.Button(file_frame, text="Browse File…", command=browse_file)
    browse_file_btn.pack(side="left")

    row_idx += 1

    dir_frame = tk.Frame(frame)
    dir_frame.grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=2)

    process_dir_radio = tk.Radiobutton(
        dir_frame,
        text="Process Directory",
        variable=ci.mode,
        value="dir",
        command=on_mode_change,
    )
    process_dir_radio.pack(side="left", padx=(0, 370))

    dir_entry = tk.Entry(dir_frame, textvariable=ci.dir_path, width=25)
    dir_entry.pack(side="left", padx=(0, 5))

    browse_dir_btn = tk.Button(dir_frame, text="Browse Directory…", command=browse_folder)
    browse_dir_btn.pack(side="left")

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
    channel_spin.grid(row=row_idx, column=0, padx=(50, 5), pady=2)
    row_idx += 1

    # parse_all_chk = tk.Checkbutton(
    #     frame, text="Parse All Channels", variable=cc.parse_all_channels
    # )

    _create_option_section(
       frame,
       row_idx,
       cc.parse_all_channels,
       "Parse All Channels",
       "Scan either a specific channel or every video channel. Selecting a channel <0 will result in reverse indexing of channels (i.e. selecting -1 " \
       "will analyze the last channel of every file scanned, rather than the first).",
    )

    # parse_all_chk.grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)
    # row_idx += 1

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
    row_idx += 2

    print(row_idx)

    # SELECT RDSes

    tk.Label(frame, text="Select Reduced Data Structures (RDS)", font=header).grid(
        row=row_idx, column=0, columnspan=3, sticky="w", padx=(5, 5), pady=(10, 5)
    )
    row_idx += 1

    _create_option_section(
        frame,
        row_idx,
        ca.enable_binarization,
        "Binarization",
        "Evaluate file(s) using Binarization branch (will generate a .CSV reduced data structure (RDS) for further analysis).",
    )
    row_idx += 2

    _create_option_section(
        frame,
        row_idx,
        ca.enable_optical_flow,
        "Optical Flow",
        "Evaluate file(s) using Optical Flow branch (will generate a .CSV reduced data structure (RDS) for further analysis).",
    )
    row_idx += 2

    _create_option_section(
        frame,
        row_idx,
        ca.enable_intensity_distribution,
        "Intensity Distribution",
        "Evaluate file(s) using Intensity Distribution branch (will generate a .CSV reduced data structure (RDS) for further analysis).",
    )
    row_idx += 2

    # Handling Dim Data
    tk.Label(frame, text="Handling Dim Data", font=header).grid(
        row=row_idx, column=0, columnspan=3, sticky="w", padx=(5, 5), pady=(10, 5)
    )
    row_idx += 1

    _create_option_section(
        frame,
        row_idx,
        cq.accept_dim_images,
        "Scan dim files",
        "Include files that may be too dim to accurately profile (e.g. low light conditions, poor contrast).",
    )
    row_idx += 2

    _create_option_section(
        frame,
        row_idx,
        cq.accept_dim_channels,
        "Scan dim channels",
        "Include channels that may be too dim to accurately profile (e.g. one channel is dim while others are better defined).",
    )
    row_idx += 2

    # Save Settings
    tk.Label(frame, text="Save Settings", font=header).grid(
        row=row_idx, column=0, columnspan=3, sticky="w", padx=(5, 5), pady=(10, 5)
    )
    row_idx += 1

    _create_option_section(
        frame,
        row_idx,
        co.verbose,
        "Verbose Output",
        "Provide additional information in the run-time Processing Log while the data is being processed (e.g. time step updates, total processing time, image dimness).",
    )
    row_idx += 2

    _create_option_section(
        frame,
        row_idx,
        co.save_graphs,
        "Save Graphs",
        "Save .PNG graphs representing chosen data structures (binarized images, optical flow fields, intensity distributions).",
    )
    row_idx += 2

    _create_option_section(
        frame,
        row_idx,
        co.save_intermediates,
        "Save Reduced Data Structures",
        "Save .CSV reduced data structures for chosen branches (binarized images, optical flow fields, intensity distributions) for further analysis.",
    )
    row_idx += 2

    _create_option_section(
        frame,
        row_idx,
        co.generate_dataset_barcode,
        "Generate Dataset Barcode",
        "Save an .PNG BARCODE matrix for the dataset, plotting the 17 BARCODE metrics for each channel in the dataset on a color-coded scale.",
    )

    row_idx += 2

    '''
    tk.Label(frame, text="Handling Dim Data", font=header).grid(
        row=row_idx, column=0, columnspan=3, sticky="w", padx=(5, 5), pady=(10, 5)
    )
    row_idx += 1

    bold = ("TkDefaultFont", 13, "bold")
    normal = ("TkDefaultFont", 13)

    tk.Checkbutton(frame, variable=cq.accept_dim_images).grid(row=row_idx + 1, column=0, sticky="w", padx=5)
    tk.Label(frame, text="Scan dim files ", font=bold).grid(
        row=row_idx + 1, column=0, sticky="w", padx=(25, 5)
    )
    tk.Label(frame, text="that may be difficult to accurately profile", font=normal).grid(
        row=row_idx + 1, column=0, sticky="w", padx=(120, 5) 
    )

    row_idx += 2

    tk.Checkbutton(frame, variable=cq.accept_dim_channels).grid(row=row_idx + 1, column=0, sticky="w", padx=5)
    tk.Label(frame, text="Scan dim channels ", font=bold).grid(
        row=row_idx + 1, column=0, sticky="w", padx=(25, 5)
    )
    tk.Label(frame, text="that may be difficult to accurately profile", font=normal).grid(
        row=row_idx + 1, column=0, sticky="w", padx=(150, 5) 
    )

    row_idx += 2

    tk.Label(frame, text="Save Settings", font=header).grid(
        row=row_idx, column=0, columnspan=3, sticky="w", padx=(5, 5), pady=(10, 5)
    )
    row_idx += 1

    tk.Checkbutton(frame, variable=co.verbose).grid(row=row_idx + 1, column=0, sticky="w", padx=5)
    tk.Label(frame, text="Provide more ", font=normal).grid(
        row=row_idx + 1, column=0, sticky="w", padx=(25, 5)
    )
    tk.Label(frame, text="verbose output", font=bold).grid(
        row=row_idx + 1, column=0, sticky="w", padx=(110, 5) 
    )

    row_idx += 2

    tk.Checkbutton(frame, variable=co.save_graphs).grid(row=row_idx + 1, column=0, sticky="w", padx=5)
    tk.Label(frame, text="Save ", font=normal).grid(
        row=row_idx + 1, column=0, sticky="w", padx=(25, 5)
    )
    tk.Label(frame, text="graphs representing sample changes", font=bold).grid(
        row=row_idx + 1, column=0, sticky="w", padx=(60, 5) 
    )

    row_idx += 2

    tk.Checkbutton(frame, variable=co.save_intermediates).grid(row=row_idx + 1, column=0, sticky="w", padx=5)
    tk.Label(frame, text="Save ", font=normal).grid(
        row=row_idx + 1, column=0, sticky="w", padx=(25, 5)
    )
    tk.Label(frame, text="reduced data structures (RDS) for further analysis", font=bold).grid(
        row=row_idx + 1, column=0, sticky="w", padx=(60, 5) 
    )

    row_idx += 2

    tk.Checkbutton(frame, variable=co.generate_dataset_barcode).grid(row=row_idx + 1, column=0, sticky="w", padx=5)
    tk.Label(frame, text="Generates an ", font=normal).grid(
        row=row_idx + 1, column=0, sticky="w", padx=(25, 5)
    )
    tk.Label(frame, text="aggregate barcode ", font=bold).grid(
        row=row_idx + 1, column=0, sticky="w", padx=(110, 5) 
    )
    tk.Label(frame, text="for the dataset", font=normal).grid(
        row=row_idx + 1, column=0, sticky="w", padx=(240, 5) 
    )

    row_idx += 2

    '''

    tk.Label(frame, text="Configuration Settings", font=header).grid(
        row=row_idx, column=0, columnspan=3, sticky="w", padx=(5, 5), pady=(10, 5)
    )
    row_idx += 1

    # Configuration file

    config_frame = tk.Frame(frame)
    config_frame.grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=2)

    config_label = tk.Label(config_frame, text="Configuration YAML File:")
    config_label.pack(side="left", padx=(0, 400))
    
    config_entry = tk.Entry(config_frame, textvariable=ci.configuration_file, width=20)
    config_entry.pack(side="left", padx=(0, 5))

    def browse_config_file():
        chosen = filedialog.askopenfilename(
            filetypes=[("YAML Files", "*.yaml"), ("YAML Files", "*.yml")],
            title="Select a Configuration YAML",
        )
        if chosen:
            ci.configuration_file.set(chosen)

    config_file_btn = tk.Button(config_frame, text="Browse YAML…", command=browse_config_file)
    config_file_btn.pack(side="left")

    create_popup(frame, "If desired, choose branch settings from a prior .YAML file.", row_idx, config_label)
    
    return frame


# def _create_analysis_section(parent, row, var, description, rds_name):
#     """Helper to create analysis module sections"""
#     # tk.Label(parent, text=title, font=("TkDefaultFont", 10, "bold")).grid(
#     #     row=row, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 0)
#     # )

#     tk.Checkbutton(parent, variable=var).grid(row=row + 1, column=0, sticky="w", padx=5)

#     bold = ("TkDefaultFont", 13, "bold")
#     normal = ("TkDefaultFont", 13)

#     tk.Label(parent, text=description, font=normal).grid(
#         row=row + 1, column=0, sticky="w", padx=(25, 5)
#     )

#     tk.Label(parent, text=rds_name, font=bold).grid(
#         row=row + 1, column=0, sticky="w", padx=(170, 5)  # adjust as needed
#     )

def create_popup(parent, description, row, title_label):
    """Helper to create a popup window describing the feature and place the icon."""
    info_icon = tk.Label(parent, text="ℹ️", font=("Arial", 12), bg=parent.winfo_toplevel().cget("bg"), fg="blue", relief="flat", borderwidth=0)
    info_icon.grid(row=row, column=0, sticky="w", padx=(title_label.winfo_reqwidth() + 30, 0))

    def show_popup(event):
        # Create popup
        popup = tk.Label(parent, text=description, bg="#202020", fg="white", relief="flat", borderwidth=4, wraplength=600)
        popup.place(x=info_icon.winfo_rootx() - parent.winfo_rootx() + info_icon.winfo_width() + 10, y=info_icon.winfo_rooty() - parent.winfo_rooty() - 20)
        popup.tkraise()

        def hide_popup(event):
            popup.destroy()  # Destroy popup
        info_icon.bind("<Leave>", hide_popup)

    info_icon.bind("<Enter>", show_popup)

def _create_option_section(parent, row, var, title, description):
    """Helper to create option sections with a checkbox, description, and a popup icon."""
    tk.Checkbutton(parent, variable=var).grid(row=row, column=0, sticky="w", padx=5)

    normal = ("TkDefaultFont", 13)

    title_label = tk.Label(parent, text=title, font=normal)
    title_label.grid(row=row, column=0, sticky="w", padx=(25, 5))

    # Call the popup creation function to create and place the info icon
    create_popup(parent, description, row, title_label)

# tk.Checkbutton(parent, variable=var).grid(row=row + 1, column=0, sticky="w", padx=5)

# tk.Label(parent, text=description).grid(
 #     row=row + 1, column=0, sticky="w", padx=(25, 5), pady=(0, 0)
# )