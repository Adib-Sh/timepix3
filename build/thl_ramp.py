
import h5py
import numpy as np
import matplotlib.pyplot as plt

filename = "thl_calibration_20250405_043423.h5"
with h5py.File(filename, 'r') as f:
    if 'pixel_hits' in f:
        pixel_hits = f['pixel_hits'][:]
        print(f"Total Number of Pixel Hits: {len(pixel_hits)}\n")

        # Count hits per THL
        unique_thls, counts = np.unique(pixel_hits['thl'], return_counts=True)

        # Print THL counts
        print("THL Value | Number of Hits")
        print("--------------------------")
        for thl, count in zip(unique_thls, counts):
            print(f"{thl:<0} | {count}")

        # Plot THL vs. Number of Hits
        plt.figure(figsize=(20, 6))
        plt.plot(unique_thls, counts, 'ob-', color='royalblue', alpha=0.7)
        plt.xlabel("THL Value")
        plt.ylabel("Number of Hits")
        plt.title("THL vs. Number of Hits")
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.show()