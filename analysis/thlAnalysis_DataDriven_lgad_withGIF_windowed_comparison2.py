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

# Window
x_min, x_max = 0, 30
y_min, y_max = 130, 180

# ============================================================
# OUTPUT
# ============================================================
output_dir = "LGAD_clean_analysis"
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

    thl_values = np.arange(
        attrs["thl_start_mv"],
        attrs["thl_end_mv"] + attrs["thl_step_mv"],
        attrs["thl_step_mv"],
    )

    return pixel_data, thl_values


data_with, thls = load_dataset(file_with)
data_without, _ = load_dataset(file_without)


# ============================================================
# CLEAN PROCESSING FUNCTION
# ============================================================
def compute_totals(pixel_data, thls):
    results = {}

    # Extract arrays once (faster + cleaner)
    xs = pixel_data["x"]
    ys = pixel_data["y"]
    thl_array = pixel_data["thl"]

    # Window mask (constant)
    window_mask = (
        (xs >= x_min) & (xs < x_max) &
        (ys >= y_min) & (ys < y_max)
    )

    for thl in thls:
        # Use np.isclose instead of ==
        thl_mask = np.isclose(thl_array, thl)

        # All hits at this THL
        hits_all = np.sum(thl_mask)

        # Hits inside window
        hits_window = np.sum(thl_mask & window_mask)

        results[thl] = {
            "total_all": int(hits_all),
            "total_window": int(hits_window),
        }

    return results


tot_with = compute_totals(data_with, thls)
tot_without = compute_totals(data_without, thls)


# ============================================================
# BUILD ARRAYS
# ============================================================
with_all = np.array([tot_with[t]["total_all"] for t in thls], dtype=np.int64)
without_all = np.array([tot_without[t]["total_all"] for t in thls], dtype=np.int64)
diff_all = with_all - without_all

with_window = np.array([tot_with[t]["total_window"] for t in thls], dtype=np.int64)
without_window = np.array([tot_without[t]["total_window"] for t in thls], dtype=np.int64)
diff_window = with_window - without_window


# ============================================================
# SANITY CHECK
# ============================================================
print("All pixels min/max diff:", diff_all.min(), diff_all.max())
print("Window pixels min/max diff:", diff_window.min(), diff_window.max())


# ============================================================
# PLOTTING FUNCTION
# ============================================================
def plot_totals(thls, with_vals, without_vals, diff_vals, title, filename):

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Positive counts in log scale
    ax1.plot(thls, with_vals, "g-", label="With source")
    ax1.plot(thls, without_vals, "r--", label="Without source")
    ax1.set_yscale("log")
    ax1.set_xlabel("Threshold (mV)")
    ax1.set_ylabel("Total hits")
    ax1.invert_xaxis()
    ax1.set_xlim
    # Difference on linear axis
    ax2 = ax1.twinx()
    ax2.plot(thls, diff_vals, "b", label="Difference")
    ax2.set_ylabel("Difference (with − without)")

    fig.suptitle(title)

    ax1.grid(alpha=0.3)

    # Combine legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="best")
    plt.xlim(780,100)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.show()
    
def plot_difference_log(thls, diff_vals, title, filename):

    plt.figure(figsize=(10, 6))
    plt.plot(thls, diff_vals, "b")
    plt.yscale("symlog", linthresh=10)

    plt.axhline(0, color="black", linewidth=1)
    plt.gca().invert_xaxis()
    plt.xlabel("Threshold (mV)")
    plt.ylabel("Hit difference (with − without)")
    #plt.ylim(0)
    plt.xlim(780,100)
    plt.title(title)
    plt.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.show()

def plot_difference_lin(thls, diff_vals, title, filename):

    plt.figure(figsize=(10, 6))
    plt.plot(thls, diff_vals, "b")
    #plt.yscale("symlog", linthresh=10)

    plt.axhline(0, color="black", linewidth=1)
    plt.gca().invert_xaxis()
    plt.xlabel("Threshold (mV)")
    plt.ylabel("Hit difference (with − without)")
    #plt.ylim(0)
    plt.xlim(780,100)
    plt.title(title)
    plt.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.show()


# ============================================================
# PLOTS
# ============================================================
plot_totals(
    thls,
    with_all,
    without_all,
    diff_all,
    "Total Hits (All Pixels)",
    "total_hits_all.png"
)

plot_totals(
    thls,
    with_window,
    without_window,
    diff_window,
    "Total Hits (Window Pixels)",
    "total_hits_window.png"
)


plot_difference_log(
    thls,
    diff_all,
    "Difference in Total Hits (All Pixels-log)",
    "difference_all_log.png"
)

plot_difference_log(
    thls,
    diff_window,
    "Difference in Total Hits (Window Pixels-log)",
    "difference_window_log.png"
)

plot_difference_lin(
    thls,
    diff_all,
    "Difference in Total Hits (All Pixels-lin)",
    "difference_all_lin.png"
)

plot_difference_lin(
    thls,
    diff_window,
    "Difference in Total Hits (Window Pixels-lin)",
    "difference_window_lin.png"
)


print("\nClean analysis complete.")
print("Results saved in:", output_dir)


