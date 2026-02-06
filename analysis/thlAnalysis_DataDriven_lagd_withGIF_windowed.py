import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import glob
import os
from PIL import Image
import io
import seaborn as sns

#input_dir = "/home/adisha/git/libkatherine/build/THLScan20250524"
input_dir = "/home/adisha/git/libkatherine/build/LGAD_0142_data_20251126/"
input_file = input_dir+"/thl_calibration_20260206_093639.h5"
sensor_width = 256
sensor_height = 256
n_pixels_to_plot = 16
base_name = os.path.splitext(os.path.basename(input_file))[0]
output_dir = f"{base_name}_analysis"
plots_dir = os.path.join(output_dir, "individual_plots")
os.makedirs(output_dir, exist_ok=True)
os.makedirs(plots_dir, exist_ok=True)

plt.style.use('default')
sns.set(
    style="white",
    context="talk",
    palette="deep"
)

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
with h5py.File(input_file, 'r') as f:
    print("Datasets in file:")
    for key in f.keys():
        print(f"  {key}: {f[key].shape}")
    
    pixel_data = f['/pixel_hits'][:]
    attrs = dict(f.attrs)
    thl_start = attrs['thl_start_mv']
    thl_end = attrs['thl_end_mv']
    thl_step = attrs['thl_step_mv']
    frames_per_thl = attrs['frames_per_thl']

unique_thls = np.arange(thl_start, thl_end + thl_step, thl_step)
print(f"\nTHL levels: {len(unique_thls)} points from {thl_start} to {thl_end} mV")

x_min, x_max = 0, 30  # Change these to focus on a specific region
y_min, y_max = 130, 180  # Change these to focus on a specific region

thl_pixel_data = {}
for thl in unique_thls:
    thl_filter = pixel_data['thl'] == thl
    thl_pixels = pixel_data[thl_filter]
    
    hit_map = np.zeros((sensor_height, sensor_width), dtype=np.uint64)
    tot_map = np.zeros((sensor_height, sensor_width), dtype=np.float32)
    count_map = np.zeros((sensor_height, sensor_width), dtype=np.uint32)
    
    for pixel in thl_pixels:
        x, y = pixel['x'], pixel['y']
    
        # Apply analysis window
        if x_min <= x < x_max and y_min <= y < y_max:
            hit_map[y, x] += 1
            tot_map[y, x] += pixel['tot']
            count_map[y, x] += 1
    mean_tot_map = np.divide(tot_map, count_map, where=count_map>0)
    window_hits = hit_map[y_min:y_max, x_min:x_max]
    thl_pixel_data[thl] = {
        'hit_map': hit_map,
        'mean_tot_map': mean_tot_map,
        'active_pixels': np.sum(window_hits > 0),
        'total_hits': np.sum(window_hits),
        'mean_tot': np.mean(pixel_data['tot'][thl_filter]) if np.any(thl_filter) else 0,
        'mean_toa': np.mean(pixel_data['toa'][thl_filter]) if np.any(thl_filter) else 0
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
plt.figure(figsize=(10, 6))
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

plt.xlabel('Threshold (mV)', fontsize=16)
plt.ylabel('Hit Count', fontsize=16)
plt.title('Threshold vs Hit Count for Active Pixels', fontsize=18)
plt.legend(fontsize=8)
plt.grid(True, alpha=0.3)
plt.gca().invert_xaxis()
plt.yscale('log')
plt.tight_layout()

threshold_plot_path = os.path.join(output_dir, 'threshold_curves.png')
plt.savefig(threshold_plot_path, dpi=300, bbox_inches='tight')
plt.show()

# Plot 1.5: Threshold vs Hit Count for sum of all active pixels
plt.figure(figsize=(10, 6))

total_hit_counts = []
thresholds = []

for thl in sorted(unique_thls):
    hit_map = thl_pixel_data[thl]['hit_map']
    # Sum hit counts for all active pixels at this threshold
    total_hits = sum(hit_map[y, x] for x, y in active_pixels)
    total_hit_counts.append(total_hits)
    thresholds.append(thl)

plt.plot(thresholds, total_hit_counts, 'go-', linewidth=2, markersize=6)
plt.xlabel('Threshold (mV)', fontsize=16)
plt.ylabel('Total Hit Count', fontsize=16)
plt.title('Threshold vs Total Hit Count (Sum of All Active Pixels)', fontsize=18)
plt.grid(True, alpha=0.3)
plt.gca().invert_xaxis()
plt.yscale('log')
plt.tight_layout()
threshold_plot_path = os.path.join(output_dir, 'threshold_curve_all_active.png')
plt.savefig(threshold_plot_path, dpi=300, bbox_inches='tight')
plt.show()

# Plot 2: Mean TOT vs Threshold
plt.figure(figsize=(10, 6))
mean_tots = [thl_pixel_data[thl]['mean_tot'] for thl in sorted(unique_thls)]
plt.plot(sorted(unique_thls), mean_tots, 'b-')
plt.xlabel('Threshold (mV)', fontsize=16)
plt.ylabel('Mean TOT',fontsize=16)
plt.title('Mean Time Over Threshold vs Threshold', fontsize=18)
plt.grid(True, alpha=0.3)
plt.gca().invert_xaxis()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'mean_tot_vs_threshold.png'), dpi=300)
plt.show()

# Plot 3: Active Pixel Count vs Threshold
plt.figure(figsize=(10, 6))
active_pixels_count = [thl_pixel_data[thl]['active_pixels'] for thl in sorted(unique_thls)]
plt.plot(sorted(unique_thls), active_pixels_count, 'ro-', markersize=4, linewidth=1.5)
plt.xlabel('Threshold (mV)', fontsize=16)
plt.ylabel('Active Pixel Count', fontsize=16)
plt.title('Number of Active Pixels vs Threshold', fontsize=18)
plt.grid(True, alpha=0.3)
plt.gca().invert_xaxis()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'active_pixels_vs_threshold.png'), dpi=300)
plt.show()

# Plot 4: Total Hits vs Threshold
plt.figure(figsize=(10, 6))
total_hits = [thl_pixel_data[thl]['total_hits'] for thl in sorted(unique_thls)]
plt.plot(sorted(unique_thls), total_hits, 'go-', markersize=4, linewidth=1.5)
plt.xlabel('Threshold (mV)', fontsize=16)
plt.ylabel('Total Hits', fontsize=16)
plt.title('Total Hits vs Threshold', fontsize=18)
plt.grid(True, alpha=0.3)
plt.yscale('log')
plt.gca().invert_xaxis()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'total_hits_vs_threshold.png'), dpi=300)
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


# Create original 2D sensor plots and GIF
frames = []
sorted_thls = sorted(unique_thls)
individual_plot_paths = []

for i, thl in enumerate(sorted_thls):   
    hit_map = thl_pixel_data[thl]['hit_map']
    total_hits_val = thl_pixel_data[thl]['total_hits']
    active_pixel_count = thl_pixel_data[thl]['active_pixels']
    mean_tot = thl_pixel_data[thl]['mean_tot']
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    masked_data = np.ma.masked_where(hit_map <= 0, hit_map)
    
    im = ax.imshow(masked_data, cmap='viridis', norm=LogNorm(vmin=vmin, vmax=vmax),
                  origin='lower', interpolation='nearest')
    
    ax.set_title(f'THL = {thl:.1f} mV\nTotal Hits: {total_hits_val:,}, Active Pixels: {active_pixel_count:,}\nMean TOT: {mean_tot:.1f}',
                fontsize=14, pad=20)
    ax.set_xlabel('X (pixels)', fontsize=14)
    ax.set_ylabel('Y (pixels)', fontsize=14)
    #plt.gca().invert_xaxis()
    
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Hit Count', fontsize=14)
    
    plot_filename = f"thl_{thl:.1f}mV_frame_{i+1:03d}.png"
    plot_path = os.path.join(plots_dir, plot_filename)
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    individual_plot_paths.append(plot_path)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    frames.append(Image.open(buf))
    plt.close(fig)

# Save original GIF
gif_path = os.path.join(output_dir, 'sensor_response.gif')
if frames:
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=250,
        loop=0
    )
    



print("\nCreating combined GIF...")
combined_gif_path = os.path.join(output_dir, 'combined_sensor_threshold.gif')
temp_combined_dir = os.path.join(output_dir, "temp_combined_frames")
os.makedirs(temp_combined_dir, exist_ok=True)

# Calculate total hit counts for all active pixels (for the plot)
total_hit_counts_sum = []
for thl in sorted_thls:
    hit_map = thl_pixel_data[thl]['hit_map']
    total_hits_sum = sum(hit_map[y, x] for x, y in active_pixels)
    total_hit_counts_sum.append(total_hits_sum)

# First pass: create and save frames to disk
combined_frame_paths = []
for i, thl in enumerate(sorted_thls):
    hit_map = thl_pixel_data[thl]['hit_map']
    total_hits_val = thl_pixel_data[thl]['total_hits']
    active_pixel_count = thl_pixel_data[thl]['active_pixels']
    current_sum = total_hit_counts_sum[i]
    
    # Create figure with two subplots side by side
    fig = plt.figure(figsize=(18, 6), dpi=100)  # Made wider for rectangular plot
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.5], wspace=0.3)  # More space for threshold plot
    
    # Left panel: 2D sensor map (custom window)
    ax1 = fig.add_subplot(gs[0])
    
    # Extract the custom window from the hit map
    hit_map_window = hit_map[y_min:y_max, x_min:x_max]
    masked_data = np.ma.masked_where(hit_map_window <= 0, hit_map_window)
    
    im = ax1.imshow(masked_data, cmap='viridis', norm=LogNorm(vmin=vmin, vmax=vmax),
                    origin='lower', interpolation='nearest',
                    extent=[x_min, x_max, y_min, y_max])
    ax1.set_title(f'Sensor Response at THL = {thl:.1f} mV', fontsize=12, fontweight='bold')
    ax1.set_xlabel('X (pixels)', fontsize=10)
    ax1.set_ylabel('Y (pixels)', fontsize=10)
    ax1.set_xlim(x_min, x_max)
    ax1.set_ylim(y_min, y_max)
    cbar = plt.colorbar(im, ax=ax1, shrink=0.8)
    cbar.set_label('Hit Count', fontsize=10)
    
    # Right panel: Total hits (sum of active pixels) vs threshold with vertical line
    ax2 = fig.add_subplot(gs[1])
    ax2.plot(sorted_thls, total_hit_counts_sum, 'go-', markersize=4, linewidth=1.5, 
             label='Sum of Active Pixels')
    ax2.axvline(x=thl, color='red', linestyle='--', linewidth=2.5, label=f'Current: {thl:.1f} mV')
    ax2.set_xlabel('Threshold (mV)', fontsize=10)
    ax2.set_ylabel('Total Hit Count (Active Pixels)', fontsize=10)
    ax2.set_title('Total Hit Count vs Threshold (Sum of Active Pixels)', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')
    ax2.invert_xaxis()  # Invert x-axis
    ax2.legend(fontsize=9)
    
    # Add text box with current statistics
    stats_text = f'Current Sum: {current_sum:,}\nTotal Hits (All): {total_hits_val:,}\nActive Pixels: {active_pixel_count:,}'
    ax2.text(0.98, 0.98, stats_text, transform=ax2.transAxes, 
             fontsize=9, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.suptitle(f'THL Calibration Analysis - Step {i+1}/{len(sorted_thls)}', 
                 fontsize=13, fontweight='bold', y=0.98)
    
    # Save frame to disk
    frame_path = os.path.join(temp_combined_dir, f'combined_frame_{i:03d}.png')
    plt.savefig(frame_path, format='png', dpi=100, bbox_inches='tight')
    combined_frame_paths.append(frame_path)
    plt.close(fig)
    
    if (i + 1) % 5 == 0:
        print(f"  Processed {i+1}/{len(sorted_thls)} frames")

# Second pass: load frames one at a time and create GIF
print("  Assembling GIF from saved frames...")
if combined_frame_paths:
    # Load first frame
    first_frame = Image.open(combined_frame_paths[0])
    
    # Create list to hold frames, but load them lazily
    remaining_frames = [Image.open(fp) for fp in combined_frame_paths[1:]]
    
    # Save GIF
    first_frame.save(
        combined_gif_path,
        save_all=True,
        append_images=remaining_frames,
        duration=250,
        loop=0,
        optimize=True  # Optimize GIF size
    )
    
    # Close all image objects
    first_frame.close()
    for frame in remaining_frames:
        frame.close()
    
    print(f"Combined GIF saved: {combined_gif_path}")
    

# Create and save summary report
summary_path = os.path.join(output_dir, 'analysis_summary.txt')
with open(summary_path, 'w') as f:
    f.write("THL CALIBRATION ANALYSIS SUMMARY\n")
    f.write("=" * 50 + "\n")
    f.write(f"Input file: {input_file}\n")
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
print(f"  - Original GIF: {gif_path}")
print(f"  - Combined GIF: {combined_gif_path}")