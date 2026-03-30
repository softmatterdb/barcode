import tkinter as tk
from tkinter import ttk, filedialog

def create_barcode_generation_tab(
        notebook: ttk.Notebook,
        config_data: dict,
) -> tk.Frame:
    frame = ttk.Frame(notebook)
    row_ba = 0
    headers = [
        'Default', 'Connectivity', 'Maximum Island Area', 'Maximum Void Area',
        'Void Area Change', 'Island Area Change', 'Initial Island Area 1',
        'Initial Island Area 2', 'Maximum Kurtosis', 'Maximum Median Skewness',
        'Maximum Mode Skewness', 'Kurtosis Difference', 'Median Skewness Difference',
        'Mode Skewness Difference', 'Speed', 'Speed Change',
        'Mean Flow Direction', 'Flow Directional Spread'
    ]

    #csv file chooser 
    tk.Label(frame, text="Select CSV Files").grid(row=row_ba, column=0, sticky="w", padx=5, pady=5)
    csv_label = tk.Label(frame, text="No files selected", wraplength=200, justify="left")
    csv_label.grid(row=row_ba, column=1, sticky="w", padx=5, pady=5)

    def browse_csv_files():
        chosen = filedialog.askopenfilenames(
            filetypes=[("CSV Files","*.csv")],
            title="Select one or more CSV files"
        )
        if chosen:
            # chosen is a tuple of paths
            config_data["gui_barcode"]["csv_paths_list"].clear()
            config_data["gui_barcode"]["csv_paths_list"].extend(chosen)
            # Update the label to show e.g. “3 files selected”
            csv_label.config(text=f"{len(chosen)} CSV files selected")
        else:
            config_data["gui_barcode"]["csv_paths_list"].clear()
            csv_label.config(text="No files selected")

    tk.Button(frame, text="Browse CSV Files...", command=browse_csv_files).grid(row=row_ba, column=2, padx=5, pady=5)
    row_ba += 1

    #aggregate location (filesaver)
    tk.Label(frame, text="Aggregate CSV Location").grid(row=row_ba, column=0, sticky="w", padx=5, pady=5)
    combo_entry = tk.Entry(frame, textvariable=config_data["gui_barcode"]["combined_location"], width=40)
    combo_entry.grid(row=row_ba, column=1, padx=5, pady=5)

    def browse_save_csv():
        chosen = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV File","*.csv")],
            initialfile="aggregate_summary.csv",
            title="Save Aggregate CSV As"
        )
        if chosen:
            config_data["gui_barcode"]["combined_location"].set(chosen)

    tk.Button(frame, text="Save As...", command=browse_save_csv).grid(row=row_ba, column=2, padx=5, pady=5)
    row_ba += 1

    #generate aggregate barcode
    tk.Checkbutton(
        frame, text="Generate Aggregate Barcode",
        variable=config_data["gui_barcode"]["generate_agg_barcode"]
    ).grid(row=row_ba, column=0, sticky="w", padx=5, pady=5)
    row_ba += 1

    #metric sort 
    tk.Label(frame, text="Sort Parameter").grid(row=row_ba, column=0, sticky="w", padx=5, pady=5)
    sort_menu = ttk.OptionMenu(
        frame,
        config_data["gui_barcode"]["sort"],
        headers[0],  # default value
        *headers     # all choices
    )
    sort_menu.grid(row=row_ba, column=1, sticky="w", padx=5, pady=5)
    row_ba += 1
    return frame, config_data