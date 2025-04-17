import h5py
import numpy as np
import matplotlib.pyplot as plt


filename = "pixel_data_20250326_212021.h5"


with h5py.File(filename, 'r') as f:

    if 'pixel_hits' in f:
        pixel_hits = f['pixel_hits'][:]
        print(f"Number of pixel hits: {len(pixel_hits)}")
        
        # Print the top 20 rows of the dataset
        print("Top 20 rows of the dataset:")
        print(pixel_hits[:20])
        

        
        x = pixel_hits['x']
        y = pixel_hits['y']
        hit_count = pixel_hits['hit_count']
        toa = pixel_hits['toa']
        tot = pixel_hits['tot']
        
        hist, xedges, yedges = np.histogram2d(x, y, bins=(256, 256), weights=hit_count)
        
        # Count Heatmap
        plt.figure(figsize=(10, 8))
        plt.imshow(hist.T, origin='lower', extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]], cmap='viridis')
        plt.colorbar(label='Hit Count')
        plt.title('Pixel Hits (Hit Count)')
        plt.xlabel('X Coordinate')
        plt.ylabel('Y Coordinate')
        #plt.savefig(f'hit_count_heatmap_{filename.replace(".h5", "")}.png')
        plt.show()
        
        # ToA Heatmap
        plt.figure(figsize=(10, 8))
        toa_hist, _, _ = np.histogram2d(x, y, bins=(256, 256), weights=toa)
        plt.imshow(toa_hist.T, origin='lower', extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]], cmap='plasma')
        plt.colorbar(label='ToA (Time of Arrival)')
        plt.title('Pixel Hits (ToA)')
        plt.xlabel('X Coordinate')
        plt.ylabel('Y Coordinate')
        #plt.savefig(f'tot_heatmap_{filename.replace(".h5", "")}.png')
        plt.show()
        
        # ToT Heatmap
        plt.figure(figsize=(10, 8))
        tot_hist, _, _ = np.histogram2d(x, y, bins=(256, 256), weights=tot)
        plt.imshow(tot_hist.T, origin='lower', extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]], cmap='inferno')
        plt.colorbar(label='ToT (Time over Threshold)')
        plt.title('Pixel Hits (ToT)')
        plt.xlabel('X Coordinate')
        plt.ylabel('Y Coordinate')
        #plt.savefig(f'toa_heatmap_{filename.replace(".h5", "")}.png')
        plt.show()
    else:
        print("Error: 'pixel_hits' dataset not found in the HDF5 file.")