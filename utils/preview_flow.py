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
    ext = file_path.lower().split(".")[-1]

    if ext in ["tif", "tiff"] and tifffile:
        img = tifffile.imread(file_path)
        if img.ndim == 3:
            temp = [img[i] for i in range(img.shape[0])]
            return temp
        elif img.ndim == 4:
            total_channels = img.shape[3]
            while channel < 0:
                channel += total_channels
            channel = min(channel, total_channels - 1)
            return [img[i, :, :, channel] for i in range(img.shape[0])]
        else:
            return [img]

    elif ext == "nd2":
        with nd2.ND2File(file_path) as ndfile:
            file = ndfile.asarray()
            if len(ndfile.sizes) not in [3, 4] or "T" not in ndfile.sizes or "Z" in ndfile.sizes:
                raise ValueError("Unsupported ND2 format for preview")
            img = np.swapaxes(np.swapaxes(file, 1, 2), 2, 3)
            if len(ndfile.sizes) == 3:
                return [img[i] for i in range(img.shape[0])]
            total_channels = img.shape[3]
            while channel < 0:
                channel += total_channels
            channel = min(channel, total_channels - 1)
            return [img[i, :, :, channel] for i in range(img.shape[0])]

    raise ValueError("Only TIFF and ND2 formats supported.")