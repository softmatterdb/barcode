import tkinter as tk
from tkinter import ttk

from gui.config import BarcodeConfigGUI

def create_flow_frame(parent, config: BarcodeConfigGUI):
    """Create the optical flow settings tab"""
    frame = ttk.Frame(parent)

    # Access config variables directly
    co = config.optical_flow_parameters

    row_f = 0
    tk.Label(frame, text="Frame Step").grid(row=row_f, column=0, sticky="w", padx=5, pady=5)
    of_f_step_spin = ttk.Spinbox(
        frame, from_=1, to=1000,
        increment=1,
        textvariable=co.frame_step,
        width=7
    )
    of_f_step_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    tk.Label(frame, text="Optical Flow Window Size").grid(row=row_f, column=0, sticky="w", padx=5, pady=5)
    win_size_spin = ttk.Spinbox(
        frame, from_=1, to=1000,
        increment=1,
        textvariable=co.win_size,
        width=7
    )
    win_size_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    tk.Label(frame, text="Downsample/Binning Factor").grid(row=row_f, column=0, sticky="w", padx=5, pady=5)
    downsample_spin = ttk.Spinbox(
        frame, from_=1, to=1000,
        increment=1,
        textvariable=co.downsample,
        width=7
    )
    downsample_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    tk.Label(frame, text="Micron to Pixel Ratio (1 nm – 1 mm)").grid(row=row_f, column=0, sticky="w", padx=5, pady=5)
    um_pixel_spin = ttk.Spinbox(
        frame, from_=10**-3, to=10**3,
        increment=10**-3,
        textvariable=co.um_pixel_ratio,
        width=9
    )
    um_pixel_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    tk.Label(frame, text="Exposure Time [seconds] (1 ms - 1 hour)").grid(row=row_f, column=0, sticky="w", padx=5, pady=5)
    frame_interval_spin = ttk.Spinbox(
        frame, from_=10**-3, to=3.6 * 10**3,
        increment=10**-3,
        textvariable=co.exposure_time,
        width=7
    )
    frame_interval_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    tk.Label(frame, text="Fraction of Frames Evaluated (0.01–0.25)").grid(row=row_f, column=0, sticky="w", padx=5, pady=5)
    of_pf_eval_spin = ttk.Spinbox(
        frame, from_=0.01, to=0.25,
        increment=0.01,
        textvariable=co.percentage_frames_evaluated,
        format="%.2f",
        width=7
    )
    of_pf_eval_spin.grid(row=row_f, column=1, padx=5, pady=5)

    return frame