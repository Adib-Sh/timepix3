import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from scipy import stats
import matplotlib as mpl
import os
from datetime import datetime
import pandas as pd
import numpy as np
from scipy.stats import skewnorm
from scipy.stats import norm
from scipy.optimize import curve_fit, minimize_scalar, root_scalar
import csv


# ======================
# Plots Styling
# ======================
def setup_plot_style():
    plt.style.use('dark_background')
    mpl.rcParams['font.family'] = 'DejaVu Sans'
    mpl.rcParams['font.size'] = 12
    mpl.rcParams['axes.edgecolor'] = 'white'
    mpl.rcParams['axes.labelcolor'] = 'white'
    mpl.rcParams['xtick.color'] = 'white'
    mpl.rcParams['ytick.color'] = 'white'
    mpl.rcParams['axes.titleweight'] = 'bold'
    mpl.rcParams['figure.titlesize'] = 18
    mpl.rcParams['figure.titleweight'] = 'bold'
    mpl.rcParams['grid.color'] = 'white'
    

# ======================
# Utility Functions
# Filter outliers using z-score
# ======================
def filter_outliers(data, counts, threshold=3):
    """Filter outliers using z-score."""
    counts = counts > 0
    valid_counts = data[counts]
    
    if len(valid_counts) <= 1:
        return data.astype(float), 0
    
    z_scores = np.abs(stats.zscore(valid_counts))
    mask = z_scores > threshold
    
    clean_data = np.copy(data).astype(float)
    clean_data[counts] = np.where(mask, np.nan, valid_counts)
    
    return clean_data, np.sum(mask)


# ======================
# 2D Hit Count Plot Function
# ======================
def plot_pixel_2d(ax, data, title, xlabel='X Coordinate', 
                  ylabel='Y Coordinate',zlabel='Hit Count', is_time=False, 
                  stats_text="", cmap=plt.cm.inferno, binned = False, norm=None):
    
    if binned:
        im = ax.imshow(data.T, origin='lower', extent=[0, 255, 0, 255], cmap=cmap,
                        interpolation='nearest')
    else:
        im =ax.imshow(data, origin='lower', cmap=cmap, norm=norm)
    ax.set_title(title, color='white')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    cbar = plt.colorbar(im, ax=ax, shrink=0.85, aspect=20, pad=0.02)
    cbar.set_label(zlabel, rotation=270, labelpad=15)
    ax.grid(True, which='both', color='white', linestyle=':', alpha=0.5)
    ax.minorticks_on()
    
    if stats_text:
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                ha='left', va='top', color='white',
                bbox=dict(facecolor='black', alpha=0.6, edgecolor='white'))
    


# ======================
# 3D Hit Count Plot Function
# ======================
def plot_pixel_3d(ax, x_val, y_val, data, title, xlabel='X Coordinate', 
                  ylabel='Y Coordinate', zlabel='Value', is_time=False, 
                  stats_text="", view_elev=30, view_azim=-45, cmap=plt.cm.inferno, binned = False):
    
    norm = LogNorm(vmin=1, vmax=np.max(data[data > 0]) if np.any(data > 0) else 1)

    z_val = np.zeros_like(x_val)
    if binned:
        dx = dy = 8*np.ones_like(z_val)
    else:
        dx = dy = np.ones_like(z_val)
    dz = data.flatten()
    mask = dz > 0
    dz_masked = dz[mask]

    if dz_masked.size > 0:
        colors = cmap(norm(dz_masked))
        ax.bar3d(x_val[mask], y_val[mask], z_val[mask], dx[mask], dy[mask], dz_masked,
                 color=colors, edgecolor='none', linewidth=0.1, alpha=0.95, shade=True)
        max_z = dz_masked.max()
    else:
        max_z = 1

    ax.set_title(title, color='white')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    #ax.set_zlabel(zlabel)
    ax.set_xlim(0, 255)
    ax.set_ylim(0, 255)
    ax.set_zlim(0, max_z * 1.1)
    ax.view_init(elev=view_elev, azim=view_azim)
    ax.grid(True, linestyle=':', alpha=0.2)
    #cbar = plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, shrink=0.7, aspect=15, pad=0.1)
    #cbar.set_label(zlabel, rotation=270, labelpad=15)
    if stats_text:
        ax.text2D(0.02, 0.95, stats_text, transform=ax.transAxes,
                  ha='left', va='top', color='white',
                  bbox=dict(facecolor='white', alpha=0.6, edgecolor='white'))
        



# ======================
# 3D Surface Plot Function (For ToT/ToA)
# ======================
def plot_surface_3d(ax, x_val, y_val, data, title, xlabel='X Coordinate', 
                   ylabel='Y Coordinate', zlabel='Value', is_time=False, 
                   stats_text="", view_elev=30, view_azim=-45, cmap=plt.cm.inferno):
    
    # Create surface plot
    surf = ax.plot_surface(x_val, y_val, data, cmap=cmap, rstride=1, cstride=1,
                          linewidth=0, antialiased=False, shade=True)
    
    ax.set_title(title, color='white')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    #ax.set_zlabel(zlabel)
    ax.set_xlim(x_val.min(), x_val.max())
    ax.set_ylim(y_val.min(), y_val.max())
    
    # Set z-axis limits based on data
    valid_data = data[~np.isnan(data)]
    if len(valid_data) > 0:
        z_min = np.nanmin(valid_data)
        z_max = np.nanmax(valid_data)
        ax.set_zlim(z_min, z_max * 1.1)
    
    ax.view_init(elev=view_elev, azim=view_azim)
    ax.grid(True, linestyle=':', alpha=0.2)
    cbar = plt.colorbar(surf, ax=ax, shrink=0.7, aspect=15, pad=0.1)
    cbar.set_label(zlabel, rotation=270, labelpad=15)
    if stats_text:
        ax.text2D(0.02, 0.95, stats_text, transform=ax.transAxes,
                 ha='left', va='top', color='white',
                 bbox=dict(facecolor='black', alpha=0.6, edgecolor='white'))
        


'''
# ======================
# Find Isolated Hits
# ======================
def isolated_hits(data, slice_width=100000, iso_dist=3, x_range=None, y_range=None):

    x_start, x_end = (x_range if x_range is not None 
                              else (data['x'].min(), data['x'].max() + 1))
    y_start, y_end = (y_range if y_range is not None 
                              else (data['y'].min(), data['y'].max() + 1))
    
    min_time = int(data['toa'].min())
    max_time = int(data['toa'].max())
    print(f"[INFO] Splitting data into {slice_width} [ns]  chunks from {min_time} to {max_time}")

    isolated_rows = []

    # Time slicing loop
    time_bins = (data['toa'] / slice_width).astype(int)
    unique_bins = np.unique(time_bins)
    print(f"[INFO] Found {len(unique_bins)} unique time bins with hits.")
    
    def spatially_isolated(x, y, hits_in_slice):
        # Get all hits at this pixel
        pixel_hits = hits_in_slice.get((x, y), [])
        
        # Reject pixel if it was hit more than once
        if len(pixel_hits) > 1:
            return False
        
        # Check neighbors
        for dx in range(-iso_dist, iso_dist + 1):
            for dy in range(-iso_dist, iso_dist + 1):
                if np.hypot(dx, dy) > iso_dist:
                    continue
                nx, ny = x + dx, y + dy
                # Skip neighbors outside window
                if nx < x_start or nx >= x_end or ny < y_start or ny >= y_end:
                    continue
                if (nx, ny) in hits_in_slice:
                    return False
        return True

    for bin_id in unique_bins:
        start = bin_id * slice_width
        end = start + slice_width
        time_slice = data[(data['toa'] >= start) & (data['toa'] < end)]
        
        if time_slice.empty:
            continue
        print(f"[DEBUG] Checking time window {start}–{end} (time bits) with {len(time_slice)} hits")
        
        # Group hits by pixel coordinates
        hits_by_xy = time_slice.groupby(['x', 'y']).groups
        hits_by_xy = {xy: idxs for xy, idxs in hits_by_xy.items() if len(idxs) == 1}
        # Check isolation for each hit
        for idx, row in time_slice.iterrows():
            x, y = row['x'], row['y']
            if spatially_isolated(x, y, hits_by_xy):
                isolated_rows.append(row.to_dict())
    
    print(f"[RESULT] Found {len(isolated_rows)} spatially isolated hits")
    return pd.DataFrame(isolated_rows)
'''
# NEW TEMPORAL FILTER (TEST)
from collections import defaultdict

def isolated_hits(
    data,
    slice_width=100000,
    iso_dist=1,
    x_range=None,
    y_range=None,
    temporal_margin=0,
):

    x_start, x_end = (x_range if x_range else (data['x'].min(), data['x'].max() + 1))
    y_start, y_end = (y_range if y_range else (data['y'].min(), data['y'].max() + 1))
    
    min_time, max_time = int(data['toa'].min()), int(data['toa'].max())
    print(f"[INFO] Time range: {min_time}–{max_time}, slice width: {slice_width}")
    
    time_bins = (data['toa'] / slice_width).astype(int)
    data = data.copy()
    data['time_bin'] = time_bins
    unique_bins = data['time_bin'].unique()
    isolated_rows = []
    
    # Time bins
    for bin_id in unique_bins:
        slice_start = bin_id * slice_width
        slice_end = slice_start + slice_width

        # Define time window
        time_window_start = slice_start - temporal_margin
        time_window_end = slice_end + temporal_margin
        time_window = data[(data['toa'] >= time_window_start) & (data['toa'] < time_window_end)]
        hits_by_xy = defaultdict(list)
        for idx, row in time_window.iterrows():
            hits_by_xy[(row['x'], row['y'])].append(row['toa'])

        # Iterate over the hits inside the time slice
        time_slice = data[(data['toa'] >= slice_start) & (data['toa'] < slice_end)]

        print(f"[DEBUG] Time slice {slice_start}–{slice_end}: {len(time_slice)} hits")

        for _, row in time_slice.iterrows():
            x, y, toa = row['x'], row['y'], row['toa']

            # Skip if this pixel fires more than once in a window
            if len(hits_by_xy.get((x, y), [])) > 1:
                continue
            
            # Check neighbors
            isolated = True
            for dx in range(-iso_dist, iso_dist + 1):
                for dy in range(-iso_dist, iso_dist + 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if not (x_start <= nx < x_end and y_start <= ny < y_end):
                        continue
                    neighbor_times = hits_by_xy.get((nx, ny), [])
                    for t in neighbor_times:
                        if abs(toa - t) <= temporal_margin:
                            isolated = False
                            break
                    if not isolated:
                        break
                if not isolated:
                    break

            if isolated:
                isolated_rows.append(row.to_dict())

    print(f"[RESULT] Isolated hits found: {len(isolated_rows)}")
    return pd.DataFrame(isolated_rows)


# ======================
# Peak TOT level
# ======================        
def peak_tot(tot_values, bins=18):
    tot_values = pd.Series(tot_values).dropna().to_numpy()
    counts, bin_edges = np.histogram(tot_values, bins=bins, density=False)
    peak_idx       = np.argmax(counts)
    peak_tot       = (bin_edges[peak_idx] + bin_edges[peak_idx + 1]) / 2
    peak_count     = counts[peak_idx]
    peak_height = peak_count

    return peak_tot, peak_height



# ======================
# Skew Normal Fit and Plot
# ======================


def get_mode(shape, loc, scale):
    result = minimize_scalar(
        lambda x: -skewnorm.pdf(x, shape, loc=loc, scale=scale),
        bounds=(loc - 5 * scale, loc + 5 * scale),
        method='bounded'
    )
    return result.x

def get_fwhm(shape, loc, scale, data):
    x = np.linspace(min(data), max(data), 10_000)
    pdf = skewnorm.pdf(x, shape, loc, scale)
    half_max = np.max(pdf) / 2
    x_peak = x[np.argmax(pdf)]

    def half_max_func(x_val):
        return skewnorm.pdf(x_val, shape, loc, scale) - half_max

    try:
        left = root_scalar(half_max_func, bracket=[min(data), x_peak], method='brentq').root
    except ValueError:
        left = x_peak
    try:
        right = root_scalar(half_max_func, bracket=[x_peak, max(data)], method='brentq').root
    except ValueError:
        right = x_peak

    return right - left

# --- Gradient-based uncertainty propagation ---
def propagate_uncertainty(func, popt, pcov, h=1e-5, args=()):
    grad = []
    for i in range(len(popt)):
        dp = np.zeros_like(popt)
        dp[i] = h
        f_plus  = func(*(popt + dp), *args)
        f_minus = func(*(popt - dp), *args)
        deriv = (f_plus - f_minus) / (2 * h)
        grad.append(deriv)
    grad = np.array(grad)
    return np.sqrt(grad.T @ pcov @ grad)

# --- Main fit function ---
def fit_skew_normal(data, bins=18, data_type="All Pixels", legend_loc='upper left', output_dir=""):
    data = np.array(data)

    # Histogram for curve_fit
    counts, bin_edges = np.histogram(data, bins=bins, density=True)
    bin_centres = (bin_edges[1:] + bin_edges[:-1]) / 2
    bin_width = bin_edges[1] - bin_edges[0]

    def pdf_model(x, a, loc, scale):
        return skewnorm.pdf(x, a, loc=loc, scale=scale)

    # Initial guess
    p0 = skewnorm.fit(data)

    # Fit
    popt, pcov = curve_fit(pdf_model, bin_centres, counts, p0=p0)
    shape, loc, scale = popt
    shape_err, loc_err, scale_err = np.sqrt(np.diag(pcov))

    # Derived quantities
    mean = skewnorm.mean(shape, loc, scale)
    mean_err = propagate_uncertainty(skewnorm.mean, popt, pcov)

    median = skewnorm.median(shape, loc, scale)
    median_err = propagate_uncertainty(skewnorm.median, popt, pcov)

    mode = get_mode(shape, loc, scale)
    mode_err = propagate_uncertainty(get_mode, popt, pcov)

    fwhm = get_fwhm(shape, loc, scale, data)
    fwhm_err = propagate_uncertainty(get_fwhm, popt, pcov, args=(data,))

    # PDF
    x = np.linspace(min(data), max(data), 10000)
    pdf = skewnorm.pdf(x, shape, loc, scale)

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.grid(True, which='both', linestyle=':', alpha=0.6)

    counts_raw, _, _ = ax.hist(
        data, bins=bins, density=False, alpha=1, color='darkorange',
        label='ToT Counts'
    )

    pdf_scaled = pdf * len(data) * bin_width
    ax.plot(x, pdf_scaled,
            color='deepskyblue', linewidth=2,
            label=(f'Skew-Normal Fit\n'
                   f'Mean = {mean:.3f} ± {mean_err:.3f}\n'
                   f'Median = {median:.3f} ± {median_err:.3f}\n'
                   f'Mode = {mode:.3f} ± {mode_err:.3f}\n'
                   f'FWHM = {fwhm:.3f} ± {fwhm_err:.3f}'))

    ax.axvline(loc, color='crimson', linestyle='--', linewidth=2, label=f'Location (loc) = {loc:.3f}')
    
    # Peaks
    x_peak = x[np.argmax(pdf)]
    peak_count_fit = skewnorm.pdf(x_peak, shape, loc, scale) * len(data) * bin_width
    peak_tot_index = np.argmax(counts)
    peak_tot_val = bin_centres[peak_tot_index]
    peak_height_hist = counts_raw.max()
    ax.plot(x_peak, peak_count_fit, 'o', color='seagreen', label=f'Peak ToT (fit) = {x_peak:.4f}')
    ax.plot(peak_tot_val, peak_height_hist, 'ro', label=f'Peak ToT (count) = {peak_tot_val:.4f}')

    ax.set_xlabel('Time-over-Threshold (ToT)', fontsize=14)
    ax.set_ylabel('Counts', fontsize=14)
    ax.set_title(f'ToT Distribution with Skew-Normal Fit {data_type}', pad=20)
    ax.legend(loc=legend_loc, fontsize=10)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        plt.savefig(os.path.join(output_dir, f'ToT Distribution {data_type}.png'),
                    dpi=150, bbox_inches='tight')

    plt.show()

    return {
        "shape": shape,        "shape_err": shape_err,
        "loc": loc,            "loc_err": loc_err,
        "scale": scale,        "scale_err": scale_err,
        "mean": mean,          "mean_err": mean_err,
        "median": median,      "median_err": median_err,
        "mode": mode,          "mode_err": mode_err,
        "fwhm": fwhm,          "fwhm_err": fwhm_err,
        "peak_tot_val": peak_tot_val, "peak_tot_count": peak_height_hist,
        "peak_tot_fit": x_peak
    }



