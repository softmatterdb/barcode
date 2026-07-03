import tkinter as tk
from tkinter import ttk, messagebox

import threading
import traceback

# import tab frame creators directly
from gui.frames.analysis.barcode_tab import create_barcode_frame
from gui.frames.analysis.comparison_tab import create_comparison_frame
from gui.frames.analysis.visualization_tab import create_visualization_frame

from core import BarcodeConfig, InputConfig, PreviewConfig, AnalysisConfig

# import configs directly
from gui.config import (
    BarcodeConfigGUI,
    InputConfigGUI,
    PreviewConfigGUI,
    AnalysisConfigGUI
)

from gui.window import setup_log_window, setup_scrollable_container


def create_tabs(parent, config: BarcodeConfigGUI, input_config: InputConfigGUI, 
                preview_config: PreviewConfigGUI, analysis_config: AnalysisConfigGUI):
    def on_tab_selection(event):
        selected_tab = notebook.tab(notebook.select(), 'text')
        if selected_tab == "Barcode Generator & CSV Aggregator":
            input_config.mode.set("agg")
        elif selected_tab == "Barcode Metric Comparison":
            input_config.mode.set("comp")
        elif selected_tab == "Reduced Data Structure Visualization":
            input_config.mode.set("rds")
    notebook = ttk.Notebook(parent, takefocus=0)
    aggregation_config = analysis_config.aggregation
    comparison_config = analysis_config.comparison
    visualization_config = analysis_config.visualization
    notebook.pack(fill="both", expand=True)

    barcode_frame = create_barcode_frame(notebook, config, aggregation_config)
    comparison_frame = create_comparison_frame(notebook, config, comparison_config)
    visualization_frame = create_visualization_frame(notebook, config, visualization_config)
    notebook.add(barcode_frame, text="Barcode Generator & CSV Aggregator")
    notebook.add(comparison_frame, text = "Barcode Metric Comparison")
    notebook.add(visualization_frame, text="Reduced Data Structure Visualization")
    notebook.bind("<<NotebookTabChanged>>", on_tab_selection)

    return notebook

def create_processing_worker(
    config: BarcodeConfig,
    input_config: InputConfig,
    analysis_config: AnalysisConfig,
):
    """Create the worker function for processing in background thread"""
    aggregation_config = analysis_config.aggregation
    comparison_config = analysis_config.comparison
    visualization_config = analysis_config.visualization

    def worker():
        try:
            mode = input_config.mode
            if mode == "agg":
                from utils.writer import generate_aggregate_csv, compare_multiple_csvs

                # Handle CSV aggregation
                combined_location = aggregation_config.output_location
                generate_agg_barcode = aggregation_config.generate_single_barcode
                generate_comparison_barcodes = aggregation_config.generate_comparison_barcodes
                separate_channels = aggregation_config.separate_channels
                sort_param = aggregation_config.sort_parameter
                csv_paths = aggregation_config.csv_paths_list
                metrics_to_visualize = aggregation_config.metrics_list

                if not csv_paths:
                    messagebox.showerror(
                        "Error", "No CSV files selected for aggregation."
                    )
                    return
                sort_choice = None if sort_param == "Default" else sort_param
                
                if generate_comparison_barcodes:
                    compare_multiple_csvs(csv_paths, sort_choice, separate_channels)

                if not combined_location and not generate_comparison_barcodes:
                    messagebox.showerror("Error", "No aggregate location specified.")
                    return
                
                if not generate_comparison_barcodes:
                    generate_aggregate_csv(
                        csv_paths, combined_location, generate_agg_barcode, sort_choice, 
                        separate_channels=separate_channels, metrics_to_visualize=metrics_to_visualize,
                    )

            elif mode == "comp":
                from utils.writer import create_metric_comparison
                create_metric_comparison(comparison_config)

        except Exception as e:
            print(f"Error during processing: {e}")
            print(traceback.format_exc())
            messagebox.showerror("Error during processing", str(e))

        finally:
            messagebox.showinfo(
                "Processing Complete", "Analysis has finished successfully."
            )

    return worker

def create_combine_page(parent, switch_page):
    frame = tk.Frame(parent)
    frame.pack(fill="both", expand=True)

    gui_config = BarcodeConfigGUI()
    gui_input_config = InputConfigGUI()
    gui_preview_config = PreviewConfigGUI()
    gui_analysis_config = AnalysisConfigGUI()

    def on_run():
        setup_log_window(parent)

        # Convert GUI configs to pure data configs
        config = gui_config.config
        input_config = gui_input_config.config
        # input_config.mode = "agg"
        analysis_config = gui_analysis_config.config

        worker = create_processing_worker(config, input_config, analysis_config)
        threading.Thread(target=worker, daemon=True).start()

    back_button = ttk.Button(frame, text="← Back", command=lambda: switch_page("home"))
    back_button.pack(anchor="w", padx=20, pady=10)

    create_tabs(
        frame,
        gui_config,
        gui_input_config,
        gui_preview_config,
        gui_analysis_config,
    )

    run_button = ttk.Button(frame, text="Analyze BARCODE Data", command=on_run)
    run_button.pack(pady=10)

    return frame