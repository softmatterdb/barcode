# import tkinter as tk
# from tkinter import ttk

# from gui.config import BarcodeConfigGUI


# def create_flow_frame(parent, config: BarcodeConfigGUI):
#     """Create the optical flow settings tab"""
#     frame = ttk.Frame(parent)

#     # Access config variables directly
#     co = config.optical_flow

#     row_f = 0

#     tk.Label(frame, text="Frame Step (Minimum: 1 Frame):").grid(
#         row=row_f, column=0, sticky="w", padx=5, pady=5
#     )
#     flow_f_step_spin = ttk.Spinbox(
#         frame, from_=1, to=1000, increment=1, textvariable=co.frame_step, width=7
#     )
#     flow_f_step_spin.grid(row=row_f, column=1, padx=5, pady=5)
#     row_f += 1

#     tk.Label(frame, text="Window Size (Minimum: 1 Pixel):").grid(
#         row=row_f, column=0, sticky="w", padx=5, pady=5
#     )
#     win_size_spin = ttk.Spinbox(
#         frame, from_=1, to=1000, increment=1, textvariable=co.window_size, width=7
#     )
#     win_size_spin.grid(row=row_f, column=1, padx=5, pady=5)
#     row_f += 1

#     tk.Label(frame, text="Downsample (Minimum: 1 Pixel):").grid(
#         row=row_f, column=0, sticky="w", padx=5, pady=5
#     )
#     downsample_spin = ttk.Spinbox(
#         frame, from_=1, to=1000, increment=1, textvariable=co.downsample_factor, width=7
#     )
#     downsample_spin.grid(row=row_f, column=1, padx=5, pady=5)
#     row_f += 1

#     tk.Label(frame, text="Nanometer to Pixel Ratio [1 nm – 1 mm]:").grid(
#         row=row_f, column=0, sticky="w", padx=5, pady=5
#     )
#     nm_pixel_spin = ttk.Spinbox(
#         frame,
#         from_=1,
#         to=10**6,
#         increment=1,
#         textvariable=co.nm_pixel_ratio,
#         width=9,
#     )
#     nm_pixel_spin.grid(row=row_f, column=1, padx=5, pady=5)
#     row_f += 1

#     tk.Label(frame, text="Frame Interval [1–1000]:").grid(
#         row=row_f, column=0, sticky="w", padx=5, pady=5
#     )
#     frame_interval_spin = ttk.Spinbox(
#         frame,
#         from_=1,
#         to=10**3,
#         increment=1,
#         textvariable=co.frame_interval_s,
#         width=7,
#     )
#     frame_interval_spin.grid(row=row_f, column=1, padx=5, pady=5)

#     return frame


import os

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from analysis.flow import calculate_optical_flow

import tkinter as tk
from tkinter import ttk

from gui.config import BarcodeConfigGUI, InputConfigGUI, PreviewConfigGUI
from utils.preview_flow import load_first_frame


def create_flow_frame(
        parent, 
        config: BarcodeConfigGUI,
        preview_config: PreviewConfigGUI,
        input_config: InputConfigGUI):
    
    """Create the optical flow settings tab"""
    frame = ttk.Frame(parent)

    # Access config variables directly
    co = config.optical_flow
    cp = preview_config
    ci = input_config

    row_f = 0

    # Frame step for optical flow
    tk.Label(frame, text="Frame Step (Minimum: 1 Frame):").grid(
        row=row_f, column=0, sticky="w", padx=5, pady=5
    )
    flow_f_step_spin = ttk.Spinbox(
        frame, from_=1, to=1000, increment=1, textvariable=co.frame_step, width=7
    )
    flow_f_step_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    #Window size for optical flow
    tk.Label(frame, text="Window Size (Minimum: 1 Pixel):").grid(
        row=row_f, column=0, sticky="w", padx=5, pady=5
    )
    win_size_spin = ttk.Spinbox(
        frame, from_=1, to=1000, increment=1, textvariable=co.window_size, width=7
    )
    win_size_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    #Downsample for optical flow
    tk.Label(frame, text="Downsample (Minimum: 1 Pixel):").grid(
        row=row_f, column=0, sticky="w", padx=5, pady=5
    )
    downsample_spin = ttk.Spinbox(
        frame, from_=1, to=1000, increment=1, textvariable=co.downsample_factor, width=7
    )
    downsample_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    #Nanometer to pixel ratio for optical flow
    tk.Label(frame, text="Nanometer to Pixel Ratio [1 nm – 1 mm]:").grid(
        row=row_f, column=0, sticky="w", padx=5, pady=5
    )
    nm_pixel_spin = ttk.Spinbox(
        frame,
        from_=1,
        to=10**6,
        increment=1,
        textvariable=co.nm_pixel_ratio,
        width=9,
    )
    nm_pixel_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    # Frame interval for optical flow
    tk.Label(frame, text="Frame Interval [1–1000]:").grid(
        row=row_f, column=0, sticky="w", padx=5, pady=5
    )
    frame_interval_spin = ttk.Spinbox(
        frame,
        from_=1,
        to=10**3,
        increment=1,
        textvariable=co.frame_interval_s,
        width=7,
    )
    frame_interval_spin.grid(row=row_f, column=1, padx=5, pady=5)

    # Sample file selection for preview
    tk.Label(frame, text="Choose image from folder for preview:").grid(
        row=row_f, column=0, sticky="w", padx=5, pady=5
    )
    sample_file_combobox = ttk.Combobox(
        frame, textvariable=cp.sample_file, state="disabled", width=30
    )

    sample_file_combobox.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1





    ##### Live preview setup #####

    preview_title = tk.Label(frame, text="Dynamic preview of first frames optical flow:")
    preview_title.grid(
        row=row_f, column=0, columnspan=2, padx=5, pady=(10, 2), sticky="w"
    )
    row_f += 1

    # Preview label
    tk.Label(frame, text="Optical Flow Field").grid(
        row=row_f, column=0, columnspan=2, padx=5, pady=5, sticky="n"
    )

    row_f += 1

    # Get background color for matplotlib figures
    root = parent.winfo_toplevel()
    bg_name = root.cget("bg")
    r, g, b = root.winfo_rgb(bg_name)
    bg_color = (r / 65535, g / 65535, b / 65535)

    # Optical flow field image figure
    fig_flow = Figure(figsize=(3, 3), facecolor=bg_color)
    ax_flow = fig_flow.add_subplot(111)
    ax_flow.set_facecolor(bg_color)
    ax_flow.axis("off")
    # ax_flow.imshow(np.zeros((10, 10)), cmap="gray")  # move this before draw

    canvas_flow = FigureCanvasTkAgg(fig_flow, master=frame)
    canvas_flow.draw()
    canvas_flow.get_tk_widget().grid(
        row=row_f, column=0, columnspan=2, padx=0, pady=(10, 5)
    )

    fig_flow.tight_layout()


    # This is the label that exists when there is no file yet selected
    preview_label = tk.Label(
        frame,
        text="Upload file to see optical flow field preview.",
        compound="center",
    )
    preview_label.grid(row=row_f, column=0, columnspan=2, padx=5, pady=(10, 5))
    row_f += 1

    # Preview functionality
    # Preview functionality
    preview_data = {"frame": None}

    def update_preview(*args):
        img = preview_data["frame"]
        if img is None:
            preview_label.grid()
            ax_flow.clear()
            ax_flow.set_facecolor(bg_color)
            ax_flow.axis("off")
            canvas_flow.draw()
            preview_label.config(
                image="", text="Upload file to see optical flow field preview."
            )
            return

        preview_label.grid_remove()

        # Set scale factor
        h, w = img.shape
        max_px = 300
        scale = max(1, int(max(h, w) / max_px) + 1)

        # Show down-sampled original

        # Show down-sampled binarized
        if img.ndim == 3 and img.shape[0] >= 2:
            images = img  # shape: (frames, height, width)
            frame_pair = (0, 1)
        else:
            # If only one frame, duplicate it (no flow, but avoids crash)
            images = np.stack([img, img])
            frame_pair = (0, 1)

        opt_config = co.config  # Get OpticalFlowConfig from GUI

        try:
            # print("hi")
            flow_output, flow_stats = calculate_optical_flow(images, frame_pair, opt_config)
            downU, downV, directions, speed = flow_output
            # Downsample for preview
            small_dir = directions[::scale, ::scale]
            ax_flow.clear()
            ax_flow.imshow(small_dir, cmap="hsv", interpolation="nearest")
            ax_flow.axis("off")
            fig_flow.tight_layout()
            canvas_flow.draw()
        except Exception as e:
            preview_label.grid()
            ax_flow.clear()
            ax_flow.set_facecolor(bg_color)
            ax_flow.axis("off")
            canvas_flow.draw()
            preview_label.config(
                image="", text=f"Error computing optical flow: {e}"
            )        
   

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


    #Live preview setup
    #preview_title = tk.Label(frame, text="Dynamic preview of first frames optical flow:")
    #preview_title.grid(
    #   row=row_f, column=0, columnspan=2, padx=5, pady=(10, 2), sticky="w"
    #)
    row_f += 1

    # Wire up events
    ci.file_path.trace_add("write", load_preview_frame)
    cp.sample_file.trace_add("write", load_preview_frame)
    config.channels.selected_channel.trace_add("write", load_preview_frame)
    config.channels.parse_all_channels.trace_add("write", load_preview_frame)
    co.frame_step.trace_add("write", update_preview)
    co.window_size.trace_add("write", update_preview)
    co.downsample_factor.trace_add("write", update_preview)
    co.nm_pixel_ratio.trace_add("write", update_preview)
    co.frame_interval_s.trace_add("write", update_preview)
    ci.dir_path.trace_add("write", update_sample_file_options)

    return frame