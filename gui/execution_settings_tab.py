import tkinter as tk
from tkinter import ttk, filedialog

def create_execution_settings_tab(
        notebook: ttk.Notebook,
        config_data: dict,
) -> tk.Frame:
    frame = ttk.Frame(notebook)
    row_idx = 0
    def browse_file():
        chosen = filedialog.askopenfilename(
            filetypes=[("TIFF Image","*.tif *.tiff"), ("ND2 Document","*.nd2")],
            title="Select a File"
        )
        if chosen:
            config_data["gui_execution"]["file_path"].set(chosen)
            config_data["gui_execution"]["dir_path"].set("")      # clear the other mode

    def browse_folder():
        chosen = filedialog.askdirectory(title="Select a Folder")
        if chosen:
            config_data["gui_execution"]["dir_path"].set(chosen)
            config_data["gui_execution"]["file_path"].set("")     # clear the other mode

    def on_mode_change():
        m = config_data["gui_execution"]["mode"].get()
        file_state = "normal" if m == "file" else "disabled"
        dir_state  = "normal" if m == "dir" else "disabled"
        file_entry.config(state=file_state)
        browse_file_btn.config(state=file_state)
        dir_entry.config(state=dir_state)
        browse_folder_btn.config(state=dir_state)

    # Process File
    tk.Radiobutton(
        frame,
        text="Process File",
        variable=config_data["gui_execution"]["mode"],   # all three share this StringVar
        value="file",        # this button sets mode="file"
        command=on_mode_change
    ).grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)

    file_entry = tk.Entry(
        frame,
        textvariable=config_data["gui_execution"]["file_path"], width=35
    )
    file_entry.grid(row=row_idx, column=1, padx=5, pady=2)

    browse_file_btn = tk.Button(
        frame,
        text="Browse File…",
        command=browse_file
    )
    browse_file_btn.grid(row=row_idx, column=2, sticky="w", padx=5)
    row_idx += 1

    # Process Directory
    tk.Radiobutton(
        frame,
        text="Process Directory",
        variable=config_data["gui_execution"]["mode"],
        value="dir",
        command=on_mode_change
    ).grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)

    dir_entry = tk.Entry(
        frame,
        textvariable=config_data["gui_execution"]["dir_path"], width=35
    )
    dir_entry.grid(row=row_idx, column=1, padx=5, pady=2)

    browse_folder_btn = tk.Button(
        frame,
        text="Browse Folder…",
        command=browse_folder
    )
    browse_folder_btn.grid(row=row_idx, sticky="w", column=2, padx=5)
    row_idx += 1

    # Combine CSVs / Generate Barcodes (aggregate mode)
    tk.Radiobutton(
        frame,
        text="Combine CSV files / Generate Barcodes",
        variable=config_data["gui_execution"]["mode"],
        value="agg",
        command=on_mode_change
    ).grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=5, pady=5)
    row_idx += 1

    #channel selection 
    tk.Label(frame, text="Choose Channel (-3 to 4):").grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
    channel_spin = tk.Spinbox(frame, 
        from_=-3, to=4, 
        textvariable=config_data["gui_execution"]["channel_selection"], 
        width=5
    )
    channel_spin.grid(row=row_idx, column=0, padx=(50,5), pady=2)
    row_idx += 1

    parse_all_chk = tk.Checkbutton(frame, text="Parse All Channels", variable=config_data["gui_execution"]["channels"])
    parse_all_chk.grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)
    row_idx += 1 

    #enforce mutual exclusion of channel selection 
    def on_channels_toggled(*args):
        if config_data["gui_execution"]["channels"].get():
            channel_spin.config(state="disabled")
        else:
            channel_spin.config(state="normal")
    config_data["gui_execution"]["channels"].trace_add("write", on_channels_toggled)

    def on_channel_selection_changed(*args):
        # If user types ANY integer, uncheck “Parse All Channels”
        if config_data["gui_execution"]["channel_selection"].get() is not None:
            config_data["gui_execution"]["channels"].set(False)

    config_data["gui_execution"]["channel_selection"].trace_add("write", on_channel_selection_changed)

    #reader execution settings 
    tk.Label(
        frame, 
        text="Image Binarization Branch", 
        font=('TkDefaultFont', 10, 'bold')
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0))
    tk.Checkbutton(
        frame,
        variable=config_data["gui_reader"]["binarization"]
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5)
    tk.Label(
        frame,
        text="Evaluate video(s) using binarization branch"
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0))
    row_idx += 2

    tk.Label(
        frame,
        text="Optical Flow Branch",
        font=('TkDefaultFont', 10, 'bold')
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0))
    tk.Checkbutton(
        frame,
        variable=config_data["gui_reader"]["optical_flow"]
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5)
    tk.Label(
        frame,
        text="Evaluate video(s) using optical flow branch"
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0))
    row_idx += 2

    tk.Label(
        frame,
        text="Intensity Distribution Branch",
        font=('TkDefaultFont', 10, 'bold')
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0))
    tk.Checkbutton(
        frame,
        variable=config_data["gui_reader"]["intensity_distribution"]
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5)
    tk.Label(
        frame,
        text="Evaluate video(s) using intensity distribution branch"
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0))
    row_idx += 2

    tk.Label(
        frame, 
        text="Include dim files", 
        font=('TkDefaultFont', 10, 'bold') 
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0)) 
    tk.Checkbutton(
        frame, variable=config_data["gui_reader"]["accept_dim_images"]
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5)
    tk.Label(
        frame, 
        text="Click to scan files that may be too dim to accurately profile"
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0)) 
    row_idx += 2 

    tk.Label(
        frame, 
        text="Include dim channels", 
        font=('TkDefaultFont', 10, 'bold') 
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0))
    tk.Checkbutton(
        frame, variable=config_data["gui_reader"]["accept_dim_channels"]
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5) 
    tk.Label(
        frame, 
        text="Click to scan channels that may be too dim to accurately profile" 
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0)) 
    row_idx += 2 

    #writer data 
    tk.Label(
        frame,
        text="Verbose",
        font=('TkDefaultFont', 10, 'bold')
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0))
    tk.Checkbutton(
        frame,
        variable=config_data["gui_reader"]["verbose"]
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5)
    tk.Label(
        frame,
        text="Show more details"
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0))
    row_idx += 2

    tk.Label(
        frame,
        text="Save Data Visualizations",
        font=('TkDefaultFont', 10, 'bold')
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0))
    tk.Checkbutton(
        frame,
        variable=config_data["gui_writer"]["save_visualizations"]
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5)
    tk.Label(
        frame,
        text="Click to save graphs representing sample changes"
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0))
    row_idx += 2

    tk.Label(
        frame,
        text="Save Reduced Data Structures",
        font=('TkDefaultFont', 10, 'bold')
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0))
    tk.Checkbutton(
        frame,
        variable=config_data["gui_writer"]["save_rds"]
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5)
    tk.Label(
        frame,
        text="Click to save reduced data structures (flow fields, binarized images, intensity distributions) for further analysis"
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0))
    row_idx += 2

    tk.Label(
        frame,
        text="Generate Dataset Barcode",
        font=('TkDefaultFont', 10, 'bold')
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0))
    tk.Checkbutton(
        frame,
        variable=config_data["gui_writer"]["generate_barcode"]
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5)
    tk.Label(
        frame,
        text="Generates an color-coded barcode visualization for the dataset"
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0))
    row_idx += 2

    tk.Label(frame, text="Configuration YAML File:").grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)
    config_entry = tk.Entry(frame, textvariable=config_data["gui_execution"]["configuration_file"], width=35)
    config_entry.grid(row=row_idx, column=1, padx=5, pady=2)
    def browse_config_file():
        chosen = filedialog.askopenfilename(
            filetypes=[("YAML Files","*.yaml *.yml")],
            title="Select a Configuration YAML"
        )
        if chosen:
            config_data["gui_execution"]["configuration_file"].set(chosen)
    tk.Button(frame, text="Browse YAML...", command=browse_config_file).grid(row=row_idx, column=2, sticky="w", padx=5)

    return frame, config_data