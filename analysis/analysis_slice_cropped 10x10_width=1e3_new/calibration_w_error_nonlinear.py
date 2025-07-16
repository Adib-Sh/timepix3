import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.optimize import curve_fit

# Load the data
df = pd.read_csv('analysis.csv')
df['energy'] = df['energy'].str.replace(',', '.').str.replace('keV', '').astype(float)
df['data_category'] = df['data_type'].str.extract(r'\((.*?)\)')[0]

# Plot settings
sns.set(style="whitegrid")
plt.figure(figsize=(18, 16))
plt.suptitle("Energy Dependence of Pixel Response Characteristics with Nonlinear Fits and Error Bars", 
             y=0.99, fontsize=14, fontweight='bold')

# --- Choose your model ---
def nonlinear_model(E, a, b, c):
    return a * E**b + c

# Optional: Linear with fixed slope
def fixed_slope_model(E, offset, fixed_slope=0.8):
    return fixed_slope * E + offset

# Fit and plot function
def fit_and_plot(ax, x, y, yerr, color, label, use_fixed_slope=False):
    if use_fixed_slope:
        # Fit only the offset (slope fixed)
        def model_fixed(E, offset):
            return fixed_slope_model(E, offset, fixed_slope=1)
        popt, _ = curve_fit(model_fixed, x, y, sigma=yerr, absolute_sigma=True)
        fit_y = model_fixed(x, *popt)
        fit_label = f"{label} fit: y=0.50x+{popt[0]:.2f} (slope fixed)"
    else:
        # General nonlinear model
        popt, _ = curve_fit(nonlinear_model, x, y, sigma=yerr, absolute_sigma=True, maxfev=5000)
        fit_y = nonlinear_model(x, *popt)
        fit_label = f"{label} fit: y={popt[0]:.2f}x^{popt[1]:.2f}+{popt[2]:.2f}"
    
    ax.plot(x, fit_y, '--', color=color, label=fit_label)

# Errorbar plot function
def plot_with_errors(ax, x, y, yerr, category, color):
    ax.errorbar(x, y, yerr=yerr, fmt='o', color=color, capsize=5, label=f'{category} ± error')

# Plot features
features = [
    ('mean', 'Mean Value'),
    ('median', 'Median Value'),
    ('fwhm_midpoint', 'FWHM Midpoint'),
    ('mode', 'Mode Value')
]

for i, (feature, ylabel) in enumerate(features, 1):
    plt.subplot(2, 2, i)
    ax = plt.gca()
    for category in df['data_category'].unique():
        subset = df[df['data_category'] == category]
        color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
        x = subset['energy'].values
        y = subset[feature].values
        yerr = subset['error'].values
        plot_with_errors(ax, x, y, yerr, category, color)
        # Toggle `use_fixed_slope=True` to fix slope to 0.5 (example)
        fit_and_plot(ax, x, y, yerr, color, category, use_fixed_slope=False)
    
    ax.set_title(f'{ylabel} by Energy Level')
    ax.set_xlabel('Energy (keV)')
    ax.set_ylabel(ylabel)
    ax.legend()

plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig('Calibration_non_linear_fit.png', dpi=150, bbox_inches='tight')
plt.show()
