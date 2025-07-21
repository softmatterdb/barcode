# Installation
Navigate to the Releases Tab of the Github Repository and download the ZIP file corresponding to the operating system that you are using. BARCODE has been tested on macOS and Windows, and has apps for both operating system.

Otherwise, if you are on Linux, or would like to be able to edit the source code, you can clone this repository and edit the source files directly. To install the required packages, you can use PIP to install them using the following command: ```pip install -r requirements.txt```. Keep in mind that this code was developed in Python 3.12 -- versions of Python prior to 3.12 may not be able to run this program from the source code.
# Usage
## Data Preparation
Currently, BARCODE only takes in TIFF and ND2 file formats. If files you wish to process are not in either format, you will need to convert them to a TIFF file using ImageJ/FIJI.

Additionally, due to the development of BARCODE as a high throughput classification program, BARCODE only takes input files of 5 GB or less. If the file is any larger, it is recommended that you crop your video and run that through the program.

## Running BARCODE
Click on the app file (or the executable if on Windows). From there, a window will appear with the user interface. The user inputs are described below. When finished specifying the operational settings, click "Run" to begin the BARCODE program.

### User Inputs
#### Execution Settings
| Setting Name                      | Description                                                                                                                                                                                                                                           |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| File/Folder Selection / Generator | Select a file or folder to run the BARCODE program on, or use the generator module to combine BARCODE CSV summaries and generate barcode visualizations without rerunning the BARCODE program                                                         |
| Channel Selection                 | Select a channel to run the program on (-1 for last channel, -2 for second to last channel, 0 for first channel, etc), or parse all channels with the program; channels are selected between -3 and 4                                                 |
| Binarization                      | Run the binarization module of the program                                                                                                                                                                                                            |
| Optical Flow                      | Run the optical flow module of the program                                                                                                                                                                                                            |
| Intensity Distribution            | Run the intensity distribution module of the program                                                                                                                                                                                                  |
| Include Dim Files                 | Run the program on files that are dim (defined as videos where the mean pixel intensity is less than $\frac{2}{e}$ times the minimum pixel intensity) -- may result in less accurate results                                                          |
| Include Dim Channels              | Run the program on channels that are dim (defined as videos where the mean pixel intensity is less than $\frac{2}{e}$ times the minimum pixel intensity) -- may result in less accurate results, which is denoted in the output file, described below |
| Verbose                           | Show more details while running the program                                                                                                                                                                                                           |
| Save Graphs                       | Save metric visualization graphs (explained below)                                                                                                                                                                                                    |
| Save Intermediates                | Save intermediate data structures (explained below)                                                                                                                                                                                                   |
| Dataset Barcode                   | Save a color "barcode" visualization of the entire dataset; useful for visualizing differences between videos                                                                                                                                         |
| Normalize Dataset Barcode         | Uses the maximum and minimum of each output metric to “normalize” the dataset color representation; if unselected, uses default bounds                                                                                                                |
| Configuration File                | Select a Configuration YAML file; overwrite all settings selected by the user with settings from input YAML file                                                                                                                                      |
\* Dim is defined as videos where the mean pixel intensity is less than $\frac{2}{e}$ times the minimum pixel intensity
#### Binarization Settings
The binarization module takes frames from the original video and binarizes those frames. Following this, the binarized video is broken into connected components, with the growth of "voids" (connected components labelled as 0) and "islands" (connected components labelled as 1) is measured

| Setting Name             | Description                                                                                                                                                                        | Limits                | Default |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- | ------- |
| Binarization Threshold   | Controls the threshold percentage of the mean which binarizes the image; offset parameter determines threshold with formula $\text{threshold} = (1 + \text{offset}) * \text{mean}$ | (-1, 1)               | 0.1     |
| Frame Step               | Controls the interval between binarized frames; affects speed of program, with larger intervals decreasing program runtime                                                         | (1, 100)              | 10      |
| Frame Start/Stop Percent | Controls window of frames to calculate average void growth over                                                                                                                    | (0.5, 0.9) / (0.9, 1) | 0.9 / 1 |
#### Optical Flow Settings
The optical flow module takes a video and calculates the optical flow field between frames.

| Setting Name             | Description                                                                                                                                                    | Limits   | Default |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------- |
| Frame Step               | Controls the interval between frames with which the flow field is calculated; larger values are less prone to noise motion between frames, have less precision | (1, 100) | 40      |
| Downsample               | Controls the interval between pixels that the flow field is sampled at; larger values are less prone to noise, have less precision                             | (1, -)   | 8       |
| Nanometer to Pixel Ratio | Controls the ratio of nanometers to pixels in the image; used to adjust optical flow output units from pixels/flow field to nanometers/second                  | (1, -)   | 1       |
| Frame Interval           | Controls the interval (in seconds) between frames; used to adjust optical flow output units from pixels/flow field to nanometers/second                        | (1, -)   | 1       |
#### Intensity Distribution Settings
The intensity distribution module compares the pixel intensity distribution of two frame ranges.

| Setting Name                | Description                                                                                                                | Limits          | Default            |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------- | --------------- | ------------------ |
| First/Last Frame            | Controls which frame is selected as the starting/second frame of the video for comparison                                  | (1, -) / (0, -) | 1 / 0 (last frame) |
| Percent of Frames Evaluated | Controls the fraction of frames which are evaluated, starting at the first frame selected and ending with the second frame | (0.01, 0.2)     | 0.1                |
#### Barcode Generator + CSV Aggregator
| Setting Name                | Description                                                              |
| --------------------------- | ------------------------------------------------------------------------ |
| CSV File Locations          | Select the CSV files representing the datasets you would like to combine |
| Aggregate Location          | Select a location for the aggregate CSV file to be located               |
| Generate Aggregate Barcode  | Controls whether or not an aggregate barcode is generated                |
| Normalize Aggregate Barcode | Determines whether or not the barcode is normalized                      |
# Outputs
## Metrics
Each module contributes 5 or 6 metrics to the BARCODE analysis. They are described below:
#### Binarization Metrics

| Metric                    | Description                                                                                                                                                                                                                                                    |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Connectivity              | The percentage of frames that are defined as connected (there exists a connected component spanning from the top to bottom of the frame, or from left to right)                                                                                                |
| Maximum Island Area       | The area of the largest island in the video (defined as a connected component of 1's in the binarized frame); calculated by averaging the area of the largest island in each frame over the frames with the top 10% largest islands                            |
| Maximum Void Area         | The area of the largest void (defined as a connected component of 0's in the binarized frame); calculated by taking the maximum void area of the largest voids discovered in each frame                                                                        |
| Void Area Change          | The percentage growth/shrinkage of the largest void; calculated by averaging the void area over a range of frames selected by the user (default as described above) and dividing by the initial void area, calculated as the average of the first 5% of frames |
| Island Area Change        | The percentage growth/shrinkage of the largest island; calculated similar to the Void Area Change metric                                                                                                                                                       |
| Initial Island Area 1 | The area of the largest island in the first frame; used as a measurement of the heterogeneity of the connected componenets in the frame                             |
| Initial Island Area 2 | The area of the second largest island in the first frame; used in combination with Initial Island Area 1 as a measurement of the heterogeneity of the connected componenets in the frame                             |

### Optical Flow Field Metrics
| Metric                            | Description                                                                                                                                                                                                                                                             |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Mean Speed                        | The average speed over all flow fields in the video; calculated by taking the magnitude of each velocity vector and averaging over the flow field, before averaging the output of each flow field                                                                       |
| Speed Change                   | The change in the average speed of throughout the video; calculated by taking the mean speed of the first flow field and the mean speed of the last flow field, and subtracting the former from the latter             |
| Mean Flow Direction               | The average direction calculated over all flow fields in the video; calculated by taking the arctan2 vector of every flow vector and averaging over the entire flow field, before averaging the output of each flow field                                               |
| Flow Directional Spread | The standard deviation calculated over all flow fields in the video; calculated by taking the arctangent of every velocity vector and taking the standard deviation of the angle distribution for each flow field, before averaging the output of each flow field       |
### Intensity Distribution Metrics
| Metric               | Description                                                                                                                                                                                                                                                                                                                                                                                          |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Kurtosis Difference  | The change in kurtosis between the first range of intensity distributions and the second range of intensity distributions (typically defined as the first and last 10% of frames); calculated using the kurtosis of each of the first 10% and last 10% of frames, averaging those, and taking the difference of the two averages |
| Mode Skewness Difference | The change in the mode skewness (defined as the difference of the mean and mode, divided by the standard deviation) between the first range of intensity distributions and the second range of intensity distributions (typically defined as the first and last 10% of frames); calculated using the mode skewness of each of the first 10% and last 10% of frames, averaging those, and taking the difference of the two averages |
| Median Skewness Difference  | The change in the median skewness (defined as the difference between the mean and median, divded by the standard deviation) between the first range of intensity distributions and the second range of intensity distributions (typically defined as the first and last 10% of frames); calculated using the median skewness of each of the first 10% and last 10% of frames, averaging those, and taking the difference of the two averages |
| Maximum Kurtosis     | The maximum kurtosis in the first and last 10% of frames -- calculated by taking the top 10% of kurtosis values for the selected frames and averaging over those |
| Maximum Mode Skewness    | The maximum mode skewness in the first and last 10% (adjustable by user) of frames -- calculated by taking the top 10% of mode skewness values for the selected frames and averaging over those |
| Maximum Median Skewness     | The maximum median skewness in the first and last 10% of frames -- calculated by taking the top 10% of median skewness values for the selected frames and averaging over those |

## Output Files
The BARCODE program can save multiple outputs.
- **Summary:** At the base level, the BARCODE program outputs the CSV file representing the 17 metrics.
- **Summary Barcode:** The BARCODE program can also output a visual representation of the data metrics described in the Summary file above. This is done by normalizing the metric values using default limits, and then plotted using the Matplotlib color map "Plasma". These visualizations are separated by channel for ease of visualization.
- **Summary Graphs:** The program can also output graphs for visualization of the analysis performed by the modules. The resilience module provides a graph plotting the change in void size over the video, while the coarsening module provides a histogram of the pixel intensities of the specified frames, as well as a plot of the difference between the first and final frames. The flow module outputs up to 3 flow fields, representing the first, middle, and last flow fields computed with optical flow.
- **Intermediate Data Structures:** The program will also output the intermediate data structures used to perform the analysis. This would be the binarized frames of the video for the resilience module, the flow fields for the flow module, and the intensity distributions for the coarsening module. All three of these are saved in CSV file format, and are comparatively small, with the largest files being at most 1-10 MB.
All file outputs are saved in a folder titled ```{name of file} BARCODE Output``` , saved in the same folder as the file. The summary and barcode are saved in the root folder where the program is running.
