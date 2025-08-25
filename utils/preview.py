import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np
import tkinter as tk
from tkinter import filedialog
from utils.reader import load_first_frame

def binarize(frame, offset_threshold):
    avg_intensity = np.mean(frame)
    threshold = avg_intensity * (1 + offset_threshold)
    new_frame = np.where(frame < threshold, 0, 1)
    return new_frame

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