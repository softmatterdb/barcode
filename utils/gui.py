import platform
import tkinter as tk
from tkinter import ttk, filedialog
import matplotlib.pyplot as plt
from cv2 import calcOpticalFlowFarneback
import numpy as np
from matplotlib import colors, cm
from matplotlib.animation import PillowWriter, ArtistAnimation
from gui.config import VisualizationConfigGUI, BarcodeConfigGUI, PreviewConfigGUI
from utils.binarization import binarize
from utils.intensity_distribution import histogram
from visualization.preview import save_rds_visualization
from utils import groupAvg, find_analysis_frames

def os_right_click(parent):
    return "<Button-2>" if platform.system() == "Darwin" else "<Button-3>"

def create_popup(parent, description, row, title_label):
    """Helper to create a popup window describing the feature and place the icon."""
    info_icon = tk.Label(parent, text="ℹ️", font=("Arial", 12), bg=parent.winfo_toplevel().cget("bg"), fg="blue", relief="flat", borderwidth=0)
    info_icon.grid(row=row, column=0, sticky="w", padx=(title_label.winfo_reqwidth() + 30, 0))

    def show_popup(event):
        # Create popup
        popup = tk.Label(parent, text=description, bg="#202020", fg="white", relief="flat", borderwidth=4, wraplength=600)
        popup.place(x=info_icon.winfo_rootx() - parent.winfo_rootx() + info_icon.winfo_width() + 10, y=info_icon.winfo_rooty() - parent.winfo_rooty() - 20)
        popup.tkraise()

        def hide_popup(event):
            popup.destroy()  # Destroy popup
        info_icon.bind("<Leave>", hide_popup)

    info_icon.bind("<Enter>", show_popup)

def create_option_section(parent, row, var, title, description):
    """Helper to create option sections with a checkbox, description, and a popup icon."""
    tk.Checkbutton(parent, variable=var).grid(row=row, column=0, sticky="w", padx=5)

    normal = ("TkDefaultFont", 13)

    title_label = tk.Label(parent, text=title, font=normal)
    title_label.grid(row=row, column=0, sticky="w", padx=(25, 5))

    # Call the popup creation function to create and place the info icon
    create_popup(parent, description, row, title_label)

def menu_popup(menu: tk.Menu, event):
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()

def save_preview_image(preview_config: VisualizationConfigGUI | PreviewConfigGUI, barcode_config: BarcodeConfigGUI, rds_type: str):
    preview_number = preview_config.preview_frame_number.get()
    frame_output_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("Portable Network Graphics", "*.png"), ("JPEG", "*.jpg")],
        initialfile=f"{rds_type} RDS Preview - Frame {preview_number}.png",
        title="Save Image File As",
    )
    if len(frame_output_path) == 0:
        return
    if isinstance(preview_config, PreviewConfigGUI):
        frames = preview_config.sample_preview
        index = preview_number
        downsample, um_pixel_ratio, flow_scale, limits = 1, 1, 1.0, None
        if rds_type == "Image_Binarization":
            original_frame = frames[preview_number]
            row, cols, figsize = 1, 2, (10 * original_frame.shape[1]/original_frame.shape[0], 5)
            bin_config = barcode_config.image_binarization_parameters.config
            threshold, bin_factor, min_size = bin_config.threshold_offset, bin_config.bin_factor, bin_config.minimum_island_size
            bin_frame = binarize(original_frame, threshold, bin_factor, min_size)
            frame = (original_frame, bin_frame)
        elif rds_type == "Optical_Flow":
            row, cols, figsize = 1, 1, (5 * frames[0].shape[1]/frames[0].shape[0], 5)
            flow_config = barcode_config.optical_flow_parameters.config
            um_pixel_ratio = barcode_config.reader.um_pixel_ratio.get()
            seconds_per_frame = barcode_config.reader.exposure_time.get()
            downsample, frame_step, win_size = flow_config.downsample, flow_config.frame_step, flow_config.win_size
            if preview_number + frame_step >= len(frames):
                frame_step = len(frames) - preview_number - 1
            frame = calcOpticalFlowFarneback(frames[preview_number], frames[preview_number + frame_step], None, 0.5, 3, win_size, 3, 5, 1.2, 0)
            frame = frame * um_pixel_ratio / (seconds_per_frame * frame_step)
            speeds = np.linalg.norm(frame, axis = -1)
            limits = (0, speeds.max())
        elif rds_type == "Intensity_Distribution":
            row, cols, figsize = 1, 1, (5, 5)
            distribution_config = barcode_config.intensity_distribution_parameters.config
            bin_number, noise_threshold = distribution_config.bin_size, distribution_config.noise_threshold
            frame = frames[preview_number]
            counts, values = histogram(frame, bin_number, noise_threshold)
            frame = np.stack([values, counts], axis = -1)
            max_x = np.max(frame[:,0])
            min_y = np.min(frame[:,1])
            max_y = np.max(frame[:,1])
            limits = (max_x, min_y, max_y)
    else:
        frames = preview_config.frames
        index = preview_config.indices[preview_number]
        frame = frames[preview_number]
        downsample, um_pixel_ratio, flow_scale, limits = 1, 1, 1.0, None
        row, cols = 1, 1
        if rds_type == "Image_Binarization":
            figsize = (5 * frame.shape[1]/frame.shape[0], 5)
        elif rds_type == "Optical_Flow":
            figsize = (5 * frame.shape[1]/frame.shape[0], 5)
            speeds = np.linalg.norm(frames, axis = -1)
            limits = (0, np.max(speeds))
            downsample = barcode_config.optical_flow_parameters.downsample.get()
            um_pixel_ratio = barcode_config.reader.um_pixel_ratio.get()
            flow_scale = preview_config.scale.get()
        elif rds_type == "Intensity_Distribution":
            figsize = (5, 5)
            max_x = np.max([np.max(f[:,0]) for f in frames])
            min_y = np.min([np.min(f[:,1]) for f in frames])
            max_y = 1
            limits = (max_x, min_y, max_y)
        elif rds_type == "Vector_Fields":
            figsize = (5 * frame.shape[1]/frame.shape[0], 5)
            limits = (np.min(frames), np.max(frames))
        elif rds_type in ["Spatial_Autocorrelation", "Velocity_Correlation"]:
            figsize = (5,5)
            max_x = np.max(frame[:,0])
            min_y = min(0, np.min(frame[:,1]))
            max_y = max(np.max(frame[:,1]), 1)
            limits = (max_x, min_y, max_y)
    fig, ax = plt.subplots(row, cols, figsize = figsize)
    plts = save_rds_visualization(ax, index, frame, rds_type, limits, downsample = downsample, um_pixel_ratio = um_pixel_ratio, flow_scale = flow_scale)
    if rds_type == "Optical_Flow" or rds_type == 'Vector_Fields':
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        norm = colors.Normalize(vmin = limits[0], vmax = limits[1])
        cma = cm.plasma
        sm = cm.ScalarMappable(cmap = cma, norm = norm)
        fig.colorbar(sm, cax = cax)
        plt.tight_layout()
    fig.savefig(frame_output_path)
    return

def save_preview_video(preview_config: VisualizationConfigGUI | PreviewConfigGUI, barcode_config: BarcodeConfigGUI, rds_type: str):
    video_output_path = filedialog.asksaveasfilename(
        defaultextension=".gif",
        filetypes=[("GIF File", "*.gif")],
        initialfile=f"{rds_type} RDS Preview.gif",
        title="Save Video File As",
    )
    if len(video_output_path) == 0:
        return
    frame_plots = []
    if isinstance(preview_config, PreviewConfigGUI):
        preview_frames = preview_config.sample_preview
        frames = []
        downsample, um_pixel_ratio, flow_scale, limits = 1, 1, 1.0, None
        if rds_type == "Image_Binarization":
            row, cols, figsize = 1, 2, (10 * preview_frames[0].shape[1]/preview_frames[0].shape[0], 5)
            bin_config = barcode_config.image_binarization_parameters.config
            threshold, bin_factor, min_size = bin_config.threshold_offset, bin_config.bin_factor, bin_config.minimum_island_size
            indices = find_analysis_frames(preview_frames, bin_config.frame_step)
            for frame_num in indices:
                frames.append([preview_frames[frame_num], binarize(preview_frames[frame_num], threshold, bin_factor, min_size)])
        elif rds_type == "Optical_Flow":
            row, cols, figsize = 1, 1, (5 * preview_frames[0].shape[1]/preview_frames[0].shape[0], 5)
            flow_config = barcode_config.optical_flow_parameters.config
            um_pixel_ratio = barcode_config.reader.um_pixel_ratio.get()
            seconds_per_frame = barcode_config.reader.exposure_time.get()
            downsample, win_size = flow_config.downsample, flow_config.win_size
            indices = find_analysis_frames(preview_frames, flow_config.frame_step)
            indices = [(indices[i], indices[i + 1]) for i in range(len(indices) - 1)]
            for frame_pair in indices:
                rds_frame = calcOpticalFlowFarneback(preview_frames[frame_pair[0]], preview_frames[frame_pair[1]], None, 0.5, 3, win_size, 3, 5, 1.2, 0)
                rds_frame = rds_frame * um_pixel_ratio / (seconds_per_frame * (frame_pair[1] - frame_pair[0]))
                frames.append(rds_frame)
            frames = np.array(frames)
            speeds = np.linalg.norm(frames, axis = -1)
            limits = (0, speeds.max())
        elif rds_type == "Intensity_Distribution":
            row, cols, figsize = 1, 1, (5, 5)
            distribution_config = barcode_config.intensity_distribution_parameters.config
            bin_number, noise_threshold = distribution_config.bin_size, distribution_config.noise_threshold
            indices = find_analysis_frames(preview_frames, bin_config.frame_step)
            for frame_num in indices:
                frame = preview_frames[frame_num]
                counts, values = histogram(frame, bin_number, noise_threshold)
                frames.append(np.stack([values, counts], axis = -1))
            max_x = np.max([np.max(frame[:,0]) for frame in preview_frames])
            min_y = np.min([np.min(frame[:,1]) for frame in preview_frames])
            max_y = np.max([np.max(frame[:,1]) for frame in preview_frames])
            limits = (max_x, min_y, max_y)
        
    else:
        frames = preview_config.frames
        indices = preview_config.indices
        flow_scale = preview_config.scale.get()
        framerate = preview_config.video_framerate.get()
        downsample = barcode_config.optical_flow_parameters.downsample.get()
        um_pixel_ratio = barcode_config.reader.um_pixel_ratio.get()
        row, cols = 1, 1
        if rds_type == "Image_Binarization":
            figsize = (5 * frames[0].shape[1]/frames[0].shape[0], 5)
        elif rds_type == "Optical_Flow":
            figsize = (5 * frames[0].shape[1]/frames[0].shape[0], 5)
            speeds = np.linalg.norm(frames, axis = -1)
            limits = (0, np.max(speeds))
        elif rds_type == "Vector_Fields":
            figsize = (5 * frames[0].shape[1]/frames[0].shape[0], 5)
            limits = (np.min(frames), np.max(frames))
        elif rds_type == "Intensity_Distribution":
            figsize = (5, 5)
            max_x = np.max([np.max(frame[:,0]) for frame in frames])
            min_y = np.min([np.min(frame[:,1]) for frame in frames])
            max_y = 1
            limits = (max_x, min_y, max_y)
        elif rds_type in ["Spatial_Autocorrelation", "Velocity_Correlation"]:
            figsize = (5,5)
            max_x = np.max([np.max(frame[:,0]) for frame in frames])
            min_y = min(0, np.min([np.min(frame[:,1]) for frame in frames]))
            max_y = max(np.max([np.max(frame[:,1]) for frame in frames]), 1)
            limits = (max_x, min_y, max_y)
    fig, ax = plt.subplots(row, cols, figsize = figsize)
    for i in range(len(frames)):
        print(f'Visualizing Frame {i}')
        plts = save_rds_visualization(ax, indices[i], frames[i], rds_type, limits, downsample = downsample, um_pixel_ratio = um_pixel_ratio, flow_scale = flow_scale)
        frame_plots.append(plts)
    if rds_type == "Optical_Flow" or rds_type == "Vector_Fields":
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        norm = colors.Normalize(vmin = limits[0], vmax = limits[1])
        cma = cm.plasma
        sm = cm.ScalarMappable(cmap = cma, norm = norm)
        cbar = fig.colorbar(sm, cax = cax)
        cbar.ax.set_ylabel(f'Speed ($\\mu$m/s)')
        plt.tight_layout()
    ani = ArtistAnimation(fig = fig, artists = frame_plots, interval = 500, repeat = False, blit = True)
    video_writer = PillowWriter(fps=framerate)
    ani.save(filename = video_output_path, writer = video_writer, progress_callback = lambda i, n: print(f'Saving frame {i}'))
    print("Video Saved!")
    return