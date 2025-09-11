import tkinter as tk
from tkinter import ttk
import os
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils.preview import load_intensity_frames
from utils.intensity_distribution import histogram, mean
from gui.config import BarcodeConfigGUI, PreviewConfigGUI, InputConfigGUI

def create_intensity_frame(parent, config: BarcodeConfigGUI, preview_config: PreviewConfigGUI, input_config: InputConfigGUI):
    cd = config.intensity_distribution_parameters
    cp = preview_config
    ci = input_config
    frame = ttk.Frame(parent)
    row_c = 0 

    tk.Label(frame, text="Distribution Number of Bins").grid(row=row_c, column=0, sticky="w", padx=5, pady=5)
    pf_eval_spin = ttk.Spinbox(
        frame, from_=100, to=500,
        increment=1,
        textvariable=cd.bin_size,
        width=7
    )
    pf_eval_spin.grid(row=row_c, column=1, padx=5, pady=5)
    row_c += 1

    tk.Label(frame, text="Distribution Noise Threshold").grid(row=row_c, column=0, sticky="w", padx=5, pady=5)
    pf_eval_spin = ttk.Spinbox(
        frame, from_=1e-5, to=1e-2,
        increment=1e-5,
        textvariable=cd.noise_threshold,
        format="%.5f",
        width=7
    )
    pf_eval_spin.grid(row=row_c, column=1, padx=5, pady=5)
    row_c += 1

        # Sample file selection
    tk.Label(frame, text="Choose image from folder for preview:").grid(
        row=row_c, column=0, sticky="w", padx=5, pady=5
    )
    sample_file_combobox = ttk.Combobox(
        frame, textvariable=cp.sample_file, state="disabled", width=30
    )
    sample_file_combobox.grid(row=row_c, column=1, padx=5, pady=5)
    
    # Intensity distribution live preview 
    row_c += 1
    tk.Label(frame, text="Intensity Distribution Preview (First vs Last Frame)").grid(
        row=row_c, column=0, columnspan=2, sticky="w", padx=5, pady=(10,2)
    )
    row_c += 1

    # Matplotlib figure placeholder
    root = parent.winfo_toplevel()
    bg_name = root.cget('bg')
    r, g, b = root.winfo_rgb(bg_name)
    bg_color = (r/65535, g/65535, b/65535)

    fig = Figure(figsize=(6, 3.5), facecolor=bg_color)
    ax  = fig.add_subplot(111)
    ax.set_facecolor(bg_color)
    ax.set_xlabel("Pixel intensity value")
    ax.set_ylabel("Probability")
    ax.grid(False)
    fig.subplots_adjust(right=0.75, bottom=0.25)

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas_widget = canvas.get_tk_widget()

    _canvas_grid = dict(row=row_c, column=0, columnspan=2, padx=5, pady=(5,10), sticky="w")
    row_c += 1

    preview_label = tk.Label(
        frame,
        text="Upload a file to see the intensity distribution preview.",
        anchor='w', justify='left'
    )

    # Show preview label by default
    preview_label.grid(row=row_c, column=0, columnspan=2, padx=5, pady=(0,10), sticky="w")
    preview_data = {"first": None, "last": None, "last_idx": None}

    def update_preview(*_args):
        initial_frame = preview_data["first"]
        final_frame = preview_data["last"]
        if initial_frame is None or final_frame is None:
            # Show label, hide canvas
            preview_label.grid()
            try:
                canvas_widget.grid_remove()
            except Exception:
                pass

            ax.clear()
            ax.set_facecolor(bg_color)
            ax.set_xlabel("Pixel Intensity Value")
            ax.set_ylabel("Probability")
            canvas.draw()
            return

        preview_label.grid_remove()
        try:
            canvas_widget.grid(**_canvas_grid)
        except Exception:
            pass
        
        bin_number = cd.bin_size.get()
        noise_threshold = cd.noise_threshold.get()
        initial_count, initial_intensities = histogram(initial_frame, bin_number, noise_threshold)
        initial_mean = mean(initial_intensities, initial_count)
        final_count, final_intensities = histogram(final_frame, bin_number, noise_threshold)
        final_mean = mean(final_intensities, final_count)
        max_intensity = max(initial_intensities[-1], final_intensities[-1])
        ax.clear()
        ax.plot(initial_intensities, initial_count, '^-', ms=4, c='darkred', alpha=0.6, label="Frame 0 Intensity Distribution")
        last_label = f"Frame {preview_data['last_idx'] - 1}" if preview_data['last_idx'] is not None else "Last Frame"
        ax.plot(final_intensities, final_count, 'v-', ms=4, c='purple', alpha=0.6, label=f"{last_label} Intensity Distribution")
        ax.axvline(x=initial_mean, ms = 4, c = 'darkred', alpha=1, label="Frame 0 Mean")
        ax.axvline(x=final_mean, ms = 4, c = 'purple', alpha=1, label=f"Frame {last_label} Mean")
        ax.axhline(0, color='dimgray', alpha=0.6)
        ax.set_xlabel("Pixel intensity value")
        ax.set_ylabel("Probability")
        ax.set_yscale('log')
        ax.set_xlim(0,max_intensity)
        ax.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), borderaxespad=0.0, frameon=False)
        canvas.draw()

    def load_preview_frame(*args):
        # Load first frame of selected file
        if ci.mode.get() == "dir":
            dir_path = ci.dir_path.get()
            sample = cp.sample_file.get()
            if not dir_path or not sample:
                preview_data.update({"first": None, "last": None, "last_idx": None})
                update_preview()
                return
            path = os.path.join(dir_path, sample)
        else:
            path = ci.file_path.get()
        if not path:
            preview_data.update({"first": None, "last": None, "last_idx": None})
            update_preview()
            return
        try:
            if config.channels.parse_all_channels.get():
                channel = 0
            else:
                channel = config.channels.selected_channel.get()
            first_frame, last_frame, num_frames = load_intensity_frames(path, channel)
            preview_data.update({"first": first_frame, "last": last_frame, "last_idx": num_frames})
        except Exception as e:
            print(path)
            print(f"[Preview] couldn't load first frame: {e}")
            preview_data.update({"first": None, "last": None, "last_idx": None})
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

    ci.file_path.trace_add("write", load_preview_frame)
    cp.sample_file.trace_add("write", load_preview_frame)
    config.channels.selected_channel.trace_add("write", load_preview_frame)
    config.channels.parse_all_channels.trace_add("write", load_preview_frame)
    cd.bin_size.trace_add("write", update_preview)
    cd.noise_threshold.trace_add("write", update_preview)
    ci.dir_path.trace_add("write", update_sample_file_options)


    tk.Label(frame, text="Frame Step").grid(row=row_c, column=0, sticky="w", padx=5, pady=5)
    f_step_spin = ttk.Spinbox(
        frame,
        from_=1, to=100,
        increment=1,
        textvariable=cd.frame_step,
        width=7
    )
    f_step_spin.grid(row=row_c, column=1, padx=5, pady=5)
    row_c += 1

    tk.Label(frame, text="Fraction of Frames Evaluated (0.01–0.25)").grid(row=row_c, column=0, sticky="w", padx=5, pady=5)
    pf_eval_spin = ttk.Spinbox(
        frame, from_=0.01, to=0.25,
        increment=0.01,
        textvariable=cd.percentage_frames_evaluated,
        format="%.2f",
        width=7
    )
    pf_eval_spin.grid(row=row_c, column=1, padx=5, pady=5)
    row_c += 1

    return frame