import tkinter as tk
from tkinter import filedialog

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np
import nd2

from utils.analysis import binarize

try:
    import tifffile
except ImportError:
    tifffile = None


def load_first_frame(file_path, channel):
    ext = file_path.lower().split(".")[-1]
    if ext in ["tif", "tiff"] and tifffile:
        img = tifffile.imread(file_path)
        if img.ndim == 3:
            return img[0]
        if img.ndim == 4:
            total_channels = img.shape[3]
            while channel < 0:
                channel = total_channels + channel
            # Clamp to valid range
            if channel >= total_channels:
                channel = total_channels - 1
            return img[0, :, :, channel]
        return img
    elif ext == "nd2":
        with nd2.ND2File(file_path) as ndfile:
            file = ndfile.asarray()
            if len(ndfile.sizes) not in [3, 4] or "T" not in ndfile.sizes or "Z" in ndfile.sizes:
                raise ValueError(
                    "Only TIFF and ND2 are supported in this demo, and required libraries must be installed."
                )
            img = np.swapaxes(np.swapaxes(file, 1, 2), 2, 3)
            if len(ndfile.sizes) == 3:
                return img[0]
            total_channels = img.shape[3]
            while channel < 0:
                channel = total_channels + channel
            # Clamp to valid range
            if channel >= total_channels:
                channel = total_channels - 1
            return img[0, :, :, channel]
    raise ValueError(
        "Only TIFF and ND2 are supported in this demo, and required libraries must be installed."
    )


def main():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select TIFF or ND2 file",
        filetypes=(
            ("Image files", "*.tif *.tiff *.nd2"),
            ("TIFF files", "*.tif *.tiff"),
            ("ND2 files", "*.nd2"),
        ),
    )
    if not file_path:
        print("No file selected.")
        return
    image = load_first_frame(file_path)
    initial_offset = 0.1

    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.25)
    bin_img = binarize(image, initial_offset)
    im = ax.imshow(bin_img, cmap="gray", vmin=0, vmax=1)
    ax.set_title(f"Offset: {initial_offset:.2f}")
    ax.axis("off")
    ax_offset = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor="lightgoldenrodyellow")
    s_offset = Slider(
        ax_offset, "Offset", -1.0, 1.0, valinit=initial_offset, valstep=0.05
    )

    def update(val):
        offset = s_offset.val
        bin_img = binarize(image, offset)
        im.set_data(bin_img)
        ax.set_title(f"Offset: {offset:.2f}")
        fig.canvas.draw_idle()

    s_offset.on_changed(update)
    plt.show()


if __name__ == "__main__":
    main()
