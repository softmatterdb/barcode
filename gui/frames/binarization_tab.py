import os
import sys

import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui.config import PreviewConfigGUI, InputConfigGUI, BarcodeConfigGUI
from utils.preview_binarization import load_first_frame, binarize

from .execution_tab import create_popup
from core import BinarizationConfig

def create_binarization_frame(
    parent,
    config: BarcodeConfigGUI,
    preview_config: PreviewConfigGUI,
    input_config: InputConfigGUI,
):
    """Create the binarization settings tab with live preview"""
    frame = ttk.Frame(parent)

    # Access config variables directly
    cb = config.binarization
    cp = preview_config
    ci = input_config

    row_b = 0

    # Checkbox to input the size of the image
    window_size_enabled = tk.BooleanVar(value=False)
    # window_size_var = tk.IntVar(value=15)

    def toggle_window_size_entry():
        if window_size_enabled.get():
            window_size_entry.config(state="normal")
            cb.window_size_enabled.set(True)
        else: 
            window_size_entry.config(state="disabled")
            cb.window_size_enabled.set(False)
    
    # Checkbox
    window_size_checkbox = tk.Checkbutton(
        frame,
        text="Enable custom window size (um/pixel):",
        variable=window_size_enabled,
        command=toggle_window_size_entry,
    )
    window_size_checkbox.grid(row=row_b, column=0, sticky="w", padx=5, pady=5)

    #Spinbox 
    window_size_entry = ttk.Spinbox(
        frame,
        increment=0.01,
        textvariable=cb.window_size_var,
        width=7,
        state="disabled"
    )

    window_size_entry.grid(row=row_b, column=1, padx=5, pady=5)

    # print(BinarizationConfig.window_size_entry)

    row_b += 1

    # Binarization Threshold with scale

    '''Can delete the three lines below once everything is working'''
    # tk.Label(frame, text="Binarization Threshold:").grid(
    #     row=row_b, column=0, sticky="w", padx=5, pady=5
    # )

    binarization_label=tk.Label(frame, text="Binarization Threshold:")
    binarization_label.grid(row=row_b, column=0, sticky="w", padx=5, pady=5)

    # Add popup for binarization threshold
    create_popup(frame, "Changes cutoff threshold for binarization. Decreasing threshold can increase noise, while increasing threshold can lead to lost" \
    "features. Use viewer to determine optimal value for sample.", row_b, binarization_label)


    scale_frame = tk.Frame(frame)
    scale_frame.columnconfigure(0, weight=0)
    for c in range(1, 10):
        scale_frame.columnconfigure(c, weight=1)
    scale_frame.columnconfigure(10, weight=0)
    scale_frame.grid(row=row_b, column=1, padx=5, pady=5, sticky="ew")

    r_offset_scale = tk.Scale(
        scale_frame,
        from_=-1.00,
        to=1.00,
        resolution=0.05,
        orient="horizontal",
        variable=cb.threshold_offset,
        length=300,
        showvalue=True,
    )
    r_offset_scale.grid(row=0, column=1, columnspan=9, sticky="ew")

    decrease_btn = tk.Button(
        scale_frame,
        text="◀",
        width=2,
        command=lambda: cb.threshold_offset.set(
            max(cb.threshold_offset.get() - 0.05, -1.00)
        ),
    )
    decrease_btn.grid(row=0, column=0, padx=(0, 2), pady=(15, 0))

    increase_btn = tk.Button(
        scale_frame,
        text="▶",
        width=2,
        command=lambda: cb.threshold_offset.set(
            min(cb.threshold_offset.get() + 0.05, 1.00)
        ),
    )
    increase_btn.grid(row=0, column=10, padx=(2, 0), pady=(15, 0))

    # Tick marks
    tick_values = [round(-1.00 + i * 0.25, 2) for i in range(9)]
    for i, val in enumerate(tick_values):
        lbl = tk.Label(scale_frame, text=f"{val:.2f}")
        lbl.grid(row=1, column=i + 1, sticky="n")
    row_b += 1

    # Sample file selection
    tk.Label(frame, text="Choose image from folder for preview:").grid(
        row=row_b, column=0, sticky="w", padx=5, pady=5
    )
    sample_file_combobox = ttk.Combobox(
        frame, textvariable=cp.sample_file, state="disabled", width=30
    )
    sample_file_combobox.grid(row=row_b, column=1, padx=5, pady=5)
    row_b += 1

    # Live preview setup
    preview_title = tk.Label(frame, text="Dynamic preview of first-frame binarization:")
    preview_title.grid(
        row=row_b, column=0, columnspan=2, padx=5, pady=(10, 2), sticky="w"
    )
    row_b += 1

    # Preview labels
    tk.Label(frame, text="Original").grid(
        row=row_b, column=0, padx=5, pady=2, sticky="n"
    )
    tk.Label(frame, text="Binarized").grid(
        row=row_b, column=1, padx=5, pady=2, sticky="n"
    )
    row_b += 1

    # Get background color for matplotlib figures
    root = parent.winfo_toplevel()
    bg_name = root.cget("bg")
    r, g, b = root.winfo_rgb(bg_name)
    bg_color = (r / 65535, g / 65535, b / 65535)

    # Original image figure
    fig_orig = Figure(figsize=(3, 3), facecolor=bg_color)
    ax_orig = fig_orig.add_subplot(111)
    ax_orig.set_facecolor(bg_color)
    ax_orig.axis("off")

    canvas_orig = FigureCanvasTkAgg(fig_orig, master=frame)
    canvas_orig.draw()
    canvas_orig.get_tk_widget().grid(row=row_b, column=0, padx=5, pady=(10, 5))
    im_orig = ax_orig.imshow(np.zeros((10, 10)), cmap="gray")
    fig_orig.tight_layout()

    # Binarized image figure
    fig_bin = Figure(figsize=(3, 3), facecolor=bg_color)
    ax_bin = fig_bin.add_subplot(111)
    ax_bin.set_facecolor(bg_color)
    ax_bin.axis("off")

    canvas_bin = FigureCanvasTkAgg(fig_bin, master=frame)
    canvas_bin.draw()
    canvas_bin.get_tk_widget().grid(row=row_b, column=1, padx=5, pady=(10, 5))
    ax_bin.imshow(np.zeros((10, 10)), cmap="gray")
    fig_bin.tight_layout()

    preview_label = tk.Label(
        frame,
        text="Upload file to see binarization threshold preview.",
        compound="center",
    )
    preview_label.grid(row=row_b, column=0, columnspan=2, padx=5, pady=(10, 5))
    row_b += 1

    # Preview functionality
    preview_data = {"frame": None}

    def update_preview(*args):
        img = preview_data["frame"]
        if img is None:
            preview_label.grid()
            ax_orig.clear()
            ax_orig.axis("off")
            canvas_orig.draw()
            ax_bin.clear()
            ax_bin.set_facecolor(bg_color)
            ax_bin.axis("off")
            canvas_bin.draw()
            preview_label.config(
                image="", text="Upload file to see binarization threshold preview."
            )
            return

        preview_label.grid_remove()

        # Set scale factor
        h, w = img.shape
        max_px = 300
        scale = max(1, int(max(h, w) / max_px) + 1)

        # Show down-sampled original
        small = img[::scale, ::scale]
        ax_orig.clear()
        ax_orig.imshow(small, cmap="gray", interpolation="nearest")
        ax_orig.axis("off")
        fig_orig.tight_layout()
        canvas_orig.draw()

        # Show down-sampled binarized
        offset = cb.threshold_offset.get()
        bin_arr = binarize(img, offset)
        small_bin = bin_arr[::scale, ::scale]
        ax_bin.clear()
        ax_bin.imshow(small_bin, cmap="gray", interpolation="nearest")
        ax_bin.axis("off")
        fig_bin.tight_layout()
        canvas_bin.draw()

    def load_preview_frame(*args):
        # Load first frame of selected file
        if ci.mode.get() == "dir":
            dir_path = ci.dir_path.get()
            sample = cp.sample_file.get()
            if not dir_path or not sample:
                preview_data["frame"] = None
                update_preview()
                return
            path = os.path.join(dir_path, sample)
        else:
            path = ci.file_path.get()
        if not path:
            preview_data["frame"] = None
            update_preview()
            return
        try:
            if config.channels.parse_all_channels.get():
                channel = 0
            else:
                channel = config.channels.selected_channel.get()
                preview_data["frame"] = load_first_frame(path, channel)
        except Exception as e:
            print(path)
            print(f"[Preview] couldn't load first frame: {e}")
            preview_data["frame"] = None
        update_preview()

    def update_sample_file_options(*args):
        dir_path = ci.dir_path.get()
        if dir_path and os.path.isdir(dir_path):
            files = [
                os.path.join(dir, f).removeprefix(dir_path + os.path.sep)
                for dir, _, files in os.walk(dir_path)
                for f in files
                if f.lower().endswith((".tif", ".nd2"))
            ]
            sample_file_combobox["values"] = files
            sample_file_combobox.config(state="readonly")
            if files:
                cp.sample_file.set(files[0])
        else:
            sample_file_combobox.set("")
            sample_file_combobox["values"] = []
            sample_file_combobox.config(state="disabled")

    # Wire up events
    ci.file_path.trace_add("write", load_preview_frame)
    cp.sample_file.trace_add("write", load_preview_frame)
    config.channels.selected_channel.trace_add("write", load_preview_frame)
    config.channels.parse_all_channels.trace_add("write", load_preview_frame)
    cb.threshold_offset.trace_add("write", update_preview)
    ci.dir_path.trace_add("write", update_sample_file_options)

    # Initialize preview
    load_preview_frame()

    # Other binarization settings
    '''Can delete the three lines below once everything is working'''
    # tk.Label(frame, text="Frame Step (res_f_step) [min=1]:").grid(
    #     row=row_b, column=0, sticky="w", padx=5, pady=5
    # )
    frame_step_label=tk.Label(frame, text="Frame Step (res_f_step_ [min=1]):")
    frame_step_label.grid(row=row_b, column=0, sticky="w", padx=5, pady=5)

    res_f_step_spin = ttk.Spinbox(
        frame, from_=1, to=100, increment=1, textvariable=cb.frame_step, width=7
    )
    res_f_step_spin.grid(row=row_b, column=1, padx=5, pady=5)

    # Add popup for frame step
    create_popup(frame, "Changes interval (in frames) between binarized frames. Affects speed of program, with larger intervals decreasing program" \
    "runtime.", row_b, frame_step_label)

    row_b += 1

    pf_start_label = tk.Label(frame, text="Frame Start Percent (pf_start 0.5-0.9):")
    pf_start_label.grid(row=row_b, column=0, sticky="w", padx=5, pady=5)

    pf_start_spin = ttk.Spinbox(
        frame,
        from_=0.5,
        to=0.9,
        increment=0.05,
        textvariable=cb.frame_start_percent,
        format="%.2f",
        width=7,
    )
    pf_start_spin.grid(row=row_b, column=1, padx=5, pady=5)

    create_popup(frame, "Change window over which binarization metrics are calculated. By default, BARCODE compares metrics from the first 5 percent of the" \
    "video to the last 10 percent of the video, calculating percentage change. Changing Frame Start Percent and Frame Stop Percent allows shifting and scaling" \
    "of the second portion to narrow in on smaller periods or investigate behavior at earlier periods. Frame Start determines beginning of second portion.", 
    row_b, pf_start_label)

    row_b += 1

    pf_stop_label=tk.Label(frame, text="Frame Stop Percent (pf_stop 0.9-1.0):")
    pf_stop_label.grid(row=row_b, column=0, sticky="w", padx=5, pady=5)

    pf_stop_spin = ttk.Spinbox(
        frame,
        from_=0.9,
        to=1.0,
        increment=0.05,
        textvariable=cb.frame_stop_percent,
        format="%.2f",
        width=7,
    )
    pf_stop_spin.grid(row=row_b, column=1, padx=5, pady=5)

    #Add popup for frame stop percent
    create_popup(frame, "Change window over which binarization metrics are calculated. By default, BARCODE compares metrics for the first 5 percent of the" \
    "video to the last 10 percent of the video, calculating percent change. Changing Frame Start Percent and Frame Stop Percent allows shifting and scaling" \
    "of the second portion to narrow in on smaller periods or investigate behavior at earlier periods. Frame Stop determines end of second portion.", row_b, 
    pf_stop_label)

    return frame
