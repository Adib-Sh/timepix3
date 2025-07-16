import h5py
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit


input_dir ="/home/adisha/git/libkatherine/build/BeamData 20250608 NanoMAX"


# --- Load and process HDF5 file containing structured PixelHit data ---
def load_threshold_scan(filename):
    with h5py.File(filename, 'r') as f:
        dataset_key = list(f.keys())[0]
        print("Reading dataset:", dataset_key)

        data = f[dataset_key][:]
        #thls = data['thl']
        #hit_counts = data['hit_count']
        
        # Filter to keep thl values from 0 to 800 inclusive
        mask = (data['thl'][:] >= 700) & (data['thl'][:] <= 800)
        thls_filtered = data['thl'][mask]
        hit_counts_filtered = data['hit_count'][mask]
        print ('Data Loaded!')
    return thls_filtered, hit_counts_filtered


def sigmoid(thl, A, k, thl0):
    """
    Sigmoid function for hit count vs threshold level.

    H(THL) = A / (1 + exp(-k * (THL - thl0)))
    """
    return A / (1 + np.exp(-k * (thl - thl0)))

def fit_hitcount_sigmoid(thl_data, hit_counts, plot_fit=True):
    """
    Fit sigmoid to hit count vs THL data.

    Parameters:
    - thl_data: 1D array of threshold levels
    - hit_counts: 1D array of hit counts corresponding to THL
    - plot_fit: bool, whether to plot the data and the fit

    Returns:
    - popt: optimized parameters [A, k, thl0]
    - pcov: covariance matrix of parameters
    """
    # Initial guess for parameters: A=max hits, k=1, thl0=median THL
    p0 = [np.max(hit_counts), 1, np.median(thl_data)]
    
    # Fit the sigmoid curve
    popt, pcov = curve_fit(sigmoid, thl_data, hit_counts, p0=p0, maxfev=10000)
    A, k, thl0 = popt
    
    if plot_fit:
        plt.figure(figsize=(8, 5))
        plt.scatter(thl_data, hit_counts, label='Data', color='blue')
        thl_fit = np.linspace(min(thl_data), max(thl_data), 200)
        hit_fit = sigmoid(thl_fit, *popt)
        plt.plot(thl_fit, hit_fit, label=f'Sigmoid Fit\nA={A:.1f}, k={k:.3f}, THL0={thl0:.2f}', color='red')
        plt.xlabel('Threshold Level (THL)')
        plt.ylabel('Hit Count')
        plt.title('Sigmoid Fit to Hit Count vs THL')
        plt.legend()
        plt.grid(True)
        plt.show()
    
    return popt, pcov


# --- Main ---
if __name__ == "__main__":
    filename = input_dir +"/thlscan_datadriven_20250608_115511.h5"
    thls, hit_counts = load_threshold_scan(filename)
    params, cov = fit_hitcount_sigmoid(thls, hit_counts, plot_fit=True)
    A, k, thl0 = params
    print(f"Fitted parameters:\nA = {A:.2f}\nk (slope) = {k:.4f}\nTHL0 (inflection) = {thl0:.2f}")
