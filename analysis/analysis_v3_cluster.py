from plot_tools_v2 import *
import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import os
import pandas as pd
from scipy.spatial import KDTree
setup_plot_style()

  
    
 
# Import Data NanoMAX
#==========================================================================================
input_dir = "/home/adisha/git/libkatherine/build/BeamData 20250608 NanoMAX"
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#energy_keV, upper_lim, lower_lim = "16keV*", 20, 0
#input_file = input_dir + "/ToTdata_datadriven_20250608_104654.h5"

#energy_keV, upper_lim, lower_lim = "12keV", 16, 0
#input_file = input_dir+"/ToTdata_datadriven_20250608_115316.h5"

#energy_keV, upper_lim, lower_lim = "10keV" , 14, 0
#input_file = input_dir+"/ToTdata_datadriven_20250608_120847.h5"

energy_keV, upper_lim, lower_lim = "8keV", 12, 0
input_file = input_dir+"/ToTdata_datadriven_20250608_122428.h5"

#energy_keV, upper_lim, lower_lim = "7keV", 12, 0
#input_file = input_dir+"/ToTdata_datadriven_20250608_125050.h5"




# Import Data FemtoMAX
#==========================================================================================
input_dir ="/home/adisha/git/libkatherine/build/BeamData 20250908 FemtoMAX"
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


#energy_keV, upper_lim, lower_lim = "17keV", 30, 5
#input_file = input_dir+"/ToTdata_datadriven_20250908_165800.h5"

#energy_keV, upper_lim, lower_lim = "16keV", 20, 5
#input_file = input_dir+"/ToTdata_datadriven_20250908_165709.h5"

#energy_keV, upper_lim, lower_lim = "15keV", 30, 5
#input_file = input_dir+"/ToTdata_datadriven_20250908_165631.h5"

#energy_keV, upper_lim, lower_lim = "14keV", 30, 0
#input_file = input_dir+"/ToTdata_datadriven_20250908_165543.h5"

#energy_keV, upper_lim, lower_lim = "13keV", 30, 0
#input_file = input_dir+"/ToTdata_datadriven_20250908_165500.h5"

#energy_keV, upper_lim, lower_lim = "12keV", 30, 0
#input_file = input_dir+"/ToTdata_datadriven_20250908_165410.h5"

#energy_keV, upper_lim, lower_lim = "11keV" , 30, 0
#input_file = input_dir+"/ToTdata_datadriven_20250908_165305.h5"

#energy_keV, upper_lim, lower_lim = "10keV" , 30, 0
#input_file = input_dir+"/ToTdata_datadriven_20250908_165219.h5"

#energy_keV, upper_lim, lower_lim = "9keV" , 30, 0
#input_file = input_dir+"/ToTdata_datadriven_20250908_165145.h5"

#energy_keV, upper_lim, lower_lim = "8keV", 30, 0
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
output_dir = f"analysis_cluster_{base_name}"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"[INFO] Created output directory: {output_dir}")
  
    
  
# Cluster finding
#==========================================================================================
def find_charge_sharing_clusters(data, temporal_window=25, spatial_distance=2, 
                                  x_range=None, y_range=None):
    
    # Filter by spatial range if specified
    data_filtered = data.copy()
    if x_range is not None:
        data_filtered = data_filtered[(data_filtered['x'] >= x_range[0]) & 
                                       (data_filtered['x'] < x_range[1])]
    if y_range is not None:
        data_filtered = data_filtered[(data_filtered['y'] >= y_range[0]) & 
                                       (data_filtered['y'] < y_range[1])]
    
    # Sort by time of arrival
    data_filtered = data_filtered.sort_values('toa').reset_index(drop=True)
    
    # Initialize cluster tracking
    cluster_id = 0
    clusters = []
    visited = np.zeros(len(data_filtered), dtype=bool)
    
    for i in range(len(data_filtered)):
        if visited[i]:
            continue
            
        # Start new cluster
        current_hit = data_filtered.iloc[i]
        cluster_hits = [i]
        visited[i] = True
        
        # Find all hits within temporal and spatial windows
        # Temporal window
        time_mask = (np.abs(data_filtered['toa'] - current_hit['toa']) <= temporal_window)
        temporal_candidates = data_filtered[time_mask & ~visited].index.tolist()
        
        if not temporal_candidates:
            # Single pixel cluster
            clusters.append({
                'cluster_id': cluster_id,
                'n_pixels': 1,
                'x_mean': current_hit['x'],
                'y_mean': current_hit['y'],
                'x_pixels': [current_hit['x']],
                'y_pixels': [current_hit['y']],
                'toa_mean': current_hit['toa'],
                'toa_min': current_hit['toa'],
                'toa_max': current_hit['toa'],
                'tot_sum': current_hit['tot'],
                'tot_individual': [current_hit['tot']],
            })
            cluster_id += 1
        
            continue
        
        # Build spatial tree for candidates
        candidates_data = data_filtered.loc[temporal_candidates]
        spatial_coords = candidates_data[['x', 'y']].values
        tree = KDTree(spatial_coords)
        
        # Query for neighbors within spatial distance
        current_coords = np.array([[current_hit['x'], current_hit['y']]])
        neighbors_idx = tree.query_ball_point(current_coords, spatial_distance)[0]
        
        # Map back to original indices
        neighbor_indices = [temporal_candidates[idx] for idx in neighbors_idx]
        
        # Add neighbors to cluster
        for idx in neighbor_indices:
            if not visited[idx]:
                cluster_hits.append(idx)
                visited[idx] = True
        
        # Extract cluster information
        cluster_data = data_filtered.iloc[cluster_hits]
        
        clusters.append({
            'cluster_id': cluster_id,
            'n_pixels': len(cluster_hits),
            'x_mean': cluster_data['x'].mean(),
            'y_mean': cluster_data['y'].mean(),
            'x_pixels': cluster_data['x'].tolist(),
            'y_pixels': cluster_data['y'].tolist(),
            'toa_mean': cluster_data['toa'].mean(),
            'toa_min': cluster_data['toa'].min(),
            'toa_max': cluster_data['toa'].max(),
            'tot_sum': cluster_data['tot'].sum(),
            'tot_individual': cluster_data['tot'].tolist(),
        })
        
        cluster_id += 1
    return pd.DataFrame(clusters)


def analyze_charge_sharing(clusters_df, min_cluster_size=2):
    # Filter for multi-pixel clusters (charge sharing events)
    charge_sharing = clusters_df[clusters_df['n_pixels'] >= min_cluster_size]
    single_pixel = clusters_df[clusters_df['n_pixels'] == 1]
    
    stats = {
        'total_clusters': len(clusters_df),
        'single_pixel_events': len(single_pixel),
        'charge_sharing_events': len(charge_sharing),
        'charge_sharing_fraction': len(charge_sharing) / len(clusters_df) if len(clusters_df) > 0 else 0,
        'mean_cluster_size': charge_sharing['n_pixels'].mean() if len(charge_sharing) > 0 else 0,
        'max_cluster_size': charge_sharing['n_pixels'].max() if len(charge_sharing) > 0 else 0,
        'mean_tot_single': single_pixel['tot_sum'].mean() if len(single_pixel) > 0 else 0,
        'mean_tot_shared': charge_sharing['tot_sum'].mean() if len(charge_sharing) > 0 else 0,
    }
    
    return stats, charge_sharing, single_pixel



def fast_cluster_finder(df, temporal_window=3, spatial_distance=3):
    """Extremely fast charge sharing cluster finder using cKDTree."""
    x = df["x"].to_numpy(np.float32)
    y = df["y"].to_numpy(np.float32)
    toa = df["toa"].to_numpy(np.float32)
    tot = df["tot"].to_numpy(np.float32)

    n = len(x)
    visited = np.zeros(n, dtype=bool)
    clusters = []

    # Build KDTree once
    coords = np.column_stack((x, y))
    tree = cKDTree(coords)

    for i in range(n):
        if visited[i]:
            continue
        # Temporal mask
        mask_time = np.abs(toa - toa[i]) <= temporal_window
        # Find neighbors within spatial distance
        idx = tree.query_ball_point(coords[i], spatial_distance)
        idx = np.array(idx, dtype=int)
        idx = idx[mask_time[idx] & ~visited[idx]]
        visited[idx] = True
        # Cluster data
        cl_x, cl_y, cl_toa, cl_tot = x[idx], y[idx], toa[idx], tot[idx]
        clusters.append((
            len(idx),
            cl_x.mean(),
            cl_y.mean(),
            cl_toa.mean(),
            cl_toa.min(),
            cl_toa.max(),
            cl_tot.sum()
        ))
    if not clusters:
        return pd.DataFrame(columns=["n_pixels","x_mean","y_mean","toa_mean","toa_min","toa_max","tot_sum"])
    return pd.DataFrame(clusters, columns=["n_pixels","x_mean","y_mean","toa_mean","toa_min","toa_max","tot_sum"])



    
    
# Data Preparation for Plotting
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


'''

# Hit Count Per-Pixel Plot
#==========================================================================================
norm = LogNorm(vmin=1, vmax=np.max(clean_hit_counts[clean_hit_counts > 0]) if np.any(clean_hit_counts > 0) else 1)
fig1 = plt.figure(figsize=(20, 9))
fig1.suptitle('Sensor Per-Pixel Hit Count', y=1.05, color='white')
# 3D Plot
ax1 = fig1.add_subplot(121, projection='3d')
plot_pixel_3d(ax1, x, y, clean_hit_counts, "Sensor 3D Plot", zlabel='Hit Count')
# 2D Plot
ax2 = fig1.add_subplot(122)
plot_pixel_2d(ax2, clean_hit_counts, "Sensor 2D Plot", norm=norm)
plt.savefig(os.path.join(output_dir, 'Sensor Per-Pixel Hit Count'), dpi=150, bbox_inches='tight')
plt.show()





# Hit Count 32x32 Binned Plot
#==========================================================================================
norm = LogNorm(vmin=1, vmax=np.max(clean_hit_counts[clean_hit_counts > 0]) if np.any(clean_hit_counts > 0) else 1)
fig2 = plt.figure(figsize=(20, 9))
fig2.suptitle('Sensor 32x32 Binned Hit Count', y=1.05, color='white')


# 3D Plot
ax1 = fig2.add_subplot(121, projection='3d')
plot_pixel_3d(ax1, x_binned, y_binned, hist.T, "Sensor 3D Plot", zlabel='Hit Count', binned=True)


# 2D Plot
ax2 = fig2.add_subplot(122)
plot_pixel_2d(ax2, hist, "Sensor 2D Plot", binned=True, norm=norm)
plt.savefig(os.path.join(output_dir, 'Sensor 32x32 Binned Hit Count'), dpi=150, bbox_inches='tight')
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

'''


# Cropped Window
#==========================================================================================

if energy_keV == "16keV*": #Only for 16kev NanoMAX data
    # Define window (Only for 16keV)
    x_start, x_end = 70, 90
    y_start, y_end = 140, 160
else:
    # Define window

    x_start, x_end = 100, 120
    y_start, y_end = 110, 130

data_cropped = data[
    (data['x'] >= x_start) & (data['x'] < x_end) &
    (data['y'] >= y_start) & (data['y'] < y_end)]

data_cropped['tot'] = pd.to_numeric(data_cropped['tot'], errors='coerce')
data_cropped['tot'] = data_cropped[data_cropped['tot'] < upper_lim]['tot']
data_cropped['tot'] = data_cropped[data_cropped['tot'] > lower_lim]['tot']
data_cropped = data_cropped.replace([np.inf, -np.inf], np.nan).dropna(subset=['tot'])

# Cropped window data preparation for plot
hit_count_map_cropped = np.zeros((257, 257), dtype=int)
np.add.at(hit_count_map_cropped, (data_cropped['y'], data_cropped['x']), 1)
mask = np.ones_like(hit_count_map_cropped, dtype=bool)
mask[y_start:y_end, x_start:x_end] = False
hit_count_map_cropped[mask] = 1

'''

# Cropped Sensor Hit Count Per-Pixel Plot
#==========================================================================================
norm = LogNorm(vmin=1, vmax=np.max(hit_count_map_cropped[hit_count_map_cropped > 0]) if np.any(hit_count_map_cropped > 0) else 1)
fig4 = plt.figure(figsize=(20, 9))
fig4.suptitle('Cropped Beam Window Per-Pixel Hit Count', y=1.05, color='white')
# 3D Plot
ax1 = fig4.add_subplot(121, projection='3d')
plot_pixel_3d(ax1, x, y, hit_count_map_cropped, "Cropped Beam Window 3D Plot", zlabel='Hit Count')
# 2D Plot
ax2 = fig4.add_subplot(122)
plot_pixel_2d(ax2, hit_count_map_cropped, "Cropped Beam Window 2D Plot", norm=norm)
plt.savefig(os.path.join(output_dir, 'Cropped Beam Window Per-Pixel Hit Count'), dpi=150, bbox_inches='tight')
plt.show()

'''

# Charge Sharing Cluster Analysis
#==========================================================================================
print("\n" + "="*80)
print("CHARGE SHARING CLUSTER ANALYSIS")
print("="*80)

# Find charge sharing clusters
clusters_df = find_charge_sharing_clusters(
    data_cropped,
    temporal_window=5,
    spatial_distance=2,
    x_range=(x_start, x_end),
    y_range=(y_start, y_end)
)

# Analyze charge sharing
cluster_stats, charge_sharing, single_pixel = analyze_charge_sharing(
    clusters_df, 
    min_cluster_size=2
)

print(f"\nCluster Statistics:")
print(f"  Total events: {cluster_stats['total_clusters']}")
print(f"  Single pixel: {cluster_stats['single_pixel_events']} ({(1-cluster_stats['charge_sharing_fraction'])*100:.1f}%)")
print(f"  Charge sharing: {cluster_stats['charge_sharing_events']} ({cluster_stats['charge_sharing_fraction']*100:.1f}%)")
print(f"  Mean cluster size: {cluster_stats['mean_cluster_size']:.2f}")
print(f"  Max cluster size: {cluster_stats['max_cluster_size']}")
print(f"  Mean ToT (single): {cluster_stats['mean_tot_single']:.2f}")
print(f"  Mean ToT (shared): {cluster_stats['mean_tot_shared']:.2f}")

# Save cluster data
clusters_df.to_csv(os.path.join(output_dir, 'clusters_data.csv'), index=False)
print(f"\n[INFO] Cluster data saved to {os.path.join(output_dir, 'clusters_data.csv')}")




# ToT Distributions and Stat List
#==========================================================================================
stats_list = []

# Charge Sharing (Multi-pixel clusters)
if len(charge_sharing) > 0:
    charge_sharing_stats = fit_skew_normal(
        charge_sharing["tot_sum"], 
        len(charge_sharing['tot_sum'].unique()),
        data_type=f"(Charge Sharing) at {energy_keV}", 
        output_dir=output_dir
    )
    charge_sharing_stats.update({
        'filename': os.path.basename(input_file),
        'energy': energy_keV,
        'timestamp': timestamp,
        'data_type': 'charge_sharing',
        'n_events': len(charge_sharing),
        'mean_cluster_size': cluster_stats['mean_cluster_size'],
    })
    stats_list.append(charge_sharing_stats)


# Single Pixel (No charge sharing)
if len(single_pixel) > 0:
    single_pixel_stats = fit_skew_normal(
        single_pixel["tot_sum"], 
        len(single_pixel['tot_sum'].unique()),
        data_type=f"(Single Pixel) at {energy_keV}", 
        output_dir=output_dir
    )
    single_pixel_stats.update({
        'filename': os.path.basename(input_file),
        'energy': energy_keV,
        'timestamp': timestamp,
        'data_type': 'single_pixel',
        'n_events': len(single_pixel),
        'mean_cluster_size': 1.0,
    })
    stats_list.append(single_pixel_stats)


# Cropped (All events in cropped window)
cropped_stats = fit_skew_normal(
    data_cropped["tot"], 
    len(data_cropped['tot'].unique()),
    data_type=f"(Cropped Pixels) at {energy_keV}", 
    output_dir=output_dir
)
cropped_stats.update({
    'filename': os.path.basename(input_file),
    'energy': energy_keV,
    'timestamp': timestamp,
    'data_type': 'cropped',
    'n_events': len(data_cropped),
    'mean_cluster_size': np.nan,
})
stats_list.append(cropped_stats)


# All Pixels
data_all = data.copy()
data_all['tot'] = pd.to_numeric(data_all['tot'], errors='coerce')
data_all['tot'] = data_all[data_all['tot'] < upper_lim]['tot']
data_all['tot'] = data_all[data_all['tot'] > lower_lim]['tot']
data_all = data_all.replace([np.inf, -np.inf], np.nan).dropna(subset=['tot'])
all_stats = fit_skew_normal(
    data_all["tot"], 
    len(data_all['tot'].unique()),
    data_type=f"(All Pixels) at {energy_keV}", 
    legend_loc='upper left', 
    output_dir=output_dir
)
all_stats.update({
    'filename': os.path.basename(input_file),
    'energy': energy_keV,
    'timestamp': timestamp,
    'data_type': 'all',
    'n_events': len(data_all),
    'mean_cluster_size': np.nan,
})
stats_list.append(all_stats)

'''

# ToA Distribution Histograms
#==========================================================================================

# Prepare ToA data for all datasets
data_charge_sharing_toa = charge_sharing.copy() if len(charge_sharing) > 0 else pd.DataFrame()
data_single_pixel_toa = single_pixel.copy() if len(single_pixel) > 0 else pd.DataFrame()
data_cropped_toa = data_cropped.copy()
data_all_toa = data_all.copy()

# Filter ToA < 1e9 for charge sharing
if len(data_charge_sharing_toa) > 0:
    data_charge_sharing_toa['toa_mean'] = pd.to_numeric(data_charge_sharing_toa['toa_mean'], errors='coerce')
    data_charge_sharing_toa = data_charge_sharing_toa.replace([np.inf, -np.inf], np.nan).dropna(subset=['toa_mean'])
    data_charge_sharing_toa = data_charge_sharing_toa[data_charge_sharing_toa['toa_mean'] < 1e9]

# Filter ToA < 1e9 for single pixel
if len(data_single_pixel_toa) > 0:
    data_single_pixel_toa['toa_mean'] = pd.to_numeric(data_single_pixel_toa['toa_mean'], errors='coerce')
    data_single_pixel_toa = data_single_pixel_toa.replace([np.inf, -np.inf], np.nan).dropna(subset=['toa_mean'])
    data_single_pixel_toa = data_single_pixel_toa[data_single_pixel_toa['toa_mean'] < 1e9]

# Filter ToA < 1e9 for cropped
data_cropped_toa['toa'] = pd.to_numeric(data_cropped_toa['toa'], errors='coerce')
data_cropped_toa = data_cropped_toa.replace([np.inf, -np.inf], np.nan).dropna(subset=['toa'])
data_cropped_toa = data_cropped_toa[data_cropped_toa['toa'] < 1e9]

# Filter ToA < 1e9 for all
data_all_toa['toa'] = pd.to_numeric(data_all_toa['toa'], errors='coerce')
data_all_toa = data_all_toa.replace([np.inf, -np.inf], np.nan).dropna(subset=['toa'])
data_all_toa = data_all_toa[data_all_toa['toa'] < 1e9]

# Create ToA distribution plot
fig_toa_dist = plt.figure(figsize=(20, 9))
fig_toa_dist.suptitle(f'Time-of-Arrival (ToA) Distributions at {energy_keV}', y=1.02, color='white')

# Charge sharing
ax1 = fig_toa_dist.add_subplot(141)
if len(data_charge_sharing_toa) > 0:
    ax1.hist(data_charge_sharing_toa['toa_mean'], bins=100, color='cyan', alpha=0.7, edgecolor='black')
    ax1.set_xlabel('Time-of-Arrival (ToA) [a.u.]', color='white')
    ax1.set_ylabel('Counts', color='white')
    ax1.set_title('Charge Sharing', color='white')
    ax1.grid(True, alpha=0.3)

# Single pixel
ax2 = fig_toa_dist.add_subplot(142)
if len(data_single_pixel_toa) > 0:
    ax2.hist(data_single_pixel_toa['toa_mean'], bins=100, color='magenta', alpha=0.7, edgecolor='black')
    ax2.set_xlabel('Time-of-Arrival (ToA) [a.u.]', color='white')
    ax2.set_ylabel('Counts', color='white')
    ax2.set_title('Single Pixel', color='white')
    ax2.grid(True, alpha=0.3)

# Cropped pixels
ax3 = fig_toa_dist.add_subplot(143)
if len(data_cropped_toa) > 0:
    ax3.hist(data_cropped_toa['toa'], bins=100, color='orange', alpha=0.7, edgecolor='black')
    ax3.set_xlabel('Time-of-Arrival (ToA) [a.u.]', color='white')
    ax3.set_ylabel('Counts', color='white')
    ax3.set_title('Cropped Pixels', color='white')
    ax3.grid(True, alpha=0.3)

# All pixels
ax4 = fig_toa_dist.add_subplot(144)
if len(data_all_toa) > 0:
    ax4.hist(data_all_toa['toa'], bins=100, color='lime', alpha=0.7, edgecolor='black')
    ax4.set_xlabel('Time-of-Arrival (ToA) [a.u.]', color='white')
    ax4.set_ylabel('Counts', color='white')
    ax4.set_title('All Pixels', color='white')
    ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'ToA_Distributions'), dpi=150, bbox_inches='tight')
plt.show()




# ToA vs ToT Correlation Plot
#==========================================================================================
fig_corr = plt.figure(figsize=(20, 9))
fig_corr.suptitle(f'ToA vs ToT Correlation at {energy_keV}', y=1.02, color='white')

# Charge sharing correlation (use toa_mean vs tot_sum)
ax1 = fig_corr.add_subplot(141)
if len(data_charge_sharing_toa) > 0:
    corr_cs = data_charge_sharing_toa[['tot_sum', 'toa_mean']].copy()
    corr_cs['tot_sum'] = pd.to_numeric(corr_cs['tot_sum'], errors='coerce')
    corr_cs['toa_mean'] = pd.to_numeric(corr_cs['toa_mean'], errors='coerce')
    corr_cs = corr_cs.replace([np.inf, -np.inf], np.nan).dropna()
    
    if len(corr_cs) > 0:
        h1 = ax1.hist2d(corr_cs['tot_sum'], corr_cs['toa_mean'], 
                        bins=[50, 50], cmap='viridis', norm=LogNorm())
        ax1.set_xlabel('Time-over-Threshold (ToT) [a.u.]', color='white')
        ax1.set_ylabel('Time-of-Arrival (ToA) [a.u.]', color='white')
        ax1.set_title('Charge Sharing', color='white')
        plt.colorbar(h1[3], ax=ax1, label='Counts')

# Single pixel correlation (use toa_mean vs tot_sum)
ax2 = fig_corr.add_subplot(142)
if len(data_single_pixel_toa) > 0:
    corr_sp = data_single_pixel_toa[['tot_sum', 'toa_mean']].copy()
    corr_sp['tot_sum'] = pd.to_numeric(corr_sp['tot_sum'], errors='coerce')
    corr_sp['toa_mean'] = pd.to_numeric(corr_sp['toa_mean'], errors='coerce')
    corr_sp = corr_sp.replace([np.inf, -np.inf], np.nan).dropna()
    
    if len(corr_sp) > 0:
        h2 = ax2.hist2d(corr_sp['tot_sum'], corr_sp['toa_mean'], 
                        bins=[50, 50], cmap='viridis', norm=LogNorm())
        ax2.set_xlabel('Time-over-Threshold (ToT) [a.u.]', color='white')
        ax2.set_ylabel('Time-of-Arrival (ToA) [a.u.]', color='white')
        ax2.set_title('Single Pixel', color='white')
        plt.colorbar(h2[3], ax=ax2, label='Counts')

# Cropped pixels correlation
ax3 = fig_corr.add_subplot(143)
if len(data_cropped_toa) > 0:
    cropped_corr = data_cropped[['tot', 'toa']].copy()
    cropped_corr['tot'] = pd.to_numeric(cropped_corr['tot'], errors='coerce')
    cropped_corr['toa'] = pd.to_numeric(cropped_corr['toa'], errors='coerce')
    cropped_corr = cropped_corr.replace([np.inf, -np.inf], np.nan).dropna()
    cropped_corr = cropped_corr[cropped_corr['toa'] < 1e9]
    
    if len(cropped_corr) > 0:
        h3 = ax3.hist2d(cropped_corr['tot'], cropped_corr['toa'], 
                        bins=[50, 50], cmap='viridis', norm=LogNorm())
        ax3.set_xlabel('Time-over-Threshold (ToT) [a.u.]', color='white')
        ax3.set_ylabel('Time-of-Arrival (ToA) [a.u.]', color='white')
        ax3.set_title('Cropped Pixels', color='white')
        plt.colorbar(h3[3], ax=ax3, label='Counts')

# All pixels correlation
ax4 = fig_corr.add_subplot(144)
if len(data_all_toa) > 0:
    all_corr = data_all[['tot', 'toa']].copy()
    all_corr['tot'] = pd.to_numeric(all_corr['tot'], errors='coerce')
    all_corr['toa'] = pd.to_numeric(all_corr['toa'], errors='coerce')
    all_corr = all_corr.replace([np.inf, -np.inf], np.nan).dropna()
    all_corr = all_corr[all_corr['toa'] < 1e9]
    
    if len(all_corr) > 0:
        h4 = ax4.hist2d(all_corr['tot'], all_corr['toa'], 
                        bins=[50, 50], cmap='viridis', norm=LogNorm())
        ax4.set_xlabel('Time-over-Threshold (ToT) [a.u.]', color='white')
        ax4.set_ylabel('Time-of-Arrival (ToA) [a.u.]', color='white')
        ax4.set_title('All Pixels', color='white')
        plt.colorbar(h4[3], ax=ax4, label='Counts')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'ToA_vs_ToT_Correlation'), dpi=150, bbox_inches='tight')
plt.show()


'''
#==========================================================================================
# Export data to a full analysis csv
#==========================================================================================
csv_filename = "analysis_charge_sharing.csv"

# Define unique keys that identify a row (if these match, we overwrite)
unique_keys = ['filename', 'energy', 'data_type']

# Create DataFrame from current session
new_data = pd.DataFrame(stats_list)

# Reorder columns for consistency
column_order = [
    'timestamp', 'filename', 'energy', 'data_type', 'n_events', 'mean_cluster_size',
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

# Fill in missing columns with NaN
for col in column_order:
    if col not in new_data.columns:
        new_data[col] = np.nan
new_data = new_data[column_order]

# Load existing file if it exists
if os.path.exists(csv_filename):
    print(f"\n[INFO] Loading existing data from {csv_filename}")
    existing_data = pd.read_csv(csv_filename)
    
    # Ensure existing data has all required columns
    for col in column_order:
        if col not in existing_data.columns:
            existing_data[col] = np.nan
    existing_data = existing_data[column_order]
    
    # Create masks for matching rows
    # For each row in new_data, check if it exists in existing_data
    existing_keys = existing_data[unique_keys].apply(lambda row: tuple(row), axis=1)
    new_keys = new_data[unique_keys].apply(lambda row: tuple(row), axis=1)
    
    # Keep only rows from existing_data that don't match any new_data rows
    mask_keep = ~existing_keys.isin(new_keys)
    filtered_existing = existing_data[mask_keep]
    
    # Report what's being updated
    n_updated = (~mask_keep).sum()
    if n_updated > 0:
        print(f"[INFO] Updating {n_updated} existing row(s) for energy={energy_keV}")
        updated_rows = existing_data[~mask_keep][unique_keys]
        for _, row in updated_rows.iterrows():
            print(f"       - Overwriting: {row['data_type']} ({row['energy']})")
    
    # Combine: keep non-matching existing rows + all new rows
    combined = pd.concat([filtered_existing, new_data], ignore_index=True)
    print(f"[INFO] Total rows in CSV: {len(combined)} ({len(filtered_existing)} existing + {len(new_data)} new)")
    
else:
    print(f"\n[INFO] Creating new file {csv_filename}")
    combined = new_data
    print(f"[INFO] Total rows in CSV: {len(combined)}")

# Sort by energy and data_type for better readability
combined = combined.sort_values(['energy', 'data_type']).reset_index(drop=True)

# Write back to file
combined.to_csv(csv_filename, index=False)
print(f"[INFO] Analysis data written to {csv_filename}")
print("="*80)



