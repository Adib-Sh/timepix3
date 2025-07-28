import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats

# Read the CSV file into a pandas DataFrame
df = pd.read_csv('analysis.csv')
# Extract numeric energy in keV
df['energy_keV'] = df['energy'].str.replace('keV', '').astype(float)

# Group by energy and data_type, then compute mean and std of fwhm and its error
grouped = df.groupby(['energy_keV', 'data_type']).agg({
    'fwhm': 'mean',
    'fwhm_err': 'mean'
}).reset_index()

plt.style.use('default')
sns.set(
    style="white",
    context="talk",
    palette="deep"
)
plt.figure(figsize=(10, 6))

for data_type in grouped['data_type'].unique():
    subset = grouped[grouped['data_type'] == data_type]
    plt.errorbar(subset['energy_keV'], subset['fwhm'], yerr=subset['fwhm_err'],
                 fmt='o-', capsize=4, label=data_type)

plt.xlabel("Energy (keV)")
plt.ylabel("Resolution (FWHM)")
plt.title("Resolution vs Energy for Different Data Types")
plt.legend(title="Data Type")
plt.tight_layout()
plt.grid(True)
plt.show()



# Compute resolution using 'mode' as the peak position instead of 'peak_tot_fit'
df['resolution'] = (df['fwhm'] / df['mode']) * 100

# Propagate uncertainty using mode and its error
rel_fwhm_err = df['fwhm_err'] / df['fwhm']
rel_mode_err = df['mode_err'] / df['mode']
df['resolution_err'] = df['resolution'] * np.sqrt(rel_fwhm_err**2 + rel_mode_err**2)

# Group by energy and data_type
resolution_mode_grouped = df.groupby(['energy_keV', 'data_type']).agg({
    'resolution': 'mean',
    'resolution_err': 'mean'
}).reset_index()

# Plot
plt.figure(figsize=(10, 6))
for dtype in resolution_mode_grouped['data_type'].unique():
    sub = resolution_mode_grouped[resolution_mode_grouped['data_type'] == dtype]
    plt.errorbar(sub['energy_keV'], sub['resolution'], yerr=sub['resolution_err'],
                 fmt='o-', capsize=4, label=dtype)

plt.xlabel("Energy (keV)")
plt.ylabel("Energy Resolution using Mode (%)")
plt.title("Energy Resolution (FWHM / Mode) vs Energy")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("Resolution_vs_Energy.png", dpi=300, bbox_inches='tight')
plt.show()



# Compute resolution using 'mode' as the peak position instead of 'peak_tot_fit'
df['resolution'] = (2.35 / np.sqrt(df['peak_tot_count'])) * 100

# Propagate uncertainty using mode and its error
rel_fwhm_err = df['fwhm_err'] / df['fwhm']
rel_mode_err = df['mode_err'] / df['mode']
df['resolution_err'] = df['resolution'] * np.sqrt(rel_fwhm_err**2 + rel_mode_err**2)

# Group by energy and data_type
resolution_mode_grouped = df.groupby(['energy_keV', 'data_type']).agg({
    'resolution': 'mean',
    'resolution_err': 'mean'
}).reset_index()

# Plot
plt.figure(figsize=(10, 6))
for dtype in resolution_mode_grouped['data_type'].unique():
    sub = resolution_mode_grouped[resolution_mode_grouped['data_type'] == dtype]
    plt.errorbar(sub['energy_keV'], sub['resolution'], yerr=sub['resolution_err'],
                 fmt='o-', capsize=4, label=dtype)

plt.xlabel("Energy (keV)")
plt.ylabel("Energy Resolution using Mode (%)")
plt.title("Energy Resolution (FWHM / Mode) vs Energy using count")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("Resolution_vs_Energy_count.png", dpi=300, bbox_inches='tight')
plt.show()