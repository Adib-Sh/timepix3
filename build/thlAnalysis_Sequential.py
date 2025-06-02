#!/usr/bin/env python3
"""
Enhanced THL Calibration Data Analysis Script
Updated to match C code data structures
"""

import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import os
from PIL import Image
import io

# Configuration
filename = "thl_calibration_20250529_144943.h5"  # Update with your actual filename
sensor_width = 256
sensor_height = 256
n_pixels_to_plot = 5

# Create output directory based on filename
base_name = os.path.splitext(os.path.basename(filename))[0]
output_dir = f"{base_name}_analysis"
plots_dir = os.path.join(output_dir, "individual_plots")

# Create directories
os.makedirs(output_dir, exist_ok=True)
os.makedirs(plots_dir, exist_ok=True)

# Define data types to match C code
pixel_dtype = np.dtype([
    ('x', 'i4'),
    ('y', 'i4'),
    ('integral_tot', 'u2'),
    ('event_count', 'u2'),
    ('hit_count', 'u1'),
    ('thl', 'i4')
])

# Load data
with h5py.File(filename, 'r') as f:
    # Check what datasets are available
    print("Datasets in file:")
    for key in f.keys():
        print(f"  {key}: {f[key].shape}")
    
    # Only pixel_hits dataset is available from C code
    pixel_data = f['/pixel_hits'][:]
    
    # Get attributes for scan parameters
    attrs = dict(f.attrs)
    thl_start = attrs['thl_start_mv']
    thl_end = attrs['thl_end_mv']
    thl_step = attrs['thl_step_mv']
    frames_per_thl = attrs['frames_per_thl']

# Reconstruct THL values from attributes
unique_thls = np.arange(thl_start, thl_end + thl_step, thl_step)
print(f"\nTHL levels: {len(unique_thls)} points from {thl_start} to {thl_end} mV")

# Organize pixel data by THL level
thl_pixel_data = {}
for thl in unique_thls:
    mask = pixel_data['thl'] == thl
    thl_pixels = pixel_data[mask]
    
    # Create 2D hit map
    hit_map = np.zeros((sensor_height, sensor_width), dtype=np.uint64)
    for pixel in thl_pixels:
        x, y = pixel['x'], pixel['y']
        if 0 <= x < sensor_width and 0 <= y < sensor_height:
            hit_map[y, x] += 1  # Count each hit
    
    thl_pixel_data[thl] = {
        'hit_map': hit_map,
        'total_hits': np.sum(hit_map),
        'active_pixels': np.sum(hit_map > 0),
        'mean_integral_tot': np.mean(pixel_data['integral_tot'][mask]) if np.any(mask) else 0
    }

# Find most active pixels across all THL levels
total_hit_map = np.zeros((sensor_height, sensor_width), dtype=np.uint64)
for data in thl_pixel_data.values():
    total_hit_map += data['hit_map']

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
    
    plt.plot(thresholds, hit_counts, 'o-', color=colors[i], 
            label=f'Pixel ({x}, {y})', linewidth=2, markersize=4)

plt.xlabel('Threshold (mV)', fontsize=12)
plt.ylabel('Hit Count', fontsize=12)
plt.title('Threshold vs Hit Count for Active Pixels', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)
plt.yscale('log')
plt.tight_layout()

# Save threshold curves plot
threshold_plot_path = os.path.join(output_dir, 'threshold_curves.png')
plt.savefig(threshold_plot_path, dpi=300, bbox_inches='tight')
plt.show()

# Plot 2: Mean integral TOT vs Threshold
plt.figure(figsize=(12, 6))
mean_tots = [thl_pixel_data[thl]['mean_integral_tot'] for thl in sorted(unique_thls)]
plt.plot(sorted(unique_thls), mean_tots, 'b-')
plt.xlabel('Threshold (mV)', fontsize=12)
plt.ylabel('Mean Integral TOT', fontsize=12)
plt.title('Mean Integral TOT vs Threshold', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'mean_tot_vs_threshold.png'), dpi=300)
plt.show()

# Plot 3: Active Pixel Count vs Threshold
plt.figure(figsize=(12, 6))
active_pixels = [thl_pixel_data[thl]['active_pixels'] for thl in sorted(unique_thls)]
plt.plot(sorted(unique_thls), active_pixels, 'ro-', markersize=4, linewidth=1.5)
plt.xlabel('Threshold (mV)', fontsize=12)
plt.ylabel('Active Pixel Count', fontsize=12)
plt.title('Number of Active Pixels vs Threshold', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'pixelCount_threshold.png'), dpi=300)
plt.show()

# Plot 4: Total hit vs Threshold
plt.figure(figsize=(12, 6))
pixels = [thl_pixel_data[thl]['total_hits'] for thl in sorted(unique_thls)]
plt.plot(sorted(unique_thls), pixels, 'ro-', markersize=4, linewidth=1.5)
plt.xlabel('Threshold (mV)', fontsize=12)
plt.ylabel('Total Hit Count', fontsize=12)
plt.title('Total Hit count vs Threshold', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'totalHit_threshold.png'), dpi=300)
plt.show()

# Determine color scale for 2D plots
all_hits = np.concatenate([data['hit_map'].flatten() for data in thl_pixel_data.values()])
all_hits = all_hits[all_hits > 0]
if len(all_hits) > 0:
    vmin = max(1, np.percentile(all_hits, 1))
    vmax = np.percentile(all_hits, 99.5)
else:
    vmin, vmax = 1, 10

print(f"Color scale: {vmin:.1f} - {vmax:.1f}")

# Create 2D sensor plots and GIF
frames = []
sorted_thls = sorted(unique_thls)
individual_plot_paths = []

for i, thl in enumerate(sorted_thls):   
    hit_map = thl_pixel_data[thl]['hit_map']
    total_hits = thl_pixel_data[thl]['total_hits']
    active_pixel_count = thl_pixel_data[thl]['active_pixels']
    mean_tot = thl_pixel_data[thl]['mean_integral_tot']
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    masked_data = np.ma.masked_where(hit_map <= 0, hit_map)
    
    # Plot
    im = ax.imshow(masked_data, cmap='viridis', norm=LogNorm(vmin=vmin, vmax=vmax),
                  origin='lower', interpolation='nearest')
    
    ax.set_title(f'THL = {thl:.1f} mV\nTotal Hits: {total_hits:,}, Active Pixels: {active_pixel_count:,}\nMean TOT: {mean_tot:.1f}',
                fontsize=14, pad=20)
    ax.set_xlabel('X (pixels)', fontsize=12)
    ax.set_ylabel('Y (pixels)', fontsize=12)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Hit Count', fontsize=12)
    
    # Save individual plot
    plot_filename = f"thl_{thl:.1f}mV_frame_{i+1:03d}.png"
    plot_path = os.path.join(plots_dir, plot_filename)
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    individual_plot_paths.append(plot_path)
    
    # Convert to image for GIF
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    frames.append(Image.open(buf))
    plt.close(fig)

# Save GIF
gif_path = os.path.join(output_dir, 'sensor_response.gif')
if frames:  # Only save if we have frames
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=200,
        loop=0
    )




# Create and save summary report
summary_path = os.path.join(output_dir, 'analysis_summary.txt')
with open(summary_path, 'w') as f:
    f.write("THL CALIBRATION ANALYSIS SUMMARY\n")
    f.write("=" * 50 + "\n")
    f.write(f"Input file: {filename}\n")
    f.write(f"Analysis date: {os.path.basename(output_dir)}\n\n")
    
    f.write("DATASET INFORMATION:\n")
    f.write(f"  Pixel hit records: {len(pixel_data)}\n")
    f.write(f"  Sensor dimensions: {sensor_width} x {sensor_height}\n\n")
    
    f.write("THL SCAN PARAMETERS:\n")
    f.write(f"  THL levels: {len(unique_thls)}\n")
    f.write(f"  THL range: {min(unique_thls):.1f} - {max(unique_thls):.1f} mV\n")
    f.write(f"  THL step: {thl_step:.1f} mV\n")
    f.write(f"  Frames per THL: {frames_per_thl}\n\n")
    
    total_hits_by_thl = [thl_pixel_data[thl]['total_hits'] for thl in sorted_thls]
    active_pixels_by_thl = [thl_pixel_data[thl]['active_pixels'] for thl in sorted_thls]
    
    f.write("ACTIVITY STATISTICS:\n")
    f.write(f"  Total hits range: {min(total_hits_by_thl):,} - {max(total_hits_by_thl):,}\n")
    f.write(f"  Active pixels range: {min(active_pixels_by_thl):,} - {max(active_pixels_by_thl):,}\n")
    
    max_hits_idx = np.argmax(total_hits_by_thl)
    max_hits_thl = sorted_thls[max_hits_idx]
    f.write(f"  Peak activity: {max_hits_thl:.1f} mV ({max(total_hits_by_thl):,} hits)\n\n")
    

print("\nAnalysis complete. Results saved in:", output_dir)
