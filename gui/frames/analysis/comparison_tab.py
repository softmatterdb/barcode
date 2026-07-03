import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
from gui.config import BarcodeConfigGUI, ComparisonConfigGUI
from core import ChannelResults
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils.reader import read_csv_to_channel_results

def create_comparison_frame(parent, config: BarcodeConfigGUI, 
    comparison_config: ComparisonConfigGUI):
    """Create the comparison plot generator tab"""
    frame = ttk.Frame(parent)

    cc = comparison_config

    metrics_list_str = [
        metric.value for metric in ChannelResults.get_metrics(just_metrics=True)
    ]

    row_bc = 0

    # CSV file chooser
    tk.Label(frame, text="Select CSV File:").grid(
        row=row_bc, column=0, sticky="w", padx=5, pady=5
    )
    csv_label = tk.Label(
        frame, text="No file selected", wraplength=200, justify="left"
    )
    csv_label.grid(row=row_bc, column=1, sticky="w", padx=5, pady=5)

    def browse_csv_file():
        chosen = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv")], title="Select a CSV file"
        )
        if chosen:
            cc.csv_location.set(chosen)
            csv_label.config(text=f"{chosen} selected")
        else:
            cc.csv_location.set("")
            csv_label.config("No file selected")

    tk.Button(frame, text="Select CSV File", command=browse_csv_file).grid(
        row=row_bc, column=2, padx=5, pady=5)
    row_bc += 1

    # Metric 1 Selection
    tk.Label(frame, text="Metric 1:").grid(
        row=row_bc, column=0, sticky="w", padx=5, pady=5
    )
    sort_menu = ttk.OptionMenu(
        frame, cc.first_comparison_metric, metrics_list_str[0], *metrics_list_str  # default value  # all choices
    )
    sort_menu.grid(row=row_bc, column=1, sticky="w", padx=5, pady=5)
    row_bc += 1

    # Metric 2 Selection
    tk.Label(frame, text="Metric 2:").grid(
        row=row_bc, column=0, sticky="w", padx=5, pady=5
    )
    sort_menu = ttk.OptionMenu(
        frame, cc.second_comparison_metric, metrics_list_str[0], *metrics_list_str  # default value  # all choices
    )
    sort_menu.grid(row=row_bc, column=1, sticky="w", padx=5, pady=5)
    row_bc += 1

    tk.Label(frame, text="Parameter Comparison Dynamic Preview").grid(
        row=row_bc, column=0, sticky="w", padx=5, pady=5
    )
    row_bc += 1

    # Matplotlib figure placeholder
    root = parent.winfo_toplevel()
    bg_name = root.cget('bg')
    r, g, b = root.winfo_rgb(bg_name)
    bg_color = (r / 65535, g / 65535, b / 65535)
    # Distribution image figure
    fig = Figure(figsize=(3, 3), facecolor=bg_color)
    ax  = fig.add_subplot(111)
    ax.set_facecolor(bg_color)
    ax.set_xlabel(cc.first_comparison_metric.get())
    ax.set_ylabel(cc.second_comparison_metric.get())
    ax.grid(True)
    fig.subplots_adjust(right=0.75, bottom=0.25)

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().grid(
        row=row_bc, column=0, columnspan=2, padx=5, pady=(10,5))
    fig.tight_layout()
    row_bc += 1

    def update_comparison(*args):
        if not cc.csv_location:
            return
        ax.clear()
        ax.grid(True)
        ax.set_xlabel(cc.first_comparison_metric.get())
        ax.set_ylabel(cc.second_comparison_metric.get())
        results = read_csv_to_channel_results(cc.csv_location.get())
        metrics = ChannelResults.get_metrics()
        first_metric = [metric for metric in metrics if metric.value == cc.first_comparison_metric.get()][0]
        second_metric = [metric for metric in metrics if metric.value == cc.second_comparison_metric.get()][0]
        param1 = [result.get_dict_data()[first_metric] for result in results]
        param2 = [result.get_dict_data()[second_metric] for result in results]
        def reset_limits(param):
            min_val = np.nanmin(param)
            max_val = np.nanmax(param)
            min_param = 0.9 * min_val if min_val > 0 else (
                1.1 * min_val if min_val < 0 else None
            )
            max_param = 0.9 * max_val if max_val < 0 else (
                1.1 * max_val if max_val > 0 else None
            )
            return min_param, max_param
        xlimits = reset_limits(param1)
        ylimits = reset_limits(param2)
        ax.set_xlim(xlimits[0], xlimits[1])
        ax.set_ylim(ylimits[0], ylimits[1])
        ax.scatter(param1, param2, c = 'black')
        canvas.draw()

    cc.csv_location.trace_add("write", update_comparison)
    cc.first_comparison_metric.trace_add("write", update_comparison)
    cc.second_comparison_metric.trace_add("write", update_comparison)

    tk.Label(frame, text="CSV Comparison Location:").grid(
        row=row_bc, column=0, sticky="w", padx=5, pady=5
    )
    combo_entry = tk.Entry(frame, textvariable=cc.output_location, width=40)
    combo_entry.grid(row=row_bc, column=1, padx=5, pady=5)

    def browse_save_csv():
        chosen = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV File", "*.csv")],
            initialfile="comparison.csv",
            title="Save Aggregate CSV As",
        )
        if chosen:
            cc.output_location.set(chosen)

    tk.Button(frame, text="Save As...", command=browse_save_csv).grid(
        row=row_bc, column=2, padx=5, pady=5
    )
    row_bc += 1
    return frame