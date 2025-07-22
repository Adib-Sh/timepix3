
import h5py
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import glob
import os
from PIL import Image
import io
import pandas as pd
from datetime import datetime


# Import Data
pwd = "/home/adisha/git/libkatherine/build/BeamData 20250608 NanoMAX/"


#energy_keV = "16keV"
#filename = pwd + "thlscan_datadriven_20250608_104734.h5"

#energy_keV = "14keV"
#filename = pwd + "thlscan_datadriven_20250608_113454.h5"

energy_keV = "12keV"
filename = pwd + "thlscan_datadriven_20250608_115511.h5"

#energy_keV = "10keV"
#filename = pwd + "thlscan_datadriven_20250608_121123.h5"

#energy_keV = "8keV"
#filename = pwd + "thlscan_datadriven_20250608_122537.h5"


# Choosing a 20x20 window
if energy_keV == "16keV":
    # Define window (Only for 16keV)
    x_min, x_max = 70, 90
    y_min, y_max = 140, 160
else:
    # Define window
    x_min, x_max = 110, 130
    y_min, y_max = 120, 140

sensor_width = 256
sensor_height = 256
n_pixels_to_plot = 10
base_name = os.path.splitext(os.path.basename(filename))[0]
output_dir = f"{base_name}_analysis_w_fit"
plots_dir = os.path.join(output_dir, "individual_plots")
os.makedirs(output_dir, exist_ok=True)
os.makedirs(plots_dir, exist_ok=True)


pixel_dtype = np.dtype([
    ('x', 'i4'),
    ('y', 'i4'),
    ('toa', 'u8'),
    ('ftoa', 'u1'),
    ('tot', 'u2'),
    ('hit_count', 'u4'),
    ('thl', 'i4')
])

# Loading data
with h5py.File(filename, 'r') as f:
    # Check what datasets are available
    print("Datasets in file:")
    for key in f.keys():
        print(f"  Total {key}: {f[key].shape}")
    
    pixel_data = f['/pixel_hits'][:]
    attrs = dict(f.attrs)
    thl_start = attrs['thl_start_mv']
    thl_end = attrs['thl_end_mv']
    thl_step = attrs['thl_step_mv']
    frames_per_thl = attrs['frames_per_thl']



unique_thls = np.arange(thl_start, thl_end + thl_step, thl_step)
unique_thls = unique_thls[::-1]
print(f"\nTHL levels: {len(unique_thls)} points from {thl_start} to {thl_end} mV")

thl_pixel_data = {}
for thl in unique_thls:
    thl_filter = pixel_data['thl'] == thl
    thl_pixels = pixel_data[thl_filter]
    
    hit_map = np.zeros((sensor_height, sensor_width), dtype=np.uint64)
    tot_map = np.zeros((sensor_height, sensor_width), dtype=np.float32)
    count_map = np.zeros((sensor_height, sensor_width), dtype=np.uint32)
    '''
    for pixel in thl_pixels:
        x, y = pixel['x'], pixel['y']
        if x_min <= x < x_max and y_min <= y < y_max:
            hit_map[y, x] += 1
            tot_map[y, x] += pixel['tot']
            count_map[y, x] += 1
    '''
    x = thl_pixels['x']
    y = thl_pixels['y']
    tot = thl_pixels['tot']
    
    roi_mask = (x >= x_min) & (x < x_max) & (y >= y_min) & (y < y_max)
    x_roi = x[roi_mask]
    y_roi = y[roi_mask]
    tot_roi = tot[roi_mask]
    
    # Initialize maps for ROI only
    hit_map = np.zeros((sensor_height, sensor_width), dtype=np.uint64)
    tot_map = np.zeros((sensor_height, sensor_width), dtype=np.float32)
    count_map = np.zeros((sensor_height, sensor_width), dtype=np.uint32)
    
    # Use np.add.at to accumulate values efficiently
    np.add.at(hit_map, (y_roi, x_roi), 1)
    np.add.at(tot_map, (y_roi, x_roi), tot_roi)
    np.add.at(count_map, (y_roi, x_roi), 1)

    #mean_tot_map = np.divide(tot_map, count_map, where=count_map>0)
    
    thl_pixel_data[thl] = {
        'hit_map': hit_map,
        #'mean_tot_map': mean_tot_map,
        'total_hits': np.sum(hit_map),
        'active_pixels': np.sum(hit_map > 0),
        'mean_tot': np.mean(pixel_data['tot'][thl_filter]) if np.any(thl_filter) else 0,
        'mean_toa': np.mean(pixel_data['toa'][thl_filter]) if np.any(thl_filter) else 0
    }
    print(f'Unique THL dataset created at THL={thl}')

# Find most active pixels across all THL levels
total_hit_map = np.zeros((sensor_height, sensor_width), dtype=np.uint64)
for data in thl_pixel_data.values():
    total_hit_map += data['hit_map']
    print(f'hit map created for {data}')
# Get top N active pixels
flat_indices = np.argsort(total_hit_map.flatten())[-n_pixels_to_plot:]
active_pixels = []
for idx in reversed(flat_indices):
    y, x = np.unravel_index(idx, total_hit_map.shape)
    if total_hit_map[y, x] > 0:
        active_pixels.append((x, y))
        print(f"Active pixel: ({x}, {y}) with {total_hit_map[y, x]} total hits")

active_pixels = active_pixels[:n_pixels_to_plot]

# Plot 1: Threshold vs Hit Count for active pixels
plt.figure(figsize=(12, 8))
colors = plt.cm.tab10(np.linspace(0, 1, len(active_pixels)))

for i, (x, y) in enumerate(active_pixels):
    hit_counts = []
    thresholds = []
    
    for thl in sorted(unique_thls):
        hit_map = thl_pixel_data[thl]['hit_map']
        hit_count = hit_map[y, x]
        hit_counts.append(hit_count)
        thresholds.append(thl)
    
    plt.plot(thresholds, hit_counts, 'o-', color=colors[i], linewidth=2, markersize=4)


plt.xlabel('Threshold (mV)', fontsize=12)
plt.ylabel('Hit Count', fontsize=12)
plt.title('Threshold vs Hit Count for Active Pixels', fontsize=14)
plt.legend([f'Pixel ({x},{y})' for (x, y) in active_pixels])
plt.grid(True, alpha=0.3)
plt.yscale('log')
plt.gca().invert_xaxis()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'threshold_curves.png'), dpi=300)
plt.show()


# Plot 3: Active Pixel Count vs Threshold
plt.figure(figsize=(12, 6))
active_pixel_counts = [thl_pixel_data[thl]['active_pixels'] for thl in sorted(unique_thls)]
plt.plot(sorted(unique_thls), active_pixel_counts, 'ro-', markersize=4, linewidth=1.5)
plt.gca().invert_xaxis()
plt.xlabel('Threshold (mV)', fontsize=12)
plt.ylabel('Active Pixel Count', fontsize=12)
plt.title('Number of Active Pixels vs Threshold', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'active_pixels_vs_threshold.png'), dpi=300)
plt.show()

# Plot 4: Total Hits vs Threshold
plt.figure(figsize=(12, 6))
total_hits = [thl_pixel_data[thl]['total_hits'] for thl in sorted(unique_thls)]
plt.plot(sorted(unique_thls), total_hits, 'go-', markersize=4, linewidth=1.5)
plt.gca().invert_xaxis()
plt.xlabel('Threshold (mV)', fontsize=12)
plt.ylabel('Total Hits', fontsize=12)
plt.title('Total Hits vs Threshold', fontsize=14)
plt.grid(True, alpha=0.3)
plt.yscale('log')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'total_hits_vs_threshold.png'), dpi=300)
plt.show()





# Convert to arrays
x_data = np.array(sorted(unique_thls))
y_data = np.array([thl_pixel_data[thl]['total_hits'] for thl in sorted(unique_thls)])

# Filter region between 600 and 700 mV
if energy_keV == "16keV":
    mask = (x_data <= 700) & (x_data >= 500)
elif energy_keV == "14keV":
    mask = (x_data <= 670) & (x_data >= 600)
elif energy_keV == "12keV":
    mask = (x_data <= 700) & (x_data >= 600)
elif energy_keV == "10keV":
    mask = (x_data <= 720) & (x_data >= 630)
elif energy_keV == "8keV":
    mask = (x_data <= 770) & (x_data >= 650)

x_fit = x_data[mask]
y_fit = y_data[mask]

# Only keep values > 0 to avoid log(0)
valid = y_fit > 0
x_fit = x_fit[valid]
y_fit_log = np.log10(y_fit[valid])

# Sigmoid in log space
def sigmoid_log(x, A, k, x0, y0):
    return A / (1 + np.exp(-k * (x - x0))) + y0

# Initial guess: try to match visually
p0 = [max(y_fit_log) - min(y_fit_log), -0.1, 650, min(y_fit_log)]

# Fit
popt_log, pcov_log = curve_fit(sigmoid_log, x_fit, y_fit_log, p0=p0, maxfev=10000)

# Evaluate fit
y_fit_smooth = 10**sigmoid_log(x_fit, *popt_log)

# Fit parameters
perr_log = np.sqrt(np.diag(pcov_log))
A, k, x0, y0 = popt_log
A_err, k_err, x0_err, y0_err = perr_log


# Plot
plt.figure(figsize=(10, 6))
plt.plot(x_data, y_data, 'go', label='Original data')
plt.plot(x_fit, y_fit_smooth, 'r-', linewidth=2, label=f'Sigmoid fit in log-space (x₀ = {x0:.3f} mV)')
plt.gca().invert_xaxis()
plt.yscale('log')
plt.xlabel('Threshold (mV)')
plt.ylabel('Total Hits')
plt.title('Improved S-curve Fit to Total Hits')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'Scurve_fit_to_total_hits.png'), dpi=300)
plt.show()

print(f"Fit (log-space): A = {A:.2f}, k = {k:.4f}, x0 = {x0:.2f}, y0 = {y0:.2f}")
print(f"Estimated 50% point (inflection): THL = {x0:.2f} mV")
print("\nAnalysis complete. Results saved in:", output_dir)



# Prepare data to export
stats_list = [{
    'timestamp': datetime.now().isoformat(timespec='seconds'),
    'filename': os.path.basename(filename),
    'energy': energy_keV,

    'shape': A,
    'shape_err': A_err,
    'loc': x0,
    'loc_err': x0_err,
    'scale': k,
    'scale_err': k_err
}]


csv_filename = "thl_analysis.csv"
unique_keys = ['filename', 'energy']

# Convert to DataFrame
new_data = pd.DataFrame(stats_list)

# Ensure consistent columns
column_order = [
    'timestamp', 'filename', 'energy',
    'shape', 'shape_err',
    'loc', 'loc_err',
    'scale', 'scale_err',
    'mean', 'mean_err',
    'median', 'median_err',
    'mode', 'mode_err',
    'fwhm', 'fwhm_err',
    'peak_tot_count',
    'peak_tot_fit'
]

for col in column_order:
    if col not in new_data.columns:
        new_data[col] = np.nan
new_data = new_data[column_order]

# Combine with previous file if exists
if os.path.exists(csv_filename):
    existing_data = pd.read_csv(csv_filename)
    mask = ~existing_data[unique_keys].apply(tuple, axis=1).isin(
        new_data[unique_keys].apply(tuple, axis=1)
    )
    combined = pd.concat([existing_data[mask], new_data], ignore_index=True)
else:
    combined = new_data

# Save to CSV
combined.to_csv(csv_filename, index=False)
print(f"[INFO] Analysis data written to {csv_filename}")