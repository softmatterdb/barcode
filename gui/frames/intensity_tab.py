import tkinter as tk
from tkinter import ttk

from gui.config import BarcodeConfigGUI
from .execution_tab import create_popup


def create_intensity_frame(parent, config: BarcodeConfigGUI):
    """Create the intensity distribution settings tab"""
    frame = ttk.Frame(parent)

    # Access config variables directly
    ci = config.intensity_distribution

    row_c = 0

    first_frame_label=tk.Label(frame, text="First Frame [min=1]:")
    first_frame_label.grid(row=row_c, column=0, sticky="w", padx=5, pady=5)

    first_frame_spin = ttk.Spinbox(
        frame, from_=1, to=10**2, increment=1, textvariable=ci.first_frame, width=7
    )
    first_frame_spin.grid(row=row_c, column=1, padx=5, pady=5)

    # Add info box
    create_popup(frame, "Select starting frame of the video. Determines portion of video that the intensity distribution "
    "is calculated over.", row_c, first_frame_label)

    row_c += 1

    last_frame_label=tk.Label(frame, text="Last Frame (Select 0 to compare ending frames):")
    last_frame_label.grid(row=row_c, column=0, sticky="w", padx=5, pady=5)

    last_frame_spin = ttk.Spinbox(
        frame, from_=0, to=10**2, increment=1, textvariable=ci.last_frame, width=7
    )
    last_frame_spin.grid(row=row_c, column=1, padx=5, pady=5)

    # Add info box
    create_popup(frame, "Select ending frame of the video. Determines portion of video that the intensity distribution"
    " is calculated over.", row_c, last_frame_label)

    row_c += 1

    pf_eval_label=tk.Label(frame, text="Percent of Frames Evaluated [0.01–0.2]:")
    pf_eval_label.grid(row=row_c, column=0, sticky="w", padx=5, pady=5)

    pf_eval_spin = ttk.Spinbox(
        frame,
        from_=0.01,
        to=0.2,
        increment=0.01,
        textvariable=ci.frames_evaluation_percent,
        format="%.2f",
        width=7,
    )
    pf_eval_spin.grid(row=row_c, column=1, padx=5, pady=5)

    # Add info box
    create_popup(frame, "Controls fraction of frames evaluated from first to last " \
    "selected. Decreasing this value increases speed of branch while decreasing compared periods "
    "(useful to narrow in on specific behavior). Increasing value " \
    "decreases processing speed while increasing precision of metrics" \
    " over a larger period.", row_c, pf_eval_label)

    return frame
