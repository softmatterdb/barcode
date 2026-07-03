import numpy as np

def velocity_correlation(flow_field: np.ndarray):
    downU, downV = flow_field[:,:,0], flow_field[:,:,1]
    m, n = downU.shape
    v_mag_squared = downU**2 + downV**2
    cx, cy = m//2, n//2
    correlation_matrix = np.zeros((m, n))
    for dx in range(-cx, cx):
        for dy in range(-cy, cy):
            x_min, x_max = max(-dx, 0), min(m, m - dx)
            y_min, y_max = max(-dy, 0), min(n, n - dy)
            vx_r = downU[x_min:x_max, y_min:y_max]
            vy_r = downV[x_min:x_max, y_min:y_max]
            vx_shifted = downU[x_min+dx:x_max+dx, y_min+dy:y_max+dy]
            vy_shifted = downV[x_min+dx:x_max+dx, y_min+dy:y_max+dy]
            dot_product = vx_shifted * vx_r + vy_shifted * vy_r
            correlation_value = np.mean(dot_product) / np.mean(v_mag_squared)
            correlation_matrix[dx + cx, dy + cy] = correlation_value
    radial_correlations = velocity_radial_average(correlation_matrix)
    return correlation_matrix, radial_correlations

def divergence(flow_field: np.ndarray, um_pix_ratio: float = 1):
    fx = flow_field[:,:,0]
    fy = flow_field[:,:,1]
    # div(f) = dfx/dx + dfy/dy
    return np.gradient(fx, um_pix_ratio, axis = 1) + np.gradient(fy, um_pix_ratio, axis = 0)

def curl(flow_field: np.ndarray, um_pix_ratio: float = 1):
    fx = flow_field[:,:,0]
    fy = flow_field[:,:,1]
    # curl(f) = dfy/dx - dfx/dy
    return np.gradient(fy, um_pix_ratio, axis = 1) - np.gradient(fx, um_pix_ratio, axis = 0)

def velocity_radial_average(frame):
    nx, ny = frame.shape
    cx, cy = nx // 2, ny // 2
    x_coord, y_coord = np.meshgrid(np.arange(-1*nx/2, nx/2), np.arange(-1*ny/2, ny/2), indexing = 'ij')
    dists = np.sqrt(x_coord ** 2 + y_coord ** 2).flatten()
    max_dist = int(np.ceil(dists.max()))
    correlation_mask = frame.flatten()
    bins = np.arange(max(nx,ny)/2+1)
    c_histogram = np.histogram(dists, bins = bins, weights = correlation_mask)[0]
    counts = np.histogram(dists, bins = bins)[0]
    return c_histogram/counts