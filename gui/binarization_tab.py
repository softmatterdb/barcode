import os

import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui.config import PreviewConfigGUI, InputConfigGUI, BarcodeConfigGUI
from utils.preview import load_binarization_frame, binarize

def create_binarization_frame(
    parent,
    config: BarcodeConfigGUI,
    preview_config: PreviewConfigGUI,
    input_config: InputConfigGUI,
):
    """Create the binarization settings tab with live preview"""
    frame = ttk.Frame(parent)

    # Access config variables directly
    cb = config.image_binarization_parameters
    cp = preview_config
    ci = input_config

    row_b = 0

    # Binarization Threshold with scale
    tk.Label(frame, text="Binarization Threshold:").grid(
        row=row_b, column=0, sticky="w", padx=5, pady=5
    )

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
        row=row_b, column=0, columnspan=3, padx=5, pady=(10, 2), sticky="w"
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
                preview_data["frame"] = load_binarization_frame(path, channel)
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
                if f.lower().endswith((".tif", ".tiff", ".nd2"))
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

    tk.Label(frame, text="Frame Step:").grid(
        row=row_b, column=0, sticky="w", padx=5, pady=5
    )
    res_f_step_spin = ttk.Spinbox(
        frame, from_=1, to=100, increment=1, textvariable=cb.frame_step, width=7
    )
    res_f_step_spin.grid(row=row_b, column=1, padx=5, pady=5)
    row_b += 1

    tk.Label(frame, text="Fraction of Frames Evaluated (0.01–0.25):").grid(
        row=row_b, column=0, sticky="w", padx=5, pady=5
    )
    pf_start_spin = ttk.Spinbox(
        frame,
        from_=0.01,
        to=0.25,
        increment=0.01,
        textvariable=cb.percentage_frames_evaluated,
        format="%.2f",
        width=7,
    )
    pf_start_spin.grid(row=row_b, column=1, padx=5, pady=5)
    row_b += 1

    return frame
