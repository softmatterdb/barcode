import tkinter as tk
from tkinter import ttk, messagebox

import threading
import traceback

# import tab frame creators directly
from gui.frames.execution_tab import create_execution_frame
from gui.frames.binarization_tab import create_binarization_frame
from gui.frames.flow_tab import create_flow_frame
from gui.frames.intensity_tab import create_intensity_frame
# from gui.frames.barcode_tab import create_barcode_frame

from core import BarcodeConfig, InputConfig, PreviewConfig, AggregationConfig

# import configs directly
from gui.config import (
    BarcodeConfigGUI,
    InputConfigGUI,
    PreviewConfigGUI,
    AggregationConfigGUI,
)

from gui.window import setup_log_window

def create_tabs(parent, config, input_config, preview_config, aggregation_config):
    notebook = ttk.Notebook(parent, takefocus=0)
    notebook.pack(fill="both", expand=True)

    execution_frame = create_execution_frame(notebook, config, input_config)
    binarization_frame = create_binarization_frame(notebook, config, preview_config, input_config)
    flow_frame = create_flow_frame(notebook, config, preview_config, input_config)
    intensity_frame = create_intensity_frame(notebook, config)
    # barcode_frame = create_barcode_frame(notebook, config, aggregation_config)

    notebook.add(execution_frame, text="Execution Settings")
    notebook.add(binarization_frame, text="Binarization Settings")
    notebook.add(flow_frame, text="Optical Flow Settings")
    notebook.add(intensity_frame, text="Intensity Distribution Settings")
    # notebook.add(barcode_frame, text="Barcode Generator + CSV Aggregator")

    return notebook

def create_processing_worker(
    config: BarcodeConfig,
    input_config: InputConfig,
    aggregation_config: AggregationConfig,
):
    """Create the worker function for processing in background thread"""

    # if input_config.configuration_file:
    #     try:
    #         config = BarcodeConfig.load_from_yaml(input_config.configuration_file)
    #     except Exception as e:
    #         messagebox.showerror("Error reading config file", str(e))
    #         return

    def worker():
        try:
            mode = input_config.mode

            if mode == "agg":
                from utils.writer import generate_aggregate_csv

                # Handle CSV aggregation
                combined_location = aggregation_config.output_location
                generate_agg_barcode = aggregation_config.generate_barcode
                sort_param = aggregation_config.sort_parameter
                csv_paths = aggregation_config.csv_paths_list

                if not csv_paths:
                    messagebox.showerror(
                        "Error", "No CSV files selected for aggregation."
                    )
                    return
                if not combined_location:
                    messagebox.showerror("Error", "No aggregate location specified.")
                    return

                sort_choice = None if sort_param == "Default" else sort_param
                generate_aggregate_csv(
                    csv_paths, combined_location, generate_agg_barcode, sort_choice
                )

            else:
                from core.pipeline import run_analysis

                # Handle file/directory processing
                file_path = input_config.file_path
                dir_path = input_config.dir_path

                if not (dir_path or file_path):
                    messagebox.showerror(
                        "Error", "No file or directory has been selected."
                    )
                    return

                channels = config.channels.parse_all_channels
                channel_selection = config.channels.selected_channel
                if not (channels or (channel_selection is not None)):
                    messagebox.showerror("Error", "No channel has been specified.")
                    return

                dir_name = dir_path if dir_path else file_path

                run_analysis(dir_name, config)

        except Exception as e:
            print(f"Error during processing: {e}")
            print(traceback.format_exc())
            messagebox.showerror("Error during processing", str(e))

        finally:
            messagebox.showinfo(
                "Processing Complete", "Analysis has finished successfully."
            )

    return worker

def create_process_page(parent, switch_page):
    frame = tk.Frame(parent)
    frame.pack(fill="both", expand=True)

    gui_config = BarcodeConfigGUI()
    gui_input_config = InputConfigGUI()
    gui_preview_config = PreviewConfigGUI()
    gui_aggregation_config = AggregationConfigGUI()

    def on_run():
        setup_log_window(parent)

        # force the value manually to see if that fixes it
        gui_input_config.mode.set("dir")

        # Convert GUI configs to pure data configs
        config = gui_config.config
        input_config = gui_input_config.config
        aggregation_config = gui_aggregation_config.config

        # print("== RUNNING TEST ==")
        # print("mode:", gui_input_config.mode.get())
        # print("file path:", gui_input_config.file_path.get())
        # print("dir path:", gui_input_config.dir_path.get())
        # print("parse all channels:", gui_config.channels.parse_all_channels.get())
        # print("===================")

        worker = create_processing_worker(config, input_config, aggregation_config)
        threading.Thread(target=worker, daemon=True).start()

    back_button = ttk.Button(frame, text="← Back", command=lambda: switch_page("home"))
    back_button.pack(anchor="w", padx=20, pady=10)

    create_tabs(
        frame,
        gui_config,
        gui_input_config,
        gui_preview_config,
        gui_aggregation_config,
    )

    run_button = ttk.Button(frame, text="Process Data", command=on_run)
    run_button.pack(pady=10)

    return frame