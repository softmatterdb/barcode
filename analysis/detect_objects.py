import numpy as np
import matplotlib.pyplot as plt
from skimage import io, color, filters, measure, morphology

# Load and binarize the image
images = io.imread('generate_rotating_ellipsoids result - 5degreesperframe.tif')  # Or .jpg if already converted
gray_image = images[0]
#gray_image = color.rgb2gray(image)
#thresh = filters.threshold_otsu(gray_image)

minimum_size = 100

def detect_objects(gray_image,minimum_size):

    thresh = 10
    binary_image = gray_image > thresh
    binary_image = morphology.remove_small_objects(binary_image, min_size=minimum_size)
    
    # Label and extract region properties
    labeled_image = measure.label(binary_image)
    regions = measure.regionprops(labeled_image)
    
    # Plot the image and axes
    fig, ax = plt.subplots()
    ax.imshow(binary_image, cmap='gray')
    
    for region in regions:
        y0, x0 = region.centroid
        orientation = region.orientation
        
        major_len = region.major_axis_length / 2
        minor_len = region.minor_axis_length / 2
    
        # Minor axis vector
        x1 = x0 + np.cos(orientation) * minor_len
        y1 = y0 - np.sin(orientation) * minor_len
        x2 = x0 - np.cos(orientation) * minor_len
        y2 = y0 + np.sin(orientation) * minor_len
        ax.plot([x1, x2], [y1, y2], '-b', linewidth=2)
    
        # Major axis vector (perpendicular to major)
        x3 = x0 + np.sin(orientation) * major_len
        y3 = y0 + np.cos(orientation) * major_len
        x4 = x0 - np.sin(orientation) * major_len
        y4 = y0 - np.cos(orientation) * major_len
        ax.plot([x3, x4], [y3, y4], '-r', linewidth=2)
    
        # Centroid
        ax.plot(x0, y0, 'go', markersize=5)
    
    plt.title('Detected Objects with Major (Red) and Minor (Blue) Axes')
    plt.axis('off')
    plt.show()
    
    #return the area, centroid, orientation of major axis for each object
    return 
    
detect_objects(gray_image, 100)