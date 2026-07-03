import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
from gui.config import VisualizationConfigGUI, BarcodeConfigGUI
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
from matplotlib import colors
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils.intensity_distribution import mean
import matplotlib.pyplot as plt
plt.style.use('utils/presentation.mplstyle')
from visualization.preview import save_rds_visualization
from gui.window import setup_log_window
import threading
from utils import groupAvg
from core import Units
from utils.gui import os_right_click, save_preview_image, save_preview_video

def save_all_correlations(vis_config: VisualizationConfigGUI):
    from visualization.preview import save_correlation_preview
    import matplotlib
    frames = vis_config.frames
    rds_type = vis_config.rds_type.get()
    if rds_type not in ["Spatial_Autocorrelation", "Velocity_Correlation"]:
        return
    figsize = (5,5)

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111)

    image_output_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG", "*.png")],
        initialfile=f"{rds_type} RDS Preview (All Frames).png",
        title="Save Image File As",
    )
    if len(image_output_path) == 0:
        return
    max_x = np.max([np.max(dist[:,0]) for dist in frames])
    min_y = min(0, np.min([np.min(dist[:,1]) for dist in frames]))
    max_y = max(np.max([np.max(dist[:,1]) for dist in frames]), 1)
    limits = (max_x, min_y, max_y)
    cmap = matplotlib.colormaps["plasma"]
    colors = cmap(np.linspace(0, 1, len(frames)))
    cutoff = np.exp(-1) if rds_type == "Spatial_Autocorrelation" else 0.5

    frame_plots = []
    for i, (frame, color) in enumerate(zip(frames, colors)):
        plts = save_correlation_preview(ax, frame, limits, i, False, color, use_lines = False)[0]
        frame_plots.append(plts)
    
    ax.hlines(cutoff, xmin = 0, xmax = 1.05 * limits[0], colors = "gray", linestyles="dashed")
    fig.savefig(image_output_path)
    

def create_processing_worker(parent, vis_config: VisualizationConfigGUI, barcode_config: BarcodeConfigGUI):
    def worker():
        try:
            save_preview_video(preview_config = vis_config, barcode_config=barcode_config, rds_type = vis_config.rds_type.get())
        except Exception as e:
                print(f"Error during processing: {e}")
    return worker


def create_visualization_frame(parent, barcode_config: BarcodeConfigGUI, config: VisualizationConfigGUI):
    """Create the correlation viewer"""
    frame = ttk.Frame(parent)
    def save_video_threads(parent, config, barcode_config):
        worker = create_processing_worker(parent, config, barcode_config)
        threading.Thread(target=worker, daemon=True).start()
    menu = tk.Menu(frame, tearoff=0)
    menu.add_command(label="Save Frame", command = lambda: save_preview_image(config, barcode_config, config.rds_type.get()))
    menu.add_command(label="Save All Frames as Video", command = lambda: save_video_threads(parent, config, barcode_config))
    menu.add_command(label="Save All Correlation Distributions", command = lambda: save_all_correlations(config))
    def menu_popup(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    row_idx = 0
    header = ("TkDefaultFont", 15, "bold")
    frame.option_add("*font", "TkDefaultFont 13")

    # File/Directory Selection
    def browse_file():
        chosen = filedialog.askopenfilename(filetypes=[("CSV File", "*.csv")], title="Select a File")
        if chosen:
            config.file_path.set(chosen)

    tk.Label(frame, text="Visualize RDS Data", font=header).grid(
        row=row_idx, column=0, columnspan=3, sticky="w", padx=(5, 5), pady=(10, 5)
    )
    row_idx += 1

    file_entry = tk.Entry(frame, textvariable=config.file_path, width=35)
    file_entry.grid(row=row_idx, column=1, padx=5, pady=2)

    browse_file_btn = tk.Button(frame, text="Browse File…", command=browse_file)
    browse_file_btn.grid(row=row_idx, column=2, sticky="w", padx=5)
    row_idx += 1

    preview_frame = tk.Frame(frame)
    preview_frame.columnconfigure(0, weight=0)
    for c in range(1, 10):
        preview_frame.columnconfigure(c, weight=1)
    preview_frame.columnconfigure(10, weight=0)
    preview_frame.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
    
    frame_number_menu = tk.Scale(
        preview_frame,
        from_=0,
        to=len(config.frames) - 1,
        resolution=1,
        orient="horizontal",
        variable=config.preview_frame_number,
        length=300,
        showvalue=True,
    )
    frame_number_menu.grid(row = 0, column=1, columnspan = 9, sticky="ew")

    frame_decrease_btn = tk.Button(
        preview_frame,
        text="◀",
        width=2,
        command=lambda: config.preview_frame_number.set(
            max(config.preview_frame_number.get() - 1, -1 * len(config.frames))
        ),
    )
    frame_decrease_btn.grid(row=0, column=0, padx=(0, 2), pady=(15, 0))

    frame_increase_btn = tk.Button(
        preview_frame,
        text="▶",
        width=2,
        command=lambda: config.preview_frame_number.set(
            min(config.preview_frame_number.get() + 1, len(config.frames) - 1)
        ),
    )
    frame_increase_btn.grid(row=0, column=10, padx=(2, 0), pady=(15, 0))
    row_idx += 1

    # Matplotlib figure placeholder
    root = parent.winfo_toplevel()
    bg_name = root.cget('bg')
    r, g, b = root.winfo_rgb(bg_name)
    bg_color = (r / 65535, g / 65535, b / 65535)
    # Distribution image figure
    fig = Figure(figsize=(3, 3), facecolor=bg_color)
    ax  = fig.add_subplot(111)
    ax.set_facecolor(bg_color)
    ax.grid(False)
    fig.subplots_adjust(right=0.75, bottom=0.25)

    canvas = FigureCanvasTkAgg(fig, master=frame)
    fig.tight_layout()
    canvas.draw()
    canvas.get_tk_widget().grid(
        row=row_idx, column=0, columnspan=3, padx=5, pady=(10,5))
    fig.tight_layout()
    row_idx += 1

    right_click = os_right_click(parent)

    canvas.get_tk_widget().bind(right_click, menu_popup)

    preview_data = {'frames': None,
                    'rds_type': None,
                    'intensity': {'min_i': 0, 'max_i': 1},
                    'correlations': {'min_c': 0, 'max_c': 1, 'max_r': 1},
                    'vectors' : {'min_value': 0, 'max_value': 1},
                    'speeds' : {'max_speed' : 1}
                    }
    def load_preview(*args):
        filepath = config.file_path.get()
        if not filepath:
            preview_data.update({'frames': None, 
                                 'rds_type': None,
                                 'intensity': {'min_i': 0, 'max_i': 1},
                                 'correlations': {'min_c': 0, 'max_c': 1, 'max_r': 1},
                                 'speeds' : {'max_speed' : 1}})
            update_preview()
            return
        frames = config.frames
        rds_type = config.rds_type.get()
        frame_number_menu.config(from_=0, to = len(frames) - 1)
        preview_data["frames"] = frames
        preview_data["rds_type"] = rds_type
        if rds_type == "Optical_Flow":
            speeds = np.linalg.norm(frames, axis = -1)
            preview_data["speeds"]["max_speed"] = np.max(speeds)
        if rds_type == 'Vector_Fields':
            preview_data['vectors']['min_value'] = np.min(frames)
            preview_data['vectors']['max_value'] = np.max(frames)
        if rds_type in ["Spatial_Autocorrelation", "Velocity_Correlation"]:
            max_radius = np.max([np.max(dist[:,0]) for dist in frames])
            min_correlation = np.min([np.min(dist[:,1]) for dist in frames])
            max_correlation = np.max([np.max(dist[:,1]) for dist in frames])
            preview_data["correlations"]["max_r"] = max_radius
            preview_data["correlations"]["min_c"] = min_correlation
            preview_data["correlations"]["max_c"] = max_correlation
        if rds_type == "Intensity_Distribution":
            max_intensity = np.max([np.max(dist[:,0]) for dist in frames])
            min_intensity_p = np.min([np.min(dist[:,1]) for dist in frames])
            preview_data["intensity"]['min_i'] = min_intensity_p
            preview_data["intensity"]['max_i'] = max_intensity
        update_preview()
        return

    def update_preview(*args):
        preview_frame_num = config.preview_frame_number.get()
        try:
            downsample = barcode_config.optical_flow_parameters.downsample.get()
            flow_scale = config.scale.get()
            um_pixel_ratio = barcode_config.reader.um_pixel_ratio.get()
        except:
            downsample, flow_scale, um_pixel_ratio = 1, 1, 1
        if not (isinstance(downsample, int) or isinstance(downsample, float)):
            downsample = 1
        if preview_data["frames"] is None:
            ax.clear()
            ax.set_facecolor(bg_color)
            ax.axis("off")
            canvas.draw()
            return
        frames = preview_data["frames"]
        if preview_data["rds_type"] == "Image_Binarization":
            ax.clear()
            h, w = frames[preview_frame_num].shape
            max_px = 300
            scale = max(1, int(max(h, w) / max_px) + 1)
            # Show down-sampled original
            small = frames[preview_frame_num,::scale, ::scale]
            ax.imshow(small, cmap="gray", interpolation="nearest")
            ax.axis("off")
            ax.set_aspect(aspect=1, adjustable="box")
            fig.tight_layout()
            canvas.draw()
        elif preview_data["rds_type"] == "Vector_Fields":
            ax.clear()
            h, w = frames[preview_frame_num].shape
            max_px = 300
            scale = max(1, int(max(h, w) / max_px) + 1)
            # Show down-sampled original
            norm = colors.Normalize(preview_data["vectors"]['min_value'], preview_data["vectors"]['max_value'])
            small = frames[preview_frame_num,::scale, ::scale]
            ax.imshow(small, cmap="plasma", norm = norm, interpolation="nearest")
            ax.axis("off")
            ax.set_aspect(aspect=1, adjustable="box")
            fig.tight_layout()
            canvas.draw()
        elif preview_data["rds_type"] == "Optical_Flow":
            ax.clear()
            downU, downV = groupAvg(frames[preview_frame_num,:,:,0], downsample), groupAvg(frames[preview_frame_num,:,:,1], downsample)
            rows, cols = downU.shape
            x = np.arange(cols)
            y = np.arange(rows)
            X, Y = np.meshgrid(x, y)
            norm = colors.Normalize(0, preview_data["speeds"]["max_speed"])
            speeds = (downU ** 2 + downV ** 2) ** (1/2)
            ax.quiver(X, Y, downU, downV, norm(speeds), cmap="plasma", scale = preview_data["speeds"]["max_speed"] / flow_scale, scale_units = 'x')
            ticks_adj = ticker.FuncFormatter(lambda x, pos: f"{x * um_pixel_ratio * downsample:g}")
            ax.axis("on")
            ax.xaxis.set_major_formatter(ticks_adj)
            ax.yaxis.set_major_formatter(ticks_adj)
            ax.set_aspect(aspect=1, adjustable="box")
            fig.tight_layout()
            canvas.draw()
        elif preview_data["rds_type"] == "Intensity_Distribution":
            ax.clear()
            dist_intensities, dist_count = frames[preview_frame_num][:,0], frames[preview_frame_num][:,1]
            initial_mean = mean(dist_intensities, dist_count)
            ax.scatter(dist_intensities, dist_count, marker='o', s=4, c='purple', alpha=1, label = "Intensity Distribution")
            ax.axvline(x=initial_mean, ms = 4, c = 'purple', alpha=1, label="Mean Intensity")
            ax.axhline(0, color='dimgray', alpha=0.6)
            ax.set_xlabel("Pixel intensity value")
            ax.set_ylabel("Probability")
            ax.set_yscale('log')
            ax.set_xlim(0, preview_data["intensity"]["max_i"] * 1.05)
            ax.set_ylim(0.9 * preview_data["intensity"]["min_i"], 1)
            ax.set_aspect(aspect='auto', adjustable="box")
            fig.tight_layout()
            canvas.draw()
        elif preview_data["rds_type"] in ["Spatial_Autocorrelation", "Velocity_Correlation"]:
            ax.clear()
            distribution = np.round(preview_data["frames"][preview_frame_num], 2)
            dist_radius = distribution[:,0]
            dist_correlation = distribution[:,1]
            ax.scatter(dist_radius, dist_correlation, marker='o', s=4, c='purple', alpha=0.6)
            ax.axhline(0, color='dimgray', alpha=0.6)
            ax.set_xlabel("R ($\\mu m$)")
            ax.set_ylabel("C(R)")
            ax.set_xlim(None, preview_data["correlations"]["max_r"] * 1.05)
            ax.set_ylim(preview_data["correlations"]["min_c"], max(1.05, 1.05 * preview_data["correlations"]["max_c"]))
            ax.set_aspect('auto')
            fig.tight_layout()
            canvas.draw()
        return
    
    config.preview_frame_number.trace_add("write", update_preview)
    config.scale.trace_add("write", update_preview)
    config.file_path.trace_add("write", load_preview)
    barcode_config.optical_flow_parameters.downsample.trace_add("write", update_preview)
    barcode_config.reader.um_pixel_ratio.trace_add("write", update_preview)

    scale_label = tk.Label(frame, text="Scale Factor")
    scale_label.grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
    scale_spin = ttk.Spinbox(
        frame, from_=10**-3, to=10**3,
        increment=10**-3,
        textvariable=config.scale,
        width=9
    )
    scale_spin.grid(row=row_idx, column=1, padx=5, pady=5)
    row_idx += 1

    micron_pixel_label = tk.Label(frame, text="Optional: Micron to Pixel Ratio (1 nm – 1 mm)")
    micron_pixel_label.grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
    um_pixel_spin = ttk.Spinbox(
        frame, from_=10**-3, to=10**3,
        increment=10**-3,
        textvariable=barcode_config.reader.um_pixel_ratio,
        width=9
    )
    um_pixel_spin.grid(row=row_idx, column=1, padx=5, pady=5)
    row_idx += 1

    exp_time_label = tk.Label(frame, text="Optional: Exposure Time [seconds] (1 ms - 1 hour)")
    exp_time_label.grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
    frame_interval_spin = ttk.Spinbox(
        frame, from_=10**-3, to=3.6 * 10**3,
        increment=10**-3,
        textvariable=barcode_config.reader.exposure_time,
        width=7
    )
    frame_interval_spin.grid(row=row_idx, column=1, padx=5, pady=5)
    row_idx += 1

    downsample_label = tk.Label(frame, text="Downsample/Binning Factor")
    downsample_label.grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
    downsample_spin = ttk.Combobox(
        frame,
        textvariable=barcode_config.optical_flow_parameters.downsample,
        values=[1, 2, 4, 8, 16],
        width=7,
    )
    downsample_spin.grid(row=row_idx, column=1, padx=5, pady=5)
    row_idx += 1

    framerate_label = tk.Label(frame, text="Frame Rate")
    framerate_label.grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
    framerate_spin = ttk.Spinbox(
        frame, from_=10**-2, to=5,
        increment=10**-2,
        textvariable=config.video_framerate,
        width=7
    )
    framerate_spin.grid(row=row_idx, column=1, padx=5, pady=5)

    return frame