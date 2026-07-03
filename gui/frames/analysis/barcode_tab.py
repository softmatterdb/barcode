import tkinter as tk
from tkinter import ttk, filedialog

from gui.config import BarcodeConfigGUI, AggregationConfigGUI
from core import ChannelResults


def create_barcode_frame(
    parent, config: BarcodeConfigGUI, aggregation_config: AggregationConfigGUI
):
    """Create the barcode generator + CSV aggregator tab"""
    frame = ttk.Frame(parent)

    ca = aggregation_config

    metrics_list_str = [
        metric.value for metric in ChannelResults.get_metrics(just_metrics=True)
    ]

    headers = ["Default"] + metrics_list_str

    row_ba = 0

    # CSV file chooser
    tk.Label(frame, text="Select CSV Files:").grid(
        row=row_ba, column=0, sticky="w", padx=5, pady=5
    )
    csv_label = tk.Label(
        frame, text="No files selected", wraplength=200, justify="left"
    )
    csv_label.grid(row=row_ba, column=1, sticky="w", padx=5, pady=5)

    def browse_csv_files():
        chosen = filedialog.askopenfilenames(
            filetypes=[("CSV Files", "*.csv")], title="Select one or more CSV files"
        )
        if chosen:
            ca.csv_paths_list.clear()
            ca.csv_paths_list.extend(chosen)
            csv_label.config(text=f"{len(chosen)} CSV files selected")
        else:
            ca.csv_paths_list.clear()
            csv_label.config(text="No files selected")

    tk.Button(frame, text="Browse CSV Files...", command=browse_csv_files).grid(
        row=row_ba, column=2, padx=5, pady=5
    )
    row_ba += 1

    # Aggregate location (filesaver)
    tk.Label(frame, text="Aggregate CSV Location:").grid(
        row=row_ba, column=0, sticky="w", padx=5, pady=5
    )
    combo_entry = tk.Entry(frame, textvariable=ca.output_location, width=40)
    combo_entry.grid(row=row_ba, column=1, padx=5, pady=5)

    def browse_save_csv():
        chosen = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV File", "*.csv")],
            initialfile="aggregate_summary.csv",
            title="Save Aggregate CSV As",
        )
        if chosen:
            ca.output_location.set(chosen)

    tk.Button(frame, text="Save As...", command=browse_save_csv).grid(
        row=row_ba, column=2, padx=5, pady=5
    )
    row_ba += 1

    # Generate aggregate barcode
    tk.Checkbutton(
        frame, text="Generate Aggregate Barcode", variable=ca.generate_single_barcode
    ).grid(row=row_ba, column=0, sticky="w", padx=5, pady=5)

    # Generate comparison barcode
    tk.Checkbutton(
        frame, text="Generate Barcodes for Comparison", 
        variable=ca.generate_comparison_barcodes).grid(row = row_ba, column=1, sticky="w", padx=5, pady=5)
    
    # Separate channels when creating barcodes
    tk.Checkbutton(
        frame, text="Separate Barcodes by Channel",
        variable=ca.separate_channels).grid(row = row_ba, column = 2, sticky="w", padx=5, pady=5)
    row_ba += 1

    # Metric sort
    tk.Label(frame, text="Sort Parameter:").grid(
        row=row_ba, column=0, sticky="w", padx=5, pady=5
    )
    sort_menu = ttk.OptionMenu(
        frame, ca.sort_parameter, headers[0], *headers  # default value  # all choices
    )
    sort_menu.grid(row=row_ba, column=1, sticky="w", padx=5, pady=5)
    row_ba += 1

    activated_metrics_choice = {}
    activated_metrics_menu = tk.Menubutton(frame, text = "Select Metrics to Visualize in BARCODE")
    ca.metrics_list.extend([True] * len(metrics_list_str))
    activated_metrics_menu.menu = tk.Menu(activated_metrics_menu)
    activated_metrics_menu["menu"]= activated_metrics_menu.menu 
    def updateActivatedMetrics():
        selected_metrics = []
        for metric, on_off in activated_metrics_choice.items():
            selected_metrics.append(bool(on_off.get()))        
        ca.metrics_list.clear()
        ca.metrics_list.extend(selected_metrics)
    for metric in metrics_list_str:
        activated_metrics_choice[metric] = tk.IntVar()
        activated_metrics_choice[metric].set(1)
        activated_metrics_menu.menu.add_checkbutton(label = metric, 
                                               variable = activated_metrics_choice[metric],
                                               onvalue=1, offvalue = 0,
                                               command = updateActivatedMetrics)
    activated_metrics_menu.grid(row=row_ba, column=0, sticky="w", padx=5, pady=5)

    return frame
