import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from mpl_toolkits.mplot3d import Axes3D
from scipy import stats
import matplotlib as mpl

# ======================
# Style Setup
# ======================
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
# Load Data
# ======================
with h5py.File('pixel_data_Si_5e9s_20250406_033436.h5', 'r') as f:
    hits = f['/pixel_hits'][:]

# ======================
# Preprocessing
# ======================
time_ns = hits['toa'] - hits['toa'].min()
time_sec = time_ns / 1e9
hit_rate = len(hits) / time_sec.max()

# Build 256x256 hit map
hit_count_map = np.zeros((256, 256), dtype=int)
np.add.at(hit_count_map, (hits['y'], hits['x']), 1)

# Outlier removal using z-score
non_zero_mask = hit_count_map > 0
hit_counts_non_zero = hit_count_map[non_zero_mask]
z_scores = np.abs(stats.zscore(hit_counts_non_zero))
clean_hit_counts = np.copy(hit_count_map)
clean_hit_counts[non_zero_mask] = np.where(z_scores < 3, hit_counts_non_zero, 0)

# Clip values for visualization
max_display_hits = np.percentile(clean_hit_counts[clean_hit_counts > 0], 99) if np.any(clean_hit_counts > 0) else 1
clipped_hits = np.clip(clean_hit_counts, 0, max_display_hits)
cmap = plt.cm.inferno
norm = LogNorm(vmin=1, vmax=max_display_hits)

# ======================
# Figure 1: Full Pixel Map (256x256)
# ======================
fig = plt.figure(figsize=(20, 9))
fig.suptitle('Sensor Per-Pixel Hit Count', y=1.05, color='white')

# --- 3D Plot ---
ax1 = fig.add_subplot(121, projection='3d')
x, y = np.meshgrid(np.arange(256), np.arange(256))
x = x.flatten()
y = y.flatten()
z = np.zeros_like(x)
dx = dy = 0.8 * np.ones_like(x)
dz = clipped_hits.flatten()
hit_mask = dz > 0

ax1.bar3d(x[hit_mask], y[hit_mask], z[hit_mask],
          dx[hit_mask], dy[hit_mask], dz[hit_mask],
          color=cmap(norm(dz[hit_mask])),
          edgecolor='none', linewidth=0.1, alpha=0.95, shade=True)

ax1.set_title('3D Per-Pixel View', color='white')
ax1.set_xlabel('X Coordinate')
ax1.set_ylabel('Y Coordinate')
ax1.set_zlabel('Hit Count')
ax1.set_xlim(0, 255)
ax1.set_ylim(0, 255)
ax1.set_zlim(0, dz.max() * 1.1)
ax1.view_init(elev=25, azim=-45)
ax1.grid(True, linestyle=':', alpha=0.2)

# --- 2D Heatmap ---
ax2 = fig.add_subplot(122)
im = ax2.imshow(clipped_hits, origin='lower', cmap=cmap, norm=norm)
ax2.set_title('2D Heatmap View', color='white')
ax2.set_xlabel('X Coordinate')
ax2.set_ylabel('Y Coordinate')
cbar2 = fig.colorbar(im, ax=ax2, shrink=0.9, aspect=20, pad=0.02)
cbar2.set_label('Hit Count', rotation=270, labelpad=15)
ax2.grid(True, which='both', color='white', linestyle=':', alpha=0.2)
ax2.minorticks_on()

stats_text = (f"Active Pixels: {np.sum(hit_mask):,}\n"
              f"Max Displayed: {max_display_hits:.0f}\n"
              f"Original Max: {np.max(hit_count_map):,}")
ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes,
         ha='left', va='top', color='white',
         bbox=dict(facecolor='black', alpha=0.6, edgecolor='white'))

plt.tight_layout()
plt.show()

# ======================
# Figure 2: Binned 32×32 Version
# ======================
hist, xedges, yedges = np.histogram2d(
    hits['x'], hits['y'],
    bins=[32, 32],
    range=[[0, 255], [0, 255]],
    weights=clean_hit_counts[hits['y'], hits['x']]
)

max_display_hits = np.percentile(hist[hist > 0], 99) if np.any(hist > 0) else 1
clipped_hist = np.clip(hist, 0, max_display_hits)

fig = plt.figure(figsize=(20, 9))
fig.suptitle('Sensor 32×32 Binned Hit Count', y=1.05)

# --- 3D Binned Plot ---
ax1 = fig.add_subplot(121, projection='3d')
xpos, ypos = np.meshgrid(xedges[:-1], yedges[:-1])
xpos, ypos = xpos.flatten(), ypos.flatten()
zpos = np.zeros_like(xpos)
dx = dy = 8 * np.ones_like(zpos)
dz = clipped_hist.flatten()

ax1.bar3d(ypos, xpos, zpos, dy, dx, dz,
          color=cmap(norm(dz)),
          edgecolor='none', linewidth=0.2, alpha=0.95, shade=True)

ax1.set_title('3D 32×32 Binned Hitmap', color='white')
ax1.set_xlabel('X Coordinate')
ax1.set_ylabel('Y Coordinate')
ax1.set_zlabel('Hit Count')
ax1.set_xlim(0, 255)
ax1.set_ylim(0, 255)
ax1.set_zlim(0, dz.max() * 1.1)
ax1.view_init(elev=25, azim=-45)
ax1.grid(True, linestyle=':', alpha=0.2)

# --- 2D Heatmap ---
ax2 = fig.add_subplot(122)
im = ax2.imshow(clipped_hist.T, origin='lower',
                extent=[0, 255, 0, 255],
                cmap=cmap, interpolation='nearest')

ax2.set_title('2D 32×32 Binned Heatmap')
ax2.set_xlabel('X Coordinate')
ax2.set_ylabel('Y Coordinate')
cbar = fig.colorbar(im, ax=ax2, shrink=0.9, aspect=20, pad=0.02)
cbar.set_label('Hit Count', rotation=270, labelpad=15)
ax2.grid(True, color='white', linestyle=':', alpha=0.2)
ax2.minorticks_on()

stats_text = (f"Active Bins: {np.sum(clipped_hist > 0)}/1024\n"
              f"Max Displayed: {max_display_hits:.0f}\n"
              f"Original Max: {np.max(hist):.0f}")
ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes,
         ha='left', va='top', color='white',
         bbox=dict(facecolor='black', alpha=0.6, edgecolor='white'))

plt.tight_layout()
plt.show()

# ======================
# Figure 3: Per-Pixel 3D ToT and ToA Distribution with Outlier Filtering
# ======================
fig = plt.figure(figsize=(24, 12))
fig.suptitle('Sensor Per-Pixel ToT and ToA Level Distribution', y=1.05)

# --- Prepare grid ---
x_edges = np.arange(257)
y_edges = np.arange(257)
x_centers = (x_edges[:-1] + x_edges[1:]) / 2
y_centers = (y_edges[:-1] + y_edges[1:]) / 2
xpos, ypos = np.meshgrid(x_centers, y_centers)

# --- Per-pixel histograms ---
tot_hist, _, _ = np.histogram2d(hits['x'], hits['y'], bins=[x_edges, y_edges], weights=hits['tot'])
toa_hist, _, _ = np.histogram2d(hits['x'], hits['y'], bins=[x_edges, y_edges], weights=time_ns)
counts, _, _ = np.histogram2d(hits['x'], hits['y'], bins=[x_edges, y_edges])

# --- Compute means ---
mean_tot = np.divide(tot_hist, counts, out=np.zeros_like(tot_hist), where=counts != 0)
mean_toa = np.divide(toa_hist, counts, out=np.zeros_like(toa_hist), where=counts != 0)

# --- Filter ToT outliers ---
valid_tot_mask = counts > 0
tot_values = mean_tot[valid_tot_mask]
tot_z = np.abs(stats.zscore(tot_values))
tot_outlier_mask = tot_z > 3
mean_tot_clean = np.copy(mean_tot)
mean_tot_clean[valid_tot_mask] = np.where(tot_outlier_mask, np.nan, tot_values)

# --- Filter ToA outliers ---
valid_toa_mask = counts > 0
toa_values = mean_toa[valid_toa_mask]
toa_z = np.abs(stats.zscore(toa_values))
toa_outlier_mask = toa_z > 3
mean_toa_clean = np.copy(mean_toa)
mean_toa_clean[valid_toa_mask] = np.where(toa_outlier_mask, np.nan, toa_values)

# ======================
# ToT Plot
# ======================
ax1 = fig.add_subplot(121, projection='3d')
surf1 = ax1.plot_surface(
    xpos, ypos, mean_tot_clean.T,
    cmap=cmap, edgecolor='none', alpha=0.95
)
ax1.set_title('Pixel-wise Time-over-Threshold (ToT)')
ax1.set_ylabel('Y', labelpad=10)
ax1.set_zlabel('Mean ToT', labelpad=10)
ax1.view_init(elev=30, azim=-45)
ax1.grid(True, linestyle=':', alpha=0.2)

cbar1 = fig.colorbar(surf1, ax=ax1, shrink=0.7, aspect=15, pad=0.1)
cbar1.set_label('Mean ToT', rotation=270, labelpad=15)

stats_text_tot = (f"Global Mean: {np.nanmean(mean_tot_clean):.2f}\n"
                  f"Min: {np.nanmin(mean_tot_clean):.2f}\n"
                  f"Max: {np.nanmax(mean_tot_clean):.2f}\n"
                  f"Filtered: {np.sum(tot_outlier_mask)} pixels")
ax1.text2D(0.02, 0.95, stats_text_tot, transform=ax1.transAxes,
           ha='left', va='top', color='white',
           bbox=dict(facecolor='black', alpha=0.6, edgecolor='white'))

# ======================
# ToA Plot
# ======================
ax2 = fig.add_subplot(122, projection='3d')
surf2 = ax2.plot_surface(
    xpos, ypos, mean_toa_clean.T / 1e6,
    cmap=cmap, edgecolor='none', alpha=0.95
)
ax2.set_title('Pixel-wise Time-of-Arrival (ToA)', pad=15)
ax2.set_xlabel('X', labelpad=10)
ax2.set_ylabel('Y', labelpad=10)
ax2.set_zlabel('Mean ToA (ms)', labelpad=10)
ax2.view_init(elev=30, azim=-45)
ax2.grid(True, linestyle=':', alpha=0.2)

cbar2 = fig.colorbar(surf2, ax=ax2, shrink=0.7, aspect=15, pad=0.1)
cbar2.set_label('Mean ToA (ms)', rotation=270, labelpad=15)

stats_text_toa = (f"Global Mean: {np.nanmean(mean_toa_clean) / 1e6:.2f} ms\n"
                  f"Min: {np.nanmin(mean_toa_clean) / 1e6:.2f} ms\n"
                  f"Max: {np.nanmax(mean_toa_clean) / 1e6:.2f} ms\n"
                  f"Filtered: {np.sum(toa_outlier_mask)} pixels")
ax2.text2D(0.02, 0.95, stats_text_toa, transform=ax2.transAxes,
           ha='left', va='top', color='white',
           bbox=dict(facecolor='black', alpha=0.6, edgecolor='white'))

plt.tight_layout()
plt.show()

# ======================
# Figure 4: 32×32 Binned 3D ToT and ToA Distribution with Outlier Filtering
# ======================
fig = plt.figure(figsize=(24, 12))
fig.suptitle('Sensor 32×32 binned ToT and ToA Level Distribution', y=1.05)

# --- Prepare grid ---
bin_size = 8  # 256/32 = 8
x_edges = np.arange(0, 257, bin_size)
y_edges = np.arange(0, 257, bin_size)
x_centers = (x_edges[:-1] + x_edges[1:]) / 2
y_centers = (y_edges[:-1] + y_edges[1:]) / 2
xpos, ypos = np.meshgrid(x_centers, y_centers)

# --- Binned histograms ---
tot_hist, _, _ = np.histogram2d(hits['x'], hits['y'], bins=[x_edges, y_edges], weights=hits['tot'])
toa_hist, _, _ = np.histogram2d(hits['x'], hits['y'], bins=[x_edges, y_edges], weights=time_ns)
counts, _, _ = np.histogram2d(hits['x'], hits['y'], bins=[x_edges, y_edges])

# --- Compute means ---
mean_tot = np.divide(tot_hist, counts, out=np.zeros_like(tot_hist), where=counts != 0)
mean_toa = np.divide(toa_hist, counts, out=np.zeros_like(toa_hist), where=counts != 0)

# --- Filter ToT outliers ---
valid_tot_mask = counts > 0
tot_values = mean_tot[valid_tot_mask]
tot_z = np.abs(stats.zscore(tot_values))
tot_outlier_mask = tot_z > 3
mean_tot_clean = np.copy(mean_tot)
mean_tot_clean[valid_tot_mask] = np.where(tot_outlier_mask, np.nan, tot_values)

# --- Filter ToA outliers ---
valid_toa_mask = counts > 0
toa_values = mean_toa[valid_toa_mask]
toa_z = np.abs(stats.zscore(toa_values))
toa_outlier_mask = toa_z > 3
mean_toa_clean = np.copy(mean_toa)
mean_toa_clean[valid_toa_mask] = np.where(toa_outlier_mask, np.nan, toa_values)

# ======================
# ToT Plot
# ======================
ax1 = fig.add_subplot(121, projection='3d')
surf1 = ax1.plot_surface(
    xpos, ypos, mean_tot_clean.T,
    cmap=cmap, edgecolor='none', alpha=0.95
)
ax1.set_title('32×32 Binned Time-over-Threshold (ToT)')
ax1.set_xlabel('X Coordinate', labelpad=10)
ax1.set_ylabel('Y Coordinate', labelpad=10)
ax1.set_zlabel('Mean ToT', labelpad=10)
ax1.view_init(elev=30, azim=-45)
ax1.grid(True, linestyle=':', alpha=0.2)

cbar1 = fig.colorbar(surf1, ax=ax1, shrink=0.7, aspect=15, pad=0.1)
cbar1.set_label('Mean ToT', rotation=270, labelpad=15)

stats_text_tot = (f"Global Mean: {np.nanmean(mean_tot_clean):.2f}\n"
                 f"Min: {np.nanmin(mean_tot_clean):.2f}\n"
                 f"Max: {np.nanmax(mean_tot_clean):.2f}\n"
                 f"Filtered: {np.sum(tot_outlier_mask)} bins")
ax1.text2D(0.02, 0.95, stats_text_tot, transform=ax1.transAxes,
          ha='left', va='top', color='white',
          bbox=dict(facecolor='black', alpha=0.6, edgecolor='white'))

# ======================
# ToA Plot
# ======================
ax2 = fig.add_subplot(122, projection='3d')
surf2 = ax2.plot_surface(
    xpos, ypos, mean_toa_clean.T / 1e6,
    cmap=cmap, edgecolor='none', alpha=0.95
)
ax2.set_title('32×32 Binned Time-of-Arrival (ToA)')
ax2.set_xlabel('X Coordinate', labelpad=10)
ax2.set_ylabel('Y Coordinate', labelpad=10)
ax2.set_zlabel('Mean ToA (ms)', labelpad=10)
ax2.view_init(elev=30, azim=-45)
ax2.grid(True, linestyle=':', alpha=0.2)

cbar2 = fig.colorbar(surf2, ax=ax2, shrink=0.7, aspect=15, pad=0.1)
cbar2.set_label('Mean ToA (ms)', rotation=270, labelpad=15)

stats_text_toa = (f"Global Mean: {np.nanmean(mean_toa_clean)/1e6:.2f} ms\n"
                 f"Min: {np.nanmin(mean_toa_clean)/1e6:.2f} ms\n"
                 f"Max: {np.nanmax(mean_toa_clean)/1e6:.2f} ms\n"
                 f"Filtered: {np.sum(toa_outlier_mask)} bins")
ax2.text2D(0.02, 0.95, stats_text_toa, transform=ax2.transAxes,
          ha='left', va='top', color='white',
          bbox=dict(facecolor='black', alpha=0.6, edgecolor='white'))

plt.tight_layout()
plt.show()