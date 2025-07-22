import tkinter as tk
from tkinter import filedialog

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np
import nd2

from analysis.flow import calculate_optical_flow

try:
    import tifffile
except ImportError:
    tifffile = None


# def read_all_frames(file_path, channel):
#     ext = file_path.lower().split(".")[-1]

#     if ext in ["tif", "tiff"] and tifffile:
#         img = tifffile.imread(file_path)
#         if img.ndim == 3:
#             return [img[i] for i in range(img.shape[0])]
#         elif img.ndim == 4:
#             total_channels = img.shape[3]
#             while channel < 0:
#                 channel += total_channels
#             channel = min(channel, total_channels - 1)
#             return [img[i, :, :, channel] for i in range(img.shape[0])]
#         else:
#             return [img]

#     elif ext == "nd2":
#         with nd2.ND2File(file_path) as ndfile:
#             file = ndfile.asarray()
#             if len(ndfile.sizes) not in [3, 4] or "T" not in ndfile.sizes or "Z" in ndfile.sizes:
#                 raise ValueError("Unsupported ND2 format for preview")
#             img = np.swapaxes(np.swapaxes(file, 1, 2), 2, 3)
#             if len(ndfile.sizes) == 3:
#                 return [img[i] for i in range(img.shape[0])]
#             total_channels = img.shape[3]
#             while channel < 0:
#                 channel += total_channels
#             channel = min(channel, total_channels - 1)
#             return [img[i, :, :, channel] for i in range(img.shape[0])]

#     raise ValueError("Only TIFF and ND2 formats supported.")

def read_all_frames(file_path, channel):
    print(f"[DEBUG] Reading file: {file_path}, channel: {channel}")
    ext = file_path.lower().split(".")[-1]
    print(f"[DEBUG] File extension: {ext}")

    if ext in ["tif", "tiff"] and tifffile:
        img = tifffile.imread(file_path)
        print(f"[DEBUG] TIFF image shape: {img.shape}")
        if img.ndim == 3:
            temp = [img[i] for i in range(img.shape[0])]
            print(len(temp))
            return temp
        elif img.ndim == 4:
            total_channels = img.shape[3]
            print(f"[DEBUG] Total channels in TIFF: {total_channels}")
            while channel < 0:
                channel += total_channels
            channel = min(channel, total_channels - 1)
            return [img[i, :, :, channel] for i in range(img.shape[0])]
        else:
            print("[DEBUG] Unusual TIFF shape, returning single image")
            return [img]

    elif ext == "nd2":
        with nd2.ND2File(file_path) as ndfile:
            file = ndfile.asarray()
            print(f"[DEBUG] ND2 raw shape: {file.shape}, sizes: {ndfile.sizes}")
            if len(ndfile.sizes) not in [3, 4] or "T" not in ndfile.sizes or "Z" in ndfile.sizes:
                raise ValueError("Unsupported ND2 format for preview")
            img = np.swapaxes(np.swapaxes(file, 1, 2), 2, 3)
            print(f"[DEBUG] Swapped ND2 shape: {img.shape}")
            if len(ndfile.sizes) == 3:
                return [img[i] for i in range(img.shape[0])]
            total_channels = img.shape[3]
            while channel < 0:
                channel += total_channels
            channel = min(channel, total_channels - 1)
            return [img[i, :, :, channel] for i in range(img.shape[0])]

    raise ValueError("Only TIFF and ND2 formats supported.")


# def main():
#     root = tk.Tk()
#     root.withdraw()
#     file_path = filedialog.askopenfilename(
#         title="Select TIFF or ND2 file",
#         filetypes=(
#             ("Image files", "*.tif *.tiff *.nd2"),
#             ("TIFF files", "*.tif *.tiff"),
#             ("ND2 files", "*.nd2"),
#         ),
#     )
#     if not file_path:
#         print("No file selected.")
#         return
#     image = load_first_frame(file_path)
#     initial_offset = 0.1

#     fig, ax = plt.subplots()
#     plt.subplots_adjust(bottom=0.25)
#     opt_img = calculate_optical_flow(image, initial_offset)
#     im = ax.imshow(bin_img, cmap="gray", vmin=0, vmax=1)
#     ax.set_title(f"Offset: {initial_offset:.2f}")
#     ax.axis("off")
#     ax_offset = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor="lightgoldenrodyellow")
#     s_offset = Slider(
#         ax_offset, "Offset", -1.0, 1.0, valinit=initial_offset, valstep=0.05
#     )

#     def update(val):
#         offset = s_offset.val
#         bin_img = binarize(image, offset)
#         im.set_data(bin_img)
#         ax.set_title(f"Offset: {offset:.2f}")
#         fig.canvas.draw_idle()

#     s_offset.on_changed(update)
#     plt.show()


# if __name__ == "__main__":
#     main()
