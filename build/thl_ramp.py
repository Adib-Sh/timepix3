import h5py
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

# Plot style
sns.set(style="whitegrid")
plt.rcParams.update({'font.size': 12})

def load_pixel_hits(filename):
    with h5py.File(filename, 'r') as f:
        if 'pixel_hits' not in f:
            raise KeyError("Dataset 'pixel_hits' not found in HDF5 file.")
        pixel_hits = f['pixel_hits'][:]
    return pixel_hits

def plot_thl_distribution(thl_values, counts):
    plt.figure(figsize=(12, 6))
    sns.lineplot(x=thl_values, y=counts, marker='o', color='royalblue')
    plt.title("THL vs Number of Pixel Hits")
    plt.xlabel("THL Value")
    plt.ylabel("Number of Hits")
    plt.tight_layout()
    plt.show()

def print_thl_summary(thl_values, counts):
    print(f"{'THL Value':<10} | {'Number of Hits':>15}")
    print("-" * 30)
    for thl, count in zip(thl_values, counts):
        print(f"{thl:<10} | {count:>15}")
    print(f"\nTotal unique THL values: {len(thl_values)}")
    print(f"Total hits: {np.sum(counts)}")

def analyze_per_pixel_threshold(pixel_hits):
    """
    Analyzes how each pixel responds across THL values.
    You can visualize per-pixel THL histograms or generate heatmaps.
    """
    print("\nRunning per-pixel threshold analysis...")

    hit_map = defaultdict(list)

    for hit in pixel_hits:
        x, y, thl = hit['x'], hit['y'], hit['thl']
        hit_map[(x, y)].append(thl)

    # Option 1: Histogram of THL values for a few pixels
    example_pixels = list(hit_map.keys())[:6]  # select first few pixels
    plt.figure(figsize=(14, 8))
    for i, pix in enumerate(example_pixels, 1):
        plt.subplot(2, 3, i)
        plt.hist(hit_map[pix], bins=30, color='steelblue', alpha=0.7)
        plt.title(f"Pixel ({pix[0]}, {pix[1]})")
        plt.xlabel("THL")
        plt.ylabel("Count")
    plt.tight_layout()
    plt.show()

    # Option 2: Mean THL map
    max_x = max(k[0] for k in hit_map) + 1
    max_y = max(k[1] for k in hit_map) + 1
    mean_thl_map = np.full((max_y, max_x), np.nan)

    for (x, y), thls in hit_map.items():
        mean_thl_map[y, x] = np.mean(thls)

    plt.figure(figsize=(10, 8))
    sns.heatmap(mean_thl_map, cmap='viridis', cbar_kws={'label': 'Mean THL'})
    plt.title("Mean THL per Pixel")
    plt.xlabel("Pixel X")
    plt.ylabel("Pixel Y")
    plt.tight_layout()
    plt.show()

def main():
    filename = "thl_calibration_20250430_222829_coarse6_200_700.h5"
    pixel_hits = load_pixel_hits(filename)

    print(f"Total Number of Pixel Hits: {len(pixel_hits)}")

    thl_values, counts = np.unique(pixel_hits['thl'], return_counts=True)

    print_thl_summary(thl_values, counts)
    plot_thl_distribution(thl_values, counts)
    analyze_per_pixel_threshold(pixel_hits)

if __name__ == "__main__":
    main()
