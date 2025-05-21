import h5py
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import MaxNLocator
from datetime import datetime
import pandas as pd
from scipy.stats import norm
from scipy import signal

# Set professional style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("talk")

# Custom colors
COLORS = {'primary': '#3366CC', 
          'secondary': '#FF9933', 
          'tertiary': '#33AA55', 
          'quartary': '#CC3366'}

def analyze_thl_calibration(filename):
    """
    Comprehensive analysis of THL calibration data from an H5 file.
    
    Parameters:
    -----------
    filename : str
        Path to the H5 file containing THL calibration data
    """
    # Extract timestamp from filename
    timestamp_str = filename.split('_')[-1].split('.')[0]
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        date_formatted = timestamp.strftime("%B %d, %Y at %H:%M:%S")
    except ValueError:
        date_formatted = "Unknown date"
    
    print(f"📊 THL Calibration Analysis")
    print(f"📅 Data collected on: {date_formatted}")
    print(f"📁 File: {filename}\n")
    
    # Open H5 file and analyze data
    with h5py.File(filename, 'r') as f:
        # Print available keys for debugging
        print(f"📋 Available datasets in file: {list(f.keys())}\n")
        
        if 'pixel_hits' in f:
            pixel_hits = f['pixel_hits'][:]
            total_hits = len(pixel_hits)
            print(f"🔢 Total Number of Pixel Hits: {total_hits:,}\n")
            
            # Basic statistics of pixel hits
            analyze_pixel_hits(pixel_hits)
            
            # Create a DataFrame for easier analysis
            df = pd.DataFrame({
                'thl': pixel_hits['thl'],
                'x': pixel_hits['x'] if 'x' in pixel_hits.dtype.names else None,
                'y': pixel_hits['y'] if 'y' in pixel_hits.dtype.names else None,
                'tot': pixel_hits['tot'] if 'tot' in pixel_hits.dtype.names else None,
                'timestamp': pixel_hits['timestamp'] if 'timestamp' in pixel_hits.dtype.names else None
            })
            
            # Drop columns that are None
            df = df.dropna(axis=1, how='all')
            
            # Create a comprehensive visualization
            create_visualization(df, date_formatted)
        else:
            print("❌ No 'pixel_hits' dataset found in the file.")
            available_keys = list(f.keys())
            if available_keys:
                print(f"Available keys: {available_keys}")
                
def analyze_pixel_hits(pixel_hits):
    """Perform detailed analysis on pixel hits data"""
    # Get available fields in the dataset
    fields = pixel_hits.dtype.names
    print(f"📊 Available fields: {fields}\n")
    
    # Count hits per THL
    unique_thls, counts = np.unique(pixel_hits['thl'], return_counts=True)
    
    # Calculate statistics
    min_thl = unique_thls.min()
    max_thl = unique_thls.max()
    avg_counts = counts.mean()
    median_counts = np.median(counts)
    std_counts = counts.std()
    
    print("📏 THL Range Statistics:")
    print(f"  • Minimum THL value: {min_thl}")
    print(f"  • Maximum THL value: {max_thl}")
    print(f"  • THL range: {max_thl - min_thl}")
    print(f"  • Number of unique THL values: {len(unique_thls)}")
    
    print("\n📈 Hit Count Statistics:")
    print(f"  • Average hits per THL: {avg_counts:.2f}")
    print(f"  • Median hits per THL: {median_counts:.2f}")
    print(f"  • Standard deviation: {std_counts:.2f}")
    print(f"  • Maximum hits: {counts.max()} at THL={unique_thls[np.argmax(counts)]}")
    print(f"  • Minimum hits: {counts.min()} at THL={unique_thls[np.argmin(counts)]}")
    
    print("\n📊 THL Value | Number of Hits (Top 10 and Bottom 10)")
    print("------------------------------------------")
    
    # Sort THL values by count
    sorted_idx = np.argsort(counts)
    
    # Print bottom 5
    for i in range(min(5, len(sorted_idx))):
        idx = sorted_idx[i]
        print(f"{unique_thls[idx]:<9} | {counts[idx]:,}")
        
    print("          ...       ...")
    
    # Print top 5
    for i in range(min(5, len(sorted_idx))):
        idx = sorted_idx[-(i+1)]
        print(f"{unique_thls[idx]:<9} | {counts[idx]:,}")

def create_visualization(df, date_formatted):
    """Create comprehensive visualizations of the THL calibration data"""
    # Count hits per THL
    thl_counts = df['thl'].value_counts().sort_index()
    unique_thls = thl_counts.index.values
    counts = thl_counts.values
    
    # Create figure with multiple subplots
    fig = plt.figure(figsize=(20, 15))
    fig.suptitle(f"THL Calibration Analysis - {date_formatted}", fontsize=16, y=0.98)
    
    # Define grid layout
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 0.8])
    
    # Plot 1: THL vs. Number of Hits (linear scale)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(unique_thls, counts, 'o-', color=COLORS['primary'], alpha=0.8, markersize=4)
    ax1.set_xlabel("THL Value")
    ax1.set_ylabel("Number of Hits")
    ax1.set_title("THL vs. Number of Hits (Linear Scale)")
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    
    # Annotate max value
    max_idx = np.argmax(counts)
    ax1.annotate(f"Max: {counts[max_idx]:,} hits",
                xy=(unique_thls[max_idx], counts[max_idx]),
                xytext=(10, 10), textcoords='offset points',
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=.2'))
    
    # Plot 2: THL vs. Number of Hits (log scale)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.semilogy(unique_thls, counts, 'o-', color=COLORS['secondary'], alpha=0.8, markersize=4)
    ax2.set_xlabel("THL Value")
    ax2.set_ylabel("Number of Hits (log scale)")
    ax2.set_title("THL vs. Number of Hits (Log Scale)")
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.xaxis.set_major_locator(MaxNLocator(integer=True))
    
    # Plot 3: Histogram of THL values
    ax3 = fig.add_subplot(gs[1, 0])
    sns.histplot(df['thl'], bins=min(50, len(unique_thls)), kde=True, ax=ax3, color=COLORS['primary'])
    ax3.set_xlabel("THL Value")
    ax3.set_ylabel("Frequency")
    ax3.set_title("Distribution of THL Values")
    
    # Plot 4: Derivative of THL curve (rate of change)
    ax4 = fig.add_subplot(gs[1, 1])
    
    # Calculate derivative
    derivative = np.gradient(counts, unique_thls)
    
    # Smooth derivative using Savitzky-Golay filter
    window_size = min(15, len(derivative) - 2)
    if window_size % 2 == 0:  # Make sure window size is odd
        window_size += 1
    
    if len(derivative) > window_size:
        smooth_derivative = signal.savgol_filter(derivative, window_size, 3)
        ax4.plot(unique_thls, smooth_derivative, '-', color=COLORS['tertiary'], alpha=0.8, linewidth=2, label='Smoothed')
        ax4.plot(unique_thls, derivative, 'o', color=COLORS['tertiary'], alpha=0.3, markersize=3, label='Raw')
    else:
        ax4.plot(unique_thls, derivative, 'o-', color=COLORS['tertiary'], alpha=0.8, markersize=4)
    
    ax4.set_xlabel("THL Value")
    ax4.set_ylabel("Rate of Change")
    ax4.set_title("Derivative of Hit Counts")
    ax4.grid(True, linestyle='--', alpha=0.7)
    ax4.legend()
    
    # Check if spatial information is available
    if 'x' in df.columns and 'y' in df.columns:
        # Plot 5: Spatial distribution of hits
        ax5 = fig.add_subplot(gs[2, :])
        
        # Limit to a reasonable sample size for visualization
        sample_size = min(10000, len(df))
        sample = df.sample(sample_size)
        
        scatter = ax5.scatter(sample['x'], sample['y'], c=sample['thl'], 
                             alpha=0.6, cmap='viridis', s=10)
        ax5.set_xlabel("X Position")
        ax5.set_ylabel("Y Position")
        ax5.set_title("Spatial Distribution of Hits (colored by THL value)")
        ax5.set_aspect('equal')
        ax5.grid(True, linestyle='--', alpha=0.4)
        cbar = plt.colorbar(scatter, ax=ax5)
        cbar.set_label('THL Value')
    else:
        # If no spatial info, create a THL cumulative distribution
        ax5 = fig.add_subplot(gs[2, :])
        # Calculate cumulative sum
        cum_counts = np.cumsum(counts)
        cum_counts_norm = cum_counts / cum_counts[-1]  # Normalize to 0-1
        
        ax5.plot(unique_thls, cum_counts_norm, '-', color=COLORS['quartary'], linewidth=2)
        ax5.set_xlabel("THL Value")
        ax5.set_ylabel("Cumulative Fraction of Hits")
        ax5.set_title("Cumulative Distribution of Hits")
        ax5.grid(True, linestyle='--', alpha=0.7)
        
        # Find 50% and 90% points
        idx_50 = np.where(cum_counts_norm >= 0.5)[0][0]
        idx_90 = np.where(cum_counts_norm >= 0.9)[0][0]
        
        ax5.axhline(y=0.5, color='gray', linestyle='--', alpha=0.7)
        ax5.axhline(y=0.9, color='gray', linestyle='--', alpha=0.7)
        ax5.axvline(x=unique_thls[idx_50], color='gray', linestyle='--', alpha=0.7)
        ax5.axvline(x=unique_thls[idx_90], color='gray', linestyle='--', alpha=0.7)
        
        ax5.annotate(f"50%: THL={unique_thls[idx_50]}", 
                    xy=(unique_thls[idx_50], 0.5),
                    xytext=(10, 10), textcoords='offset points',
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=.2'))
        
        ax5.annotate(f"90%: THL={unique_thls[idx_90]}", 
                    xy=(unique_thls[idx_90], 0.9),
                    xytext=(10, 10), textcoords='offset points',
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=.2'))
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.show()

    # Return the figure in case it's needed
    return fig

if __name__ == "__main__":
    # File to analyze
    filename = "thl_calibration_20250521_061323.h5"
    
    # Run analysis
    analyze_thl_calibration(filename)