from plot_tools_v2 import *

import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import os
import pandas as pd


setup_plot_style()

  
    
   
# Import Data NanoMAX
#==========================================================================================
input_dir = "/home/adisha/git/libkatherine/build/BeamData 20250608 NanoMAX"
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

energy_keV, upper_lim, lower_lim = "16keV", 20, 0
input_file = input_dir + "/ToTdata_datadriven_20250608_104654.h5"

#energy_keV, upper_lim, lower_lim = "12keV", 16, 0
#input_file = input_dir+"/ToTdata_datadriven_20250608_115316.h5"

#energy_keV, upper_lim, lower_lim = "10keV" , 14, 0
#input_file = input_dir+"/ToTdata_datadriven_20250608_120847.h5"

#energy_keV, upper_lim, lower_lim = "8keV", 12, 0
#input_file = input_dir+"/ToTdata_datadriven_20250608_122428.h5"

#energy_keV, upper_lim, lower_lim = "7keV", 12, 0
#input_file = input_dir+"/ToTdata_datadriven_20250608_125050.h5"



### EXTRA DATA

#energy_keV, upper_lim, lower_lim = "14keV", 18, 0
#input_file = input_dir+"/ToTdata_datadriven_20250608_112924.h5"

#energy_keV = "7,5keV"
#input_file = input_dir+"/ToTdata_datadriven_20250608_125050.h5"

#energy_keV = "6,5keV"
#input_file = input_dir+"/ToTdata_datadriven_20250608_125050.h5"

#energy_keV = "6keV"
#input_file = input_dir+"/ToTdata_datadriven_20250608_125823.h5"

#energy_keV = "6keV_Flux32X"
#input_file = input_dir+"/ToTdata_datadriven_20250608_131937.h5"


# Import Data FemtoMAX
#==========================================================================================
input_dir ="/home/adisha/git/libkatherine/build/BeamData 20250908 FemtoMAX"
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


#energy_keV, upper_lim, lower_lim = "17keV", 30, 3
#input_file = input_dir+"/ToTdata_datadriven_20250908_165800.h5"

#energy_keV, upper_lim, lower_lim = "16keV", 30, 5
#input_file = input_dir+"/ToTdata_datadriven_20250908_165709.h5"

#energy_keV, upper_lim, lower_lim = "15keV", 30, 5
#input_file = input_dir+"/ToTdata_datadriven_20250908_165631.h5"

#energy_keV, upper_lim, lower_lim = "14keV", 30, 0
#input_file = input_dir+"/ToTdata_datadriven_20250908_165543.h5"

#energy_keV, upper_lim, lower_lim = "13keV", 30, 0
#input_file = input_dir+"/ToTdata_datadriven_20250908_165500.h5"

#energy_keV, upper_lim, lower_lim = "12keV", 30, 2
#input_file = input_dir+"/ToTdata_datadriven_20250908_165410.h5"

#energy_keV, upper_lim, lower_lim = "11keV" , 30, 0
#input_file = input_dir+"/ToTdata_datadriven_20250908_165305.h5"

#energy_keV, upper_lim, lower_lim = "10keV" , 30, 0
#input_file = input_dir+"/ToTdata_datadriven_20250908_165219.h5"

#energy_keV, upper_lim, lower_lim = "9keV" , 30, 0
#input_file = input_dir+"/ToTdata_datadriven_20250908_165145.h5"

#energy_keV, upper_lim, lower_lim = "8keV", 30, 2
#input_file = input_dir+"/ToTdata_datadriven_20250908_165057.h5"

#energy_keV, upper_lim, lower_lim = "7keV", 30, 0
#input_file = input_dir+"/ToTdata_datadriven_20250908_164918.h5"

#energy_keV, upper_lim, lower_lim = "6eV", 20, 0
#input_file = input_dir+"/ToTdata_datadriven_20250908_164723.h5"


with h5py.File(input_file, 'r') as f:
    data = f['/pixel_hits'][:]
    data = pd.DataFrame(data)




# Output folder
#==========================================================================================
base_name = os.path.splitext(os.path.basename(input_file))[0]
output_dir = f"analysis_{base_name}"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"[INFO] Created output directory: {output_dir}")
    
    
    
# Data Prepration for Plotting
#==========================================================================================
# Per-Pixel Data For Hit Count
hit_count_map = np.zeros((257, 257), dtype=int)
np.add.at(hit_count_map, (data['y'], data['x']), 1)
clean_hit_counts, sum1 = filter_outliers(hit_count_map, hit_count_map > 0)
x, y = np.meshgrid(np.arange(257), np.arange(257))
x, y = x.flatten(), y.flatten()


# Per-Pixel Data For ToT
x_edges_full = np.arange(257)
y_edges_full = np.arange(257)
x_centers_full = (x_edges_full[:-1] + x_edges_full[1:]) / 2
y_centers_full = (y_edges_full[:-1] + y_edges_full[1:]) / 2
xpos_full, ypos_full = np.meshgrid(x_centers_full, y_centers_full)
tot_hist_full, _, _ = np.histogram2d(data['x'], data['y'], bins=[x_edges_full, y_edges_full], weights=data['tot'])
counts_full, _, _ = np.histogram2d(data['x'], data['y'], bins=[x_edges_full, y_edges_full])
mean_tot_full = np.divide(tot_hist_full, counts_full, out=np.zeros_like(tot_hist_full), where=counts_full != 0)


# 32x32 Binned Data For Hit Count
hist, xedges, yedges = np.histogram2d(
    data['x'], data['y'],
    bins=[32, 32],
    range=[[0, 257], [0, 257]],
    weights=None)
x_binned, y_binned = np.meshgrid(xedges[:-1], yedges[:-1])
x_binned, y_binned = x_binned.flatten(), y_binned.flatten()


# 32x32 Binned Data For ToT
bin_size = 8  # 256/32 = 8
x_edges_bin = np.arange(0, 257, bin_size)
y_edges_bin = np.arange(0, 257, bin_size)
x_centers_bin = (x_edges_bin[:-1] + x_edges_bin[1:]) / 2
y_centers_bin = (y_edges_bin[:-1] + y_edges_bin[1:]) / 2
xpos_bin, ypos_bin = np.meshgrid(x_centers_bin, y_centers_bin)
tot_hist_bin, _, _ = np.histogram2d(data['x'], data['y'], bins=[x_edges_bin, y_edges_bin], weights=data['tot'])
counts_bin, _, _ = np.histogram2d(data['x'], data['y'], bins=[x_edges_bin, y_edges_bin])
mean_tot_bin = np.divide(tot_hist_bin, counts_bin, out=np.zeros_like(tot_hist_bin), where=counts_bin != 0)



# Hit Count Per-Pixel Plot
#==========================================================================================
norm = LogNorm(vmin=1, vmax=np.max(clean_hit_counts[clean_hit_counts > 0]) if np.any(clean_hit_counts > 0) else 1)
fig1 = plt.figure(figsize=(20, 9))
fig1.suptitle('Sensor Per-Pixel Hit Count', y=1.05, color='white')
# 3D Plot
ax1 = fig1.add_subplot(121, projection='3d')
plot_pixel_3d(ax1,x, y,clean_hit_counts,"Sensor 3D Plot", zlabel='Hit Count')
# 2D Plot
ax2 = fig1.add_subplot(122)
plot_pixel_2d(ax2, clean_hit_counts, "Sensor 2D Plot",  norm=norm)
plt.savefig(os.path.join(output_dir, 'Sensor Per-Pixel Hit Count'), dpi=150, bbox_inches='tight')
plt.show()




# Hit Count 32x32 Binned Plot
#==========================================================================================
norm = LogNorm(vmin=1, vmax=np.max(clean_hit_counts[clean_hit_counts > 0]) if np.any(clean_hit_counts > 0) else 1)
fig2 = plt.figure(figsize=(20, 9))
fig2.suptitle('Sensor Per-Pixel Hit Count', y=1.05, color='white')


# 3D Plot
ax1 = fig2.add_subplot(121, projection='3d')
plot_pixel_3d(ax1,x_binned, y_binned,hist.T,"Sensor 3D Plot", zlabel='Hit Count', binned = True)


# 2D Plot
ax2 = fig2.add_subplot(122)
plot_pixel_2d(ax2, hist, "Sensor 2D Plot", binned = True, norm=norm)
plt.savefig(os.path.join(output_dir, 'Sensor Per-Pixel Hit Count'), dpi=150, bbox_inches='tight')
plt.show()




# Spatial ToT Plot
#==========================================================================================
fig3 = plt.figure(figsize=(20, 9))
fig3.suptitle('Time-over-Threshold (ToT) Sensor Spatial Distribution', y=1.05, color='white')


# Per-pixel ToT plot
ax1 = fig3.add_subplot(121, projection='3d')
plot_surface_3d(ax1, xpos_full, ypos_full, mean_tot_full.T,
    title='Per-Pixel Time-over-Threshold (ToT)', zlabel='Mean ToT')


# 32x32 binned ToT plot
ax2 = fig3.add_subplot(122, projection='3d')
plot_surface_3d(ax2, xpos_bin, ypos_bin, mean_tot_bin.T,
    title='32×32 Binned Time-over-Threshold (ToT)', zlabel='Mean ToT')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'Per-Pixel Time-over-Threshold (ToT)'), dpi=150, bbox_inches='tight')
plt.show()




# Cropped Window
#==========================================================================================
if energy_keV == "16keV":
    # Define window (Only for 16keV)
    x_start, x_end = 70, 75
    y_start, y_end = 140, 145
else:
    # Define window
    x_start, x_end = 110, 115
    y_start, y_end = 120, 125

data_cropped = data[
    (data['x'] >= x_start) & (data['x'] < x_end) &
    (data['y'] >= y_start) & (data['y'] < y_end)]

data_cropped['tot'] = pd.to_numeric(data_cropped['tot'], errors='coerce')
data_cropped['tot'] = data_cropped[data_cropped['tot'] < upper_lim]['tot']
data_cropped['tot'] = data_cropped[data_cropped['tot'] > lower_lim]['tot']
data_cropped = data_cropped.replace([np.inf, -np.inf], np.nan).dropna(subset=['tot'])
# Cropped window data prepration for plot
hit_count_map_cropped = np.zeros((257, 257), dtype=int)
np.add.at(hit_count_map_cropped, (data_cropped['y'], data_cropped['x']), 1)
mask = np.ones_like(hit_count_map_cropped, dtype=bool)
mask[y_start:y_end, x_start:x_end] = False
hit_count_map_cropped[mask] = 1




# Cropped Sensor Hit Count Per-Pixel Plot
#==========================================================================================
norm = LogNorm(vmin=1, vmax=np.max(hit_count_map_cropped[hit_count_map_cropped > 0]) if np.any(hit_count_map_cropped > 0) else 1)
fig1 = plt.figure(figsize=(20, 9))
fig1.suptitle('Cropped Beam window Per-Pixel Hit Count', y=1.05, color='white')
# 3D Plot
ax1 = fig1.add_subplot(121, projection='3d')
plot_pixel_3d(ax1,x, y,hit_count_map_cropped,"Cropped Beam window 3D Plot", zlabel='Hit Count')
# 2D Plot
ax2 = fig1.add_subplot(122)
plot_pixel_2d(ax2, hit_count_map_cropped, "Cropped Beam window 2D Plot",  norm=norm)
plt.savefig(os.path.join(output_dir, 'Cropped Beam window Per-Pixel Hit Count'), dpi=150, bbox_inches='tight')
plt.show()




# Isolated Pixels
#==========================================================================================
# Finding isolated pixels
data_isolated = isolated_hits(
    data_cropped,
    slice_width=1e5,
    iso_dist=1,
    x_range= None,
    y_range= None,
    temporal_margin=20,
)

data_isolated['tot'] = pd.to_numeric(data_isolated['tot'], errors='coerce')
data_isolated['tot'] = data_isolated[data_isolated['tot'] < upper_lim]['tot']
data_isolated = data_isolated.replace([np.inf, -np.inf], np.nan).dropna(subset=['tot'])




# ToT Distributions and Stat List
#==========================================================================================
stats_list = []

# Isolated
isolated_stats = fit_skew_normal(data_isolated["tot"], len(data_isolated['tot'].unique()),
                data_type = f"(Isolated Hits) at {energy_keV}", output_dir=output_dir)
isolated_stats.update({
    'filename': os.path.basename(input_file),
    'energy': energy_keV,
    'timestamp': timestamp,
    'data_type': 'isolated',
})
stats_list.append(isolated_stats)


# Cropped
cropped_stats = fit_skew_normal(data_cropped["tot"], len(data_cropped['tot'].unique()),
                data_type = f"(Cropped Pixels) at {energy_keV}", output_dir=output_dir)
cropped_stats.update({
    'filename': os.path.basename(input_file),
    'energy': energy_keV,
    'timestamp': timestamp,
    'data_type': 'cropped',
})
stats_list.append(cropped_stats)


# All
data_all = data
data_all['tot'] = pd.to_numeric(data_all['tot'], errors='coerce')
data_all['tot'] = data_all[data_all['tot'] < upper_lim]['tot']
data_all['tot'] = data_all[data_all['tot'] > lower_lim]['tot']
data_all = data_all.replace([np.inf, -np.inf], np.nan).dropna(subset=['tot'])
all_stats = fit_skew_normal(data_all["tot"], len(data_all['tot'].unique()),
                data_type = f"(All Pixels) at {energy_keV}", legend_loc='upper left', output_dir=output_dir)
all_stats.update({
    'filename': os.path.basename(input_file),
    'energy': energy_keV,
    'timestamp': timestamp,
    'data_type': 'all',
})
stats_list.append(all_stats)




# ToA Distribution Histograms
#==========================================================================================

# Prepare ToA data for all three datasets
data_isolated_toa = data_isolated.copy()
data_isolated_toa['toa'] = pd.to_numeric(data_isolated_toa['toa'], errors='coerce')
data_isolated_toa = data_isolated_toa.replace([np.inf, -np.inf], np.nan).dropna(subset=['toa'])
data_isolated_toa = data_isolated_toa[data_isolated_toa['toa'] < 1e9]

data_cropped_toa = data_cropped.copy()
data_cropped_toa['toa'] = pd.to_numeric(data_cropped_toa['toa'], errors='coerce')
data_cropped_toa = data_cropped_toa.replace([np.inf, -np.inf], np.nan).dropna(subset=['toa'])
data_cropped_toa = data_cropped_toa[data_cropped_toa['toa'] < 1e9]

data_all_toa = data.copy()
data_all_toa['toa'] = pd.to_numeric(data_all_toa['toa'], errors='coerce')
data_all_toa = data_all_toa.replace([np.inf, -np.inf], np.nan).dropna(subset=['toa'])
data_all_toa = data_all_toa[data_all_toa['toa'] < 1e9]

# Create ToA distribution plot
fig_toa_dist = plt.figure(figsize=(20, 9))
fig_toa_dist.suptitle(f'Time-of-Arrival (ToA) Distributions at {energy_keV}', y=1.02, color='white')

# Isolated hits
ax1 = fig_toa_dist.add_subplot(131)
if len(data_isolated_toa) > 0:
    ax1.hist(data_isolated_toa['toa'], bins=100, color='deepskyblue', alpha=0.7, edgecolor='black')
    ax1.set_xlabel('Time-of-Arrival (ToA) [ns]', color='white')
    ax1.set_ylabel('Counts', color='white')
    ax1.set_title('Isolated Hits', color='white')
    ax1.grid(True, alpha=0.3)

# Cropped pixels
ax2 = fig_toa_dist.add_subplot(132)
if len(data_cropped_toa) > 0:
    ax2.hist(data_cropped_toa['toa'], bins=100, color='darkorange', alpha=0.7, edgecolor='black')
    ax2.set_xlabel('Time-of-Arrival (ToA) [ns]', color='white')
    ax2.set_ylabel('Counts', color='white')
    ax2.set_title('Cropped Pixels', color='white')
    ax2.grid(True, alpha=0.3)

# All pixels
ax3 = fig_toa_dist.add_subplot(133)
if len(data_all_toa) > 0:
    ax3.hist(data_all_toa['toa'], bins=100, color='limegreen', alpha=0.7, edgecolor='black')
    ax3.set_xlabel('Time-of-Arrival (ToA) [ns]', color='white')
    ax3.set_ylabel('Counts', color='white')
    ax3.set_title('All Pixels', color='white')
    ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, f'ToA_Distributions_{energy_keV}'), dpi=150, bbox_inches='tight')
plt.show()




# ToA vs ToT Correlation Plot
#==========================================================================================
fig_corr = plt.figure(figsize=(20, 9))
fig_corr.suptitle(f'ToA vs ToT Correlation at {energy_keV}', y=1.02, color='white')

# Isolated hits correlation
ax1 = fig_corr.add_subplot(131)
if len(data_isolated_toa) > 0 and len(data_isolated) > 0:
    isolated_corr = data_isolated[['tot', 'toa']].copy()
    isolated_corr['tot'] = pd.to_numeric(isolated_corr['tot'], errors='coerce')
    isolated_corr['toa'] = pd.to_numeric(isolated_corr['toa'], errors='coerce')
    isolated_corr = isolated_corr.replace([np.inf, -np.inf], np.nan).dropna()
    isolated_corr = isolated_corr[isolated_corr['toa'] < 1e9]
    
    if len(isolated_corr) > 0:
        h1 = ax1.hist2d(isolated_corr['tot'], isolated_corr['toa'], 
                        bins=[50, 50], cmap='viridis', norm=LogNorm())
        ax1.set_xlabel('Time-over-Threshold (ToT) [ns]', color='white')
        ax1.set_ylabel('Time-of-Arrival (ToA) [ns]', color='white')
        ax1.set_title('Isolated Hits', color='white')
        plt.colorbar(h1[3], ax=ax1, label='Counts')

# Cropped pixels correlation
ax2 = fig_corr.add_subplot(132)
if len(data_cropped_toa) > 0 and len(data_cropped) > 0:
    cropped_corr = data_cropped[['tot', 'toa']].copy()
    cropped_corr['tot'] = pd.to_numeric(cropped_corr['tot'], errors='coerce')
    cropped_corr['toa'] = pd.to_numeric(cropped_corr['toa'], errors='coerce')
    cropped_corr = cropped_corr.replace([np.inf, -np.inf], np.nan).dropna()
    cropped_corr = cropped_corr[cropped_corr['toa'] < 1e9]
    
    if len(cropped_corr) > 0:
        h2 = ax2.hist2d(cropped_corr['tot'], cropped_corr['toa'], 
                        bins=[50, 50], cmap='viridis', norm=LogNorm())
        ax2.set_xlabel('Time-over-Threshold (ToT) [ns]', color='white')
        ax2.set_ylabel('Time-of-Arrival (ToA) [ns]', color='white')
        ax2.set_title('Cropped Pixels', color='white')
        plt.colorbar(h2[3], ax=ax2, label='Counts')

# All pixels correlation
ax3 = fig_corr.add_subplot(133)
if len(data_all_toa) > 0 and len(data_all) > 0:
    all_corr = data_all[['tot', 'toa']].copy()
    all_corr['tot'] = pd.to_numeric(all_corr['tot'], errors='coerce')
    all_corr['toa'] = pd.to_numeric(all_corr['toa'], errors='coerce')
    all_corr = all_corr.replace([np.inf, -np.inf], np.nan).dropna()
    all_corr = all_corr[all_corr['toa'] < 1e9]
    
    if len(all_corr) > 0:
        h3 = ax3.hist2d(all_corr['tot'], all_corr['toa'], 
                        bins=[50, 50], cmap='viridis', norm=LogNorm())
        ax3.set_xlabel('Time-over-Threshold (ToT) [ns]', color='white')
        ax3.set_ylabel('Time-of-Arrival (ToA) [ns]', color='white')
        ax3.set_title('All Pixels', color='white')
        plt.colorbar(h3[3], ax=ax3, label='Counts')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, f'ToA_vs_ToT_Correlation_{energy_keV}'), dpi=150, bbox_inches='tight')
plt.show()




# Export data to a full analysis csv
#==========================================================================================
csv_filename = "analysis.csv"  # analysis file (for now works only for NanoMAX data´)
unique_keys = ['filename', 'energy', 'data_type']  # To identify duplicate entries

# Create DataFrame from current session
new_data = pd.DataFrame(stats_list)

# Reorder columns for consistency
column_order = [
    'timestamp', 'filename', 'energy', 'data_type',
    'shape', 'shape_err',
    'loc', 'loc_err',
    'scale', 'scale_err',
    'mean', 'mean_err',
    'median', 'median_err',
    'mode', 'mode_err',
    'fwhm', 'fwhm_err',
    'peak_tot_val',
    'peak_tot_count',
    'peak_tot_fit'
]

# Fill in missing columns just in case
for col in column_order:
    if col not in new_data.columns:
        new_data[col] = np.nan
new_data = new_data[column_order]

# Load existing file if present
if os.path.exists(csv_filename):
    existing_data = pd.read_csv(csv_filename)

    # Drop any rows from existing that match (filename, energy, data_type)
    mask = ~existing_data[unique_keys].apply(tuple, axis=1).isin(
        new_data[unique_keys].apply(tuple, axis=1)
    )
    combined = pd.concat([existing_data[mask], new_data], ignore_index=True)
else:
    combined = new_data

# Write back to file
combined.to_csv(csv_filename, index=False)
print(f"[INFO] Analysis data written to {csv_filename}")