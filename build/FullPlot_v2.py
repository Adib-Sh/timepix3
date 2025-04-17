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
# ======================
def filter_outliers(data, counts, threshold=3):
    """Filter outliers using z-score.
    
    Args:
        data: Array of values to filter
        counts: Array indicating valid data points (where counts > 0)
        threshold: Z-score threshold for outlier detection
        
    Returns:
        Filtered data with outliers replaced by NaN, count of outliers
    """
    valid_mask = counts > 0
    valid_values = data[valid_mask]
    
    if len(valid_values) <= 1:
        return data.astype(float), 0  # Not enough data for z-score
    
    z_scores = np.abs(stats.zscore(valid_values))
    outlier_mask = z_scores > threshold
    
    # Create a clean copy with float data type to support NaN values
    clean_data = np.copy(data).astype(float)
    clean_data[valid_mask] = np.where(outlier_mask, np.nan, valid_values)
    
    return clean_data, np.sum(outlier_mask)

def create_stats_text(data, prefix="", is_time=False, outlier_count=0, suffix="pixels"):
    """Create standardized statistics text for plots."""
    divisor = 1e6 if is_time else 1
    unit = " ms" if is_time else ""
    
    # Check if we have valid data for statistics
    if np.all(np.isnan(data)):
        return f"{prefix}No valid data points\nFiltered: {outlier_count} {suffix}"
    
    return (f"{prefix}Global Mean: {np.nanmean(data)/divisor:.2f}{unit}\n"
            f"Min: {np.nanmin(data)/divisor:.2f}{unit}\n"
            f"Max: {np.nanmax(data)/divisor:.2f}{unit}\n"
            f"Filtered: {outlier_count} {suffix}")

def plot_surface_3d(ax, xpos, ypos, zdata, title, xlabel='X Coordinate', 
                    ylabel='Y Coordinate', zlabel='Value', is_time=False, 
                    stats_text="", view_elev=30, view_azim=-45):
    """Create a standardized 3D surface plot with consistent styling."""
    divisor = 1e6 if is_time else 1
    cmap = plt.cm.inferno
    
    # Create a masked array to handle NaN values properly
    z_plot = zdata/divisor
    masked_z = np.ma.masked_invalid(z_plot)
    
    surf = ax.plot_surface(
        xpos, ypos, masked_z,
        cmap=cmap, edgecolor='none', alpha=0.95
    )
    
    ax.set_title(title)
    ax.set_xlabel(xlabel, labelpad=10)
    ax.set_ylabel(ylabel, labelpad=10)
    ax.set_zlabel(zlabel, labelpad=10)
    
    # Set explicit axis limits
    ax.set_xlim(0, 255)
    ax.set_ylim(0, 255)
    
    # Set z-limits safely based on non-NaN values only
    valid_z = masked_z.compressed()  # Gets non-masked values
    if len(valid_z) > 0:
        zmin, zmax = np.min(valid_z), np.max(valid_z)
        # Add a bit of padding to z-limits
        padding = (zmax - zmin) * 0.1 if zmax > zmin else 0.1
        ax.set_zlim(zmin - padding, zmax + padding)
    else:
        # Fallback z-limits if no valid data
        ax.set_zlim(0, 1)
    
    ax.view_init(elev=view_elev, azim=view_azim)
    ax.grid(True, linestyle=':', alpha=0.2)
    
    cbar = plt.colorbar(surf, ax=ax, shrink=0.7, aspect=15, pad=0.1)
    cbar.set_label(zlabel, rotation=270, labelpad=15)
    
    # Add stats text
    if stats_text:
        ax.text2D(0.02, 0.95, stats_text, transform=ax.transAxes,
                 ha='left', va='top', color='white',
                 bbox=dict(facecolor='black', alpha=0.6, edgecolor='white'))
    
    return surf


setup_plot_style()
    
# Load Data
with h5py.File('pixel_data_Si_1e9s_20250406_033424.h5', 'r') as f:
    hits = f['/pixel_hits'][:]

# Preprocessing
time_ns = hits['toa'] - hits['toa'].min()
time_sec = time_ns / 1e9
hit_rate = len(hits) / time_sec.max()

# Build 256x256 hit map
hit_count_map = np.zeros((256, 256), dtype=int)
np.add.at(hit_count_map, (hits['y'], hits['x']), 1)

# Apply outlier filtering to hit counts
clean_hit_counts, _ = filter_outliers(hit_count_map, hit_count_map > 0)

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

# Ensure we have valid bars to plot
if np.any(hit_mask):
    ax1.bar3d(x[hit_mask], y[hit_mask], z[hit_mask],
            dx[hit_mask], dy[hit_mask], dz[hit_mask],
            color=cmap(norm(dz[hit_mask])),
            edgecolor='none', linewidth=0.1, alpha=0.95, shade=True)
    
    max_z = np.max(dz[hit_mask]) if np.any(dz[hit_mask]) else 1
else:
    max_z = 1

ax1.set_title('3D Per-Pixel View', color='white')
ax1.set_xlabel('X Coordinate')
ax1.set_ylabel('Y Coordinate')
ax1.set_zlabel('Hit Count')
ax1.set_xlim(0, 255)
ax1.set_ylim(0, 255)
ax1.set_zlim(0, max_z * 1.1)  # Safe z-limit
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
    weights=None
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
# Process ToT and ToA data for both 256x256 and 32x32 binned
# ======================
# --- Full resolution (256x256) processing ---
x_edges_full = np.arange(257)
y_edges_full = np.arange(257)
x_centers_full = (x_edges_full[:-1] + x_edges_full[1:]) / 2
y_centers_full = (y_edges_full[:-1] + y_edges_full[1:]) / 2
xpos_full, ypos_full = np.meshgrid(x_centers_full, y_centers_full)

# Calculate histograms for full resolution
tot_hist_full, _, _ = np.histogram2d(hits['x'], hits['y'], bins=[x_edges_full, y_edges_full], weights=hits['tot'])
toa_hist_full, _, _ = np.histogram2d(hits['x'], hits['y'], bins=[x_edges_full, y_edges_full], weights=time_ns)
counts_full, _, _ = np.histogram2d(hits['x'], hits['y'], bins=[x_edges_full, y_edges_full])

# Compute means
mean_tot_full = np.divide(tot_hist_full, counts_full, out=np.zeros_like(tot_hist_full), where=counts_full != 0)
mean_toa_full = np.divide(toa_hist_full, counts_full, out=np.zeros_like(toa_hist_full), where=counts_full != 0)

# Filter outliers
mean_tot_full_clean, tot_outliers_full = filter_outliers(mean_tot_full, counts_full)
mean_toa_full_clean, toa_outliers_full = filter_outliers(mean_toa_full, counts_full)

# --- Binned (32x32) processing ---
bin_size = 8  # 256/32 = 8
x_edges_bin = np.arange(0, 257, bin_size)
y_edges_bin = np.arange(0, 257, bin_size)
x_centers_bin = (x_edges_bin[:-1] + x_edges_bin[1:]) / 2
y_centers_bin = (y_edges_bin[:-1] + y_edges_bin[1:]) / 2
xpos_bin, ypos_bin = np.meshgrid(x_centers_bin, y_centers_bin)

# Calculate histograms for binned resolution
tot_hist_bin, _, _ = np.histogram2d(hits['x'], hits['y'], bins=[x_edges_bin, y_edges_bin], weights=hits['tot'])
toa_hist_bin, _, _ = np.histogram2d(hits['x'], hits['y'], bins=[x_edges_bin, y_edges_bin], weights=time_ns)
counts_bin, _, _ = np.histogram2d(hits['x'], hits['y'], bins=[x_edges_bin, y_edges_bin])

# Compute means
mean_tot_bin = np.divide(tot_hist_bin, counts_bin, out=np.zeros_like(tot_hist_bin), where=counts_bin != 0)
mean_toa_bin = np.divide(toa_hist_bin, counts_bin, out=np.zeros_like(toa_hist_bin), where=counts_bin != 0)

# Filter outliers
mean_tot_bin_clean, tot_outliers_bin = filter_outliers(mean_tot_bin, counts_bin)
mean_toa_bin_clean, toa_outliers_bin = filter_outliers(mean_toa_bin, counts_bin)

# ======================
# Figure 3: ToT Distribution (Full and Binned)
# ======================
fig = plt.figure(figsize=(24, 12))
fig.suptitle('Time-over-Threshold (ToT) Distribution', y=1.05)

# Per-pixel ToT plot
ax1 = fig.add_subplot(121, projection='3d')
stats_text_tot_full = create_stats_text(
    mean_tot_full_clean, 
    outlier_count=tot_outliers_full,
    suffix="pixels"
)
plot_surface_3d(
    ax1, xpos_full, ypos_full, mean_tot_full_clean.T,
    title='Per-Pixel Time-over-Threshold (ToT)',
    zlabel='Mean ToT',
    stats_text=stats_text_tot_full
)

# 32x32 binned ToT plot
ax2 = fig.add_subplot(122, projection='3d')
stats_text_tot_bin = create_stats_text(
    mean_tot_bin_clean, 
    outlier_count=tot_outliers_bin,
    suffix="bins"
)
plot_surface_3d(
    ax2, xpos_bin, ypos_bin, mean_tot_bin_clean.T,
    title='32×32 Binned Time-over-Threshold (ToT)',
    zlabel='Mean ToT',
    stats_text=stats_text_tot_bin
)

plt.tight_layout()
plt.show()

# ======================
# Figure 4: ToA Distribution (Full and Binned)
# ======================
fig = plt.figure(figsize=(24, 12))
fig.suptitle('Time-of-Arrival (ToA) Distribution', y=1.05)

# Per-pixel ToA plot
ax1 = fig.add_subplot(121, projection='3d')
stats_text_toa_full = create_stats_text(
    mean_toa_full_clean, 
    is_time=True, 
    outlier_count=toa_outliers_full,
    suffix="pixels"
)
plot_surface_3d(
    ax1, xpos_full, ypos_full, mean_toa_full_clean.T,
    title='Per-Pixel Time-of-Arrival (ToA)',
    zlabel='Mean ToA (ms)',
    is_time=True,
    stats_text=stats_text_toa_full
)

# 32x32 binned ToA plot
ax2 = fig.add_subplot(122, projection='3d')
stats_text_toa_bin = create_stats_text(
    mean_toa_bin_clean, 
    is_time=True, 
    outlier_count=toa_outliers_bin,
    suffix="bins"
)
plot_surface_3d(
    ax2, xpos_bin, ypos_bin, mean_toa_bin_clean.T,
    title='32×32 Binned Time-of-Arrival (ToA)',
    zlabel='Mean ToA (ms)',
    is_time=True,
    stats_text=stats_text_toa_bin
)

plt.tight_layout()
plt.show()


# ======================
# Figure 5: ToT Distribution (Energy Spectrum) - Unfiltered Data
# ======================
from scipy.optimize import curve_fit
fig = plt.figure(figsize=(18, 10))
fig.suptitle('Time-over-Threshold (ToT) Energy Spectrum - Unfiltered Data', y=1.02)

ax1 = fig.add_subplot(111)
tot_values = hits['tot']
bins = np.linspace(0, np.max(tot_values), 150)  # Reduced number of bins for better statistics

# Create histogram
n, bins, patches = ax1.hist(tot_values, bins=bins, alpha=0.75, color='cyan',
                           edgecolor='white', linewidth=0.5, label='Data')

# Set log scale for y-axis
ax1.set_yscale('log')
ax1.grid(True, linestyle=':', alpha=0.7)
ax1.set_xlabel('Time-over-Threshold (ToT)')
ax1.set_ylabel('Count (log scale)')

# Find the peak region more robustly
max_bin_idx = np.argmax(n)
peak_x = (bins[max_bin_idx] + bins[max_bin_idx+1])/2
peak_y = n[max_bin_idx]

# Gaussian function for fitting
def gaussian(x, a, mu, sigma):
    return a * np.exp(-(x - mu)**2 / (2 * sigma**2))

# Select data around the peak (wider window)
fit_window = 10 * (bins[1] - bins[0])  # Increased window size
fit_mask = (bins[:-1] > peak_x - fit_window) & (bins[:-1] < peak_x + fit_window)

# Improved initial guesses
initial_guess = [peak_y, peak_x, fit_window/2]

# Set bounds to prevent unrealistic parameters
bounds = ([0.1*peak_y, peak_x - 2*fit_window, 0.1*(bins[1]-bins[0])],  # Lower bounds
          [10*peak_y, peak_x + 2*fit_window, 5*fit_window])  # Upper bounds

try:
    # Perform the fit with increased max iterations and bounds
    popt, pcov = curve_fit(gaussian, bins[:-1][fit_mask], n[fit_mask], 
                   p0=initial_guess, bounds=bounds, maxfev=2000)
    
    # Calculate FWHM
    fwhm = 2 * np.sqrt(2 * np.log(2)) * popt[2]  # FWHM = 2.355 * sigma
    
    # Plot the fitted Gaussian (only where y_fit > 0 for log scale)
    x_fit = np.linspace(peak_x - 2*fit_window, peak_x + 2*fit_window, 500)
    y_fit = gaussian(x_fit, *popt)
    valid_fit = y_fit > 0.1  # Only plot above 0.1 to avoid log scale issues
    ax1.plot(x_fit[valid_fit], y_fit[valid_fit], 'r-', linewidth=2,
            label=f'Gaussian Fit\nμ={popt[1]:.2f}, σ={popt[2]:.2f}\nFWHM={fwhm:.2f}')
    
    # Add FWHM markers
    half_max = popt[0]/2
    if half_max > 1:  # Only plot if half_max is reasonable
        left_fwhm = popt[1] - np.sqrt(2*np.log(2))*popt[2]
        right_fwhm = popt[1] + np.sqrt(2*np.log(2))*popt[2]
        ax1.axvline(left_fwhm, color='orange', linestyle='--', alpha=0.7)
        ax1.axvline(right_fwhm, color='orange', linestyle='--', alpha=0.7)
        ax1.axhline(half_max, color='green', linestyle=':', alpha=0.5)
    
    stats_text = (f"Total Hits: {len(tot_values):,}\n"
                f"Mean: {np.mean(tot_values):.2f}\n"
                f"Median: {np.median(tot_values):.2f}\n"
                f"Std Dev: {np.std(tot_values):.2f}\n"
                f"Min: {np.min(tot_values):.2f}\n"
                f"Max: {np.max(tot_values):.2f}\n"
                f"FWHM: {fwhm:.2f}")
    
except Exception as e:
    print(f"Fit failed with error: {e}")
    print("Trying alternative fitting approach...")
    
    # Fallback: Use histogram peak properties directly
    peak_region = n[fit_mask]
    rough_sigma = np.sqrt(np.sum(peak_region * (bins[:-1][fit_mask] - peak_x)**2) / np.sum(peak_region))
    rough_fwhm = 2.355 * rough_sigma
    
    stats_text = (f"Total Hits: {len(tot_values):,}\n"
                f"Mean: {np.mean(tot_values):.2f}\n"
                f"Median: {np.median(tot_values):.2f}\n"
                f"Std Dev: {np.std(tot_values):.2f}\n"
                f"Min: {np.min(tot_values):.2f}\n"
                f"Max: {np.max(tot_values):.2f}\n"
                f"Approx FWHM: {rough_fwhm:.2f} (from peak properties)")

# Add stats box
ax1.text(0.98, 0.98, stats_text, transform=ax1.transAxes,
        ha='right', va='top', color='white',
        bbox=dict(facecolor='black', alpha=0.6, edgecolor='white'))

ax1.legend(loc='upper left')
plt.tight_layout()
plt.show()

# ======================
# Figure 6: ToT vs ToA Correlation - Unfiltered Data
# ======================
fig = plt.figure(figsize=(18, 10))
fig.suptitle('Time-over-Threshold vs Time-of-Arrival Correlation - Unfiltered Data', y=1.02)

ax = fig.add_subplot(111)

# Convert time to milliseconds for better readability
toa_ms = time_ns / 1e6

# Create a 2D histogram for density visualization
h, xedges, yedges, im = ax.hist2d(toa_ms, hits['tot'], 
                                  bins=[100, 100], 
                                  cmap=plt.cm.viridis, 
                                  norm=LogNorm())

ax.set_xlabel('Time of Arrival (ms)')
ax.set_ylabel('Time over Threshold (ToT)')
ax.set_title('ToT vs ToA Correlation - Unfiltered')
ax.grid(True, linestyle=':', alpha=0.3)

# Add colorbar
cbar = plt.colorbar(im, ax=ax)
cbar.set_label('Hit Count (log scale)')

# Calculate correlation coefficient
corr_coef, p_value = stats.pearsonr(toa_ms, hits['tot'])

# Add correlation statistics
stats_text = (f"Pearson Correlation: {corr_coef:.4f}\n"
              f"p-value: {p_value:.4e}\n"
              f"Total Hits: {len(hits):,}")

ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
         ha='left', va='top', color='white',
         bbox=dict(facecolor='black', alpha=0.6, edgecolor='white'))

plt.tight_layout()
plt.show()

# ======================
# Figure 7: Hit Rate Over Time - Unfiltered Data
# ======================
fig = plt.figure(figsize=(18, 10))
fig.suptitle('Hit Rate Over Time - Unfiltered Data', y=1.02)

ax = fig.add_subplot(111)

# Create time bins (in seconds)
max_time_sec = time_sec.max()
time_bins = np.linspace(0, max_time_sec, 100)
hist, bin_edges = np.histogram(time_sec, bins=time_bins)

# Convert counts to rate (hits per second)
bin_widths = np.diff(bin_edges)
hit_rates = hist / bin_widths

# Plot hit rate over time
ax.plot(bin_edges[:-1] + bin_widths/2, hit_rates, 'o-', color='cyan', markersize=4, linewidth=1.5)
ax.fill_between(bin_edges[:-1] + bin_widths/2, 0, hit_rates, alpha=0.3, color='cyan')

# Add rolling average
window_size = 5  # Adjust window size as needed
if len(hit_rates) > window_size:
    rolling_avg = np.convolve(hit_rates, np.ones(window_size)/window_size, mode='valid')
    rolling_times = bin_edges[:-1][window_size-1:] + bin_widths[window_size-1:]/2
    ax.plot(rolling_times, rolling_avg, 'r-', linewidth=2, 
            label=f'{window_size}-point Moving Average')
    ax.legend(loc='upper right')

ax.set_xlabel('Time (seconds)')
ax.set_ylabel('Hit Rate (hits/second)')
ax.set_title('Sensor Hit Rate Over Time - Unfiltered')
ax.grid(True, linestyle=':', alpha=0.7)

# Add zero line
ax.axhline(y=0, color='white', linestyle='-', alpha=0.3)

# Calculate min and max hit rates for better y-axis limits
min_rate = np.min(hit_rates)
max_rate = np.max(hit_rates)
y_padding = (max_rate - min_rate) * 0.1 if max_rate > min_rate else max_rate * 0.1
ax.set_ylim(max(0, min_rate - y_padding), max_rate + y_padding)

# Add statistics
mean_rate = np.mean(hit_rates)
std_rate = np.std(hit_rates)
stats_text = (f"Mean Rate: {mean_rate:.2f} hits/s\n"
              f"Std Dev: {std_rate:.2f} hits/s\n"
              f"Global Rate: {hit_rate:.2f} hits/s\n"
              f"Total Duration: {max_time_sec:.2f} s\n"
              f"Total Hits: {len(hits):,}")

ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
        ha='left', va='top', color='white',
        bbox=dict(facecolor='black', alpha=0.6, edgecolor='white'))

plt.tight_layout()
plt.show()