import h5py
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from collections import defaultdict
import seaborn as sns

# -------------------------
# Sigmoid (S-curve) function
# -------------------------
def s_curve(x, A, x0, k):
    return A / (1 + np.exp(-(x - x0) / k))

# -------------------------
# Load HDF5 file
# -------------------------
filename = "thl_calibration_20250521_061323.h5"  # Replace with actual filename
with h5py.File(filename, 'r') as f:
    thl_data = f['/thl_scan'][:]
    pixel_data = f['/pixel_hits'][:]

# -------------------------
# Plot overall THL scan
# -------------------------
thls = np.array([point['thl'] for point in thl_data])
hits = np.array([point['hits'] for point in thl_data])

plt.figure(figsize=(8, 5))
plt.plot(thls, hits, marker='o')
plt.title("Total Hits vs THL")
plt.xlabel("THL")
plt.ylabel("Total Hits")
plt.grid(True)
plt.tight_layout()
plt.show()

# -------------------------
# Organize pixel hit data
# -------------------------
pixel_hits = defaultdict(lambda: defaultdict(int))
for hit in pixel_data:
    coord = (hit['x'], hit['y'])
    pixel_hits[coord][hit['thl']] += hit['hit_count']

# -------------------------
# Select 6 pixels with most total counts
# -------------------------
total_counts = {coord: sum(thl_dict.values()) for coord, thl_dict in pixel_hits.items()}
top_pixels = sorted(total_counts.items(), key=lambda x: -x[1])[:6]
selected_coords = [coord for coord, _ in top_pixels]

# -------------------------
# Plot selected pixels
# -------------------------
plt.figure(figsize=(10, 6))
for coord in selected_coords:
    thl_vals = sorted(pixel_hits[coord].keys())
    counts = [pixel_hits[coord][t] for t in thl_vals]
    plt.plot(thl_vals, counts, label=f"Pixel {coord}")
plt.title("Pixel-specific Hits vs THL")
plt.xlabel("THL")
plt.ylabel("Hit Count")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# -------------------------
# S-Curve fit: extract threshold and noise
# -------------------------
threshold_map = np.full((256, 256), np.nan)
noise_map = np.full((256, 256), np.nan)
dead_pixel_map = np.zeros((256, 256), dtype=bool)

for (x, y), hits_by_thl in pixel_hits.items():
    thls = sorted(hits_by_thl)
    counts = [hits_by_thl[t] for t in thls]
    total = sum(counts)
    
    # Skip pixels with no activity
    if total < 10:
        dead_pixel_map[y, x] = True
        continue

    try:
        p0 = [max(counts), thls[np.argmax(counts)], 2.0]  # A, x0, k
        popt, _ = curve_fit(s_curve, thls, counts, p0=p0, maxfev=10000)
        A, x0, k = popt
        threshold_map[y, x] = x0
        noise_map[y, x] = abs(k)
    except:
        dead_pixel_map[y, x] = True  # Poor fit or unstable
        continue

# -------------------------
# Plot threshold map
# -------------------------
plt.figure(figsize=(8, 6))
sns.heatmap(threshold_map, cmap='viridis', cbar_kws={'label': 'Threshold (THL)'})
plt.title("2D Threshold Map")
plt.xlabel("Pixel X")
plt.ylabel("Pixel Y")
plt.tight_layout()
plt.show()

# -------------------------
# Plot noise map
# -------------------------
plt.figure(figsize=(8, 6))
sns.heatmap(noise_map, cmap='magma', cbar_kws={'label': 'Noise (THL slope)'})
plt.title("2D Noise Map")
plt.xlabel("Pixel X")
plt.ylabel("Pixel Y")
plt.tight_layout()
plt.show()

# -------------------------
# Plot dead pixel map
# -------------------------
plt.figure(figsize=(8, 6))
plt.imshow(dead_pixel_map, cmap='gray_r')
plt.title("Dead Pixels (White = Dead)")
plt.xlabel("Pixel X")
plt.ylabel("Pixel Y")
plt.tight_layout()
plt.show()

# -------------------------
# Print threshold stats
# -------------------------
valid_thresholds = threshold_map[~np.isnan(threshold_map)]
print("=== Threshold Statistics ===")
print(f"Mean Threshold: {np.mean(valid_thresholds):.2f}")
print(f"Std Threshold: {np.std(valid_thresholds):.2f}")
print(f"Dead Pixels: {np.sum(dead_pixel_map)} / {threshold_map.size}")
