import tkinter as tk
from tkinter import ttk

from gui.config import BarcodeConfigGUI


def create_flow_frame(parent, config: BarcodeConfigGUI):
    """Create the optical flow settings tab"""
    frame = ttk.Frame(parent)

    # Access config variables directly
    co = config.optical_flow

    row_f = 0

    tk.Label(frame, text="Frame Step (Minimum: 1 Frame):").grid(
        row=row_f, column=0, sticky="w", padx=5, pady=5
    )
    flow_f_step_spin = ttk.Spinbox(
        frame, from_=1, to=1000, increment=1, textvariable=co.frame_step, width=7
    )
    flow_f_step_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    tk.Label(frame, text="Window Size (Minimum: 1 Pixel):").grid(
        row=row_f, column=0, sticky="w", padx=5, pady=5
    )
    win_size_spin = ttk.Spinbox(
        frame, from_=1, to=1000, increment=1, textvariable=co.window_size, width=7
    )
    win_size_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

    tk.Label(frame, text="Downsample (Minimum: 1 Pixel):").grid(
        row=row_f, column=0, sticky="w", padx=5, pady=5
    )
    downsample_spin = ttk.Spinbox(
        frame, from_=1, to=1000, increment=1, textvariable=co.downsample_factor, width=7
    )
    downsample_spin.grid(row=row_f, column=1, padx=5, pady=5)
    row_f += 1

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

    return frame
