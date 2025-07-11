import sys, yaml, os 
from barcoder import process_directory
from writer import generate_aggregate_csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox 
import argparse 

import numpy as np
from preview_binarization import load_first_frame, binarize 
from PIL import Image, ImageTk 
from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 

import cv2 as cv 
from flow import groupAvg 

import threading 

from tkinter import *
import traceback


def set_config_data(args = None):
    config_data = {}
    reader_data = {}
    writer_data = {}
    resilience_data = {}
    flow_data = {}
    coarsening_data = {}
    if args:
        reader_data = {
            'accept_dim_channels':args.dim_channels,
            'accept_dim_images':args.dim_images,
            'channel_select':'All' if args.channels else int(args.channel_selection),
            'coarsening':args.check_coarsening,
            'flow':args.check_flow,
            'resilience':args.check_resilience,
            'return_graphs':args.return_graphs,
            'verbose':args.verbose
        }
        
        writer_data = {
            'return_intermediates':args.return_intermediates,
            'stitch_barcode':args.stitch_barcode
        }
        
        if reader_data['resilience']:
            resilience_data = {
                'evaluation_settings':{
                    'f_start':float(args.pf_start),
                    'f_stop':float(args.pf_stop)
                },
                'frame_step':int(args.res_f_step),
                'r_offset':float(args.r_offset),
            }
        if reader_data['flow']:
            flow_data = {
                'downsample':int(args.downsample),
                'frame_step':int(args.flow_f_step),
                'frame_interval':int(args.frame_interval),
                'nm_pixel_ratio':int(args.nm_pixel_ratio),
                'win_size':int(args.win_size)
            }

        if reader_data['coarsening']:
            coarsening_data = {
                'evaluation_settings':{
                    'first_frame':int(args.first_frame), 
                    'last_frame':False if int(args.last_frame) == 0 else int(args.last_frame)
                },
                'mean_mode_frames_percent':float(args.pf_evaluation),
            }

        config_data = {
            'coarse_parameters':coarsening_data,
            'flow_parameters':flow_data,
            'reader':reader_data,
            'resilience_parameters':resilience_data,
            'writer':writer_data
        }
        
    return config_data

def main ():

    root = tk.Tk()
    root.title("BARCODE: Biomaterial Activity Readouts to Categorize, Optimize, Design, and Engineer")
    root.grid_rowconfigure(0, weight=1) 
    root.grid_columnconfigure(0, weight=1) 

    #prevent border from highlighting 
    style = ttk.Style()
    style.configure("TNotebook", borderwidth=0, relief="flat")
    #optional: disables tab borders 
    #style.configure("TNotebook.Tab", borderwidth=0, padding=[5, 2])
    style.map("TNotebook.Tab",
        focuscolor=[("", "")]
    )

    #enable scrolling 
    container = ttk.Frame(root)
    container.grid(row=0, column=0, sticky="nsew") 

    canvas = tk.Canvas(
        container, 
        bd=0, 
        highlightthickness=0, #prevents border from highlighting 
        takefocus=0 
    )
    v_scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    h_scroll = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)
    canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

    v_scroll.pack(side="right", fill="y")
    h_scroll.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)

    scrollable_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def on_frame_config(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    scrollable_frame.bind("<Configure>", on_frame_config)

    # vertical scroll by wheel, horizontal when Shift+wheel
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    canvas.bind_all("<Shift-MouseWheel>", lambda e: canvas.xview_scroll(int(-1*(e.delta/120)), "units"))

    notebook = ttk.Notebook(scrollable_frame, takefocus=0) 
    notebook.pack(fill="both", expand=True)

    execution_frame = ttk.Frame(notebook)
    binarize_frame  = ttk.Frame(notebook)
    flow_frame      = ttk.Frame(notebook)
    coarse_frame    = ttk.Frame(notebook)
    barcode_frame   = ttk.Frame(notebook)
    notebook.add(execution_frame, text="Execution Settings")
    notebook.add(binarize_frame,  text="Binarization Settings")
    notebook.add(flow_frame,      text="Optical Flow Settings")
    notebook.add(coarse_frame,    text="Intensity Distribution Settings")
    notebook.add(barcode_frame,   text="Barcode Generator + CSV Aggregator")

    #define variable for each argument 
    # ---- Execution Settings group ----
    file_path_var        = tk.StringVar()   # corresponds to --file_path
    dir_path_var         = tk.StringVar()   # corresponds to --dir_path
    channels_var         = tk.BooleanVar()  # corresponds to --channels
    channel_selection_var= tk.IntVar()      # corresponds to --channel_selection
    mode_var = tk.StringVar(value="file")

    def browse_file():
        chosen = filedialog.askopenfilename(
            filetypes=[("TIFF Image","*.tif"), ("ND2 Document","*.nd2")],
            title="Select a File"
        )
        if chosen:
            file_path_var.set(chosen)
            dir_path_var.set("")      # clear the other mode

    def browse_folder():
        chosen = filedialog.askdirectory(title="Select a Folder")
        if chosen:
            dir_path_var.set(chosen)
            file_path_var.set("")     # clear the other mode

    def on_mode_change():
        m = mode_var.get()
        file_state = "normal" if m == "file" else "disabled"
        dir_state  = "normal" if m == "dir" else "disabled"
        file_entry.config(state=file_state)
        browse_file_btn.config(state=file_state)
        dir_entry.config(state=dir_state)
        browse_folder_btn.config(state=dir_state)

    # ---- Reader Execution Settings ----
    check_resilience_var = tk.BooleanVar()  # --check_resilience
    check_flow_var       = tk.BooleanVar()  # --check_flow
    check_coarsening_var = tk.BooleanVar()  # --check_coarsening
    dim_images_var       = tk.BooleanVar()  # --dim_images
    dim_channels_var     = tk.BooleanVar()  # --dim_channels

    # ---- Writer Data ----
    verbose_var           = tk.BooleanVar() # --verbose
    return_graphs_var     = tk.BooleanVar() # --return_graphs
    return_intermediates_var = tk.BooleanVar() # --return_intermediates
    stitch_barcode_var    = tk.BooleanVar() # --stitch_barcode
    configuration_file_var= tk.StringVar()  # --configuration_file

    # ---- Binarization Settings ----
    r_offset_var    = tk.DoubleVar(value=0.1)   # --r_offset
    res_f_step_var  = tk.IntVar(value=10)       # --res_f_step
    pf_start_var    = tk.DoubleVar(value=0.9)   # --pf_start
    pf_stop_var     = tk.DoubleVar(value=1.0)   # --pf_stop
    sample_file_var = tk.StringVar() 

    # ---- Optical Flow Settings ----
    flow_f_step_var    = tk.IntVar(value=10)    # --flow_f_step
    win_size_var       = tk.IntVar(value=32)    # --win_size
    downsample_var     = tk.IntVar(value=8)     # --downsample
    nm_pixel_ratio_var = tk.DoubleVar(value=1.0)     # --nm_pixel_ratio
    frame_interval_var = tk.IntVar(value=1)     # --frame_interval

    # ---- Intensity Distribution Settings ----
    first_frame_var   = tk.IntVar(value=1)      # --first_frame
    last_frame_var    = tk.IntVar(value=0)      # --last_frame
    pf_evaluation_var = tk.DoubleVar(value=0.1) # --pf_evaluation

    # ---- Barcode Generator + CSV Aggregator ----
    csv_paths_list      = []                   # we’ll store a Python list of file-paths (instead of a StringVar)
    combined_location_var = tk.StringVar()     # --combined_location
    generate_agg_barcode_var = tk.BooleanVar() # --generate_agg_barcode
    sort_var            = tk.StringVar(value="Default")  # --sort
    headers = [
        'Default', 'Connectivity', 'Maximum Island Area', 'Maximum Void Area',
        'Void Area Change', 'Island Area Change', 'Initial Island Area 1',
        'Initial Island Area 2', 'Maximum Kurtosis', 'Maximum Median Skewness',
        'Maximum Mode Skewness', 'Kurtosis Difference', 'Median Skewness Difference',
        'Mode Skewness Difference', 'Mean Speed', 'Speed Change',
        'Mean Flow Direction', 'Flow Directional Spread'
    ]

    #build widgets 
    row_idx = 0 
    
    #EXECUTION SETTINGS 
    row_idx = 0

    # Process File
    tk.Radiobutton(
        execution_frame,
        text="Process File",
        variable=mode_var,   # all three share this StringVar
        value="file",        # this button sets mode_var="file"
        command=on_mode_change
    ).grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)

    file_entry = tk.Entry(
        execution_frame,
        textvariable=file_path_var, width=35
    )
    file_entry.grid(row=row_idx, column=1, padx=5, pady=2)

    browse_file_btn = tk.Button(
        execution_frame,
        text="Browse File…",
        command=browse_file
    )
    browse_file_btn.grid(row=row_idx, column=2, sticky="w", padx=5)
    row_idx += 1

    # Process Directory
    tk.Radiobutton(
        execution_frame,
        text="Process Directory",
        variable=mode_var,
        value="dir",
        command=on_mode_change
    ).grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)

    dir_entry = tk.Entry(
        execution_frame,
        textvariable=dir_path_var, width=35
    )
    dir_entry.grid(row=row_idx, column=1, padx=5, pady=2)

    browse_folder_btn = tk.Button(
        execution_frame,
        text="Browse Folder…",
        command=browse_folder
    )
    browse_folder_btn.grid(row=row_idx, sticky="w", column=2, padx=5)
    row_idx += 1

    # Combine CSVs / Generate Barcodes (aggregate mode)
    tk.Radiobutton(
        execution_frame,
        text="Combine CSV files / Generate Barcodes",
        variable=mode_var,
        value="agg",
        command=on_mode_change
    ).grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=5, pady=5)
    row_idx += 1

    #channel selection 
    tk.Label(execution_frame, text="Choose Channel (-3 to 4):").grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
    channel_spin = tk.Spinbox(execution_frame, 
        from_=-4, to=4, 
        textvariable=channel_selection_var, 
        width=5
    )
    channel_spin.grid(row=row_idx, column=0, padx=(50,5), pady=2)
    row_idx += 1

    parse_all_chk = tk.Checkbutton(execution_frame, text="Parse All Channels", variable=channels_var)
    parse_all_chk.grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)
    row_idx += 1 

    #enforce mutual exclusion of channel selection 
    def on_channels_toggled(*args):
        if channels_var.get():
            channel_spin.config(state="disabled")
        else:
            channel_spin.config(state="normal")
    channels_var.trace_add("write", on_channels_toggled)

    def on_channel_selection_changed(*args):
        # If user types ANY integer, uncheck “Parse All Channels”
        if channel_selection_var.get() is not None:
            channels_var.set(False)

    channel_selection_var.trace_add("write", on_channel_selection_changed)

    #reader execution settings 
    tk.Label(
        execution_frame, 
        text="Binarization", 
        font=('TkDefaultFont', 10, 'bold')
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0))
    tk.Checkbutton(
        execution_frame,
        variable=check_resilience_var
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5)
    tk.Label(
        execution_frame,
        text="Evaluate video(s) using binarization branch"
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0))
    row_idx += 2

    tk.Label(
        execution_frame,
        text="Optical Flow",
        font=('TkDefaultFont', 10, 'bold')
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0))
    tk.Checkbutton(
        execution_frame,
        variable=check_flow_var
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5)
    tk.Label(
        execution_frame,
        text="Evaluate video(s) using optical flow branch"
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0))
    row_idx += 2

    tk.Label(
        execution_frame,
        text="Intensity Distribution",
        font=('TkDefaultFont', 10, 'bold')
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0))
    tk.Checkbutton(
        execution_frame,
        variable=check_coarsening_var
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5)
    tk.Label(
        execution_frame,
        text="Evaluate video(s) using intensity distribution branch"
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0))
    row_idx += 2

    tk.Label(
        execution_frame, 
        text="Include dim files", 
        font=('TkDefaultFont', 10, 'bold') 
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0)) 
    tk.Checkbutton(
        execution_frame, variable=dim_images_var
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5)
    tk.Label(
        execution_frame, 
        text="Click to scan files that may be too dim to accurately profile"
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0)) 
    row_idx += 2 

    tk.Label(
        execution_frame, 
        text="Include dim channels", 
        font=('TkDefaultFont', 10, 'bold') 
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0))
    tk.Checkbutton(
        execution_frame, variable=dim_channels_var
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5) 
    tk.Label(
        execution_frame, 
        text="Click to scan channels that may be too dim to accurately profile" 
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0)) 
    row_idx += 2 

    #writer data 
    tk.Label(
        execution_frame,
        text="Verbose",
        font=('TkDefaultFont', 10, 'bold')
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0))
    tk.Checkbutton(
        execution_frame,
        variable=verbose_var
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5)
    tk.Label(
        execution_frame,
        text="Show more details"
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0))
    row_idx += 2

    tk.Label(
        execution_frame,
        text="Save Graphs",
        font=('TkDefaultFont', 10, 'bold')
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0))
    tk.Checkbutton(
        execution_frame,
        variable=return_graphs_var
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5)
    tk.Label(
        execution_frame,
        text="Click to save graphs representing sample changes"
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0))
    row_idx += 2

    tk.Label(
        execution_frame,
        text="Save Reduced Data Structures",
        font=('TkDefaultFont', 10, 'bold')
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0))
    tk.Checkbutton(
        execution_frame,
        variable=return_intermediates_var
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5)
    tk.Label(
        execution_frame,
        text="Click to save reduced data structures (flow fields, binarized images, intensity distributions) for further analysis"
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0))
    row_idx += 2

    tk.Label(
        execution_frame,
        text="Dataset Barcode",
        font=('TkDefaultFont', 10, 'bold')
    ).grid(row=row_idx, column=0, columnspan=3, sticky="w", padx=5, pady=(10,0))
    tk.Checkbutton(
        execution_frame,
        variable=stitch_barcode_var
    ).grid(row=row_idx+1, column=0, sticky="w", padx=5)
    tk.Label(
        execution_frame,
        text="Generates an aggregate barcode for the dataset"
    ).grid(row=row_idx+1, column=0, sticky="w", padx=(25,5), pady=(0,0))
    row_idx += 2

    tk.Label(execution_frame, text="Configuration YAML File:").grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)
    config_entry = tk.Entry(execution_frame, textvariable=configuration_file_var, width=35)
    config_entry.grid(row=row_idx, column=1, padx=5, pady=2)
    def browse_config_file():
        chosen = filedialog.askopenfilename(
            filetypes=[("YAML Files","*.yaml"), ("YAML Files","*.yml")],
            title="Select a Configuration YAML"
        )
        if chosen:
            configuration_file_var.set(chosen)
    tk.Button(execution_frame, text="Browse YAML...", command=browse_config_file).grid(row=row_idx, column=2, sticky="w", padx=5)
    row_idx += 1

    #BINARIZATION SETTINGS 
    row_b = 0

    tk.Label(binarize_frame, text="Binarization Threshold:").grid(row=row_b, column=0, sticky="w", padx=5, pady=5)
    scale_frame = tk.Frame(binarize_frame)
    scale_frame.columnconfigure(0, weight=0) 
    for c in range (1, 10): 
        scale_frame.columnconfigure(c, weight=1) 
    scale_frame.columnconfigure(10, weight=0) 
    scale_frame.grid(row=row_b, column=1, padx=5, pady=5, sticky="ew")

    r_offset_scale = tk.Scale(
        scale_frame, 
        from_=-1.00, 
        to=1.00, 
        resolution=0.05, 
        orient="horizontal", 
        variable=r_offset_var, 
        length=300, 
        showvalue=True
    )
    r_offset_scale.grid(row=0, column=1, columnspan=9, sticky="ew")

    decrease_btn = tk.Button(
        scale_frame, text="◀", width=2, 
        command=lambda: r_offset_var.set(max(r_offset_var.get() - 0.05, -1.00)) 
    )
    decrease_btn.grid(row=0, column=0, padx=(0,2), pady=(15,0)) 
    increase_btn = tk.Button(
        scale_frame, text="▶", width=2, 
        command=lambda: r_offset_var.set(min(r_offset_var.get() + 0.05, 1.00)) 
    )
    increase_btn.grid(row=0, column=10, padx=(2,0), pady=(15,0)) 
    
    tick_values = [round(-1.00+i*0.25, 2) for i in range(9)]
    for i, val in enumerate(tick_values):
        #scale_frame.columnconfigure(i, weight=1)
        lbl = tk.Label(scale_frame, text=f"{val:.2f}")
        lbl.grid(row=1, column=i+1, sticky="n")
    row_b += 1

    tk.Label(binarize_frame, text="Choose image from folder for preview:").grid(
        row=row_b, column=0, stick="w", padx=5, pady=5
    )
    sample_file_combobox = ttk.Combobox(
        binarize_frame, textvariable=sample_file_var, state="disabled", width=30 
    )
    sample_file_combobox.grid(row=row_b, column=1, padx=5, pady=5) 
    row_b += 1 

    #live binarization preview 
    preview_title = tk.Label(
        binarize_frame, 
        text="Dynamic preview of first-frame binarization:" 
    )
    preview_title.grid(
        row=row_b, column=0, columnspan=2, 
        padx=5, pady=(10,2), sticky="w"
    )
    row_b += 1 

    #labels 
    tk.Label(binarize_frame, text="Original").grid(
        row=row_b, column=0,
        padx=5, pady=2, sticky="n"
    )
    tk.Label(binarize_frame, text="Binarized").grid(
        row=row_b, column=1,
        padx=5, pady=2, sticky="n"
    )
    row_b += 1

    # now recreate your figure on the next row
    bg_name = root.cget('bg')
    r, b, g = root.winfo_rgb(bg_name)
    bg_color = (r/65535, g/65535, b/65535)
    fig_orig = Figure(figsize=(3,3), facecolor=bg_color)
    ax_orig = fig_orig.add_subplot(111)
    ax_orig.set_facecolor(bg_color)
    ax_orig.axis('off')
    
    canvas_orig = FigureCanvasTkAgg(fig_orig, master=binarize_frame) 
    canvas_orig.draw() 
    canvas_orig.get_tk_widget().grid(row=row_b, column=0, padx=5, pady=(10,5)) 
    im_orig = ax_orig.imshow(np.zeros((10,10)), cmap='gray') 
    fig_orig.tight_layout() 

    fig_bin = Figure(figsize=(3,3), facecolor=bg_color) 
    ax_bin = fig_bin.add_subplot(111) 
    ax_bin.set_facecolor(bg_color) 
    ax_bin.axis('off') 

    canvas_bin = FigureCanvasTkAgg(fig_bin, master=binarize_frame) 
    canvas_bin.draw() 
    canvas_bin.get_tk_widget().grid(row=row_b, column=1, padx=5, pady=(10,5)) 
    ax_bin.imshow(np.zeros((10,10)), cmap='gray') 
    fig_bin.tight_layout() 

    preview_label = tk.Label(
        binarize_frame, 
        text="Upload file to see binarization threshold preview.", 
        compound="center" 
    )
    preview_label.grid(row=row_b, column=0, columnspan=2, padx=5, pady=(10,5)) 
    row_b += 1 

    preview_data = {"frame": None}

    def update_preview(*args):
        img = preview_data["frame"]
        if img is None:
            preview_label.grid() 
            # clear original axis & revert binarized label
            ax_orig.clear(); ax_orig.axis('off')
            canvas_orig.draw()
            ax_bin.clear() 
            ax_bin.set_facecolor(bg_color) 
            ax_bin.axis('off') 
            canvas_bin.draw() 
            preview_label.config(
                image='',
                text="Upload file to see binarization threshold preview."
            )
            return

        preview_label.grid_remove() 

        #set scale factor 
        h, w = img.shape 
        max_px = 300 
        scale = max(1, int(max(h, w)/max_px)+1) 

        #show down-sampled original
        small = img[::scale, ::scale] 
        ax_orig.clear() 
        ax_orig.imshow(small, cmap='gray', interpolation='nearest') 
        ax_orig.axis('off') 
        fig_orig.tight_layout() 
        canvas_orig.draw() 

        #show down-sampled binarized 
        offset = r_offset_var.get()
        bin_arr = binarize(img, offset)
        small_bin = bin_arr[::scale, ::scale] 
        ax_bin.clear() 
        ax_bin.imshow(small_bin, cmap='gray', interpolation='nearest') 
        ax_bin.axis('off') 
        fig_bin.tight_layout() 
        canvas_bin.draw() 


    def load_preview_frame(*args):
        #load first frame of selected file
        if mode_var.get()=="dir":
            dir_path = dir_path_var.get()
            sample = sample_file_var.get() 
            if not dir_path or not sample: 
                preview_data["frame"] = None 
                update_preview()
                return 
            path = os.path.join(dir_path, sample) 
        else: 
            path = file_path_var.get() 
        if not path:
            preview_data["frame"] = None
            update_preview()
            return
        try:
            preview_data["frame"] = load_first_frame(path)
        except Exception as e:
            print(f"[Preview] couldn't load first frame: {e}")
            preview_data["frame"] = None
        update_preview()

    # whenever the user picks a new file, reload the first frame
    file_path_var.trace_add("write", load_preview_frame)
    sample_file_var.trace_add("write", load_preview_frame) 
    # whenever threshold changes, re-bin & redraw
    r_offset_var.trace_add("write", update_preview)

    def update_sample_file_options(*args): 
        dir_path = dir_path_var.get() 
        if dir_path and os.path.isdir(dir_path):
            # list only .tif and .nd2 files
            files = [
                f for f in os.listdir(dir_path)
                if f.lower().endswith(('.tif', '.nd2'))
            ]
            sample_file_combobox['values'] = files
            sample_file_combobox.config(state='readonly')
            if files:
                sample_file_var.set(files[0])
        else:
            sample_file_combobox.set('')
            sample_file_combobox['values'] = []
            sample_file_combobox.config(state='disabled')
    
    #update combobox 
    dir_path_var.trace_add("write", update_sample_file_options) 

    # kick everything off once
    load_preview_frame()

    tk.Label(binarize_frame, text="Frame Step (res_f_step) [min=1]:").grid(row=row_b, column=0, sticky="w", padx=5, pady=5)
    res_f_step_spin = ttk.Spinbox(
        binarize_frame,
        from_=1, to=100,
        increment=1,
        textvariable=res_f_step_var,
        width=7
    )
    res_f_step_spin.grid(row=row_b, column=1, padx=5, pady=5)
    row_b += 1

    tk.Label(binarize_frame, text="Frame Start Percent (pf_start 0.5–0.9):").grid(row=row_b, column=0, sticky="w", padx=5, pady=5)
    pf_start_spin = ttk.Spinbox(
        binarize_frame,
        from_=0.5, to=0.9,
        increment=0.05,
        textvariable=pf_start_var,
        format="%.2f",
        width=7
    )
    pf_start_spin.grid(row=row_b, column=1, padx=5, pady=5)
    row_b += 1

    tk.Label(binarize_frame, text="Frame Stop Percent (pf_stop 0.9–1.0):").grid(row=row_b, column=0, sticky="w", padx=5, pady=5)
    pf_stop_spin = ttk.Spinbox(
        binarize_frame,
        from_=0.9, to=1.0,
        increment=0.05,
        textvariable=pf_stop_var,
        format="%.2f",
        width=7
    )
    pf_stop_spin.grid(row=row_b, column=1, padx=5, pady=5)
    row_b += 1

    #OPTICAL FLOW SETTINGS 
    row_f = 0 
    tk.Label(flow_frame, text="Frame Step (Minimum: 1 Frame):").grid(row=row_f, column=0, sticky="w", padx=5, pady=5)
    flow_f_step_spin = ttk.Spinbox(
        flow_frame, from_=1, to=1000,
        increment=1,
        textvariable=flow_f_step_var,
        width=7
    )
    flow_f_step_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    tk.Label(flow_frame, text="Window Size (Minimum: 1 Pixel):").grid(row=row_f, column=0, sticky="w", padx=5, pady=5)
    win_size_spin = ttk.Spinbox(
        flow_frame, from_=1, to=1000,
        increment=1,
        textvariable=win_size_var,
        width=7
    )
    win_size_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    tk.Label(flow_frame, text="Downsample (Minimum: 1 Pixel):").grid(row=row_f, column=0, sticky="w", padx=5, pady=5)
    downsample_spin = ttk.Spinbox(
        flow_frame, from_=1, to=1000,
        increment=1,
        textvariable=downsample_var,
        width=7
    )
    downsample_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    #downsample optical flow preview 
    # preview_flow_title = tk.Label(flow_frame, text="Dynamic preview of optical flow (first two frames):") 
    # preview_flow_title.grid(
    #     row=row_f, column=0, columnspan=2, padx=5, pady=(10,2), sticky="w" 
    # )
    # row_f += 1 

    # fig_flow = Figure(figsize=(3,3), facecolor=bg_color) 
    # ax_flow = fig_flow.ad_subplot(111) 

    tk.Label(flow_frame, text="Nanometer to Pixel Ratio [1 nm – 1 mm]:").grid(row=row_f, column=0, sticky="w", padx=5, pady=5)
    nm_pixel_spin = ttk.Spinbox(
        flow_frame, from_=1, to=10**6,
        increment=1,
        textvariable=nm_pixel_ratio_var,
        width=9
    )
    nm_pixel_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    tk.Label(flow_frame, text="Frame Interval [1–1000]:").grid(row=row_f, column=0, sticky="w", padx=5, pady=5)
    frame_interval_spin = ttk.Spinbox(
        flow_frame, from_=1, to=10**3,
        increment=1,
        textvariable=frame_interval_var,
        width=7
    )
    frame_interval_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    #INTENSITY DISTRIBUTION SETTINGS 
    row_c = 0 

    tk.Label(coarse_frame, text="First Frame [min=1]:").grid(row=row_c, column=0, sticky="w", padx=5, pady=5)
    first_frame_spin = ttk.Spinbox(
        coarse_frame, from_=1, to=10**2,
        increment=1,
        textvariable=first_frame_var,
        width=7
    )
    first_frame_spin.grid(row=row_c, column=1, padx=5, pady=5)
    row_c += 1

    tk.Label(coarse_frame, text="Last Frame (Select 0 to compare ending frames):").grid(row=row_c, column=0, sticky="w", padx=5, pady=5)
    last_frame_spin = ttk.Spinbox(
        coarse_frame, from_=0, to=10**2,
        increment=1,
        textvariable=last_frame_var,
        width=7
    )
    last_frame_spin.grid(row=row_c, column=1, padx=5, pady=5)
    row_c += 1

    tk.Label(coarse_frame, text="Percent of Frames Evaluated [0.01–0.2]:").grid(row=row_c, column=0, sticky="w", padx=5, pady=5)
    pf_eval_spin = ttk.Spinbox(
        coarse_frame, from_=0.01, to=0.2,
        increment=0.01,
        textvariable=pf_evaluation_var,
        format="%.2f",
        width=7
    )
    pf_eval_spin.grid(row=row_c, column=1, padx=5, pady=5)
    row_c += 1

    #BARCODE GENERATOR + CSV AGGREGATOR 
    row_ba = 0

    #csv file chooser 
    tk.Label(barcode_frame, text="Select CSV Files:").grid(row=row_ba, column=0, sticky="w", padx=5, pady=5)
    csv_label = tk.Label(barcode_frame, text="No files selected", wraplength=200, justify="left")
    csv_label.grid(row=row_ba, column=1, sticky="w", padx=5, pady=5)

    def browse_csv_files():
        chosen = filedialog.askopenfilenames(
            filetypes=[("CSV Files","*.csv")],
            title="Select one or more CSV files"
        )
        if chosen:
            # chosen is a tuple of paths
            csv_paths_list.clear()
            csv_paths_list.extend(chosen)
            # Update the label to show e.g. “3 files selected”
            csv_label.config(text=f"{len(chosen)} CSV files selected")
        else:
            csv_paths_list.clear()
            csv_label.config(text="No files selected")

    tk.Button(barcode_frame, text="Browse CSV Files...", command=browse_csv_files).grid(row=row_ba, column=2, padx=5, pady=5)
    row_ba += 1

    #aggregate location (filesaver)
    tk.Label(barcode_frame, text="Aggregate CSV Location:").grid(row=row_ba, column=0, sticky="w", padx=5, pady=5)
    combo_entry = tk.Entry(barcode_frame, textvariable=combined_location_var, width=40)
    combo_entry.grid(row=row_ba, column=1, padx=5, pady=5)

    def browse_save_csv():
        chosen = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV File","*.csv")],
            initialfile="aggregate_summary.csv",
            title="Save Aggregate CSV As"
        )
        if chosen:
            combined_location_var.set(chosen)

    tk.Button(barcode_frame, text="Save As...", command=browse_save_csv).grid(row=row_ba, column=2, padx=5, pady=5)
    row_ba += 1

    #generate aggregate barcode
    tk.Checkbutton(
        barcode_frame, text="Generate Aggregate Barcode",
        variable=generate_agg_barcode_var
    ).grid(row=row_ba, column=0, sticky="w", padx=5, pady=5)
    row_ba += 1

    #metric sort 
    tk.Label(barcode_frame, text="Sort Parameter:").grid(row=row_ba, column=0, sticky="w", padx=5, pady=5)
    sort_menu = ttk.OptionMenu(
        barcode_frame,
        sort_var,
        headers[0],  # default value
        *headers     # all choices
    )
    sort_menu.grid(row=row_ba, column=1, sticky="w", padx=5, pady=5)
    row_ba += 1

    #Run button
    run_button = ttk.Button(root, text="Run", command=lambda: on_run())
    run_button.grid(row=1, column=0, pady=10, sticky="n") 

    #Run 
    def on_run():
        #terminal message window 
        log_win = tk.Toplevel(root) 
        log_win.title("Processing Log") 

        log_frame = ttk.Frame(log_win) 
        log_frame.pack(fill='both', expand=True) 
        log_frame.rowconfigure(0, weight=1) 
        log_frame.columnconfigure(0, weight=1) 

        log_text = tk.Text(log_frame, state='disabled', wrap='word', font=('Segoe UI', 10)) 
        log_text.pack(side='left', fill='both', expand=True) 
        
        log_scroll = ttk.Scrollbar(log_frame, orient='vertical', command=log_text.yview) 
        log_scroll.pack(side='right', fill='y') 
        log_text.configure(yscrollcommand=log_scroll.set) 
        
        root.update_idletasks() 

        class TextRedirector:
            def __init__(self, widget):
                self.widget = widget
            def write(self, msg):
                try:
                    # enable → insert → scroll → disable
                    self.widget.configure(state='normal')
                    self.widget.insert('end', msg)
                    self.widget.see('end')
                    self.widget.configure(state='disabled')
                except:
                    raise Exception("Program Terminated Early")
            def flush(self):
                pass

        sys.stdout = TextRedirector(log_text) 
        sys.stderr = TextRedirector(log_text) 

        #create a thread to run background tasks 
        def worker(): 
            try: 
                #read all variable values 
                file_path        = file_path_var.get()
                dir_path         = dir_path_var.get()
                channels         = channels_var.get()
                channel_selection= channel_selection_var.get()
                mode = mode_var.get()
                settings = argparse.Namespace() 
                settings.barcode_generation = (mode == "agg")

                check_resilience = check_resilience_var.get()
                check_flow       = check_flow_var.get()
                check_coarsening = check_coarsening_var.get()
                dim_images       = dim_images_var.get()
                dim_channels     = dim_channels_var.get()

                verbose          = verbose_var.get()
                return_graphs    = return_graphs_var.get()
                return_intermediates = return_intermediates_var.get()
                stitch_barcode   = stitch_barcode_var.get()
                configuration_file = configuration_file_var.get()

                r_offset         = r_offset_var.get()
                res_f_step       = res_f_step_var.get()
                pf_start         = pf_start_var.get()
                pf_stop          = pf_stop_var.get()

                flow_f_step      = flow_f_step_var.get()
                win_size         = win_size_var.get()
                downsample       = downsample_var.get()
                nm_pixel_ratio   = nm_pixel_ratio_var.get()
                frame_interval   = frame_interval_var.get()

                first_frame      = first_frame_var.get()
                last_frame       = last_frame_var.get()
                pf_evaluation    = pf_evaluation_var.get()

                csv_paths        = csv_paths_list[:]  # copy of the list
                combined_location= combined_location_var.get()
                generate_agg_barcode = generate_agg_barcode_var.get()
                sort_param       = sort_var.get()

                #build settings namespace to mimic argparse 
                settings.file_path        = file_path
                settings.dir_path         = dir_path
                settings.channels         = channels
                settings.channel_selection= channel_selection

                settings.check_resilience = check_resilience
                settings.check_flow       = check_flow
                settings.check_coarsening = check_coarsening
                settings.dim_images       = dim_images
                settings.dim_channels     = dim_channels

                settings.verbose          = verbose
                settings.return_graphs    = return_graphs
                settings.return_intermediates = return_intermediates
                settings.stitch_barcode   = stitch_barcode
                settings.configuration_file = configuration_file

                settings.r_offset         = r_offset
                settings.res_f_step       = res_f_step
                settings.pf_start         = pf_start
                settings.pf_stop          = pf_stop

                settings.flow_f_step      = flow_f_step
                settings.win_size         = win_size
                settings.downsample       = downsample
                settings.nm_pixel_ratio   = nm_pixel_ratio
                settings.frame_interval   = frame_interval

                settings.first_frame      = first_frame
                settings.last_frame       = last_frame
                settings.pf_evaluation    = pf_evaluation

                # csv_paths as a list of paths 
                settings.csv_paths        = csv_paths
                settings.combined_location= combined_location
                settings.generate_agg_barcode = generate_agg_barcode
                settings.sort             = sort_param

                #branch 
                if settings.barcode_generation:
                    if not settings.csv_paths:
                        messagebox.showerror("Error", "No CSV files selected for aggregation.")
                        return
                    if not settings.combined_location:
                        messagebox.showerror("Error", "No aggregate location specified.")
                        return

                    files = settings.csv_paths 
                    combined_csv_loc = settings.combined_location 
                    gen_barcode = settings.generate_agg_barcode 

                    sort_choice = None if settings.sort=='Default' else settings.sort 

                    try:
                        generate_aggregate_csv(files, combined_csv_loc, gen_barcode, sort_choice)
                        messagebox.showinfo("Success", "Combined CSV and barcodes generated!")
                    except Exception as e:
                        messagebox.showerror("Error during aggregation", str(e))
                    return 

                else:
                    #process file or folder 
                    if not (settings.dir_path or settings.file_path):
                        messagebox.showerror("Error", "No file or directory has been selected.")
                        return
                    if not (settings.channels or (settings.channel_selection is not None)):
                        messagebox.showerror("Error", "No channel has been specified.")
                        return

                    dir_name = settings.dir_path if settings.dir_path else settings.file_path 

                    # If configuration YAML is provided, load it instead of using set_config_data:
                    if settings.configuration_file:
                        try:
                            with open(settings.configuration_file, 'r') as f:
                                config_data = yaml.load(f, Loader=yaml.FullLoader)
                        except Exception as e:
                            messagebox.showerror("Error reading config file", str(e))
                            return
                    else:
                        settings.dim_channels = dim_channels
                        settings.dim_images   = dim_images
                        settings.channels     = channels
                        settings.channel_selection = channel_selection
                        settings.check_coarsening   = check_coarsening
                        settings.check_flow         = check_flow
                        settings.check_resilience   = check_resilience
                        settings.return_graphs      = return_graphs
                        settings.verbose            = verbose

                        settings.return_intermediates = return_intermediates
                        settings.stitch_barcode    = stitch_barcode

                        settings.pf_start = pf_start
                        settings.pf_stop  = pf_stop
                        settings.res_f_step = res_f_step
                        settings.r_offset   = r_offset

                        settings.downsample     = downsample
                        settings.flow_f_step    = flow_f_step
                        settings.frame_interval = frame_interval
                        settings.nm_pixel_ratio = nm_pixel_ratio
                        settings.win_size       = win_size

                        settings.first_frame   = first_frame
                        settings.last_frame    = last_frame
                        settings.pf_evaluation = pf_evaluation

                        config_data = set_config_data(settings)

                    #print directory name 
                    try:
                        if os.path.isdir(dir_name):
                            print(dir_name, flush=True)
                        process_directory(dir_name, config_data)
                        messagebox.showinfo("Success", "Processing complete!")
                    except Exception as e:
                        messagebox.showerror("Error during processing", str(e))
                    return
            except Exception as e: 
                messagebox.showerror("Error during processing", str(e)) 

        threading.Thread(target=worker, daemon=True).start() 

    root.update_idletasks() 
    bbox = canvas.bbox("all") #returns (x1, y1, x2, y2) 
    if bbox: 
        content_width  = bbox[2] - bbox[0] 
        content_height = bbox[3] - bbox[1] 
        canvas.config(width=content_width, height=content_height) 
        root.update_idletasks() 

    root.mainloop()


if __name__ == "__main__":
    main()

