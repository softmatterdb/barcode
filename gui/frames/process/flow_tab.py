import os, threading
from typing import Tuple, TypeAlias
import cv2 as cv
import numpy as np
import matplotlib.ticker as ticker
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, filedialog

import matplotlib.pyplot as plt
plt.style.use('utils/presentation.mplstyle')
from utils import groupAvg
from utils.gui import create_popup, save_preview_image, save_preview_video, os_right_click
from gui.config import BarcodeConfigGUI, InputConfigGUI, PreviewConfigGUI, ReaderConfigGUI, OpticalFlowConfigGUI
FramePair: TypeAlias = Tuple[int, int]

def calculate_optical_flow(video: np.ndarray, frame_pair: tuple[int, int], 
                           flow_config: OpticalFlowConfigGUI, in_config: ReaderConfigGUI):
    win_size = flow_config.win_size.get()
    downsample = flow_config.downsample.get()
    exposure_time = in_config.exposure_time.get()
    um_pix_ratio = in_config.um_pixel_ratio.get()
    start, stop = frame_pair
    flow = cv.calcOpticalFlowFarneback(video[start], video[stop], None, 0.5, 3, win_size, 3, 5, 1.2, 0)
    flow_reduced = groupAvg(flow, downsample)
    downU = flow_reduced[:,:,0]
    downV = flow_reduced[:,:,1]
    # Conversion: px/interval * interval/frame * 1/(sec/frame) * um/px
    downU = np.flipud(downU)* 1/(exposure_time) * 1/(stop - start) * um_pix_ratio
    downV = -1 * np.flipud(downV)* 1/(exposure_time) * 1/(stop - start) * um_pix_ratio
    
    speed = (downU ** 2 + downV ** 2) ** (1/2)
    direction = np.arctan2(downV, downU)
    flow_field = [downU, downV, direction, speed]
    return flow_field

def create_processing_worker(parent, config: BarcodeConfigGUI, preview_config: PreviewConfigGUI):
    def worker():
        try:
            save_preview_video(config = config, preview_config = preview_config, rds_type = "Optical_Flow")
        except Exception as e:
                print(f"Error during processing: {e}")
    return worker

def create_flow_frame(parent, config: BarcodeConfigGUI, preview_config: PreviewConfigGUI, 
                      input_config: InputConfigGUI):
    """Create the optical flow settings tab"""
    frame = ttk.Frame(parent)
    def save_video_threads():
        worker = create_processing_worker(parent, config, preview_config)
        threading.Thread(target=worker, daemon=True).start()
    menu = tk.Menu(frame, tearoff=0)
    menu.add_command(label="Save Frame", command = lambda: save_preview_image(preview_config, config, "Optical_Flow"))
    menu.add_command(label="Save All Frames as Video", command = save_video_threads)
    def menu_popup(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # Access config variables directly
    co = config.optical_flow_parameters
    ci = input_config
    cp = preview_config
    cr = config.reader

    row_f = 0
    frame_step_label = tk.Label(frame, text="Frame Step")
    frame_step_label.grid(row=row_f, column=0, sticky="w", padx=5, pady=5)
    of_f_step_spin = ttk.Spinbox(
        frame, from_=1, to=1000,
        increment=1,
        textvariable=co.frame_step,
        width=7
    )
    of_f_step_spin.grid(row=row_f, column=1, padx=5, pady=5)
    create_popup(frame, "Change interval (in frames) between frames used to calculate optical flow field. Will affect speed of program, with larger" \
    "intervals decreasing program runtime.", row_f, frame_step_label)
    row_f += 1

    win_size_label = tk.Label(frame, text="Optical Flow Window Size")
    win_size_label.grid(row=row_f, column=0, sticky="w", padx=5, pady=5)
    win_size_spin = ttk.Combobox(
        frame,
        textvariable=co.win_size,
        values=[4, 8, 16, 32],
        width=7,
    )
    win_size_spin.grid(row=row_f, column=1, padx=5, pady=5)
    create_popup(frame, "Define size of region around each pixel used to calculate optical flow field. Larger window sizes result in less noise, but" \
    "blurrier motion fields. Smaller window sizes detect smaller movement within the material, but are more susceptible to random noise.", row_f, 
    win_size_label)
    row_f += 1

    downsample_label = tk.Label(frame, text="Downsample/Binning Factor")
    downsample_label.grid(row=row_f, column=0, sticky="w", padx=5, pady=5)
    downsample_spin = ttk.Combobox(
        frame,
        textvariable=co.downsample,
        values=[2, 4, 8, 16],
        width=7,
    )
    downsample_spin.grid(row=row_f, column=1, padx=5, pady=5)
    create_popup(frame, "Control interval between pixels that flow field is sampled at. Increasing downsampling reduces noise (along with precision) and" \
    "is recommended for large-scale movement of areas of material. Decreasing downsampling is recommended for movement of many smaller areas of material.",
    row_f, downsample_label)
    row_f += 1

    frame_number_label = tk.Label(frame, text="Preview Frame Number:")
    frame_number_label.grid(
        row=row_f, column = 0, sticky="w", padx=5, pady=5
    )

    preview_frame = tk.Frame(frame)
    preview_frame.columnconfigure(0, weight=0)
    for c in range(1, 10):
        preview_frame.columnconfigure(c, weight=1)
    preview_frame.columnconfigure(10, weight=0)
    preview_frame.grid(row=row_f, column=1, padx=5, pady=5, sticky="ew")
    
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
    row_f += 1

    tk.Label(frame, text="Choose image from folder for preview:").grid(
        row=row_f, column=0, sticky="w", padx=5, pady=5
    )
    sample_file_combobox = ttk.Combobox(
        frame, textvariable=cp.sample_file, state="disabled", width=30
    )

    sample_file_combobox.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    ## Optical Flow Live Preview ##
    preview_title = tk.Label(frame, text="Optical Flow Field Dynamic Preview")
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

    canvas_flow = FigureCanvasTkAgg(fig_flow, master=frame)
    canvas_flow.draw()
    canvas_flow.get_tk_widget().grid(
        row=row_f, column=0, columnspan=2, padx=0, pady=(10, 5)
    )

    fig_flow.tight_layout()
    right_click = os_right_click(parent)
    canvas_flow.get_tk_widget().bind(right_click, menu_popup)



    # This is the label that exists when there is no file yet selected
    preview_label = tk.Label(
        frame,
        text="Upload file to see optical flow field preview.",
        compound="center",
    )
    preview_label.grid(row=row_f, column=0, columnspan=2, padx=5, pady=(10, 5))
    row_f += 1

    # Preview functionality
    all_data = {"frames": np.array([])}

    def update_preview(*args):
        frames = all_data["frames"]

        if frames is None:
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

        try:
            opt_config = co.config
            preview_frame_num = cp.preview_frame_number.get()
            if preview_frame_num >= len(frames) - opt_config.frame_step:
                preview_frame_num = len(frames) - 1 - opt_config.frame_step
            first_pair = (preview_frame_num, preview_frame_num + opt_config.frame_step)
            downsample = opt_config.downsample
        except tk.TclError as e:
            first_pair = (0, 1)
            downsample = 8

        def visualize_optical_flow(ax, fig, canvas, flow_output):
            downU, downV, directions, speed = flow_output
            ax.clear()
            ax.quiver(downU, downV, color="blue")
            ticks_adj = ticker.FuncFormatter(lambda x, pos: f"{x * downsample:g}")
            ax.xaxis.set_major_formatter(ticks_adj)
            ax.yaxis.set_major_formatter(ticks_adj)
            ax.set_aspect(aspect=1, adjustable="box")
            fig_flow.tight_layout()
            canvas_flow.draw()

        try:
            flow_output = calculate_optical_flow(frames, first_pair, co, cr)
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

    def load_all_frames(*args):
        # access from outer closure or global
        if ci.mode.get() == "dir":
            path = cp.sample_file.get()
            if not path:
                all_data["frames"] = []
                update_preview()
                return
        else:
            path = ci.file_path.get()
            cp.sample_file.set(path)

        if not path:
            all_data["frames"] = []
            update_preview()
            return

        try:
            if config.channels.parse_all_channels.get():
                channel = 0
            else:
                channel = config.channels.selected_channel.get()
            frame_data = cp.sample_preview
            frame_number_menu.config(from_=0, to = len(frame_data) - 1)
            
            all_data["frames"] = frame_data[:,:,:,channel]  # delegate to core logic
        except Exception as e:
            print("Flow", path)
            print(f"[Preview] couldn't load all frames: {e}")
            all_data["frames"] = []

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

    row_f += 1

    # Wire up events
    ci.file_path.trace_add("write", load_all_frames)
    cp.sample_file.trace_add("write", load_all_frames)
    config.channels.selected_channel.trace_add("write", load_all_frames)
    config.channels.parse_all_channels.trace_add("write", load_all_frames)
    co.frame_step.trace_add("write", update_preview)
    co.win_size.trace_add("write", update_preview)
    co.downsample.trace_add("write", update_preview)
    ci.dir_path.trace_add("write", update_sample_file_options)
    cp.preview_frame_number.trace_add("write", update_preview)

    frame_fraction_label = tk.Label(frame, text="Fraction of Frames Evaluated (0.01–0.25)")
    frame_fraction_label.grid(row=row_f, column=0, sticky="w", padx=5, pady=5)
    of_pf_eval_spin = ttk.Spinbox(
        frame, from_=0.01, to=0.25,
        increment=0.01,
        textvariable=co.percentage_frames_evaluated,
        format="%.2f",
        width=7
    )
    of_pf_eval_spin.grid(row=row_f, column=1, padx=5, pady=5)
    create_popup(frame, "Used for determining frames for averaging in calculation of speed change; not used for calculation of other optical flow metrics; decreasing this results in fewer frames being used for these averages, at the cost of more sensitivity to noise", row_f, frame_fraction_label)

    return frame