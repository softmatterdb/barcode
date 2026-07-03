import os, threading

import tkinter as tk
from tkinter import ttk, filedialog

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import matplotlib.pyplot as plt
plt.style.use('utils/presentation.mplstyle')
from gui.config import PreviewConfigGUI, InputConfigGUI, BarcodeConfigGUI
from utils.binarization import binarize, invert_frame
from utils.gui import create_popup, create_option_section, save_preview_image, save_preview_video, os_right_click

def create_processing_worker(parent, config: BarcodeConfigGUI, preview_config: PreviewConfigGUI):
    def worker():
        try:
            save_preview_video(preview_config = preview_config, barcode_config = config, rds_type = "Image_Binarization")
        except Exception as e:
            print(f"Error during processing: {e}")
    return worker

def create_binarization_frame(
    parent,
    config: BarcodeConfigGUI,
    preview_config: PreviewConfigGUI,
    input_config: InputConfigGUI,
):
    """Create the binarization settings tab with live preview"""
    frame = ttk.Frame(parent)
    def save_video_threads():
        worker = create_processing_worker(parent, config, preview_config)
        threading.Thread(target=worker, daemon=True).start()
    menu = tk.Menu(frame, tearoff=0)
    menu.add_command(label="Save Frame", command = lambda: save_preview_image(preview_config, config, "Image_Binarization"))
    menu.add_command(label="Save All Frames as Video", command = save_video_threads)
    def menu_popup(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # Access config variables directly
    cb = config.image_binarization_parameters
    cp = preview_config
    ci = input_config

    row_b = 0

    create_option_section(
        frame, 
        row_b, 
        cb.enable_physical_units, 
        "Output Unit Conversion", 
        "Convert island and void sizes from percentage of FOV to real units of square microns -- uses micron-pixel ratio in Execution Settings or ND2 metadata."
    )
    row_b += 1

    create_option_section(
        frame,
        row_b,
        cb.invert_binarization,
        "Invert Binarization",
        "Invert the binarized image"
    )
    row_b += 1


    # Binarization Threshold with scale
    threshold_label = tk.Label(frame, text="Binarization Threshold:")
    threshold_label.grid(
        row=row_b, column=0, sticky="w", padx=5, pady=5
    )
    create_popup(frame, "Changes cutoff threshold for binarization. Decreasing threshold can increase noise, while increasing threshold can lead to lost" \
    "features. Use viewer to determine optimal value for sample.", row_b, threshold_label)

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
        resolution=0.025,
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
            max(cb.threshold_offset.get() - 0.025, -1.00)
        ),
    )
    decrease_btn.grid(row=0, column=0, padx=(0, 2), pady=(15, 0))

    increase_btn = tk.Button(
        scale_frame,
        text="▶",
        width=2,
        command=lambda: cb.threshold_offset.set(
            min(cb.threshold_offset.get() + 0.025, 1.00)
        ),
    )
    increase_btn.grid(row=0, column=10, padx=(2, 0), pady=(15, 0))

    # Tick marks
    tick_values = [round(-1.00 + i * 0.25, 2) for i in range(9)]
    for i, val in enumerate(tick_values):
        lbl = tk.Label(scale_frame, text=f"{val:.3f}")
        lbl.grid(row=1, column=i + 1, sticky="n")
    row_b += 1

    binning_label = tk.Label(frame, text="Binning Ratio:")
    binning_label.grid(
        row=row_b, column = 0, sticky="w", padx=5, pady=5
    )
    binning_menu = ttk.Combobox(
        frame,
        textvariable=cb.bin_factor,
        values=[1, 2, 4, 8],
        width=5,
        state="readonly"  # force selection from list
    )
    binning_menu.grid(row = row_b, column=1, padx=5, pady=5)

    row_b += 1
    
    neighbor_fraction_label = tk.Label(frame, text="Fraction of Neighboring Islands")
    neighbor_fraction_label.grid(
        row=row_b, column = 0, sticky="w", padx=5, pady=5
    )
    neighbor_fraction_menu = ttk.Spinbox(
        frame, from_=0.05, to=1, increment=0.05, textvariable=cb.neighbor_island_fraction, width=7
    )
    neighbor_fraction_menu.grid(
        row = row_b, column = 1, sticky="w", padx=5, pady=5
    )
    row_b += 1

    minimum_island_label = tk.Label(frame, text="Minimum Island Size")
    minimum_island_label.grid(
        row = row_b, column = 0, sticky = "w", padx = 5, pady = 5
    )
    minimum_island_menu = ttk.Spinbox(
        frame, from_=1, to=100, increment = 1, textvariable=cb.minimum_island_size, width=7
    )
    minimum_island_menu.grid(
        row = row_b, column = 1, sticky="w", padx=5, pady=5
    )
    row_b += 1

    frame_number_label = tk.Label(frame, text="Preview Frame Number:")
    frame_number_label.grid(
        row=row_b, column = 0, sticky="w", padx=5, pady=5
    )

    preview_frame = tk.Frame(frame)
    preview_frame.columnconfigure(0, weight=0)
    for c in range(1, 10):
        preview_frame.columnconfigure(c, weight=1)
    preview_frame.columnconfigure(10, weight=0)
    preview_frame.grid(row=row_b, column=1, padx=5, pady=5, sticky="ew")
    
    frame_number_menu = tk.Scale(
        preview_frame,
        from_=0,
        to=len(cp.sample_preview) - 1,
        resolution=1,
        orient="horizontal",
        variable=cp.preview_frame_number,
        length=300,
        showvalue=True,
    )
    frame_number_menu.grid(row = 0, column=1, columnspan = 9, sticky="ew")

    frame_decrease_btn = tk.Button(
        preview_frame,
        text="◀",
        width=2,
        command=lambda: cp.preview_frame_number.set(
            max(cp.preview_frame_number.get() - 1, -1 * len(cp.sample_preview))
        ),
    )
    frame_decrease_btn.grid(row=0, column=0, padx=(0, 2), pady=(15, 0))

    frame_increase_btn = tk.Button(
        preview_frame,
        text="▶",
        width=2,
        command=lambda: cp.preview_frame_number.set(
            min(cp.preview_frame_number.get() + 1, len(cp.sample_preview) - 1)
        ),
    )
    frame_increase_btn.grid(row=0, column=10, padx=(2, 0), pady=(15, 0))
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

    ## Image Binarization Live Preview ##
    preview_title = tk.Label(frame, text="Image Binarization Dynamic Preview")
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

    # Matplotlib figure placeholder
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
    canvas_orig.get_tk_widget().grid(
        row=row_b, column=0, padx=5, pady=(10, 5))
    im_orig = ax_orig.imshow(np.zeros((10, 10)), cmap="gray")
    fig_orig.tight_layout()

    # Binarized image figure
    fig_bin = Figure(figsize=(3, 3), facecolor=bg_color)
    ax_bin = fig_bin.add_subplot(111)
    ax_bin.set_facecolor(bg_color)
    ax_bin.axis("off")

    canvas_bin = FigureCanvasTkAgg(fig_bin, master=frame)
    canvas_bin.draw()
    canvas_bin.get_tk_widget().grid(
        row=row_b, column=1, padx=5, pady=(10, 5))
    ax_bin.imshow(np.zeros((10, 10)), cmap="gray")
    fig_bin.tight_layout()

    preview_label = tk.Label(
        frame,
        text="Upload file to see binarization threshold preview.",
        compound="center",
    )
    preview_label.grid(row=row_b, column=0, columnspan=2, padx=5, pady=(10, 5))
    row_b += 1

    right_click = os_right_click(parent)

    canvas_orig.get_tk_widget().bind(right_click, menu_popup)
    canvas_bin.get_tk_widget().bind(right_click, menu_popup)

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
        try:
            offset = cb.threshold_offset.get()
            bin_factor = cb.bin_factor.get()
            min_island_size = cb.minimum_island_size.get()
            invert_binarization = cb.invert_binarization.get()
        except tk.TclError as e:
            offset, bin_factor, min_island_size, invert_binarization = 0.1, 2, 1, False
        bin_arr = binarize(img, offset, bin_factor, min_island_size)
        if invert_binarization:
            bin_arr = invert_frame(bin_arr)
        small_bin = bin_arr[::scale, ::scale]
        ax_bin.clear()
        ax_bin.imshow(small_bin, cmap="gray", interpolation="nearest")
        ax_bin.axis("off")
        fig_bin.tight_layout()
        canvas_bin.draw()

    def load_preview_frame(*args):
        # Load first frame of selected file
        if ci.mode.get() == "dir":
            path = cp.sample_file.get()
        else:
            path = ci.file_path.get()
            cp.sample_file.set(path)
        if not path:
            preview_data["frame"] = None
            update_preview()
            return
        try:
            if config.channels.parse_all_channels.get():
                channel = 0
            else:
                channel = config.channels.selected_channel.get()
            frame_data = cp.sample_preview
            frame_number_menu.config(from_=0, to = len(frame_data) - 1)
            try:
                sample_preview_frame = cp.preview_frame_number.get()
            except tk.TclError as e:
                sample_preview_frame = 0
            preview_data["frame"] = frame_data[sample_preview_frame,:,:,channel]
        except Exception as e:
            # print(sample)
            print("Binarization", path)
            print(f"[Preview] couldn't load first frame: {e}")
            preview_data["frame"] = None
        update_preview()

    def update_sample_file_options(*args):
        dir_path = ci.dir_path.get()
        if dir_path and os.path.isdir(dir_path):
            files = [
                os.path.join(dir, f)
                for dir, _, files in os.walk(dir_path)
                for f in files
                if f.lower().endswith((".tif", ".tiff", ".nd2", ".avi", ".mp4"))
            ]
            sample_file_combobox["values"] = files

            sample_file_combobox.config(state="readonly")
            if files:
                cp.sample_file.set(files[0])
                def resize_combobox():
                    new_width = max(len(file) for file in files)  # Add some padding
                    sample_file_combobox.config(width=new_width)
                sample_file_combobox.config(postcommand=resize_combobox)
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
    cb.bin_factor.trace_add("write", update_preview)
    cp.preview_frame_number.trace_add("write", load_preview_frame)
    cb.minimum_island_size.trace_add("write", update_preview)
    cb.invert_binarization.trace_add("write", update_preview)

    # Initialize preview
    load_preview_frame()

    # Other binarization settings

    frame_step_label = tk.Label(frame, text="Frame Step:")
    frame_step_label.grid(
        row=row_b, column=0, sticky="w", padx=5, pady=5
    )
    create_popup(frame, "Changes interval (in frames) between binarized frames. Affects speed of program, with larger intervals decreasing program" \
    " runtime.", row_b, frame_step_label)
    res_f_step_spin = ttk.Spinbox(
        frame, from_=1, to=100, increment=1, textvariable=cb.frame_step, width=7
    )
    res_f_step_spin.grid(row=row_b, column=1, padx=5, pady=5)
    row_b += 1

    frame_fraction_label = tk.Label(frame, text="Fraction of Frames Evaluated (0.01–0.25):")
    frame_fraction_label.grid(
        row=row_b, column=0, sticky="w", padx=5, pady=5
    )
    create_popup(frame, "Used for determining frames for averaging in calculation of initial maximum island area and maximum island/void area change; not used for calculation of maximum island/void area; decreasing this results in fewer frames being used for these averages, at the cost of more sensitivity to noise", row_b, frame_fraction_label)
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
