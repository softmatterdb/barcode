import os
import tkinter as tk
from tkinter import ttk
import numpy as np
from utils import groupAvg
from utils.analysis.image_binarization import binarize
from utils.reader import load_binarization_frame
from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 

def create_image_binarization_tab(
        root: tk.Tk,
        notebook: ttk.Notebook,
        config_data: dict,
) -> tk.Frame:
    frame = ttk.Frame(notebook)
    row_b = 0
    tk.Label(frame, text="Binarization Threshold").grid(row=row_b, column=0, sticky="w", padx=5, pady=5)
    scale_frame = tk.Frame(frame)
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
        variable=config_data["gui_binarization"]["threshold_offset"], 
        length=300, 
        showvalue=True
    )
    r_offset_scale.grid(row=0, column=1, columnspan=9, sticky="ew")

    decrease_btn = tk.Button(
        scale_frame, text="◀", width=2, 
        command=lambda: config_data["gui_binarization"]["threshold_offset"].set(max(config_data["gui_binarization"]["threshold_offset"].get() - 0.05, -1.00)) 
    )
    decrease_btn.grid(row=0, column=0, padx=(0,2), pady=(15,0)) 
    increase_btn = tk.Button(
        scale_frame, text="▶", width=2, 
        command=lambda: config_data["gui_binarization"]["threshold_offset"].set(min(config_data["gui_binarization"]["threshold_offset"].get() + 0.05, 1.00)) 
    )
    increase_btn.grid(row=0, column=10, padx=(2,0), pady=(15,0)) 
    
    tick_values = [round(-1.00+i*0.25, 2) for i in range(9)]
    for i, val in enumerate(tick_values):
        lbl = tk.Label(scale_frame, text=f"{val:.2f}")
        lbl.grid(row=1, column=i+1, sticky="n")
    row_b += 1

    tk.Label(frame, text="Choose image from folder for preview:").grid(
        row=row_b, column=0, stick="w", padx=5, pady=5
    )
    sample_file_combobox = ttk.Combobox(
        frame, textvariable=config_data["gui_binarization"]["sample_file"], state="disabled", width=30 
    )
    sample_file_combobox.grid(row=row_b, column=1, padx=5, pady=5) 
    row_b += 1 

    #live binarization preview 
    preview_title = tk.Label(
        frame, 
        text="Dynamic preview of first-frame binarization:" 
    )
    preview_title.grid(
        row=row_b, column=0, columnspan=2, 
        padx=5, pady=(10,2), sticky="w"
    )
    row_b += 1 

    #labels 
    tk.Label(frame, text="Original").grid(
        row=row_b, column=0,
        padx=5, pady=2, sticky="n"
    )
    tk.Label(frame, text="Binarized").grid(
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
    
    canvas_orig = FigureCanvasTkAgg(fig_orig, master=frame) 
    canvas_orig.draw() 
    canvas_orig.get_tk_widget().grid(row=row_b, column=0, padx=5, pady=(10,5)) 
    im_orig = ax_orig.imshow(np.zeros((10,10)), cmap='gray') 
    fig_orig.tight_layout() 

    fig_bin = Figure(figsize=(3,3), facecolor=bg_color) 
    ax_bin = fig_bin.add_subplot(111) 
    ax_bin.set_facecolor(bg_color) 
    ax_bin.axis('off') 

    canvas_bin = FigureCanvasTkAgg(fig_bin, master=frame) 
    canvas_bin.draw() 
    canvas_bin.get_tk_widget().grid(row=row_b, column=1, padx=5, pady=(10,5)) 
    ax_bin.imshow(np.zeros((10,10)), cmap='gray') 
    fig_bin.tight_layout() 

    preview_label = tk.Label(
        frame, 
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
        offset = config_data["gui_binarization"]["threshold_offset"].get()
        bin_arr = groupAvg(binarize(img, offset), 2, True)
        small_bin = bin_arr[::scale, ::scale] 
        ax_bin.clear() 
        ax_bin.imshow(small_bin, cmap='gray', interpolation='nearest') 
        ax_bin.axis('off') 
        fig_bin.tight_layout() 
        canvas_bin.draw() 


    def load_preview_frame(*args):
        #load first frame of selected file
        channel = 0 if config_data["gui_execution"]["channels"].get() else config_data["gui_execution"]["channel_selection"].get()
        if config_data["gui_execution"]["mode"].get()=="dir":
            dir_path = config_data["gui_execution"]["dir_path"].get()
            sample = config_data["gui_binarization"]["sample_file"].get() 
            if not dir_path or not sample: 
                preview_data["frame"] = None 
                update_preview()
                return 
            path = os.path.join(dir_path, sample) 
        else: 
            path = config_data["gui_execution"]["file_path"].get()
        if not path:
            preview_data["frame"] = None
            update_preview()
            return
        try:
            preview_data["frame"] = load_binarization_frame(path, channel)
        except Exception as e:
            print(f"[Preview] couldn't load first frame: {e}")
            preview_data["frame"] = None
        update_preview()

    # whenever the user picks a new file, reload the first frame
    config_data["gui_execution"]["file_path"].trace_add("write", load_preview_frame)
    config_data["gui_binarization"]["sample_file"].trace_add("write", load_preview_frame) 
    config_data["gui_execution"]["channels"].trace_add("write", load_preview_frame)
    config_data["gui_execution"]["channel_selection"].trace_add("write", load_preview_frame)
    # whenever threshold changes, re-bin & redraw
    config_data["gui_binarization"]["threshold_offset"].trace_add("write", update_preview)

    def update_sample_file_options(*args): 
        dir_path = config_data["gui_execution"]["dir_path"].get() 
        if dir_path and os.path.isdir(dir_path):
            # list only .tif and .nd2 files
            files = [
                os.path.join(dir, f).removeprefix(dir_path + os.path.sep)
                for dir, _, files in os.walk(dir_path)
                for f in files
                if f.lower().endswith((".tif", ".tiff", ".nd2"))
            ]
            sample_file_combobox['values'] = files
            sample_file_combobox.config(state='readonly')
            if files:
                config_data["gui_binarization"]["sample_file"].set(files[0])
        else:
            sample_file_combobox.set('')
            sample_file_combobox['values'] = []
            sample_file_combobox.config(state='disabled')
    
    #update combobox 
    config_data["gui_execution"]["dir_path"].trace_add("write", update_sample_file_options) 

    # kick everything off once
    load_preview_frame()

    tk.Label(frame, text="Frame Step").grid(row=row_b, column=0, sticky="w", padx=5, pady=5)
    ib_f_step_spin = ttk.Spinbox(
        frame,
        from_=1, to=100,
        increment=1,
        textvariable=config_data["gui_binarization"]["frame_step"],
        width=7
    )
    ib_f_step_spin.grid(row=row_b, column=1, padx=5, pady=5)
    row_b += 1

    tk.Label(frame, text="Fraction of Frames Evaluated (0.01–0.25)").grid(row=row_b, column=0, sticky="w", padx=5, pady=5)
    ib_pf_eval_spin = ttk.Spinbox(
        frame, from_=0.01, to=0.25,
        increment=0.01,
        textvariable=config_data["gui_binarization"]["percentage_frames_evaluated"],
        format="%.2f",
        width=7
    )
    ib_pf_eval_spin.grid(row=row_b, column=1, padx=5, pady=5)
    return frame, config_data