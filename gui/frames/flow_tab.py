import os
from typing import Tuple, TypeAlias

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as ticker

from analysis.flow import calculate_optical_flow, calculate_frame_pairs

import tkinter as tk
from tkinter import ttk

from gui.config import BarcodeConfigGUI, InputConfigGUI, PreviewConfigGUI
from utils.preview_flow import read_all_frames

FramePair: TypeAlias = Tuple[int, int]

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
    all_data = {"frames": []}

    def update_preview(*args):
        frames = all_data["frames"]

        if frames is None:
            print("THERE ARE NOT FRAMES")
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

        # first_frame = frames[0]

        # # Set scale factor
        # h, w = first_frame.shape
        # max_px = 300
        # scale = max(1, int(max(h, w) / max_px) + 1)

        opt_config = co.config
        first_pair = (0, opt_config.frame_step)
        # print(opt_config)

        # if first_frame.ndim == 3 and first_frame.shape[0] >= 2:
        #     images = first_frame  # shape: (frames, height, width)
        #     # frame_pairs = calculate_frame_pairs(len(images), opt_config.frame_step)
        #     first_pair = (0, opt_config.frame_step)
        #     print(first_pair)
        # else:
        #     images = np.stack([first_frame, first_frame])
        #     # frame_pairs = calculate_frame_pairs(len(images), opt_config.frame_step)
        #     # first_pair = frame_pairs[0]
        #     first_pair = (0, opt_config.frame_step)
        #     print(first_pair)

        def visualize_optical_flow(ax, fig, canvas, flow_output):
            downU, downV, directions, speed = flow_output
            
            ax.clear()
            ax.quiver(downU, downV, color="blue")
            ticks_adj = ticker.FuncFormatter(lambda x, pos: f"{x * opt_config.downsample_factor:g}")
            ax.xaxis.set_major_formatter(ticks_adj)
            ax.yaxis.set_major_formatter(ticks_adj)
            ax.set_aspect(aspect=1, adjustable="box")
            fig_flow.tight_layout()
            canvas_flow.draw()


        try:
            # print("hi")
            flow_output, flow_stats = calculate_optical_flow(frames, first_pair, opt_config)
            visualize_optical_flow(ax_flow, fig_flow, canvas_flow, flow_output)
        except Exception as e:
            preview_label.grid()
            ax_flow.clear()
            ax_flow.set_facecolor(bg_color)
            ax_flow.axis("off")
            canvas_flow.draw()
            preview_label.config(
                image="", text=f"Error computing optical flow: {e}"
            )        
   

    # def load_all_frames(*args):
    #     # Load first frame of selected file
    #     if ci.mode.get() == "dir":
    #         dir_path = ci.dir_path.get()
    #         sample = cp.sample_file.get()
    #         if not dir_path or not sample:
    #             preview_data["frame"] = None
    #             update_preview()
    #             return
    #         path = os.path.join(dir_path, sample)
    #     else:
    #         path = ci.file_path.get()
    #     if not path:
    #         preview_data["frame"] = None
    #         update_preview()
    #         return
    #     try:
    #         if config.channels.parse_all_channels.get():
    #             channel = 0
    #         else:
    #             channel = config.channels.selected_channel.get()
    #             preview_data["frame"] = load_first_frame(path, channel)
    #     except Exception as e:
    #         print(path)
    #         print(f"[Preview] couldn't load first frame: {e}")
    #         preview_data["frame"] = None
    #     update_preview()

    def load_all_frames(*args):
        # access from outer closure or global
        if ci.mode.get() == "dir":
            dir_path = ci.dir_path.get()
            sample = cp.sample_file.get()
            if not dir_path or not sample:
                all_data["frames"] = []
                update_preview()
                return
            path = os.path.join(dir_path, sample)
        else:
            path = ci.file_path.get()

        if not path:
            all_data["frames"] = []
            update_preview()
            return

        try:
            if config.channels.parse_all_channels.get():
                channel = 0
            else:
                channel = config.channels.selected_channel.get()

            all_data["frames"] = read_all_frames(path, channel)  # delegate to core logic
            # print("frames: ", frames)
        except Exception as e:
            print(f"[Preview] couldn't load all frames: {e}")
            all_data["frames"] = []

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
    ci.file_path.trace_add("write", load_all_frames)
    cp.sample_file.trace_add("write", load_all_frames)
    config.channels.selected_channel.trace_add("write", load_all_frames)
    config.channels.parse_all_channels.trace_add("write", load_all_frames)
    co.frame_step.trace_add("write", update_preview)
    co.window_size.trace_add("write", update_preview)
    co.downsample_factor.trace_add("write", update_preview)
    co.nm_pixel_ratio.trace_add("write", update_preview)
    co.frame_interval_s.trace_add("write", update_preview)
    ci.dir_path.trace_add("write", update_sample_file_options)

    return frame