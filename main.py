import sys, yaml, os, threading
from analysis import process_directory
from utils.writer import generate_aggregate_csv
import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox
from gui import (create_execution_settings_tab, create_barcode_generation_tab,
    create_image_binarization_tab, create_optical_flow_tab, create_intensity_distribution_tab)

def set_config_data(gui_config: dict) -> dict:
    def convert_tk_config(config: dict) -> dict:
        new_config = {}
        for key, val in config.items():
            new_config[key] = val.get()
        return new_config
    config_data = {}
    if gui_config:
        if gui_config["gui_execution"]["configuration_file"].get():
            try:
                with open(gui_config["gui_execution"]["configuration_file"].get(), "r") as f:
                    config_data = yaml.load(f, Loader=yaml.FullLoader)
            except Exception as e:
                messagebox.showerror("Error reading config file", str(e))
                return config_data
        else:
            execution_settings = convert_tk_config(gui_config["gui_execution"])
            channel_select = "All" if execution_settings["channels"] else execution_settings["channel_selection"]
            config_data["reader"] = convert_tk_config(gui_config["gui_reader"])
            config_data["reader"]["channel_select"] = channel_select
            config_data["writer"] = convert_tk_config(gui_config["gui_writer"])
            config_data["image_binarization_parameters"] = convert_tk_config(gui_config["gui_binarization"])
            config_data["optical_flow_parameters"] = convert_tk_config(gui_config["gui_optical_flow"])
            config_data["intensity_distribution_parameters"] = convert_tk_config(gui_config["gui_intensity_distribution"])
            config_data["image_binarization_parameters"].pop("sample_file", None)
    return config_data

def main ():
    root = tk.Tk()
    root.title("BARCODE: Biomaterial Activity Readouts to Categorize, Optimize, Design, and Engineer")
    root.grid_rowconfigure(0, weight=1) 
    root.grid_columnconfigure(0, weight=1) 

    #prevent border from highlighting 
    style = ttk.Style()
    style.configure("TNotebook", borderwidth=0, relief="flat")
    #optional: disables tab borders 
    #style.configure("TNotebook.Tab", borderwidth=0, padding=[5, 2])
    style.map("TNotebook.Tab",
        focuscolor=[("", "")]
    )

    #enable scrolling 
    container = ttk.Frame(root)
    container.grid(row=0, column=0, sticky="nsew") 

    canvas = tk.Canvas(
        container, 
        bd=0, 
        highlightthickness=0, #prevents border from highlighting 
        takefocus=0 
    )
    v_scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    h_scroll = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)
    canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

    v_scroll.pack(side="right", fill="y")
    h_scroll.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)

    scrollable_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def on_frame_config(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    scrollable_frame.bind("<Configure>", on_frame_config)

    # vertical scroll by wheel, horizontal when Shift+wheel
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    canvas.bind_all("<Shift-MouseWheel>", lambda e: canvas.xview_scroll(int(-1*(e.delta/120)), "units"))

    notebook = ttk.Notebook(scrollable_frame, takefocus=0) 
    notebook.pack(fill="both", expand=True)

    gui_config_data = {
        "gui_execution" : {
            "file_path" : tk.StringVar(),
            "dir_path" : tk.StringVar(),
            "channels" : tk.BooleanVar(),
            "channel_selection" : tk.IntVar(),
            "mode" : tk.StringVar(value="file"),
            "configuration_file" : tk.StringVar()  # --configuration_file
        },
        "gui_reader" : {
            "accept_dim_channels" : tk.BooleanVar(),
            "accept_dim_images" : tk.BooleanVar(),
            "binarization" : tk.BooleanVar(),
            "optical_flow" : tk.BooleanVar(),
            "intensity_distribution" : tk.BooleanVar(),
            "verbose" : tk.BooleanVar(),
        },
        "gui_writer" : {
            "save_visualizations" : tk.BooleanVar(),
            "save_rds" : tk.BooleanVar(),
            "generate_barcode" : tk.BooleanVar(),
        },
        "gui_binarization" : {
            "threshold_offset" : tk.DoubleVar(value=0.1),
            "frame_step" : tk.IntVar(value=10),
            "percentage_frames_evaluated" : tk.DoubleVar(value=0.05),
            "sample_file" : tk.StringVar(),
        },
        "gui_optical_flow" : {
            "frame_step" : tk.IntVar(value=10),
            "win_size" : tk.IntVar(value=32),
            "downsample" : tk.IntVar(value=8),
            "um_pixel_ratio" : tk.DoubleVar(value=1.0),
            "exposure_time" : tk.DoubleVar(value=1.0),
            "percentage_frames_evaluated" : tk.DoubleVar(value=0.05),
        },
        "gui_intensity_distribution" : {
            "bin_size" : tk.IntVar(value = 300),
            "frame_step" : tk.IntVar(value=10),
            "noise_threshold" : tk.DoubleVar(value=5e-4),
            "percentage_frames_evaluated" : tk.DoubleVar(value=0.05),
        },
        "gui_barcode" : {
            "csv_paths_list" : [],
            "combined_location" : tk.StringVar(),
            "generate_agg_barcode" : tk.BooleanVar(),
            "sort" : tk.StringVar(value="Default"),
        },
    }

    execution_frame, gui_config_data = create_execution_settings_tab(notebook, gui_config_data)
    binarize_frame, gui_config_data = create_image_binarization_tab(root, notebook, gui_config_data)
    flow_frame, gui_config_data = create_optical_flow_tab(notebook, gui_config_data)
    id_frame, gui_config_data= create_intensity_distribution_tab(notebook, gui_config_data)
    barcode_frame, gui_config_data   = create_barcode_generation_tab(notebook, gui_config_data)
    notebook.add(execution_frame, text="Execution Settings")
    notebook.add(binarize_frame, text="Binarization Settings")
    notebook.add(flow_frame, text="Optical Flow Settings")
    notebook.add(id_frame, text="Intensity Distribution Settings")
    notebook.add(barcode_frame, text="Barcode Generator + CSV Aggregator")

    #Run button
    run_button = ttk.Button(root, text="Run", command=lambda: on_run())
    run_button.grid(row=1, column=0, pady=10, sticky="n") 

    #Run 
    def on_run():
        #terminal message window 
        log_win = tk.Toplevel(root) 
        log_win.title("Processing Log") 

        log_frame = ttk.Frame(log_win) 
        log_frame.pack(fill='both', expand=True) 
        log_frame.rowconfigure(0, weight=1) 
        log_frame.columnconfigure(0, weight=1) 

        log_text = tk.Text(log_frame, state='disabled', wrap='word', font=('Segoe UI', 10)) 
        log_text.pack(side='left', fill='both', expand=True) 
        
        log_scroll = ttk.Scrollbar(log_frame, orient='vertical', command=log_text.yview) 
        log_scroll.pack(side='right', fill='y') 
        log_text.configure(yscrollcommand=log_scroll.set) 
        
        root.update_idletasks() 

        class TextRedirector:
            def __init__(self, widget):
                self.widget = widget
            def write(self, msg):
                try:
                    # enable → insert → scroll → disable
                    self.widget.configure(state='normal')
                    self.widget.insert('end', msg)
                    self.widget.see('end')
                    self.widget.configure(state='disabled')
                except:
                    raise Exception("Program Terminated Early")
            def flush(self):
                pass

        sys.stdout = TextRedirector(log_text) 
        sys.stderr = TextRedirector(log_text) 

        #create a thread to run background tasks 
        def worker(): 
            try: 
                toggle_barcode_generation = (gui_config_data["gui_execution"]["mode"].get() == "agg")
                if toggle_barcode_generation:
                    barcode_generation_settings = gui_config_data["gui_barcode"]
                    if len(barcode_generation_settings["csv_paths_list"]) == 0:
                        messagebox.showerror("Error", "No CSV files selected for aggregation.")
                        return
                    if not barcode_generation_settings["combined_location"].get():
                        messagebox.showerror("Error", "No aggregate location specified.")
                        return
                    files = barcode_generation_settings["csv_paths_list"] 
                    combined_csv_loc = barcode_generation_settings["combined_location"].get()
                    gen_barcode = barcode_generation_settings["generate_agg_barcode"].get()
                    sort_choice = None if barcode_generation_settings["sort"].get() =='Default' else barcode_generation_settings["sort"].get()

                    try:
                        generate_aggregate_csv(files, combined_csv_loc, gen_barcode, sort_choice)
                        messagebox.showinfo("Success", "Combined CSV and barcodes generated!")
                    except Exception as e:
                        messagebox.showerror("Error during aggregation", str(e))
                    return 

                else:
                    execution_settings = gui_config_data["gui_execution"]
                    dir_path = execution_settings["dir_path"].get()
                    file_path = execution_settings["file_path"].get()
                    #process file or folder 
                    if not (dir_path or file_path):
                        messagebox.showerror("Error", "No file or directory has been selected.")
                        return
                    if not (execution_settings["channels"].get() or (execution_settings["channel_selection"].get() is not None)):
                        messagebox.showerror("Error", "No channel has been specified.")
                        return
                    dir_name = dir_path if dir_path else file_path 
                    config_data = set_config_data(gui_config_data)

                    #print directory name 
                    try:
                        if os.path.isdir(dir_name):
                            print(dir_name, flush=True)
                        process_directory(dir_name, config_data)
                        messagebox.showinfo("Success", "Processing complete!")
                    except Exception as e:
                        messagebox.showerror("Error during processing", str(e))
                    return
            except Exception as e: 
                messagebox.showerror("Error during processing", str(e)) 

        threading.Thread(target=worker, daemon=True).start() 

    root.update_idletasks() 
    bbox = canvas.bbox("all") #returns (x1, y1, x2, y2) 
    if bbox: 
        content_width  = bbox[2] - bbox[0] 
        content_height = bbox[3] - bbox[1] 
        canvas.config(width=content_width, height=content_height) 
        root.update_idletasks() 

    root.mainloop()


if __name__ == "__main__":
    main()