import h5py
import numpy as np
import matplotlib.pyplot as plt
import os
import seaborn as sns

# ============================================================
# INPUT FILES
# ============================================================
input_dir = "/home/adisha/git/libkatherine/build/LGAD_0142_data_20251126/"
file_with = input_dir + "thl_calibration_20260206_093639.h5"
file_without = input_dir + "thl_calibration_20260206_101302_noSource.h5"

# ============================================================
# PARAMETERS
# ============================================================
sensor_width = 256
sensor_height = 256

x_min, x_max = 0, 30
y_min, y_max = 130, 180

window_width = x_max - x_min
window_height = y_max - y_min
total_window_pixels = window_width * window_height

dominance_factor = 1.5  # 50% more hits

# ============================================================
# OUTPUT
# ============================================================
output_dir = "LGAD_comparison_analysis"
os.makedirs(output_dir, exist_ok=True)

plt.style.use("default")
sns.set(style="white", context="talk")

# ============================================================
# LOAD DATA
# ============================================================
def load_dataset(filename):
    with h5py.File(filename, "r") as f:
        pixel_data = f["/pixel_hits"][:]
        attrs = dict(f.attrs)

    thls = np.arange(
        attrs["thl_start_mv"],
        attrs["thl_end_mv"] + attrs["thl_step_mv"],
        attrs["thl_step_mv"],
    )

    return pixel_data, thls


data_with, thls = load_dataset(file_with)
data_without, _ = load_dataset(file_without)

# ============================================================
# SINGLE PASS PROCESSING
# ============================================================
def process_dataset(pixel_data, thls):

    xs = pixel_data["x"]
    ys = pixel_data["y"]
    thl_array = pixel_data["thl"]

    window_mask = (
        (xs >= x_min) & (xs < x_max) &
        (ys >= y_min) & (ys < y_max)
    )

    results = {}

    for thl in thls:

        thl_mask = np.isclose(thl_array, thl)
        mask_window = thl_mask & window_mask

        # Totals
        total_all = int(np.sum(thl_mask))
        total_window = int(np.sum(mask_window))

        # Pixel hit map (window only)
        hit_map = np.zeros((sensor_height, sensor_width), dtype=np.int32)

        xs_sel = xs[mask_window]
        ys_sel = ys[mask_window]

        for x, y in zip(xs_sel, ys_sel):
            hit_map[y, x] += 1

        results[thl] = {
            "total_all": total_all,
            "total_window": total_window,
            "hit_map": hit_map
        }

    return results


with_data = process_dataset(data_with, thls)
without_data = process_dataset(data_without, thls)

# ============================================================
# BUILD TOTAL ARRAYS
# ============================================================
with_all = np.array([with_data[t]["total_all"] for t in thls])
without_all = np.array([without_data[t]["total_all"] for t in thls])
diff_all = with_all - without_all

with_window = np.array([with_data[t]["total_window"] for t in thls])
without_window = np.array([without_data[t]["total_window"] for t in thls])
diff_window = with_window - without_window

print("\nAll pixels diff min/max:", diff_all.min(), diff_all.max())
print("Window pixels diff min/max:", diff_window.min(), diff_window.max())

# ============================================================
# COMBINED TOTALS AND DIFFERENCE PLOTS
# ============================================================

def plot_totals(thls, with_vals, without_vals, diff_vals, title, filename):
    """Plot counts in log scale and difference on a secondary linear axis."""

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Counts in log scale
    ax1.plot(thls, with_vals, "g-", label="With source")
    ax1.plot(thls, without_vals, "r--", label="Without source")
    ax1.set_yscale("log")
    ax1.set_xlabel("Threshold (mV)")
    ax1.set_ylabel("Total hits (log scale)")
    ax1.invert_xaxis()
    ax1.grid(alpha=0.3)

    # Difference on linear axis
    ax2 = ax1.twinx()
    ax2.plot(thls, diff_vals, "b", label="Difference (with - without)")
    ax2.set_ylabel("Difference (linear)")
    
    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="best")

    fig.suptitle(title)
    plt.xlim(780, 100)  # Invert x-axis manually
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.show()


def plot_difference_log(thls, diff_vals, title, filename):
    """Difference with symmetric log scale for better visibility of negative values."""
    plt.figure(figsize=(10, 6))
    plt.plot(thls, diff_vals, "b")
    plt.yscale("symlog", linthresh=10)
    plt.axhline(0, color="black", linewidth=1)
    plt.gca().invert_xaxis()
    plt.xlabel("Threshold (mV)")
    plt.ylabel("Hit difference (with − without)")
    #plt.xlim(780, 100)
    plt.title(title)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.show()


def plot_difference_lin(thls, diff_vals, title, filename):
    """Difference on linear scale."""
    plt.figure(figsize=(10, 6))
    plt.plot(thls, diff_vals, "b")
    plt.axhline(0, color="black", linewidth=1)
    plt.gca().invert_xaxis()
    plt.xlabel("Threshold (mV)")
    plt.ylabel("Hit difference (with − without)")
    #plt.xlim(, 100)
    plt.title(title)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.show()


# ============================================================
# CALLING PLOTS WITH EXISTING DATA
# ============================================================

# All pixels
plot_totals(thls, with_all, without_all, diff_all, 
            "Total Hits and Difference (All Pixels)", "total_hits_and_diff_all.png")
plot_difference_log(thls, diff_all, "Difference in All Pixels (symlog)", "diff_all_symlog.png")
plot_difference_lin(thls, diff_all, "Difference in All Pixels (linear)", "diff_all_linear.png")

# Window pixels
plot_totals(thls, with_window, without_window, diff_window, 
            "Total Hits and Difference (Window Pixels)", "total_hits_and_diff_window.png")
plot_difference_log(thls, diff_window, "Difference in Window Pixels (symlog)", "diff_window_symlog.png")
plot_difference_lin(thls, diff_window, "Difference in Window Pixels (linear)", "diff_window_linear.png")

# ============================================================
# PER-PIXEL COMPARISON (FIXED LOGIC)
# ============================================================
print("\n--- Per-Pixel Comparison (Corrected Logic) ---")

total_diff_per_thl = []
illuminated_pixels_per_thl = []
paired_diff_per_thl = []

for thl in thls:

    map_with = with_data[thl]["hit_map"]
    map_without = without_data[thl]["hit_map"]

    # --------------------------------------------------------
    # FULL PHYSICAL DIFFERENCE (CORRECT)
    # --------------------------------------------------------
    diff_map = map_with - map_without

    window_diff = diff_map[y_min:y_max, x_min:x_max]

    # True total difference
    total_diff = np.sum(window_diff)
    total_diff_per_thl.append(total_diff)

    # Count pixels activated by source (physically meaningful)
    activated_pixels = np.sum(
        (map_with[y_min:y_max, x_min:x_max] > 0) &
        (map_without[y_min:y_max, x_min:x_max] == 0)
    )
    illuminated_pixels_per_thl.append(activated_pixels)

    # --------------------------------------------------------
    # STRICT PAIRED ANALYSIS (OPTIONAL / CONSERVATIVE)
    # --------------------------------------------------------
    paired_mask = (map_with > 0) & (map_without > 0)
    paired_diff = np.zeros_like(map_with)
    paired_diff[paired_mask] = diff_map[paired_mask]

    window_paired_diff = paired_diff[y_min:y_max, x_min:x_max]
    paired_total = np.sum(window_paired_diff)
    paired_diff_per_thl.append(paired_total)

    # --------------------------------------------------------
    # Skip plotting if almost uniform or too small
    # --------------------------------------------------------
    active_fraction = np.sum(window_diff != 0) / window_diff.size

    if active_fraction > 0.95:
        print(f"THL {thl:.1f} mV → skipping per-pixel plot: almost full illumination")
        continue

    if np.abs(total_diff) < 1:
        print(f"THL {thl:.1f} mV → skipping per-pixel plot: negligible difference")
        continue

    # --------------------------------------------------------
    # Plot full physical difference
    # --------------------------------------------------------
    plt.figure(figsize=(6, 6))
    vmax = np.max(np.abs(window_diff))
    plt.imshow(
        window_diff,
        origin="lower",
        extent=[x_min, x_max, y_min, y_max],
        cmap="bwr",
        vmin=-vmax,
        vmax=vmax,
    )
    plt.colorbar(label="Hit difference (with - without)")
    plt.title(f"Per-Pixel Difference (FULL)\nTHL = {thl:.1f} mV")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"per_pixel_diff_full_{thl:.1f}mV.png"), dpi=300)
    plt.show()

    # --------------------------------------------------------
    # Plot strict paired difference (optional)
    # --------------------------------------------------------
    if np.any(window_paired_diff != 0):
        plt.figure(figsize=(6, 6))
        vmax = np.max(np.abs(window_paired_diff))
        plt.imshow(
            window_paired_diff,
            origin="lower",
            extent=[x_min, x_max, y_min, y_max],
            cmap="bwr",
            vmin=-vmax,
            vmax=vmax,
        )
        plt.colorbar(label="Paired hit difference")
        plt.title(f"Per-Pixel Difference (PAIRED)\nTHL = {thl:.1f} mV")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"per_pixel_diff_paired_{thl:.1f}mV.png"), dpi=300)
        plt.show()


# ============================================================
# SUMMARY PLOTS
# ============================================================

# Total physical difference
plt.figure(figsize=(10, 6))
plt.plot(thls, total_diff_per_thl, "-", label="Full difference")
plt.plot(thls, paired_diff_per_thl, "--", label="Paired-only difference")
plt.gca().invert_xaxis()
plt.xlabel("Threshold (mV)")
plt.ylabel("Total Hit Difference")
plt.title("Total Difference in Window vs Threshold")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "total_difference_vs_thl_corrected.png"), dpi=300)
plt.show()

# Activated pixels
plt.figure(figsize=(10, 6))
plt.plot(thls, illuminated_pixels_per_thl, "o")
plt.gca().invert_xaxis()
plt.xlabel("Threshold (mV)")
plt.ylabel("Source-Activated Pixels")
plt.title("Number of Pixels Activated by Source vs Threshold")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "activated_pixels_vs_thl.png"), dpi=300)
plt.show()

print("\nCorrected analysis complete. Results saved in:", output_dir)



