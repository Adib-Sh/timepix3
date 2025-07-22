import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats

# Read the CSV file into a pandas DataFrame
df = pd.read_csv('analysis_cut16.csv')

# Clean up the energy column (handle "7,5keV" format)
df['energy'] = df['energy'].str.replace(',', '.').str.replace('keV', '').astype(float)

# Create a column for the data type (Isolated Hits, Cropped Pixels, All Pixels)
df['data_category'] = df['data_type'].str.extract(r'\((.*?)\)')
df['data_category'] = df['data_category'].fillna(df['data_type'])

# Set up the plotting style

plt.style.use('default')
sns.set(
    style="white",
    context="talk",
    palette="deep"
)
plt.figure(figsize=(20, 14))
plt.suptitle("Energy Dependence of Pixel Response Characteristics", 
             fontsize=20, fontweight='bold', y=1.0)

# Function to add linear fit to a plot
def add_linear_fit(ax, x, y, color, label):
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    line = slope * x + intercept
    ax.plot(x, line, '--', color=color, alpha=0.5, 
            label=f'{label} fit: y={slope:.2f}x+{intercept:.2f}\n(R²={r_value**2:.2f})')

# Function to plot with error bars
def plot_with_errors(ax, x, y, errors, category, color):
    ax.errorbar(x, y, yerr=errors, fmt='o', color=color, 
                capsize=5, capthick=2, elinewidth=2, 
                label=f'{category} ± error')

# Plot 1: Mean values by energy for each data category
plt.subplot(2, 2, 1)
ax1 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax1, subset['energy'], subset['mean'], subset['mean_err'], category, color)
    add_linear_fit(ax1, subset['energy'], subset['mean'], color, category)
ax1.set_title('Mean Values by Energy Level', fontsize=16, fontweight='bold')
ax1.set_xlabel("Energy (keV)", fontsize=14)
ax1.set_ylabel('Mean Value (ToT Clock Cycle)', fontsize=14)
ax1.tick_params(labelsize=12)
ax1.grid(True)
ax1.legend(fontsize=10)

# Plot 2: Median values by energy for each data category
plt.subplot(2, 2, 2)
ax2 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax2, subset['energy'], subset['median'], subset['median_err'], category, color)
    add_linear_fit(ax2, subset['energy'], subset['median'], color, category)
ax2.set_title('Median Values by Energy Level', fontsize=16, fontweight='bold')
ax2.set_xlabel("Energy (keV)", fontsize=14)
ax2.set_ylabel('Median Value (ToT Clock Cycle)', fontsize=14)
ax2.tick_params(labelsize=12)
ax2.grid(True)
ax2.legend(fontsize=10)

# Plot 3: Mode values by energy for each data category
plt.subplot(2, 2, 3)
ax3 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax3, subset['energy'], subset['mode'], subset['mode_err'], category, color)
    add_linear_fit(ax3, subset['energy'], subset['mode'], color, category)
ax3.set_title('Mode Values by Energy Level', fontsize=16, fontweight='bold')
ax3.set_xlabel("Energy (keV)", fontsize=14)
ax3.set_ylabel('Mode Value (ToT Clock Cycle)', fontsize=14)
ax3.tick_params(labelsize=12)
ax3.grid(True)
ax3.legend(fontsize=10)

'''
# Plot 4: ToT Value at Peak (fit) by energy for each data category
plt.subplot(2, 2, 4)
ax6 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax6, subset['energy'], subset['peak_tot_fit'], 0, category, color)
    add_linear_fit(ax6, subset['energy'], subset['peak_tot_fit'], color, category)
plt.title('ToT Value at Peak (fit) by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('ToT Value at Peak')
plt.legend()

# Plot 5: ToT Value at Peak (histogram) by energy for each data category
plt.subplot(2, 2, 5)
ax6 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax6, subset['energy'], subset['peak_tot_count'], 0, category, color)
    add_linear_fit(ax6, subset['energy'], subset['peak_tot_count'], color, category)
plt.title('ToT Value at Peak (Max Count) by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('ToT Value at Peak')
plt.legend()
'''
# Plot 6: FWHM by energy for each data category
plt.subplot(2, 2, 4)
ax6 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax6, subset['energy'], subset['fwhm'], subset['fwhm_err'], category, color)
    add_linear_fit(ax6, subset['energy'], subset['fwhm'], color, category)
ax6.set_title('FWHM by Energy Level', fontsize=16, fontweight='bold')
ax6.set_xlabel("Energy (keV)", fontsize=14)
ax6.set_ylabel('FWHM', fontsize=14)
ax6.tick_params(labelsize=12)
ax6.grid(True)
ax6.legend(fontsize=10)
plt.tight_layout()
fig = plt.gcf()

fig.savefig('Calibration_test_with_errors_cut16_4plots.png', dpi=300)

plt.show()

fig, ax7 = plt.subplots(figsize=(20, 12))
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax7, subset['energy'], subset['mode'], subset['mode_err'], category, color)
    add_linear_fit(ax7, subset['energy'], subset['mode'], color, category)
ax7.set_title('Mode Values by Energy Level', fontsize=20, fontweight='bold')
ax7.set_xlabel("Energy (keV)", fontsize=16, fontweight='bold')
ax7.set_ylabel('Mode Value (ToT Clock Cycle)', fontsize=16, fontweight='bold')
ax7.tick_params(labelsize=14)
ax7.grid(True)
ax7.legend(fontsize=12)
plt.tight_layout()
fig.savefig("Mode_vs_Energy_presentation_cut16.png", dpi=300, bbox_inches='tight')
plt.show()


summary_table = df.copy()
summary_table = summary_table[[
    'energy', 'data_category',
    'mean', 'mean_err',
    'median', 'median_err',
    'mode', 'mode_err',
    'fwhm', 'fwhm_err',
    'peak_tot_count',
    'peak_tot_fit'
]].round(3)

# Sort by energy and data type
summary_table = summary_table.sort_values(by=['energy', 'data_category'])

# Print table to terminal
print("\n=== Summary of Fit Results ===\n")
print(summary_table.to_string(index=False))