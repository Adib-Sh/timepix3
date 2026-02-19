import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, TwoSlopeNorm
import os
import io
from PIL import Image
import seaborn as sns

# ============================================================
# INPUT FILES
# ============================================================
input_dir = "/home/adisha/git/libkatherine/build/LGAD_0142_data_20251126/"
input_file_with = input_dir + "/thl_calibration_20260206_093639.h5"
input_file_without = input_dir + "thl_calibration_20260206_101302_noSource.h5"

# ============================================================
# PARAMETERS
# ============================================================
sensor_width = 256
sensor_height = 256
n_pixels_to_plot = 16

# Analysis window
x_min, x_max = 0, 30
y_min, y_max = 130, 180

# ============================================================
# OUTPUT DIR
# ============================================================
base_name = "LGAD_THL_Source_Subtraction"
output_dir = base_name + "_analysis"
plots_dir = os.path.join(output_dir, "plots")
gif_dir = os.path.join(output_dir, "gifs")
os.makedirs(plots_dir, exist_ok=True)
os.makedirs(gif_dir, exist_ok=True)

# ============================================================
# STYLE
# ============================================================
plt.style.use("default")
sns.set(style="white", context="talk")

# ============================================================
# DATA LOADING FUNCTION
# ============================================================
def load_thl_dataset(filename):
    with h5py.File(filename, "r") as f:
        pixel_data = f["/pixel_hits"][:]
        attrs = dict(f.attrs)

    unique_thls = np.arange(
        attrs["thl_start_mv"],
        attrs["thl_end_mv"] + attrs["thl_step_mv"],
        attrs["thl_step_mv"],
    )

    return pixel_data, attrs, unique_thls


pixel_data_with, attrs, unique_thls = load_thl_dataset(input_file_with)
pixel_data_without, _, _ = load_thl_dataset(input_file_without)

# ============================================================
# PER-THL PROCESSING
# ============================================================
def process_dataset(pixel_data, unique_thls):
    thl_data = {}

    for thl in unique_thls:
        mask = pixel_data["thl"] == thl
        thl_pixels = pixel_data[mask]

        hit_map = np.zeros((sensor_height, sensor_width), dtype=np.uint64)
        tot_map = np.zeros_like(hit_map, dtype=np.float32)
        count_map = np.zeros_like(hit_map, dtype=np.uint32)

        for p in thl_pixels:
            x, y = p["x"], p["y"]
            if x_min <= x < x_max and y_min <= y < y_max:
                hit_map[y, x] += 1
                tot_map[y, x] += p["tot"]
                count_map[y, x] += 1

        mean_tot_map = np.divide(tot_map, count_map, where=count_map > 0)

        window_hits = hit_map[y_min:y_max, x_min:x_max]

        thl_data[thl] = {
            "hit_map": hit_map,
            "mean_tot_map": mean_tot_map,
            "total_hits_window": np.sum(window_hits),
            "total_hits_all": np.sum(hit_map),
            "active_pixels": np.sum(window_hits > 0),
            "mean_tot": np.mean(thl_pixels["tot"]) if len(thl_pixels) else 0,
        }

    return thl_data


thl_with = process_dataset(pixel_data_with, unique_thls)
thl_without = process_dataset(pixel_data_without, unique_thls)

# ============================================================
# DIFFERENCE DATA
# ============================================================
thl_diff = {}
for thl in unique_thls:
    thl_diff[thl] = {
        "hit_map": thl_with[thl]["hit_map"] - thl_without[thl]["hit_map"],
        "total_hits_window": thl_with[thl]["total_hits_window"]
        - thl_without[thl]["total_hits_window"],
        "total_hits_all": thl_with[thl]["total_hits_all"]
        - thl_without[thl]["total_hits_all"],
        "active_pixels": thl_with[thl]["active_pixels"]
        - thl_without[thl]["active_pixels"],
        "mean_tot": thl_with[thl]["mean_tot"] - thl_without[thl]["mean_tot"],
    }

# ============================================================
# FIND MOST SOURCE-SENSITIVE PIXELS
# ============================================================
total_diff_map = np.zeros((sensor_height, sensor_width), dtype=np.int64)
for thl in unique_thls:
    total_diff_map += np.maximum(
    thl_diff[thl]["hit_map"], 0
    ).astype(np.int64)

flat_idx = np.argsort(total_diff_map.flatten())[-n_pixels_to_plot:]
active_pixels = [
    (np.unravel_index(i, total_diff_map.shape)[1],
     np.unravel_index(i, total_diff_map.shape)[0])
    for i in reversed(flat_idx)
    if total_diff_map.flatten()[i] > 0
]

print("Most source-sensitive pixels:")
for x, y in active_pixels:
    print(f"  ({x},{y})")

# ============================================================
# PLOT 1: PER-PIXEL HIT CURVES
# ============================================================
plt.figure(figsize=(11, 7))
colors = plt.cm.tab10(np.linspace(0, 1, len(active_pixels)))

for i, (x, y) in enumerate(active_pixels):
    h_with = [thl_with[t]["hit_map"][y, x] for t in unique_thls]
    h_wo = [thl_without[t]["hit_map"][y, x] for t in unique_thls]
    h_diff = np.array(h_with) - np.array(h_wo)

    plt.plot(unique_thls, h_with, "-", color=colors[i], alpha=0.7)
    plt.plot(unique_thls, h_wo, "--", color=colors[i], alpha=0.7)
    plt.plot(unique_thls, h_diff, "o", color=colors[i], label=f"({x},{y})")

plt.yscale("log")
plt.gca().invert_xaxis()
plt.xlabel("Threshold (mV)")
plt.ylabel("Hit count")
plt.title("Per-pixel hit response (with / without / difference)")
plt.legend(fontsize=8)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(plots_dir, "pixel_hit_curves.png"), dpi=300)
plt.show()

# ============================================================
# PLOT 2: TOTAL HITS VS THL (ACTIVE PIXELS)
# ============================================================
def plot_total(metric, ylabel, fname):
    with_vals = [thl_with[t][metric] for t in unique_thls]
    wo_vals = [thl_without[t][metric] for t in unique_thls]
    diff_vals = np.array(with_vals) - np.array(wo_vals)

    plt.figure(figsize=(10, 6))
    plt.plot(unique_thls, with_vals, "g-", label="With source")
    plt.plot(unique_thls, wo_vals, "r--", label="Without source")
    plt.plot(unique_thls, diff_vals, "b-o", label="Difference")
    plt.yscale("log")
    plt.gca().invert_xaxis()
    plt.xlabel("Threshold (mV)")
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, fname), dpi=300)
    plt.show()


plot_total("total_hits_window", "Total hits (active pixels)", "total_hits_active_pixels.png")
plot_total("total_hits_all", "Total hits (all pixels)", "total_hits_all_pixels.png")

# ============================================================
# PLOT 3: MEAN TOT VS THL
# ============================================================
plt.figure(figsize=(10, 6))
plt.plot(unique_thls, [thl_with[t]["mean_tot"] for t in unique_thls], "g-", label="With source")
plt.plot(unique_thls, [thl_without[t]["mean_tot"] for t in unique_thls], "r--", label="Without source")
plt.plot(unique_thls, [thl_diff[t]["mean_tot"] for t in unique_thls], "b-o", label="Difference")
plt.gca().invert_xaxis()
plt.xlabel("Threshold (mV)")
plt.ylabel("Mean TOT")
plt.title("Mean TOT vs Threshold")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(plots_dir, "mean_tot_vs_threshold.png"), dpi=300)
plt.show()

# ============================================================
# PLOT 4: DIFFERENCE MAP GIF
# ============================================================
frames = []
vmax = np.percentile(np.abs(total_diff_map), 99)
norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)

for thl in unique_thls:
    fig, ax = plt.subplots(figsize=(7, 7))
    diff_map = thl_diff[thl]["hit_map"][y_min:y_max, x_min:x_max]

    im = ax.imshow(
        diff_map,
        cmap="RdBu",
        norm=norm,
        origin="lower",
        extent=[x_min, x_max, y_min, y_max],
    )
    ax.set_title(f"Hit difference (with − without)\nTHL = {thl:.1f} mV")
    plt.colorbar(im, ax=ax, label="Δ hits")

    buf = io.BytesIO()
    plt.savefig(buf, dpi=150, bbox_inches="tight")
    buf.seek(0)
    frames.append(Image.open(buf))
    plt.close(fig)

gif_path = os.path.join(gif_dir, "difference_map.gif")
frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=250, loop=0)

print("\nAnalysis complete")
print("Results saved in:", output_dir)
print("Difference GIF:", gif_path)
