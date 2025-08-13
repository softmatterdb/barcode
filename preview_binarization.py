import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np
import tkinter as tk
from tkinter import filedialog
import nd2
try:
    import tifffile
except ImportError:
    tifffile = None

def binarize(frame, offset_threshold):
    avg_intensity = np.mean(frame)
    threshold = avg_intensity * (1 + offset_threshold)
    new_frame = np.where(frame < threshold, 0, 1)
    return new_frame

def load_first_frame(file_path, channel = 0):
    ext = file_path.lower().split('.')[-1]
    if ext in ['tif', 'tiff'] and tifffile:
        img = tifffile.imread(file_path)
        if not len(img.shape) in [3, 4] or img.shape[0] <= 5:
            raise TypeError('File must be time series data with at least 5 frames...')
        img = img[0,:,:,channel] if len(img.shape) == 4 else img[0]
        return img
    elif ext == 'nd2':
        with nd2.ND2File(file_path) as ndfile:
            # ND2Reader returns an iterable over frames; grab the first frame
            # It may return a (y, x) or (c, y, x) array; handle both
            if len(ndfile.sizes) >= 5:
                    raise TypeError("Incorrect file dimensions: file must be time series data with 1+ channels (4 dimensions total)")
            if "Z" in ndfile.sizes:
                raise TypeError('Z-stack identified, skipping to next file...')
            if 'T' not in ndfile.sizes or len(ndfile.shape) <= 2 or ndfile.sizes['T'] <= 5:
                raise TypeError('Too few frames, unable to capture dynamics, skipping to next file...')
            if ndfile == None:
                raise TypeError('Unable to read file, skipping to next file...')
            file = ndfile.asarray()
            arr = np.swapaxes(np.swapaxes(file, 1, 2), 2, 3)

            # If ND2 contains channels, select channel 0 by default
            arr = arr[0,:,:,channel] if arr.ndim == 4 else arr[0]
            return arr
    raise ValueError("Only TIFF and ND2 are supported in this demo, and required libraries must be installed.")

def main():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select TIFF or ND2 file",
        filetypes=(
            ("Image files", "*.tif *.tiff *.nd2"),
            ("TIFF files", "*.tif *.tiff"),
            ("ND2 files", "*.nd2"),
        )
    )
    if not file_path:
        print("No file selected.")
        return
    image = load_first_frame(file_path)
    initial_offset = 0.1

    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.25)
    bin_img = binarize(image, initial_offset)
    im = ax.imshow(bin_img, cmap='gray', vmin=0, vmax=1)
    ax.set_title(f"Offset: {initial_offset:.2f}")
    ax.axis('off')
    ax_offset = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor='lightgoldenrodyellow')
    s_offset = Slider(ax_offset, 'Offset', -1.0, 1.0, valinit=initial_offset, valstep=0.05)

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