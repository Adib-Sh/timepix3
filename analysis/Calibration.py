import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats

# Read the CSV file into a pandas DataFrame
df = pd.read_csv('analysis_1_test.csv')

# Clean up the energy column (handle "7,5keV" format)
df['energy'] = df['energy'].str.replace(',', '.').str.replace('keV', '').astype(float)

# Create a column for the data type (Isolated Hits, Cropped Pixels, All Pixels)
df['data_category'] = df['data_type'].str.extract(r'\((.*?)\)')[0]

# Set up the plotting style
sns.set(style="whitegrid")
plt.figure(figsize=(12, 16))  # Slightly taller figure to accommodate title

# Add main title for the whole figure
plt.suptitle("Energy Dependence of Pixel Response Characteristics with Linear Fits", 
             y=1.02, fontsize=14, fontweight='bold')

# Function to add linear fit to a plot
def add_linear_fit(ax, x, y, color, label):
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    line = slope * x + intercept
    ax.plot(x, line, '--', color=color, alpha=0.5, 
            label=f'{label} fit: y={slope:.2f}x+{intercept:.2f}\n(R²={r_value**2:.2f})')

# Plot 1: Mean values by energy for each data category
plt.subplot(3, 2, 1)
ax1 = sns.lineplot(data=df, x='energy', y='mean', hue='data_category', marker='o', legend=False)
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    add_linear_fit(ax1, subset['energy'], subset['mean'], 
                  sns.color_palette()[list(df['data_category'].unique()).index(category)], 
                  category)
plt.title('Mean Values by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('Mean Value')
plt.legend()

# Plot 2: Median values by energy for each data category
plt.subplot(3, 2, 2)
ax2 = sns.lineplot(data=df, x='energy', y='median', hue='data_category', marker='o', legend=False)
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    add_linear_fit(ax2, subset['energy'], subset['median'], 
                  sns.color_palette()[list(df['data_category'].unique()).index(category)], 
                  category)
plt.title('Median Values by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('Median Value')
plt.legend()

# Plot 3: FWHM Midpoint by energy for each data category
plt.subplot(3, 2, 3)
ax3 = sns.lineplot(data=df, x='energy', y='fwhm_midpoint', hue='data_category', marker='o', legend=False)
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    add_linear_fit(ax3, subset['energy'], subset['fwhm_midpoint'], 
                  sns.color_palette()[list(df['data_category'].unique()).index(category)], 
                  category)
plt.title('FWHM Midpoint by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('FWHM Midpoint')
plt.legend()

# Plot 4: Mode values by energy for each data category
plt.subplot(3, 2, 4)
ax4 = sns.lineplot(data=df, x='energy', y='mode', hue='data_category', marker='o', legend=False)
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    add_linear_fit(ax4, subset['energy'], subset['mode'], 
                  sns.color_palette()[list(df['data_category'].unique()).index(category)], 
                  category)
plt.title('Mode Values by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('Mode Value')
plt.legend()

# Plot 5: FWHM by energy for each data category
plt.subplot(3, 2, 5)
ax4 = sns.lineplot(data=df, x='energy', y='fwhm', hue='data_category', marker='o', legend=False)
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    add_linear_fit(ax4, subset['energy'], subset['fwhm'], 
                  sns.color_palette()[list(df['data_category'].unique()).index(category)], 
                  category)
plt.title('FWHM by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('FWHM')
plt.legend()

# Plot 5: ToT Value at Peak by energy for each data category
plt.subplot(3, 2, 6)
ax4 = sns.lineplot(data=df, x='energy', y='tot_at_peak', hue='data_category', marker='o', legend=False)
for category in df['data_category'].unique():
    subset = df[df['data_category'] == category]
    add_linear_fit(ax4, subset['energy'], subset['tot_at_peak'], 
                  sns.color_palette()[list(df['data_category'].unique()).index(category)], 
                  category)
plt.title('ToT Value at Peak by Energy Level')
plt.xlabel('Energy (keV)')
plt.ylabel('ToT Value at Peak')
plt.legend()

plt.savefig('Calibration_test', dpi=150, bbox_inches='tight')
plt.tight_layout()
plt.show()