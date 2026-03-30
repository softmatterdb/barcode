import tkinter as tk
from tkinter import ttk

def create_intensity_distribution_tab(
        notebook: ttk.Notebook,
        config_data: dict,
) -> tk.Frame:
    frame = ttk.Frame(notebook)
    row_c = 0 
    tk.Label(frame, text="Frame Step").grid(row=row_c, column=0, sticky="w", padx=5, pady=5)
    id_f_step_spin = ttk.Spinbox(
        frame,
        from_=1, to=100,
        increment=1,
        textvariable=config_data["gui_intensity_distribution"]["frame_step"],
        width=7
    )
    id_f_step_spin.grid(row=row_c, column=1, padx=5, pady=5)
    row_c += 1

    tk.Label(frame, text="Distribution Number of Bins").grid(row=row_c, column=0, sticky="w", padx=5, pady=5)
    id_pf_eval_spin = ttk.Spinbox(
        frame, from_=100, to=500,
        increment=1,
        textvariable=config_data["gui_intensity_distribution"]["bin_size"],
        width=7
    )
    id_pf_eval_spin.grid(row=row_c, column=1, padx=5, pady=5)
    row_c += 1

    tk.Label(frame, text="Distribution Noise Threshold").grid(row=row_c, column=0, sticky="w", padx=5, pady=5)
    id_pf_eval_spin = ttk.Spinbox(
        frame, from_=1e-5, to=1e-2,
        increment=1e-5,
        textvariable=config_data["gui_intensity_distribution"]["noise_threshold"],
        format="%.5f",
        width=7
    )
    id_pf_eval_spin.grid(row=row_c, column=1, padx=5, pady=5)
    row_c += 1

    tk.Label(frame, text="Fraction of Frames Evaluated (0.01–0.25)").grid(row=row_c, column=0, sticky="w", padx=5, pady=5)
    id_pf_eval_spin = ttk.Spinbox(
        frame, from_=0.01, to=0.25,
        increment=0.01,
        textvariable=config_data["gui_intensity_distribution"]["percentage_frames_evaluated"],
        format="%.2f",
        width=7
    )
    id_pf_eval_spin.grid(row=row_c, column=1, padx=5, pady=5)
    return frame, config_data