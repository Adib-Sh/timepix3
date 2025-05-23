import h5py
import numpy as np
import pandas as pd
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
filename = "thl_calibration_FE55_300-1200_skip800-840_20250522_040712.h5"  # Replace with actual filename
with h5py.File(filename, 'r') as f:
    pixel_hits = f['pixel_hits'][:]
    total_hits = len(pixel_hits)
    print(f"🔢 Total Number of Pixel Hits: {total_hits:,}\n")
    
    # Create a DataFrame for easier analysis
    df = pd.DataFrame({
        'thl': pixel_hits['thl'],
        'x': pixel_hits['x'] if 'x' in pixel_hits.dtype.names else None,
        'y': pixel_hits['y'] if 'y' in pixel_hits.dtype.names else None,
        'tot': pixel_hits['tot'] if 'tot' in pixel_hits.dtype.names else None,
        'timestamp': pixel_hits['timestamp'] if 'timestamp' in pixel_hits.dtype.names else None
    })
    
    # Drop columns that are None
    df = df.dropna(axis=1, how='all')

# -------------------------
# Plot overall THL scan
# -------------------------
thls = df["thl"]
thl_counts = df['thl'].value_counts().sort_index()
unique_thls = thl_counts.index.values
counts = thl_counts.values

plt.figure(figsize=(8, 5))
plt.plot(unique_thls, counts, marker='o')
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
for hit in df:
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
