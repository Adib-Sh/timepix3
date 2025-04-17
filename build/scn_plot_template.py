import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from mpl_toolkits.mplot3d import Axes3D
from scipy.ndimage import gaussian_filter
from sklearn.cluster import DBSCAN
from scipy.stats import binned_statistic
from scipy import stats

# Load data
with h5py.File('pixel_data_Si_5e9s_20250406_033436.h5', 'r') as f:
    hits = f['/pixel_hits'][:]

# Calculate basic metrics
time_ns = hits['toa'] - hits['toa'].min()
time_sec = time_ns / 1e9
hit_rate = len(hits) / time_sec.max()
hitmap, xedges, yedges = np.histogram2d(hits['x'], hits['y'], bins=[128, 128], range=[[0, 255], [0, 255]])


# =============================================
# Figure 1: 3D Pixel Hitmap Per Pixel
# =============================================

# Create per-pixel hit count array
hit_count_map = np.zeros((256, 256), dtype=int)
for hit in hits:
    x, y = hit['x'], hit['y']
    if 0 <= x < 256 and 0 <= y < 256:
        hit_count_map[y, x] += 1

# Outlier removal
non_zero_mask = hit_count_map > 0
hit_counts_non_zero = hit_count_map[non_zero_mask]
z_scores = np.abs(stats.zscore(hit_counts_non_zero))
outlier_threshold = 3 #how many sigma
clean_hit_counts = np.copy(hit_count_map)
clean_hit_counts[non_zero_mask] = np.where(z_scores < outlier_threshold, hit_counts_non_zero, 0)

# Visualization limits
max_display_hits = np.percentile(clean_hit_counts[clean_hit_counts > 0], 99) if np.any(clean_hit_counts > 0) else 1
clipped_hits = np.clip(clean_hit_counts, 0, max_display_hits)

# Create figure with 2 subplots
fig = plt.figure(figsize=(20, 9))

# Add unified title
fig.suptitle('Sensor Per-Pixel Hit Count', fontsize=16, y=1.05)

cmap = plt.cm.plasma
norm = LogNorm(vmin=1, vmax=max_display_hits)

# =====================
# 3D Plot with Plasma Colormap (Left)
# =====================
ax1 = fig.add_subplot(121, projection='3d')

# Prepare 3D coordinates
x, y = np.meshgrid(np.arange(256), np.arange(256))
x = x.flatten()
y = y.flatten()
z = np.zeros_like(x)
dx = dy = 0.8 * np.ones_like(x)
dz = clipped_hits.flatten()

# Plot 3D with plasma colormap
hit_mask = dz > 0
ax1.bar3d(x[hit_mask], y[hit_mask], z[hit_mask],
          dx[hit_mask], dy[hit_mask], dz[hit_mask],
          color='skyblue',
          edgecolor='skyblue', linewidth=0.2, alpha=0.8)

ax1.set_title('3D Per-Pixel View', pad=15)
ax1.set_xlabel('X Coordinate', labelpad=14)
ax1.set_ylabel('Y Coordinate', labelpad=14)
ax1.set_zlabel('Hit Count', labelpad=14)
# Set viewing angle to look "into" the plot
ax1.view_init(elev=25, azim=-45)
ax1.set_xlim(0, 255)
ax1.set_ylim(0, 255)
ax1.set_zlim(0, dz.max()*1.1)
ax1.grid(True, linestyle=':', alpha=0.5)

# =====================
# 2D Heatmap with Viridis (Right)
# =====================
ax2 = fig.add_subplot(122)
im = ax2.imshow(clipped_hits, origin='lower', cmap=cmap, norm=norm)
ax2.set_title('2D Heatmap View', pad=15)
ax2.set_xlabel('X Coordinate', labelpad=14)
ax2.set_ylabel('Y Coordinate', labelpad=14)

# Add colorbars
mappable3D = plt.cm.ScalarMappable(cmap='plasma', norm=plt.Normalize(vmin=1, vmax=max_display_hits))
mappable3D.set_array(dz[hit_mask])


cbar2 = fig.colorbar(im, ax=ax2, shrink=1, pad=0.02)
cbar2.set_label('Hit Count', rotation=270, labelpad=15)

# Add grid to 2D plot
ax2.grid(True, which='both', color='white', linestyle=':', alpha=0.5)

# Add statistics annotation
stats_text = (f"Active Pixels: {np.sum(hit_mask):,}\n"
             f"Max Displayed: {max_display_hits:.0f}\n"
             f"Original Max: {np.max(hit_count_map):,}")
ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes,
         ha='left', va='top', bbox=dict(facecolor='white', alpha=0.8))

plt.tight_layout()
plt.show()

# =============================================
# Figure 2: 3D Pixel Hitmap 32*32 bins
# =============================================
# Correct way to bin the cleaned data into 32x32
hist, xedges, yedges = np.histogram2d(
    hits['x'],  # Use original hit coordinates
    hits['y'],
    bins=[32, 32],
    range=[[0, 255], [0, 255]],
    weights=clean_hit_counts[hits['y'], hits['x']]  # Apply cleaned weights
)

# Clip to 99th percentile
max_display_hits = np.percentile(hist[hist > 0], 99) if np.any(hist > 0) else 1
clipped_hist = np.clip(hist, 0, max_display_hits)

# Create figure
fig = plt.figure(figsize=(20, 9))
fig.suptitle('Sensor 32*32 bins Hit Count', fontsize=16, y=1.05)
# =====================================
# 3D Binned Plot (32×32) - Left (Skyblue)
# =====================================´
ax1 = fig.add_subplot(121, projection='3d')

# 3D coordinates
xpos, ypos = np.meshgrid(xedges[:-1], yedges[:-1])
xpos, ypos = xpos.flatten(), ypos.flatten()
zpos = np.zeros_like(xpos)
dx = dy = 8 * np.ones_like(zpos)
dz = clipped_hist.flatten()

# Plot 3D bars
ax1.bar3d(ypos, xpos, zpos, dy, dx, dz,
          color='skyblue',
          edgecolor='k', alpha=0.8, linewidth=0.5)

ax1.set_title('3D 32*32 bins Hitmap', pad=15)
ax1.set_xlabel('X Coordinate', labelpad=10)
ax1.set_ylabel('Y Coordinate', labelpad=10)
ax1.set_zlabel('Hit Count', labelpad=10)
# Set viewing angle to look "into" the plot
ax1.view_init(elev=25, azim=-45)  # Adjusted for better origin visibility

# Manually set axis limits if needed
ax1.set_xlim(0, 255)
ax1.set_ylim(0, 255)
ax1.set_zlim(0, dz.max()*1.1)
ax1.grid(True, linestyle=':', alpha=0.5)

# =====================================
# 2D Heatmap (32×32) - Right (Plasma)
# =====================================
ax2 = fig.add_subplot(122)

# Plot heatmap with plasma
im = ax2.imshow(clipped_hist.T, origin='lower', 
                extent=[0, 255, 0, 255],
                cmap='plasma',
                interpolation='nearest')

ax2.set_title('2D 32*32 bins Heatmap', pad=15)
ax2.set_xlabel('X Coordinate')
ax2.set_ylabel('Y Coordinate')

# Add colorbar
cbar = fig.colorbar(im, ax=ax2, shrink=1)
cbar.set_label('Hit Count', rotation=270, labelpad=15)

# Add grid and statistics
ax2.grid(True, color='white', linestyle=':', alpha=0.3)
stats_text = (f"Active Bins: {np.sum(clipped_hist > 0)}/1024\n"
             f"Max Displayed: {max_display_hits:.0f}\n"
             f"Original Max: {np.max(hist):.0f}")
ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes,
         ha='left', va='top', bbox=dict(facecolor='white', alpha=0.8))

plt.tight_layout()
plt.show()

# =============================================
# Figure 2: 3D ToT Distribution
# =============================================
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')
tot_hist, _, _ = np.histogram2d(hits['x'], hits['y'], bins=[32, 32], range=[[0, 255], [0, 255]], weights=hits['tot'])
counts, _, _ = np.histogram2d(hits['x'], hits['y'], bins=[32, 32], range=[[0, 255], [0, 255]])
mean_tot = np.divide(tot_hist, counts, out=np.zeros_like(tot_hist), where=counts!=0)
surf = ax.plot_surface(xpos.reshape(32, 32), ypos.reshape(32, 32), mean_tot.T, cmap='plasma', edgecolor='none')
fig.colorbar(surf, ax=ax, label='Mean ToT')
ax.set_title('Figure 2: 3D ToT Distribution')
ax.set_xlabel('X coordinate')
ax.set_ylabel('Y coordinate')
ax.set_zlabel('Mean ToT')
plt.tight_layout()
plt.show()

# =============================================
# Figure 3: 3D ToA Distribution
# =============================================
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')
toa_hist, _, _ = np.histogram2d(hits['x'], hits['y'], bins=[32, 32], range=[[0, 255], [0, 255]], weights=time_ns)
mean_toa = np.divide(toa_hist, counts, out=np.zeros_like(toa_hist), where=counts!=0)
surf = ax.plot_surface(xpos.reshape(32, 32), ypos.reshape(32, 32), mean_toa.T/1e6, cmap='magma', edgecolor='none')
fig.colorbar(surf, ax=ax, label='Mean ToA (ms)')
ax.set_title('Figure 3: 3D ToA Distribution')
ax.set_xlabel('X coordinate')
ax.set_ylabel('Y coordinate')
ax.set_zlabel('Mean ToA (ms)')
plt.tight_layout()
plt.show()

# =============================================
# Figure 4: ToT Distribution (Energy Spectrum)
# =============================================
plt.figure(figsize=(10, 6))
plt.hist(hits['tot'], bins=100, range=(0, np.percentile(hits['tot'], 99.9)))
plt.xlabel('Time Over Threshold (ToT)')
plt.ylabel('Count')
plt.title('Figure 4: ToT Distribution (Energy Proxy)')
plt.grid(True)
plt.show()

# =============================================
# Figure 5: Hit Rate Over Time
# =============================================
plt.figure(figsize=(10, 6))
time_bins = np.linspace(0, time_sec.max(), 100)
plt.hist(time_sec, bins=time_bins)
plt.xlabel('Time (s)')
plt.ylabel('Hit Rate (counts/bin)')
plt.title(f'Figure 5: Hit Rate Over Time (Avg: {hit_rate:.0f} hits/s)')
plt.grid(True)
plt.show()

# =============================================
# Figure 6: Smoothed Pixel Hitmap
# =============================================
plt.figure(figsize=(10, 8))
smooth_hitmap = gaussian_filter(hitmap, sigma=1.5)
plt.imshow(smooth_hitmap.T, origin='lower', cmap='viridis', norm=LogNorm())
plt.colorbar(label='Hit Count (log scale)')
plt.title('Figure 6: Smoothed Pixel Hitmap')
plt.xlabel('X coordinate')
plt.ylabel('Y coordinate')
plt.show()

# =============================================
# Figure 7: ToT vs ToA Correlation
# =============================================
plt.figure(figsize=(10, 8))
plt.hexbin(hits['tot'], time_ns/1e6, bins='log', gridsize=50, cmap='plasma')
plt.colorbar(label='log10(count)')
plt.xlabel('Time Over Threshold (ToT)')
plt.ylabel('Time of Arrival (ms)')
plt.title('Figure 7: ToT vs ToA Correlation')
plt.grid(True)
plt.show()

# =============================================
# Figure 8: Pixel Hit Count Distribution
# =============================================
plt.figure(figsize=(10, 6))
pixel_hits = np.unique(hits[['x', 'y']], axis=0, return_counts=True)[1]
plt.hist(pixel_hits, bins=50, log=True)
plt.xlabel('Hits per Pixel')
plt.ylabel('Number of Pixels (log scale)')
plt.title('Figure 8: Pixel Hit Count Distribution')
plt.grid(True)
plt.show()

# =============================================
# Figure 9: Cluster Identification
# =============================================
plt.figure(figsize=(10, 8))
sample_size = min(10000, len(hits))
sample_idx = np.random.choice(len(hits), size=sample_size, replace=False)
sample_hits = hits[sample_idx]
coords = np.column_stack((sample_hits['x'], sample_hits['y'], sample_hits['toa']/1e7))
clustering = DBSCAN(eps=5, min_samples=5).fit(coords)
plt.scatter(sample_hits['x'], sample_hits['y'], c=clustering.labels_, cmap='nipy_spectral', s=5, alpha=0.7)
plt.colorbar(label='Cluster ID')
plt.title(f'Figure 9: Cluster Identification (n={len(set(clustering.labels_))-1} clusters)')
plt.xlabel('X coordinate')
plt.ylabel('Y coordinate')
plt.grid(True)
plt.show()

# =============================================
# Figure 10: Timewalk Analysis
# =============================================
plt.figure(figsize=(12, 6))
active_pixels = np.unique(hits[['x', 'y']], axis=0)
sample_pixel = active_pixels[np.random.choice(len(active_pixels))]
pixel_mask = (hits['x'] == sample_pixel[0]) & (hits['y'] == sample_pixel[1])
pixel_hits = hits[pixel_mask]
tot_bins = np.linspace(0, np.percentile(pixel_hits['tot'], 95), 20)
mean_toa = binned_statistic(pixel_hits['tot'], pixel_hits['toa'], statistic='mean', bins=tot_bins)[0]
bin_centers = (tot_bins[:-1] + tot_bins[1:]) / 2

plt.scatter(pixel_hits['tot'], pixel_hits['toa'], alpha=0.3)
plt.plot(bin_centers, mean_toa, 'r-', linewidth=2)
plt.xlabel('ToT (Energy Proxy)')
plt.ylabel('ToA (ns)')
plt.title(f'Figure 10: Timewalk Analysis for Pixel ({sample_pixel[0]}, {sample_pixel[1]})')
plt.grid(True)

if np.sum(~np.isnan(mean_toa)) > 3:
    slope = np.polyfit(bin_centers[~np.isnan(mean_toa)], mean_toa[~np.isnan(mean_toa)], 1)[0]
    plt.text(0.7, 0.1, f'Slope: {slope:.2f} ns/ToT', transform=plt.gca().transAxes, bbox=dict(facecolor='white', alpha=0.8))
plt.show()