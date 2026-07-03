import tkinter as tk
from tkinter import ttk
import os, threading
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils.gui import create_popup, save_preview_image, save_preview_video, os_right_click
from utils.intensity_distribution import histogram, mean
from gui.config import BarcodeConfigGUI, PreviewConfigGUI, InputConfigGUI

def create_processing_worker(parent, config: BarcodeConfigGUI, preview_config: PreviewConfigGUI):
    def worker():
        try:
            save_preview_video(config = config, preview_config = preview_config, rds_type = "Intensity_Distribution")
        except Exception as e:
                print(f"Error during processing: {e}")
    return worker

def create_intensity_frame(parent, config: BarcodeConfigGUI, preview_config: PreviewConfigGUI, input_config: InputConfigGUI):
    cd = config.intensity_distribution_parameters
    cp = preview_config
    ci = input_config
    frame = ttk.Frame(parent)
    def save_video_threads():
        worker = create_processing_worker(parent, config, preview_config)
        threading.Thread(target=worker, daemon=True).start()
    menu = tk.Menu(frame, tearoff=0)
    menu.add_command(label="Save Frame", command = lambda: save_preview_image(preview_config, config, "Intensity_Distribution"))
    menu.add_command(label="Save All Frames as Video", command = save_video_threads)
    def menu_popup(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    row_c = 0 

    dist_bins_label = tk.Label(frame, text="Distribution Number of Bins")
    dist_bins_label.grid(row=row_c, column=0, sticky="w", padx=5, pady=5)
    pf_eval_spin = ttk.Spinbox(
        frame, from_=100, to=500,
        increment=1,
        textvariable=cd.bin_size,
        width=7
    )
    pf_eval_spin.grid(row=row_c, column=1, padx=5, pady=5)
    create_popup(frame, "Controls the number of bins in histogram; increasing/decreasing the number of bins may result in binning artifacts that affect accuracy of intensity distribution", row_c, dist_bins_label)
    row_c += 1

    dist_thresh_label = tk.Label(frame, text="Distribution Noise Threshold")
    dist_thresh_label.grid(row=row_c, column=0, sticky="w", padx=5, pady=5)
    pf_eval_spin = ttk.Spinbox(
        frame, from_=1e-5, to=1e-2,
        increment=1e-5,
        textvariable=cd.noise_threshold,
        format="%.5f",
        width=7
    )
    pf_eval_spin.grid(row=row_c, column=1, padx=5, pady=5)
    create_popup(frame, "Controls the minimum normalized probability in the intensity distribution; increasing/decreasing this will affect the sensitivity of the metrics to noise", row_c, dist_thresh_label)
    row_c += 1

    frame_number_label = tk.Label(frame, text="Preview Frame Number:")
    frame_number_label.grid(
        row=row_c, column = 0, sticky="w", padx=5, pady=5
    )

    preview_frame = tk.Frame(frame)
    preview_frame.columnconfigure(0, weight=0)
    for c in range(1, 10):
        preview_frame.columnconfigure(c, weight=1)
    preview_frame.columnconfigure(10, weight=0)
    preview_frame.grid(row=row_c, column=1, padx=5, pady=5, sticky="ew")
    
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
    row_c += 1

        # Sample file selection
    tk.Label(frame, text="Choose image from folder for preview:").grid(
        row=row_c, column=0, sticky="w", padx=5, pady=5
    )
    sample_file_combobox = ttk.Combobox(
        frame, textvariable=cp.sample_file, state="disabled", width=30
    )
    sample_file_combobox.grid(row=row_c, column=1, padx=5, pady=5)
    row_c += 1

    ## Intensity Distribution Live Preview ##    
    preview_title = tk.Label(frame, text="Intensity Distribution Dynamic Preview")
    preview_title.grid(
        row=row_c, column=0, columnspan=2, sticky="w", padx=5, pady=(10,2)
    )
    row_c += 1

    # Preview labels
    tk.Label(frame, text="Intensity Distribution").grid(
        row = row_c, column = 0, padx = 5, pady = 2, sticky = "n"
    )
    row_c += 1

    # Matplotlib figure placeholder
    root = parent.winfo_toplevel()
    bg_name = root.cget('bg')
    r, g, b = root.winfo_rgb(bg_name)
    bg_color = (r / 65535, g / 65535, b / 65535)
    # Distribution image figure
    fig = Figure(figsize=(5, 3), facecolor=bg_color)
    ax  = fig.add_subplot(111)
    ax.set_facecolor(bg_color)
    ax.set_xlabel("Pixel Intensity Value")
    ax.set_ylabel("Probability")
    ax.grid(False)
    fig.subplots_adjust(right=0.75, bottom=0.25)

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().grid(
        row=row_c, column=0, columnspan=2, padx=5, pady=(10,5))
    fig.tight_layout()
    right_click = os_right_click(parent)

    canvas.get_tk_widget().bind(right_click, menu_popup)
    row_c += 1

    preview_label = tk.Label(
        frame,
        text="Upload a file to see the intensity distribution preview.",
        anchor='w', justify='left'
    )

    # Show preview label by default
    preview_label.grid(row=row_c, column=0, columnspan=2, padx=5, pady=(0,10), sticky="w")
    row_c += 1

    # Preview functionality
    preview_data = {"frame": None, "intensity": None}

    def update_preview(*_args):
        frame_dist = preview_data["frame"]
        if frame_dist is None:
            preview_label.grid()
            ax.clear()
            ax.set_facecolor(bg_color)
            ax.axis("off")
            canvas.draw()
            preview_label.config(
                image="", text="Upload file to see intensity distribution preview."
            )
            return

        preview_label.grid_remove()
        
        try:
            bin_number = cd.bin_size.get()
            noise_threshold = cd.noise_threshold.get()
        except tk.TclError as e:
            bin_number = 300
            noise_threshold = 5e-4
        dist_count, dist_intensities = histogram(frame_dist, bin_number, noise_threshold)
        initial_mean = mean(dist_intensities, dist_count)
        ax.clear()
        ax.scatter(dist_intensities, dist_count, marker='^', s=4, c='purple', alpha=0.6, label = "Intensity Distribution")
        ax.axvline(x=initial_mean, ms = 4, c = 'purple', alpha=1, label="Mean Intensity")
        ax.axhline(0, color='dimgray', alpha=0.6)
        ax.set_xlabel("Pixel intensity value")
        ax.set_ylabel("Probability")
        ax.set_yscale('log')
        ax.set_xlim(0, preview_data["intensity"] * 1.05)
        ax.set_ylim(0.9 * noise_threshold, 1)
        ax.legend(loc=0, bbox_to_anchor=(1.02, 0.5), borderaxespad=0.0, frameon=False, fontsize = 'x-small')
        fig.tight_layout()
        canvas.draw()

    def load_preview_frame(*args):
        # Load first frame of selected file
        if ci.mode.get() == "dir":
            path = cp.sample_file.get()
            if not path:
                preview_data.update({"frame": None, "intensity": None})
                update_preview()
                return
        else:
            path = ci.file_path.get()
            cp.sample_file.set(path)
        if not path:
            preview_data.update({"frame": None, "intensity": None})
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
            max_intensity = np.max(frame_data[:,:,:,channel])
            preview_data.update({"frame": frame_data[sample_preview_frame,:,:,channel], "intensity": max_intensity})
        except Exception as e:
            print("Intensity", path)
            print(f"[Preview] couldn't load first frame: {e}")
            preview_data["frame"].update({"frame": None, "intensity": None})
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

    ci.file_path.trace_add("write", load_preview_frame)
    cp.sample_file.trace_add("write", load_preview_frame)
    config.channels.selected_channel.trace_add("write", load_preview_frame)
    config.channels.parse_all_channels.trace_add("write", load_preview_frame)
    cd.bin_size.trace_add("write", update_preview)
    cd.noise_threshold.trace_add("write", update_preview)
    ci.dir_path.trace_add("write", update_sample_file_options)
    cp.preview_frame_number.trace_add("write", load_preview_frame)

    row_c += 1

    frame_step_label = tk.Label(frame, text="Frame Step")
    frame_step_label.grid(row=row_c, column=0, sticky="w", padx=5, pady=5)
    f_step_spin = ttk.Spinbox(
        frame,
        from_=1, to=100,
        increment=1,
        textvariable=cd.frame_step,
        width=7
    )
    f_step_spin.grid(row=row_c, column=1, padx=5, pady=5)
    create_popup(frame, "Changes interval (in frames) between frames used for intensity distribution analysis. Affects speed of program, with larger intervals decreasing program" \
    " runtime.", row_c, frame_step_label)
    row_c += 1

    frame_fraction_label = tk.Label(frame, text="Fraction of Frames Evaluated (0.01–0.25)")
    frame_fraction_label.grid(row=row_c, column=0, sticky="w", padx=5, pady=5)
    pf_eval_spin = ttk.Spinbox(
        frame, from_=0.01, to=0.25,
        increment=0.01,
        textvariable=cd.percentage_frames_evaluated,
        format="%.2f",
        width=7
    )
    pf_eval_spin.grid(row=row_c, column=1, padx=5, pady=5)
    create_popup(frame, "Used for determining frames for averaging in calculation of initial maximum island area and maximum island/void area change; not used for calculation of maximum island/void area; decreasing this results in fewer frames being used for these averages, at the cost of more sensitivity to noise", row_c, frame_fraction_label)
    row_c += 1

    return frame