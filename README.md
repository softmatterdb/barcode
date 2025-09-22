# Table of Contents
- [Table of Contents](#table-of-contents)
- [Installation](#installation)
- [Usage](#usage)
  - [Data Preparation](#data-preparation)
  - [Running BARCODE \& User Settings](#running-barcode--user-settings)
    - [Execution Settings](#execution-settings)
    - [Binarization Settings](#binarization-settings)
    - [Optical Flow Settings](#optical-flow-settings)
    - [Intensity Distribution Settings](#intensity-distribution-settings)
    - [Barcode Generator + CSV Aggregator](#barcode-generator--csv-aggregator)
- [Outputs](#outputs)
  - [Metrics](#metrics)
    - [Binarization Metrics](#binarization-metrics)
    - [Optical Flow Field Metrics](#optical-flow-field-metrics)
    - [Intensity Distribution Metrics](#intensity-distribution-metrics)
  - [Output Files](#output-files)

# Installation
Navigate to the Releases Tab of the Github Repository and download the ZIP file corresponding to the operating system that you are using. BARCODE has been tested on macOS 14, 15, and 16, as well as on Windows 10 and 11, and has apps for both operating system. The download + installation should take under a minute.

Otherwise, if you are on Linux, or would like to be able to edit the source code, you can clone this repository and edit the source files directly. To install the required packages, you can use PIP to install them using the following command: ```pip install -r requirements.txt```. Keep in mind that this code was developed in Python 3.12 -- versions of Python prior to 3.12 may not be able to run this program from the source code.
# Usage
## Data Preparation
Currently, BARCODE only takes in TIFF and ND2 file formats. If files you wish to process are not in either format, you will need to convert them to a TIFF file using ImageJ/FIJI.- [Installation](#installation)

## Running BARCODE & User Settings
Click on the app file to open the program. From there, a window will appear with the user interface. The user inputs are described below. When finished specifying the operational settings, click "Run" to begin the BARCODE program. A more detailed tutorial for running BARCODE, including test data, is included [here](https://www.livingbam.org/barcode-tutorial). It should take 10-15 seconds on a standard desktop computer to analyze the test data using the software.

### Execution Settings
| Setting Name                      | Description                                                                                                                                                                                                                                           |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Process File | Select a file or folder to run the BARCODE program on|
| Process Directory | Select a folder to run the BARCODE program on (can not be combined with the "Process File" option above) |
| Combine CSV Files / Generate Barcodes | Use the generator module to combine BARCODE CSV summaries and generate barcode visualizations without rerunning the program (can not be combined with the "Process File" or "Process Directory" option above) |
| Choose Channel                 | Select a channel to run the program on (-1 for last channel, -2 for second to last channel, 0 for first channel, etc) |
| Parse All Channels | Analyze all channels for each video with the program (can not be combined with the "Choose Channel" option) |
| Binarization | Analyze all chosen videos with the binarization module | 
| Optical Flow | Analyze all chosen videos with the optical flow module |
| Intensity Distribution | Analyze all chosen videos with the intensity distribution module |
| Include Dim Files | Run the program on files that are dim (defined as videos where the mean pixel intensity is less than $\frac{2}{e}$ times the minimum pixel intensity) -- files meeting this criteria are labeled in the BARCODE CSV file under the Flags section with a numerical label of 1 |
| Include Dim Channels | Run the program on channels that are dim (defined in "Include Dim Files" setting) -- video channels meeting this criteria are labeled in the BARCODE CSV file under the Flags section (described in "Include Dim Files" setting) |
| Verbose | Prints more details while running the program to output display, including modules run on videos, time to analyze files, etc. |
| Save Data Visualizations | Saves representations of binarization, optical flow, and intensity distribution branches as .png files for further analysis |
| Save Reduced Data Structures | Saves reduced data structures used to perform computation of metrics |
| Generate Dataset Barcode | Save a color "barcode" visualization of the entire dataset; useful for visualizing differences between videos |
| Configuration File | Select a Configuration YAML file; overwrite all settings selected by the user with settings from input YAML file |

### Binarization Settings
The binarization module takes frames from the original video and binarizes those frames. Following this, the binarized video is broken into connected components, with the growth of "voids" (connected components labelled as 0) and "islands" (connected components labelled as 1) measured. A live preview of the binarization is shown in the program to enable qualitative analysis of the effect of the binarization and the sensitivity to the binarization threshold.

| Setting Name | Description | Limits | Default Value |
| - | - | - | - |
| Binarization Threshold | Controls the threshold percentage of the mean which binarizes the image; offset parameter determines the binarization threshold for a given frame as $(1 + \text{offset}) * \overline{B(i)}$, where $\overline{B(i)}$ represents the mean pixel intensity for frame $i$ | (-1, 1) | 0.1 |
| Frame Step | Controls the interval between binarized frames; affects speed of program, with larger intervals decreasing program runtime at potential loss of accuracy | (1, 100) | 10 |
| Fraction of Frames Evaluated | Used for determining frames for averaging in calculation of initial maximum island area and maximum island/void area change; not used for calculation of maximum island/void area; decreasing this results in fewer frames being used for these averages, at the cost of more sensitivity to noise | (0.01, 0.25) | 0.05 |

### Optical Flow Settings
The optical flow module takes frames from a video file and calculates the optical flow field using Farneback's Optical Flow algorithm.

| Setting Name | Description | Limits | Default Value |
| - | - | - | - |
| Frame Step | Controls the interval between frames with which the flow field is calculated; larger values are less prone to noise motion between frames, have less precision | (1, 100) | 10 |
| Optical Flow Window Size | Controls the window size used to compute the flow fields, described further in the [OpenCV documentation here](https://docs.opencv.org/3.4/dc/d6b/group__video__track.html#ga5d10ebbd59fe09c5f650289ec0ece5af) | (1, 1000) | 32 |
| Downsample | Controls the interval between pixels that the flow field is sampled at; larger values are less prone to noise, have less precision | (1, 1000) | 8 |
| Micron to Pixel Ratio | Controls the ratio of microns to pixels in the image; if ND2 files are evaluated, this is taken from the metadata instead; used to adjust optical flow output units from pixels/flow field to microns/second | (0.001, 1000) | 1 |
| Exposure Time \[seconds\] | Controls the interval (in seconds) between frames; if ND2 files are evaluated, this is taken from the metadata instead; used to adjust optical flow output units from pixels/flow field to microns/second | (0.001, 3600) | 1 |
| Fraction of Frames Evaluated | Used for determining frames for averaging in calculation of speed change; not used for calculation of other optical flow metrics; decreasing this results in fewer frames being used for these averages, at the cost of more sensitivity to noise | (0.01, 0.25) | 0.05 |

### Intensity Distribution Settings
The intensity distribution module takes frames from a video and creates a intensity distribution histogram. The kurtosis, median skewness, and mode skewness are then calculated from this distribution.

| Setting Name | Description | Limits | Default Value |
| - | - | - | - |
| Frame Step | Controls the interval between frames for which the intensity distributions are calculated; affects speed of program, with larger intervals decreasing program runtime | (1, 100) | 10 |
| Distribution Number of Bins | Controls the number of bins in histogram; increasing/decreasing the number of bins may result in binning artifacts that affect accuracy of intensity distribution | (100, 500) | 300 |
| Distribution Noise Threshold | Controls the minimum normalized probability in the intensity distribution; probabilities below this threshold are set to 0 and the distribution is renormalized; increasing/decreasing this will affect the sensitivity of the metrics to noise, which is particularly relevant for higher pixel intensity values | (0.00001, 0.01) | 0.0005 |
| Fraction of Frames Evaluated | Used for determining frames for averaging in calculation of kurtosis/median skewness/mode skewness change; not used for calculation of maximum kurtosis/median skewness/mode skewness metrics; decreasing this results in fewer frames being used for these averages, at the cost of more sensitivity to noise | (0.01, 0.25) | 0.05 |
### Barcode Generator + CSV Aggregator
| Setting Name |  Description |
| - | - |
| CSV File Locations | Select the CSV files representing the datasets you would like to combine |
| Aggregate Location | Select a location for the aggregate CSV file to be located |
| Generate Aggregate Barcode | Controls whether or not a colorized barcode is generated |
| Sort Parameter | Determines which metric is used to sort the colorized barcode; if left on Default, the barcode will be sorted by filename/order of files within the CSV files aggregated |

# Outputs
## Metrics
Each module contributes 4-7 metrics to the BARCODE analysis. They are described below:
### Binarization Metrics
The Binarization module uses a binarization threshold (defined [above](#binarization-settings)) to convert each selected frame from a given video from grayscale to 0's and 1's. This binarized image is then segmented into "islands" (a region comprising of only 1's) and "voids" (a region comprising of only 0's). The following metrics are computed with respect to these definitions.
| Metric | Description  |
| - | - |
| **Connectivity** | The percentage of frames that are defined as "connected" (there exists a single island spanning from the top to bottom of the frame, or from the left to right of the frame) |
| **Maximum Island Area** | The area of the largest island in the video; calculated by averaging the area of the largest island in each frame over the frames with the top 10% largest islands |
| **Maximum Void Area** | The area of the largest void; calculated in a similar manner to the ***Maximum Island Area*** metric |
| **Maximum Island Area Change** | The percentage growth/shrinkage of the largest island; calculated by averaging the island area over the first *X* percent and last *X* percent of frames and calculating the difference between these two averages |
| **Maximum Void Area Change** | The percentage growth/shrinkage of the largest void; calculated in a similar manner to the ***Maximum Island Area Change*** metric |
| **Initial Maximum Island Area** | The area of the largest island in the first *X* percent of frames; used as a measurement of the heterogeneity of the island areas in the frame |
| **Initial 2nd Maximum Island Area** | The area of the second largest island in the first *X* percent of frames; used in combination with ***Initial Maximum Island Area*** as a measurement of the heterogeneity of the connected componenets in the frame |

### Optical Flow Field Metrics
The Optical Flow module computes a "flow field" for pairs of frames as selected by the user, with each flow field consisting of a $m/p$ x $n/p$ grid of velocity vectors, where $m$ x $n$ are the dimensions of a given frame, and $p$ is the downsampling factor (defined [above](#optical-flow-settings)). The following metrics are computed with respect to these definitions.
| Metric | Description |
| - | - |
| **Mean Speed** | The average speed over all flow fields in the video; calculated by taking the magnitude of each velocity vector and averaging over the flow field, before averaging the output of each flow field. |
| **Speed Change** | The change in the average speed throughout the video; calculated in a similar manner to the ***Maximum Island Area Change*** metrics. |
| **Mean Flow Direction** | The average direction of the velocity vectors throughout the video; calculated by normalizing the velocity vectors to unit vectors, then taking the average of the $x$ and $y$ components for each vector separately over all flow fields, and then taking the two-argument arctan2 function to calculate an average flow direction. |
| **Flow Directional Spread** | The average variance in the direction of the velocity vectors throughout the video; calculated by taking the unit velocity vectors described in the ***Mean Flow Direction***, then the calculating the length of the mean vector for each flow field. Using the definition of circular variance, the variance is then averaged over all frames. |
### Intensity Distribution Metrics
The Intensity Distribution module computes a intensity distribution histogram for all selected frames by the user. The histogram counts are normalized to provide a probability distribution of pixel intensity values, with intensity values with a probability below a user-defined noise threshold (defined [above](#intensity-distribution-settings)) being set to zero. From this intensity probability distribution, the kurtosis, median skewness (defined for a given histogram as $3 * \frac{\text{mean} - \text{median}}{\text{standard deviation}}$), and mode skewness (defined for a given histogram as $3 * \frac{\text{mean} - \text{mode}}{\text{standard deviation}}$). The following metrics are computed with respect to these definitions.
| Metric | Description |
| - | - |
| **Maximum Kurtosis** | The maximum kurtosis in the selected frames -- calculated by taking the top 10% of kurtosis values for the selected frames and averaging over those |
| **Maximum Median Skewness** | The maximum median skewness in the selected frames -- calculated in a similar manner to ***Maximum Kurtosis***. |
| **Maximum Mode Skewness** | The maximum mode skewness in the selected frames of the video -- calculated in a similar manner to ***Maximum Kurtosis***. |
| **Kurtosis Change** | The change in kurtosis between the beginning and the end of the video, calculated in a similar manner to the ***Maximum Island Area Change*** |
| **Median Skewness Change** | The change in the median skewness between the beginning and end of the video, calculated in a similar manner to the ***Kurtosis Change*** |
| **Mode Skewness Difference** | The change in the mode skewness between the beginning and end of the video, calculated in a similar manner to the ***Kurtosis Change*** |

## Output Files
The BARCODE program saves multiple outputs during the course of the analysis.
- **Summary:** At the base level, the BARCODE program outputs a CSV file containing a 1x20 matrix for each video channel analyzed in a given dataset. Each matrix contains an entry listing the name of the video file being analyzed, followed by the channel analyzed for the given file -- in the case of the "Parse All Channels" setting being selected, this results in one entry for each distinct channel in a given video file. This is followed by the "Flags" parameter, which lists potential issues that BARCODE may have encountered within the dataset -- the meaning of these flags is described below. Following this is the 1x17 matrix describing the outputs of BARCODE's 3 branches. Any branch that is not used will have NaN (Not a Number) values populating the corresponding metrics for that branch.
  - **Flags:** There are certain quality warnings that BARCODE produces to warn about potential unreliability in the output metrics, represented with a number being used to represent each potential quality warning. 
    - **1:** A flag value of 1 indicates that a video/channel has been designated as "dim" or low contrast. This is defined as a video where the first and last frame of the video have a minimum pixel intensity value greater than or equal to $\frac{2}{e}$ times the mean pixel intensity value. This can affect the accuracy of all three branches, and is therefore listed to give users insight as to the reliability of BARCODE's output for that file.
    - **2:**: A flag value of 2 indicates that a video/channel has been designated as saturated. This is defined as a video where all frames have a mode pixel intensity value equal to the maximum pixel intensity value. This can affect the accuracy of the Intensity Distribution branch, as is therefore only shown if the Intensity Distribution branch is used.
- **Summary Barcode:** The BARCODE program can also output a visual representation of the data metrics described in the Summary file above. For each metric, this is done by normalizing the metric values using a combination of predetermined limits and the extrema values for a given metric to a 0-1 scale. These normalized values are then plotted using the Matplotlib color map "Plasma". These visualizations are separated by channel for ease of visualization.
- **Visualizations:** The program can also output graphs for visualization of the analysis performed by the modules. The binarization module provides a graph plotting the change in the area of the largest island and void over the video, while the intensity distribution module provides a histogram of the pixel intensities of the first and last frames of the video. These two graphs are saved in a file labeled "Summary Graphs.png". Additionally, the binarization module outputs 3 images comparing the first, middle, and final frames before and after binarization, saved as "Binarization Frame *X* Comparison.png", where *X* is the number of the video frame displayed. This can help validate the accuracy of the binarization with a given binarization threshold. The optical flow module similarly outputs 3 flow fields, representing the first, middle, and last flow fields computed with optical flow, and saved as "Frame *X1* to *X2* Flow Field.png", with *X1* and *X2* being the frames between which the flow field was computed.
- **Reduced Data Structures:** The program will also output the reduced data structures used to perform the analysis. This would be the binarized frames of the video for the binarization module, the flow fields for the optical flow module, and the intensity distributions for the intensity distribution module. All three of these are saved in CSV file format, and are comparatively small, with the largest files being at most 1-10 MB.

The visualizations and reduced data structures are saved in a folder titled ```{name of file} BARCODE Output```, saved in the same folder as the file, within a subfolder for each channel evaluated. The summary and barcode are saved in the root folder where the program is running.
