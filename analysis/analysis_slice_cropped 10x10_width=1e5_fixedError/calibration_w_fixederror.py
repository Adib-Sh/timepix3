import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats

# Read the CSV file into a pandas DataFrame
df = pd.read_csv('analysis.csv')

# Clean up the energy column (handle "7,5keV" format)
df['energy'] = df['energy'].str.replace(',', '.').str.replace('keV', '').astype(float)

# Create a column for the data type (Isolated Hits, Cropped Pixels, All Pixels)
df['data_category'] = df['data_type'].str.extract(r'\((.*?)\)')
df['data_category'] = df['data_category'].fillna(df['data_type'])

# Set up the plotting style

plt.style.use('default')
sns.set(style="whitegrid")
plt.figure(figsize=(18, 22))  # Increased figure size for better visibility

# Add main title for the whole figure
plt.suptitle("Energy Dependence of Pixel Response Characteristics with Linear Fits and Error Bars", 
             y=1, fontsize=14, fontweight='bold')

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
plt.subplot(3, 2, 1)
ax1 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax1, subset['energy'], subset['mean'], subset['mean_err'], category, color)
    add_linear_fit(ax1, subset['energy'], subset['mean'], color, category)
plt.title('Mean Values by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('Mean Value')
plt.legend()

# Plot 2: Median values by energy for each data category
plt.subplot(3, 2, 2)
ax2 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax2, subset['energy'], subset['median'], subset['median_err'], category, color)
    add_linear_fit(ax2, subset['energy'], subset['median'], color, category)
plt.title('Median Values by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('Median Value')
plt.legend()


# Plot 3: Mode values by energy for each data category
plt.subplot(3, 2, 3)
ax4 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax4, subset['energy'], subset['mode'], subset['mode_err'], category, color)
    add_linear_fit(ax4, subset['energy'], subset['mode'], color, category)
plt.title('Mode Values by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('Mode Value')
plt.legend()


# Plot 4: ToT Value at Peak (fit) by energy for each data category
plt.subplot(3, 2, 4)
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
plt.subplot(3, 2, 5)
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

# Plot 6: FWHM by energy for each data category
plt.subplot(3, 2, 6)
ax5 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax5, subset['energy'], subset['fwhm'], subset['fwhm_err'], category, color)
    add_linear_fit(ax5, subset['energy'], subset['fwhm'], color, category)
plt.title('FWHM by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('FWHM')
plt.legend()
plt.tight_layout()
fig = plt.gcf()

fig.savefig('Calibration_test_with_errors.png', dpi=300)

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