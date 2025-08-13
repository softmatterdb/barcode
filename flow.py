import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv
import os, csv, functools, builtins
import matplotlib.ticker as ticker
import matplotlib.colors as colors
import matplotlib
matplotlib.use('Agg')
from utils import groupAvg, find_analysis_frames

def analyze_optical_flow(file, name, channel, frame_stride, downsample, exposure_time, um_pix_ratio, frame_eval_percent, save_visualizations, save_rds, verbose, winsize = 32):
    # Defines print to enable printing only if verbose setting set to True
    print = functools.partial(builtins.print, flush=True)
    vprint = print if verbose else lambda *a, **k: None
    vprint('Beginning Optical Flow Analysis')

    def execute_opt_flow(images, start, stop, writer):
        if stop == start:
            return
        flow = cv.calcOpticalFlowFarneback(images[start], images[stop], None, 0.5, 3, winsize, 3, 5, 1.2, 0)
        flow_reduced = groupAvg(flow, downsample)
        downU = flow_reduced[:,:,0]
        downV = flow_reduced[:,:,1]
        downU = np.flipud(downU)* 1/(exposure_time) * 1/(stop - start) * um_pix_ratio
        downV = -1 * np.flipud(downV)* 1/(exposure_time) * 1/(stop - start) * um_pix_ratio

        if save_rds:
            writer.writerow([f"Flow Field ({start} - {stop})"])
            writer.writerow(["X-Direction"])
            writer.writerows(downU)
            writer.writerow(["Y-Direction"])
            writer.writerows(downV)
        
        speed = (downU ** 2 + downV ** 2) ** (1/2)
        direction = np.arctan2(downV, downU)

        img_shape = downU.shape[0] / downU.shape[1]
        if (start, stop) in visualization_flow_fields and save_visualizations:
            fig, ax = plt.subplots(figsize=(10 * img_shape,10))
            norm = colors.Normalize(vmin = 0, vmax = np.max(speed))
            cma = matplotlib.cm.plasma
            sm = matplotlib.cm.ScalarMappable(cmap = cma, norm = norm)
            q = ax.quiver(downU, downV, norm(speed))
            plt.colorbar(sm, ax = ax)
            figname = f'Frame {start} to {stop} Flow Field.png'
            figpath = os.path.join(name, figname)
            ticks_adj = ticker.FuncFormatter(lambda x, _: '{0:g}'.format(x * downsample))
            ax.xaxis.set_major_formatter(ticks_adj)
            ax.yaxis.set_major_formatter(ticks_adj)
            ax.set_aspect(aspect=1, adjustable='box')

            fig.savefig(figpath)
            plt.close('all')
        
        # Convert speed from pixels / interval to nm/sec
        # Conversion: px/interval * interval/frame * 1/(sec/frame) * um/px
        vx_list.append(np.mean(np.cos(direction)))
        vy_list.append(np.mean(np.sin(direction)))
        speeds.append(np.mean(speed))
        return

    image = file[:,:,:,channel]
    # Error Checking: Empty Images
    if (image == 0).all():
       return [np.nan] * 4
    frame_indices, frame_stride = find_analysis_frames(image, frame_stride)
    flow_field_indices = [(frame_indices[i], frame_indices[i + 1]) for i in range(len(frame_indices) - 1)]
    num_frames_analysis = int(np.ceil(frame_eval_percent * len(flow_field_indices)))

    mid_point = flow_field_indices[int((len(flow_field_indices) - 1)/2)]
    visualization_flow_fields = [flow_field_indices[0], mid_point, flow_field_indices[-1]]

    vx_list = []
    vy_list = []
    speeds = []
    filename = os.path.join(name, 'OpticalFlow.csv')

    # Prepares the intermediate file for saving if setting is turned on
    if save_rds:
        myfile = open(filename, "w")
        csvwriter = csv.writer(myfile)
    else: 
        csvwriter = None

    for frame_pair in flow_field_indices:
        execute_opt_flow(image, frame_pair[0], frame_pair[1], csvwriter)
        
    # Close the CSV intermediate file
    if save_rds:
        myfile.close()

    vx_list = np.array(vx_list)
    vy_list = np.array(vy_list)
    speeds = np.array(speeds)

    vector_lengths = np.sqrt(vx_list ** 2 + vy_list ** 2)
    sigma_thetas = np.sqrt(-2 * np.log(vector_lengths))

    theta = np.arctan2(np.nanmean(vy_list), np.nanmean(vx_list)) # Metric for average flow direction # "Mean Flow Direction"
    sigma_theta = np.nanmean(sigma_thetas) # Metric for st. dev of flow (-pi, pi) # "Flow Directional Spread"
    mean_speed = np.nanmean(speeds) # Metric for avg. speed (units of um/s) # Average speed
    delta_speed = np.nanmean(speeds[-num_frames_analysis:]) - np.nanmean(speeds[:num_frames_analysis]) # Metric for change in speed # "Speed Change"
    return [mean_speed, delta_speed, theta, sigma_theta]
