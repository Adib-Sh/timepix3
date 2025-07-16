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
plt.subplot(4, 2, 1)
ax1 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax1, subset['energy'], subset['mean'], subset['error'], category, color)
    add_linear_fit(ax1, subset['energy'], subset['mean'], color, category)
plt.title('Mean Values by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('Mean Value')
plt.legend()

# Plot 2: Median values by energy for each data category
plt.subplot(4, 2, 2)
ax2 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax2, subset['energy'], subset['median'], subset['error'], category, color)
    add_linear_fit(ax2, subset['energy'], subset['median'], color, category)
plt.title('Median Values by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('Median Value')
plt.legend()

# Plot 3: FWHM Midpoint by energy for each data category
plt.subplot(4, 2, 3)
ax3 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax3, subset['energy'], subset['fwhm_midpoint'], subset['error'], category, color)
    add_linear_fit(ax3, subset['energy'], subset['fwhm_midpoint'], color, category)
plt.title('FWHM Midpoint by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('FWHM Midpoint')
plt.legend()

# Plot 4: Mode values by energy for each data category
plt.subplot(4, 2, 4)
ax4 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax4, subset['energy'], subset['mode'], subset['error'], category, color)
    add_linear_fit(ax4, subset['energy'], subset['mode'], color, category)
plt.title('Mode Values by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('Mode Value')
plt.legend()


# Plot 5: ToT Value at Peak (fit) by energy for each data category
plt.subplot(4, 2, 5)
ax6 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax6, subset['energy'], subset['peak_tot(fit)'], subset['error'], category, color)
    add_linear_fit(ax6, subset['energy'], subset['peak_tot(fit)'], color, category)
plt.title('ToT Value at Peak (fit) by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('ToT Value at Peak')
plt.legend()

# Plot 6: ToT Value at Peak (histogram) by energy for each data category
plt.subplot(4, 2, 6)
ax6 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax6, subset['energy'], subset['peak_tot(histogram)'], subset['error'], category, color)
    add_linear_fit(ax6, subset['energy'], subset['peak_tot(histogram)'], color, category)
plt.title('ToT Value at Peak (Max Count) by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('ToT Value at Peak')
plt.legend()

# Plot 7: FWHM by energy for each data category
plt.subplot(4, 2, 7)
ax5 = plt.gca()
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    color = sns.color_palette()[list(df['data_category'].unique()).index(category)]
    plot_with_errors(ax5, subset['energy'], subset['fwhm'], subset['error'], category, color)
    add_linear_fit(ax5, subset['energy'], subset['fwhm'], color, category)
plt.title('FWHM by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('FWHM')
plt.legend()
plt.tight_layout()
fig = plt.gcf()

fig.savefig('Calibration_test_with_errors.png', dpi=300)

plt.show()