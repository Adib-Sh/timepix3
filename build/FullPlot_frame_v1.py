import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import os
from datetime import datetime
from scipy import stats

plt.style.use('dark_background')

# ===== Utility Functions =====
def filter_outliers(data, counts, threshold=3):
    valid_mask = counts > 0
    valid_values = data[valid_mask]
    if len(valid_values) <= 1:
        return data.astype(float), 0
    z_scores = np.abs(stats.zscore(valid_values))
    outlier_mask = z_scores > threshold
    clean_data = np.copy(data).astype(float)
    clean_data[valid_mask] = np.where(outlier_mask, np.nan, valid_values)
    return clean_data, np.sum(outlier_mask)

def create_stats_text(data, prefix="", outlier_count=0, suffix="pixels"):
    if np.all(np.isnan(data)):
        return f"{prefix}No valid data points\nFiltered: {outlier_count} {suffix}"
    return (f"{prefix}Mean: {np.nanmean(data):.2f}\n"
            f"Min: {np.nanmin(data):.2f}\n"
            f"Max: {np.nanmax(data):.2f}\n"
            f"Filtered: {outlier_count} {suffix}")

def plot_surface_3d(ax, xpos, ypos, zdata, title, zlabel='Value', stats_text=""):
    masked_z = np.ma.masked_invalid(zdata)
    surf = ax.plot_surface(xpos, ypos, masked_z, cmap='inferno', edgecolor='none', alpha=0.95)
    ax.set_title(title)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel(zlabel)
    ax.set_xlim(0, 255)
    ax.set_ylim(0, 255)
    valid_z = masked_z.compressed()
    if len(valid_z) > 0:
        zmin, zmax = np.min(valid_z), np.max(valid_z)
        padding = (zmax - zmin) * 0.1 if zmax > zmin else 0.1
        ax.set_zlim(zmin - padding, zmax + padding)
    else:
        ax.set_zlim(0, 1)
    ax.view_init(elev=30, azim=-45)
    ax.grid(True, linestyle=':', alpha=0.2)
    cbar = plt.colorbar(surf, ax=ax, shrink=0.7, aspect=15, pad=0.1)
    cbar.set_label(zlabel, rotation=270, labelpad=15)
    if stats_text:
        ax.text2D(0.02, 0.95, stats_text, transform=ax.transAxes,
                  ha='left', va='top', color='white',
                  bbox=dict(facecolor='black', alpha=0.6, edgecolor='white'))

def plot_heatmap_2d(ax, data, title, zlabel='Value'):
    im = ax.imshow(data.T, origin='lower', cmap='inferno', norm=LogNorm(vmin=1, vmax=np.nanmax(data)))
    ax.set_title(title)
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    cbar = plt.colorbar(im, ax=ax, shrink=0.9, aspect=20, pad=0.02)
    cbar.set_label(zlabel, rotation=270, labelpad=15)
    ax.grid(True, linestyle=':', alpha=0.2)
    ax.minorticks_on()

# ===== Main Function =====
def main(input_file):
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = f"analysis_{base_name}"
    os.makedirs(output_dir, exist_ok=True)

    with h5py.File(input_file, 'r') as f:
        hits = f['/pixel_hits'][:]

    if hits.size == 0:
        print("No hits found.")
        return

    x = hits['x']
    y = hits['y']
    tot_values = hits['integral_tot']
    event_counts = hits['event_count']

    # Hit count map
    hit_count_map = np.zeros((256, 256), dtype=int)
    np.add.at(hit_count_map, (y, x), 1)

    # Histogram grids
    edges = np.arange(257)
    bin_edges = np.arange(0, 257, 8)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    xpos_bin, ypos_bin = np.meshgrid(bin_centers, bin_centers)

    # Tot mean (full res)
    tot_hist, _, _ = np.histogram2d(x, y, bins=[edges, edges], weights=tot_values)
    counts, _, _ = np.histogram2d(x, y, bins=[edges, edges])
    mean_tot = np.divide(tot_hist, counts, out=np.zeros_like(tot_hist), where=counts != 0)
    mean_tot_clean, outliers = filter_outliers(mean_tot, counts)

    # Event count (full res)
    event_hist, _, _ = np.histogram2d(x, y, bins=[edges, edges], weights=event_counts)
    mean_event = np.divide(event_hist, counts, out=np.zeros_like(event_hist), where=counts != 0)
    mean_event_clean, event_outliers = filter_outliers(mean_event, counts)

    # Tot mean (binned)
    tot_hist_bin, _, _ = np.histogram2d(x, y, bins=[bin_edges, bin_edges], weights=tot_values)
    count_bin, _, _ = np.histogram2d(x, y, bins=[bin_edges, bin_edges])
    mean_tot_bin = np.divide(tot_hist_bin, count_bin, out=np.zeros_like(tot_hist_bin), where=count_bin != 0)
    mean_tot_bin_clean, tot_outliers_bin = filter_outliers(mean_tot_bin, count_bin)

    # Event count (binned)
    event_hist_bin, _, _ = np.histogram2d(x, y, bins=[bin_edges, bin_edges], weights=event_counts)
    mean_event_bin = np.divide(event_hist_bin, count_bin, out=np.zeros_like(event_hist_bin), where=count_bin != 0)
    mean_event_bin_clean, event_outliers_bin = filter_outliers(mean_event_bin, count_bin)

    x_centers = np.arange(256) + 0.5
    y_centers = np.arange(256) + 0.5
    xpos, ypos = np.meshgrid(x_centers, y_centers)

    # ===== Plot: Mean Event Count (Full) =====
    fig = plt.figure(figsize=(20, 9))
    fig.suptitle("Mean Event Count - Full Resolution", y=1.05)
    ax1 = fig.add_subplot(121, projection='3d')
    stats_text_event = create_stats_text(mean_event_clean, outlier_count=event_outliers)
    plot_surface_3d(ax1, xpos, ypos, mean_event_clean.T, "3D Per-Pixel Event Count", zlabel="Mean Event Count", stats_text=stats_text_event)
    ax2 = fig.add_subplot(122)
    plot_heatmap_2d(ax2, mean_event_clean, "2D Per-Pixel Event Count", zlabel="Mean Event Count")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'event_count_full.png'), dpi=150)
    plt.show()
    plt.close()

    # ===== Plot: Mean Event Count (Binned) =====
    fig = plt.figure(figsize=(20, 9))
    fig.suptitle("Mean Event Count - 32×32 Binned", y=1.05)
    ax1 = fig.add_subplot(121, projection='3d')
    stats_text_event_bin = create_stats_text(mean_event_bin_clean, outlier_count=event_outliers_bin, suffix="bins")
    plot_surface_3d(ax1, xpos_bin, ypos_bin, mean_event_bin_clean.T, "3D Binned Event Count", zlabel="Mean Event Count", stats_text=stats_text_event_bin)
    ax2 = fig.add_subplot(122)
    plot_heatmap_2d(ax2, mean_event_bin_clean, "2D Binned Event Count", zlabel="Mean Event Count")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'event_count_binned.png'), dpi=150)
    plt.show()
    plt.close()

    # ===== Plot: Mean ToT (Full) =====
    fig = plt.figure(figsize=(20, 9))
    fig.suptitle("Mean ToT - Full Resolution", y=1.05)
    ax1 = fig.add_subplot(121, projection='3d')
    stats_text_tot = create_stats_text(mean_tot_clean, outlier_count=outliers)
    plot_surface_3d(ax1, xpos, ypos, mean_tot_clean.T, "3D Per-Pixel ToT", zlabel="Mean ToT", stats_text=stats_text_tot)
    ax2 = fig.add_subplot(122)
    plot_heatmap_2d(ax2, mean_tot_clean, "2D Per-Pixel ToT", zlabel="Mean ToT")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'tot_full.png'), dpi=150)
    plt.show()
    plt.close()

    # ===== Plot: ToT Histogram =====
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(tot_values, bins=100, color='cyan', edgecolor='white', alpha=0.75, log=True)
    ax.set_xlabel('Integral ToT')
    ax.set_ylabel('Counts (log scale)')
    ax.set_title('ToT Distribution')
    ax.grid(True, linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'tot_histogram.png'), dpi=150)
    plt.show()
    plt.close()

    print(f"Plotting complete. Results in: {output_dir}")

if __name__ == "__main__":
    main("ToTdata_frame_20250608_104705.h5")  # Replace with your file name
