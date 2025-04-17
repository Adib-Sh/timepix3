import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter
import argparse
import os

def load_thl_data(filename):
    """
    Load data from the THL calibration HDF5 file
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")
    
    print(f"Loading data from {filename}...")
    with h5py.File(filename, 'r') as f:
        # Read attributes
        thl_start = f.attrs['thl_start']
        thl_end = f.attrs['thl_end']
        thl_step = f.attrs['thl_step']
        frames_per_thl = f.attrs['frames_per_thl']
        
        # Read pixel hits
        pixel_hits = f['/pixel_hits'][:]
        
        # Read THL scan data if it exists
        thl_scan = None
        if '/thl_scan' in f:
            thl_scan = f['/thl_scan'][:]
        
    return {
        'thl_start': thl_start,
        'thl_end': thl_end,
        'thl_step': thl_step,
        'frames_per_thl': frames_per_thl,
        'pixel_hits': pixel_hits,
        'thl_scan': thl_scan
    }

def format_with_suffix(x, pos):
    """Format tick labels with appropriate suffix (K, M, etc.)"""
    if x >= 1e6:
        return f'{x*1e-6:.0f}M'
    elif x >= 1e3:
        return f'{x*1e-3:.0f}K'
    else:
        return f'{x:.0f}'

def plot_thl_scan_curve(data):
    """
    Plot the overall S-curve showing hits vs THL value
    """
    print("Generating THL S-curve plot...")
    
    # Extract unique THL values
    thl_values = np.arange(data['thl_start'], data['thl_end'] + 1, data['thl_step'])
    
    # Count hits for each THL value
    hits_per_thl = {}
    for hit in data['pixel_hits']:
        thl = hit['thl']
        if thl not in hits_per_thl:
            hits_per_thl[thl] = 0
        hits_per_thl[thl] += 1
    
    # Convert to arrays for plotting
    x = []
    y = []
    for thl in sorted(hits_per_thl.keys()):
        x.append(thl)
        y.append(hits_per_thl[thl] / data['frames_per_thl'])  # Normalize by frames per THL
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(x, y, '-o', markersize=4)
    plt.yscale('log')
    plt.grid(True, which='both', linestyle='--', alpha=0.7)
    plt.xlabel('THL Value')
    plt.ylabel('Average Hits per Frame (log scale)')
    plt.title('THL S-Curve: Hit Rate vs Threshold')
    plt.gca().yaxis.set_major_formatter(FuncFormatter(format_with_suffix))
    
    # Find the threshold point (steepest part of the curve)
    if len(x) > 5:  # Need enough points to calculate derivative
        x_array = np.array(x)
        y_array = np.array(y)
        # Calculate approximate derivative
        dy_dx = np.diff(y_array) / np.diff(x_array)
        steepest_idx = np.argmin(dy_dx)  # Find steepest negative slope
        threshold_point = x_array[steepest_idx]
        
        plt.axvline(x=threshold_point, color='r', linestyle='--', 
                   label=f'Threshold point: {threshold_point}')
        plt.legend()
    
    plt.tight_layout()
    return plt.gcf()

def plot_hit_map(data):
    """
    Plot a 2D heatmap of hit counts across the detector
    """
    print("Generating hit map...")
    
    # Initialize hit map
    hit_map = np.zeros((256, 256))
    
    # Fill hit map
    for hit in data['pixel_hits']:
        x, y = hit['x'], hit['y']
        if 0 <= x < 256 and 0 <= y < 256:
            hit_map[y, x] += 1
    
    # Plot
    plt.figure(figsize=(10, 8))
    plt.imshow(hit_map, cmap='viridis', norm=LogNorm(vmin=1))
    plt.colorbar(label='Hit Count (log scale)')
    plt.xlabel('X Pixel')
    plt.ylabel('Y Pixel')
    plt.title('Detector Hit Map')
    plt.tight_layout()
    return plt.gcf()

def plot_thl_distributions(data):
    """
    Plot histograms for different THL ranges
    """
    print("Generating THL distribution plots...")
    
    thl_values = np.arange(data['thl_start'], data['thl_end'] + 1, data['thl_step'])
    
    # Split THL range into three regions for comparison
    low_idx = len(thl_values) // 3
    high_idx = 2 * len(thl_values) // 3
    
    low_range = thl_values[:low_idx]
    mid_range = thl_values[low_idx:high_idx]
    high_range = thl_values[high_idx:]
    
    plt.figure(figsize=(15, 5))
    
    # For each region, plot TOT distribution
    regions = [('Low THL', low_range, 'blue'), 
               ('Mid THL', mid_range, 'green'),
               ('High THL', high_range, 'red')]
    
    for i, (label, thl_range, color) in enumerate(regions):
        # Filter hits for this THL range
        tot_values = []
        for hit in data['pixel_hits']:
            if hit['thl'] in thl_range:
                tot_values.append(hit['tot'])
        
        if tot_values:
            plt.subplot(1, 3, i+1)
            plt.hist(tot_values, bins=50, color=color, alpha=0.7)
            plt.title(f'{label} ({min(thl_range)}-{max(thl_range)})')
            plt.xlabel('TOT Value')
            plt.ylabel('Count')
            plt.yscale('log')
            plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return plt.gcf()

def plot_toa_distributions(data):
    """
    Plot Time of Arrival (TOA) distributions for different THL ranges
    """
    print("Generating TOA distribution plots...")
    
    thl_values = np.arange(data['thl_start'], data['thl_end'] + 1, data['thl_step'])
    
    # Split THL range into three regions for comparison
    low_idx = len(thl_values) // 3
    high_idx = 2 * len(thl_values) // 3
    
    low_range = thl_values[:low_idx]
    mid_range = thl_values[low_idx:high_idx]
    high_range = thl_values[high_idx:]
    
    plt.figure(figsize=(15, 5))
    
    # For each region, plot TOA distribution
    regions = [('Low THL', low_range, 'blue'), 
               ('Mid THL', mid_range, 'green'),
               ('High THL', high_range, 'red')]
    
    for i, (label, thl_range, color) in enumerate(regions):
        # Filter hits for this THL range
        toa_values = []
        for hit in data['pixel_hits']:
            if hit['thl'] in thl_range:
                toa_values.append(hit['toa'] % 1000)  # Modulo to see structure in timing
        
        if toa_values:
            plt.subplot(1, 3, i+1)
            plt.hist(toa_values, bins=50, color=color, alpha=0.7)
            plt.title(f'{label} ({min(thl_range)}-{max(thl_range)})')
            plt.xlabel('TOA Value (mod 1000)')
            plt.ylabel('Count')
            plt.yscale('log')
            plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return plt.gcf()

def plot_per_pixel_threshold(data):
    """
    Create a per-pixel threshold map
    """
    print("Generating per-pixel threshold map...")
    
    # Initialize threshold map
    threshold_map = np.zeros((256, 256))
    counts_map = np.zeros((256, 256))
    
    # Identify threshold for each pixel (THL value where hits drop significantly)
    thl_values = np.arange(data['thl_start'], data['thl_end'] + 1, data['thl_step'])
    pixel_thl_hits = {}
    
    # Count hits per pixel per THL
    for hit in data['pixel_hits']:
        x, y, thl = hit['x'], hit['y'], hit['thl']
        if 0 <= x < 256 and 0 <= y < 256:
            key = (x, y, thl)
            if key not in pixel_thl_hits:
                pixel_thl_hits[key] = 0
            pixel_thl_hits[key] += 1
    
    # For each pixel, find the threshold point
    for x in range(256):
        for y in range(256):
            hits_by_thl = []
            for thl in thl_values:
                hits = pixel_thl_hits.get((x, y, thl), 0)
                hits_by_thl.append(hits)
            
            if sum(hits_by_thl) > 10:  # Only consider pixels with enough hits
                hits_by_thl = np.array(hits_by_thl)
                # Find the steepest drop in hits
                if len(hits_by_thl) > 5:
                    diffs = np.diff(hits_by_thl)
                    if np.min(diffs) < 0:  # Ensure there's a negative transition
                        idx = np.argmin(diffs)
                        threshold_map[y, x] = thl_values[idx]
                        counts_map[y, x] = sum(hits_by_thl)
    
    # Plot
    plt.figure(figsize=(10, 8))
    mask = counts_map > 0
    plt.imshow(np.ma.masked_array(threshold_map, ~mask), cmap='plasma')
    plt.colorbar(label='Threshold Value')
    plt.xlabel('X Pixel')
    plt.ylabel('Y Pixel')
    plt.title('Per-Pixel Threshold Map')
    plt.tight_layout()
    return plt.gcf()

def analyze_noisy_pixels(data):
    """
    Identify and analyze noisy pixels
    """
    print("Analyzing noisy pixels...")
    
    # Count hits per pixel
    pixel_hits = {}
    for hit in data['pixel_hits']:
        x, y = hit['x'], hit['y']
        if 0 <= x < 256 and 0 <= y < 256:
            key = (x, y)
            if key not in pixel_hits:
                pixel_hits[key] = 0
            pixel_hits[key] += 1
    
    # Convert to array
    hit_counts = []
    for key, count in pixel_hits.items():
        hit_counts.append((key[0], key[1], count))
    
    # Sort by hit count
    hit_counts.sort(key=lambda x: x[2], reverse=True)
    
    # Create hit count map for visualization
    hit_map = np.zeros((256, 256))
    for x, y, count in hit_counts:
        hit_map[y, x] = count
    
    # Plot noisy pixel distribution
    plt.figure(figsize=(15, 5))
    
    # Plot 1: Hit count map
    plt.subplot(1, 3, 1)
    plt.imshow(hit_map, norm=LogNorm(vmin=1), cmap='hot')
    plt.colorbar(label='Hit Count')
    plt.title('Pixel Hit Map')
    plt.xlabel('X Pixel')
    plt.ylabel('Y Pixel')
    
    # Plot 2: Top noisy pixels
    plt.subplot(1, 3, 2)
    if hit_counts:
        top_n = min(20, len(hit_counts))
        x = np.arange(top_n)
        heights = [count for _, _, count in hit_counts[:top_n]]
        plt.bar(x, heights, color='orange')
        plt.title(f'Top {top_n} Noisy Pixels')
        plt.xlabel('Pixel Rank')
        plt.ylabel('Hit Count')
        plt.yscale('log')
        plt.grid(True, axis='y', alpha=0.3)
    
    # Plot 3: Histogram of hit counts
    plt.subplot(1, 3, 3)
    if hit_counts:
        counts = [count for _, _, count in hit_counts]
        plt.hist(counts, bins=50, color='green', alpha=0.7)
        plt.title('Hit Count Distribution')
        plt.xlabel('Hit Count')
        plt.ylabel('Number of Pixels')
        plt.yscale('log')
        plt.xscale('log')
        plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return plt.gcf()

def create_dashboard(data, output_dir):
    """
    Create comprehensive dashboard with all plots
    """
    print("Creating comprehensive dashboard...")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Setup the figure
    fig = plt.figure(figsize=(18, 12))
    gs = gridspec.GridSpec(3, 3, figure=fig)
    
    # Plot THL S-curve
    ax1 = fig.add_subplot(gs[0, :2])
    
    # Extract unique THL values
    thl_values = np.arange(data['thl_start'], data['thl_end'] + 1, data['thl_step'])
    
    # Count hits for each THL value
    hits_per_thl = {}
    for hit in data['pixel_hits']:
        thl = hit['thl']
        if thl not in hits_per_thl:
            hits_per_thl[thl] = 0
        hits_per_thl[thl] += 1
    
    # Convert to arrays for plotting
    x = []
    y = []
    for thl in sorted(hits_per_thl.keys()):
        x.append(thl)
        y.append(hits_per_thl[thl] / data['frames_per_thl'])
    
    ax1.plot(x, y, '-o', markersize=4)
    ax1.set_yscale('log')
    ax1.grid(True, which='both', linestyle='--', alpha=0.7)
    ax1.set_xlabel('THL Value')
    ax1.set_ylabel('Average Hits per Frame (log scale)')
    ax1.set_title('THL S-Curve: Hit Rate vs Threshold')
    ax1.yaxis.set_major_formatter(FuncFormatter(format_with_suffix))
    
    # Find the threshold point (steepest part of the curve)
    if len(x) > 5:
        x_array = np.array(x)
        y_array = np.array(y)
        dy_dx = np.diff(y_array) / np.diff(x_array)
        steepest_idx = np.argmin(dy_dx)
        threshold_point = x_array[steepest_idx]
        ax1.axvline(x=threshold_point, color='r', linestyle='--', 
                   label=f'Threshold: {threshold_point}')
        ax1.legend()
    
    # Plot hit map
    ax2 = fig.add_subplot(gs[0, 2])
    hit_map = np.zeros((256, 256))
    for hit in data['pixel_hits']:
        x, y = hit['x'], hit['y']
        if 0 <= x < 256 and 0 <= y < 256:
            hit_map[y, x] += 1
    
    im = ax2.imshow(hit_map, cmap='viridis', norm=LogNorm(vmin=1))
    plt.colorbar(im, ax=ax2, label='Hit Count')
    ax2.set_title('Detector Hit Map')
    
    # Plot TOT distributions
    ax3 = fig.add_subplot(gs[1, :])
    
    # Split THL range into regions
    low_idx = len(thl_values) // 3
    high_idx = 2 * len(thl_values) // 3
    
    low_range = thl_values[:low_idx]
    mid_range = thl_values[low_idx:high_idx]
    high_range = thl_values[high_idx:]
    
    regions = [('Low THL', low_range, 'blue'), 
               ('Mid THL', mid_range, 'green'),
               ('High THL', high_range, 'red')]
    
    # Plot overlaid TOT distributions
    for label, thl_range, color in regions:
        tot_values = []
        for hit in data['pixel_hits']:
            if hit['thl'] in thl_range:
                tot_values.append(hit['tot'])
        
        if tot_values:
            ax3.hist(tot_values, bins=50, color=color, alpha=0.5, 
                    label=f'{label} ({min(thl_range)}-{max(thl_range)})')
    
    ax3.set_title('TOT Distributions by THL Range')
    ax3.set_xlabel('TOT Value')
    ax3.set_ylabel('Count')
    ax3.set_yscale('log')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # Plot per-pixel threshold
    ax4 = fig.add_subplot(gs[2, :2])
    threshold_map = np.zeros((256, 256))
    counts_map = np.zeros((256, 256))
    
    # Calculate per-pixel threshold
    pixel_thl_hits = {}
    for hit in data['pixel_hits']:
        x, y, thl = hit['x'], hit['y'], hit['thl']
        if 0 <= x < 256 and 0 <= y < 256:
            key = (x, y, thl)
            if key not in pixel_thl_hits:
                pixel_thl_hits[key] = 0
            pixel_thl_hits[key] += 1
    
    for x in range(256):
        for y in range(256):
            hits_by_thl = []
            for thl in thl_values:
                hits = pixel_thl_hits.get((x, y, thl), 0)
                hits_by_thl.append(hits)
            
            if sum(hits_by_thl) > 10:
                hits_by_thl = np.array(hits_by_thl)
                if len(hits_by_thl) > 5:
                    diffs = np.diff(hits_by_thl)
                    if np.min(diffs) < 0:
                        idx = np.argmin(diffs)
                        threshold_map[y, x] = thl_values[idx]
                        counts_map[y, x] = sum(hits_by_thl)
    
    mask = counts_map > 0
    im = ax4.imshow(np.ma.masked_array(threshold_map, ~mask), cmap='plasma')
    plt.colorbar(im, ax=ax4, label='Threshold Value')
    ax4.set_title('Per-Pixel Threshold Map')
    
    # Plot noise analysis
    ax5 = fig.add_subplot(gs[2, 2])
    pixel_hits = {}
    for hit in data['pixel_hits']:
        x, y = hit['x'], hit['y']
        key = (x, y)
        if key not in pixel_hits:
            pixel_hits[key] = 0
        pixel_hits[key] += 1
    
    if pixel_hits:
        counts = list(pixel_hits.values())
        ax5.hist(counts, bins=50, color='green', alpha=0.7)
        ax5.set_title('Hit Count Distribution')
        ax5.set_xlabel('Hit Count')
        ax5.set_ylabel('Number of Pixels')
        ax5.set_yscale('log')
        ax5.set_xscale('log')
        ax5.grid(True, alpha=0.3)
    
    # Adjust layout and save
    plt.tight_layout()
    dashboard_path = os.path.join(output_dir, 'thl_dashboard.png')
    plt.savefig(dashboard_path, dpi=150)
    print(f"Dashboard saved to {dashboard_path}")
    
    return fig

def main():
    parser = argparse.ArgumentParser(description='Visualize Timepix3 THL calibration data')
    parser.add_argument('filename', help='HDF5 file from THL calibration')
    parser.add_argument('--output', '-o', default='output', help='Output directory for plots')
    args = parser.parse_args()
    
    # Load data
    data = load_thl_data(args.filename)
    
    # Create output directory
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # Create individual plots
    s_curve_fig = plot_thl_scan_curve(data)
    s_curve_fig.savefig(os.path.join(args.output, 'thl_s_curve.png'), dpi=150)
    
    hit_map_fig = plot_hit_map(data)
    hit_map_fig.savefig(os.path.join(args.output, 'hit_map.png'), dpi=150)
    
    tot_fig = plot_thl_distributions(data)
    tot_fig.savefig(os.path.join(args.output, 'tot_distributions.png'), dpi=150)
    
    toa_fig = plot_toa_distributions(data)
    toa_fig.savefig(os.path.join(args.output, 'toa_distributions.png'), dpi=150)
    
    threshold_fig = plot_per_pixel_threshold(data)
    threshold_fig.savefig(os.path.join(args.output, 'pixel_threshold_map.png'), dpi=150)
    
    noisy_fig = analyze_noisy_pixels(data)
    noisy_fig.savefig(os.path.join(args.output, 'noisy_pixel_analysis.png'), dpi=150)
    
    # Create comprehensive dashboard
    dashboard_fig = create_dashboard(data, args.output)
    
    print(f"All plots saved to {args.output} directory")
    
    # Show plots if running interactively
    plt.show()

if __name__ == "__main__":
    main()