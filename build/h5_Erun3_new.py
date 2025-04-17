import h5py
import numpy as np
import matplotlib.pyplot as plt

filename = "pixel_data_20250405_024447.h5"
with h5py.File(filename, 'r') as f:
    if 'pixel_hits' in f:
        pixel_hits = f['pixel_hits'][:]
        print(f"Number of pixel hits: {len(pixel_hits)}")
        
        # Print top 20 rows of the dataset
        print("\nTop 20 rows of pixel_hits dataset:")
        print("\nx, y, toa, ftoa, tot, hit_count")
        for i in range(min(10, len(pixel_hits))):
            print(pixel_hits[i]['x'], pixel_hits[i]['y'], pixel_hits[i]['toa'], pixel_hits[i]['ftoa'],
                  pixel_hits[i]['tot'], pixel_hits[i]['hit_count'])
        
        # Extract data
        x = pixel_hits['x']
        y = pixel_hits['y']
        hit_count = pixel_hits['hit_count']
        toa = pixel_hits['toa']
        tot = pixel_hits['tot']
        
        # Define common plotting parameters
        bins = (256, 256)  # 256x256 pixel detector
        extent = [0, 255, 0, 255]  # Full sensor extent
        
        # Check if the hit_count_summary dataset exists
        if 'hit_count_summary' in f:
            # Use the direct hit count summary
            hit_count_map = f['hit_count_summary'][:]
            
            # 1. Event Count Heatmap from Summary
            plt.figure(figsize=(10, 8))
            plt.imshow(hit_count_map, origin='lower', extent=extent, cmap='inferno')
            plt.colorbar(label='Hit Count')
            plt.title('Pixel Hits (Total Hit Count per Pixel)')
            plt.xlabel('X Coordinate')
            plt.ylabel('Y Coordinate')
            #plt.savefig(f'hit_count_heatmap_{filename.replace(".h5", "")}.png')
            plt.show()
        else:
            
            # Calculate hit counts by counting unique pixel occurrences
            hit_count_map = np.zeros((256, 256), dtype=int)
            for i in range(len(pixel_hits)):
                x_val = x[i]
                y_val = y[i]
                if 0 <= x_val < 256 and 0 <= y_val < 256:
                    hit_count_map[y_val, x_val] += 1
            hit_count_map[0][0] = 0
            cleaned_hit_count_map= np.clip(hit_count_map, 1, 10)
            # 1. Event Count Heatmap (Calculated)
            plt.figure(figsize=(10, 8))
            plt.imshow(cleaned_hit_count_map, origin='lower', extent=extent, cmap='inferno')
            plt.colorbar(label='Hit Count')
            plt.title('Pixel Hits (Total Hit Count per Pixel)')
            plt.xlabel('X Coordinate')
            plt.ylabel('Y Coordinate')
            #plt.savefig(f'hit_count_heatmap_{filename.replace(".h5", "")}.png')
            plt.show()
        
        # 2. ToA Heatmap (mean time of arrival per pixel)
        # Create an empty map to store sum of ToA values
        toa_sum_map = np.zeros((256, 256), dtype=float)
        # Count occurrences of each pixel for averaging
        count_map = np.zeros((256, 256), dtype=int)
        
        # Sum up ToA values for each pixel
        for i in range(len(pixel_hits)):
            x_val = x[i]
            y_val = y[i]
            if 0 <= x_val < 256 and 0 <= y_val < 256:
                toa_sum_map[y_val, x_val] += pixel_hits['toa'][i]
                count_map[y_val, x_val] += 1
        
        # Calculate mean ToA (avoiding division by zero)
        toa_mean_map = np.zeros_like(toa_sum_map)
        nonzero_mask = count_map > 0
        toa_mean_map[nonzero_mask] = toa_sum_map[nonzero_mask] / count_map[nonzero_mask]
        cleaned_toa_mean_map = np.clip(toa_mean_map, 0, 5e+08)
        plt.figure(figsize=(10, 8))
        plt.imshow(toa_sum_map[nonzero_mask], origin='lower', extent=extent, cmap='inferno')
        plt.colorbar(label='Mean ToA (Time of Arrival)')
        plt.title('Pixel Hits (Mean ToA)')
        plt.xlabel('X Coordinate')
        plt.ylabel('Y Coordinate')
        #plt.savefig(f'toa_heatmap_{filename.replace(".h5", "")}.png')
        plt.show()
        
        # 3. ToT Heatmap (mean time over threshold per pixel)
        # Create an empty map to store sum of ToT values
        tot_sum_map = np.zeros((256, 256), dtype=float)
        
        # Sum up ToT values for each pixel
        for i in range(len(pixel_hits)):
            x_val = pixel_hits[i]['x']
            y_val = pixel_hits[i]['y']
            if 0 <= x_val < 256 and 0 <= y_val < 256:
                tot_sum_map[y_val, x_val] += pixel_hits[i]['tot']
        
        # Calculate mean ToT (avoiding division by zero)
        tot_mean_map = np.zeros_like(tot_sum_map)
        tot_mean_map[nonzero_mask] = tot_sum_map[nonzero_mask] / count_map[nonzero_mask]
        
        plt.figure(figsize=(10, 8))
        plt.imshow(tot_mean_map, origin='lower', extent=extent, cmap='inferno')
        plt.colorbar(label='Mean ToT (Time over Threshold)')
        plt.title('Pixel Hits (Mean ToT)')
        plt.xlabel('X Coordinate')
        plt.ylabel('Y Coordinate')
        #plt.savefig(f'tot_heatmap_{filename.replace(".h5", "")}.png')
        plt.show()
        
        # 4. Event Count vs ToT (histogram)
        plt.figure(figsize=(12, 6))
        cleaned_tot = np.clip(cleaned_hit_count_map,0, np.mean(cleaned_hit_count_map) * 1.5)
        plt.hist(cleaned_tot, bins=100, alpha=0.7)
        plt.xlabel('ToT Value (Time over Threshold)')
        plt.ylabel('Event Count')
        plt.title('Distribution of Time over Threshold (ToT)')
        plt.grid(alpha=0.3)
        #plt.savefig(f'tot_histogram_{filename.replace(".h5", "")}.png')
        plt.show()
        
        # 5. 2D Histogram of ToT vs Hit Count
        plt.figure(figsize=(12, 8))
        
        # Get max hit count per pixel
        max_hit_per_pixel = np.zeros(len(x), dtype=int)
        for i in range(len(pixel_hits)):
            x_val = pixel_hits[i]['x']
            y_val = pixel_hits[i]['y']
            if 0 <= x_val < 256 and 0 <= y_val < 256:
                max_hit_per_pixel[i] = hit_count_map[y_val, x_val]
        
        # Create scatter plot with hexbin
        cleaned_max_hit_per_pixel = np.clip(max_hit_per_pixel, 0, 10)
        plt.hexbin(tot, max_hit_per_pixel, gridsize=50, cmap='viridis', bins='log', mincnt=1)
        plt.colorbar(label='Number of Pixels')
        plt.xlabel('ToT Value (Time over Threshold)')
        plt.ylabel('Hit Count per Pixel')
        plt.title('Correlation between ToT and Hit Count')
        plt.grid(alpha=0.3)
        #plt.savefig(f'tot_vs_hitcount_{filename.replace(".h5", "")}.png')
        plt.show()
        
    else:
        print("Error: 'pixel_hits' dataset not found in the HDF5 file.")