import h5py
import numpy as np
import matplotlib.pyplot as plt

file_path = 'pixel_data_20250326_212021.h5'

COLUMN_NAMES = ['X', 'Y', 'ToA', 'fToA', 'ToT']


def find_datasets(name, obj):
    if isinstance(obj, h5py.Dataset):
        print(f"Dataset: {name}")
        print(f"  Shape: {obj.shape}")
        print(f"  Data type: {obj.dtype}")
        print(f"  Compression: {obj.compression}")
        print(f"  Chunking: {obj.chunks}")
        print(f"  Size: {obj.size}")
        datasets.append(name)

def read_metadata(group):
    print("\nMetadata:")
    for attr_name in group.attrs:
        attr_value = group.attrs[attr_name]
        print(f"  {attr_name}: {attr_value}")


def plot_pixel_data(dataset):
    data = dataset[:]
    x = data[:, 0]
    y = data[:, 1] 
    toa = data[:, 2] 
    tot = data[:, 3] 

    # Scatter plot of pixel positions
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, c=toa, cmap='viridis', alpha=1)
    plt.colorbar(label='Time of Arrival (ToA)')
    plt.title("Pixel Data: ToA")
    plt.xlabel("X")
    plt.ylabel("Y ")
    plt.grid(True)
    plt.show()
    
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, c=tot, cmap='viridis', alpha=1)
    plt.colorbar(label='Time over Threshold (ToT)')
    plt.title("Pixel Data: ToT")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.grid(True)
    plt.show()
    
    # Histogram of ToT
    plt.figure(figsize=(10, 6))
    plt.hist(tot, bins=50, color='blue', alpha=0.7)
    plt.title("Pixel Data: Time over Threshold (ToT) Distribution")
    plt.xlabel("ToT")
    plt.ylabel("Count")
    plt.grid(True)
    plt.show()


with h5py.File(file_path, 'r') as file:
    datasets = [] 
    file.visititems(find_datasets)
    
    if not datasets:
        print("No datasets found in the file.")
    else:
        print("\nAvailable datasets:")
        for i, dataset_name in enumerate(datasets):
            print(f"{i + 1}. {dataset_name}")
        
        try:
            selection = int(input("Enter the number of the dataset to inspect: ")) - 1
            if 0 <= selection < len(datasets):
                dataset_name = datasets[selection]
                dataset = file[dataset_name]
                
                print(f"\nDetails of dataset: '{dataset_name}'")
                print(f"  Shape: {dataset.shape}")
                print(f"  Data type: {dataset.dtype}")
                print(f"  Compression: {dataset.compression}")
                print(f"  Chunking: {dataset.chunks}")
                print(f"  Size: {dataset.size}")

                if dataset_name.endswith('pixel_data'):
                    print("\nColumn names:")
                    print(COLUMN_NAMES)

                    print("\nFirst 20 rows of pixel data:")
                    print(dataset[:20])
                    
                    plot_pixel_data(dataset)
                    
                    
                if isinstance(dataset.parent, h5py.Group):
                    read_metadata(dataset.parent)
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a valid number.")

def plot_pixel_counts(file_path):
    with h5py.File(file_path, 'r') as file:
        # Read the pixel_counts dataset
        pixel_counts = file['pixel_counts'][:]
        
        plt.figure(figsize=(12, 10))
        
        im = plt.imshow(pixel_counts, 
                       cmap='viridis',
                       interpolation='nearest',
                       origin='lower')
        
        plt.colorbar(im, label='Counts')
        
        plt.title('Pixel Counts (256×256)')
        plt.xlabel('X Position')
        plt.ylabel('Y Position')
        plt.grid(False)
        plt.show()
        
        total_counts = np.sum(pixel_counts)
        max_counts = np.max(pixel_counts)
        mean_counts = np.mean(pixel_counts)
        
        print(f"\nPixel Count Statistics:")
        print(f"Total counts: {total_counts}")
        print(f"Maximum counts in a single pixel: {max_counts}")
        print(f"Mean counts per pixel: {mean_counts:.2f}")
        
        plt.figure(figsize=(10, 6))
        plt.hist(pixel_counts.flatten(), bins=50, color='blue', alpha=0.7)
        plt.title("Distribution of Pixel Counts")
        plt.xlabel("Counts per Pixel")
        plt.ylabel("Number of Pixels")
        plt.grid(True)
        plt.show()
plot_pixel_counts(file_path)
