import h5py
import numpy as np
import matplotlib.pyplot as plt
import os

# List available HDF5 files
hdf5_files = [f for f in os.listdir() if f.endswith('.h5') and f.startswith('bias_scan')]
if not hdf5_files:
    print("No bias scan HDF5 files found in current directory.")
    exit()

# Let user choose which file to analyze
print("Available bias scan files:")
for i, f in enumerate(hdf5_files):
    print(f"{i+1}: {f}")

while True:
    try:
        choice = int(input("\nEnter file number to analyze (1-{}): ".format(len(hdf5_files))))
        if 1 <= choice <= len(hdf5_files):
            filename = hdf5_files[choice-1]
            break
        else:
            print("Please enter a number between 1 and", len(hdf5_files))
    except ValueError:
        print("Please enter a valid number")

print(f"\nAnalyzing file: {filename}\n")

# Open the HDF5 file and print structure
print("=== HDF5 File Structure ===")
with h5py.File(filename, 'r') as f:
    # Print attributes
    print("\nFile Attributes:")
    for attr in f.attrs:
        print(f"{attr}: {f.attrs[attr]}")
    
    # Store parameters for later use
    bias_start = f.attrs['bias_start']
    bias_end = f.attrs['bias_end']
    bias_step = f.attrs['bias_step']
    
    # Print datasets
    print("\nDatasets:")
    def print_objects(name, obj):
        if isinstance(obj, h5py.Dataset):
            print(f"  {name} (shape: {obj.shape}, dtype: {obj.dtype})")
    f.visititems(print_objects)
    
    # Load the bias scan results
    scan_data = f['/bias_scan'][:]
    
    # Print first 20 lines of scan data
    print("\nFirst 20 lines of /bias_scan data:")
    print("Bias(V) | Frame | Hits")
    print("----------------------")
    for i in range(min(20, len(scan_data))):
        print(f"{scan_data[i]['bias']:6.1f} | {scan_data[i]['frame_idx']:5} | {scan_data[i]['hits']}")

    # Calculate total hits per bias value
    bias_values = np.unique(scan_data['bias'])
    total_hits = []
    
    for bias in bias_values:
        total_hits.append(np.sum(scan_data[scan_data['bias'] == bias]['hits']))

# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(bias_values, total_hits, 'bo-', linewidth=2, markersize=8)

# Add labels and title
plt.title('Total Hits vs Bias Voltage\nFile: {}'.format(filename), fontsize=14)
plt.xlabel('Bias Voltage (V)', fontsize=12)
plt.ylabel('Total Hits', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)

# Add scan parameters annotation
params_text = f"Scan Parameters:\nStart: {bias_start}V\nEnd: {bias_end}V\nStep: {bias_step}V"
plt.annotate(params_text, xy=(0.02, 0.98), xycoords='axes fraction',
            ha='left', va='top', bbox=dict(boxstyle='round', fc='white', alpha=0.8))

plt.tight_layout()
plt.show()