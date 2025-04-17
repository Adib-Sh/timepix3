
import h5py
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

file_path = 'Fe55-155V_newconfig_holes_true.h5'
with h5py.File(file_path, 'r') as file:
    # Function to recursively find and print dataset names and their top 10 rows
    def print_datasets(name, obj):
        if isinstance(obj, h5py.Dataset):
            print(f"\nDataset: {name}")
            print(f"Shape: {obj.shape}")
            print(f"Data type: {obj.dtype}")
            print("Top 10 rows:")
            print(obj[:10])  # Print the first 10 rows of the dataset

    # Traverse the file and print dataset information
    print("Datasets in the file:")
    file.visititems(print_datasets)
# Open the HDF5 file
with h5py.File(file_path, 'r') as file:
    # Assuming the dataset is named 'pixel_data'
    dataset = file["frame_0/pixel_data"]
    
    # Extract data
    x = dataset[:, 0]
    y = dataset[:, 1]
    toa = dataset[:, 2]
    tot = dataset[:, 3]

    # Create a single figure with two subplots
    fig = plt.figure(figsize=(20, 8))  # Larger figure size

    # First subplot: 3D Scatter plot for ToA
    ax1 = fig.add_subplot(121, projection='3d')  # 1 row, 2 columns, first subplot
    scatter1 = ax1.scatter(x, y, toa, c=toa, cmap='viridis_r', alpha=1)
    ax1.set_xlabel('X', fontsize = 15)
    ax1.set_ylabel('Y', fontsize = 15)
    ax1.set_zlabel('Time of Arrival (ToA)', fontsize = 14)
    ax1.set_zlim([min(toa), max(toa)])  # Set Z-axis limits
    ax1.set_box_aspect([1, 1, 1])  # Equal aspect ratio for X, Y, Z axes
    ax1.view_init(elev=30, azim=45)  # Adjust viewing angle
    plt.colorbar(scatter1, ax=ax1, label='Time of Arrival (ToA)')
    ax1.set_title("3D Pixel Data: ToA", fontsize = 15)

    # Second subplot: 3D Scatter plot for ToT
    ax2 = fig.add_subplot(122, projection='3d')  # 1 row, 2 columns, second subplot
    scatter2 = ax2.scatter(x, y, tot, c=tot, cmap='viridis_r', alpha=1)
    ax2.set_xlabel('X', fontsize = 15)
    ax2.set_ylabel('Y', fontsize = 15)
    ax2.set_zlabel('Time over Threshold (ToT)', fontsize = 14)
    ax2.set_zlim([min(tot), max(tot)])  # Set Z-axis limits
    ax2.set_box_aspect([1, 1, 1])  # Equal aspect ratio for X, Y, Z axes
    ax2.view_init(elev=30, azim=45)  # Adjust viewing angle
    plt.colorbar(scatter2, ax=ax2, label='Time over Threshold (ToT)')
    ax2.set_title("3D Pixel Data: ToT", fontsize = 15)

    # Adjust layout to prevent overlap
    plt.tight_layout()
    plt.show()
    
    # Histogram of ToT
    plt.figure(figsize=(10, 6))
    plt.hist(tot, bins=50, color='indigo', alpha=0.9)
    plt.title("Pixel Data: Time over Threshold (ToT) Distribution")
    plt.xlabel("ToT")
    plt.ylabel("Count")
    plt.grid(True)
    plt.show()
