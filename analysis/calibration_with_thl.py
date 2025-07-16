import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# --- Load CSV ---
csv_path = "analysis_1.csv"
df = pd.read_csv(csv_path)

# --- Preprocess ---
df["energy_keV"] = df["energy"].str.replace("keV", "").astype(float)
filtered_df = df[df["data_type"].str.contains("Isolated Hits")].copy()

# Extract values
energies = filtered_df["energy_keV"].values
tot_values = filtered_df["median"].values
fwhm_values = filtered_df["fwhm"].values

# --- Filter: keep E > 8 keV only ---
threshold_energy = 6.0
mask = energies > threshold_energy
energies_valid = energies[mask]
tot_values_valid = tot_values[mask]
tot_errors = fwhm_values[mask] / 2.355  # Approx. std dev from FWHM

# --- Fit Model: ToT = a * (E - E_th)^b ---
def tot_model(E, a, b):
    return a * (E - threshold_energy)**b

popt, _ = curve_fit(tot_model, energies_valid, tot_values_valid, p0=[1, 1])
a, b = popt

# --- Plot ---
E_fit = np.linspace(min(energies_valid), max(energies_valid), 300)
ToT_fit = tot_model(E_fit, *popt)

plt.figure(figsize=(8, 5))
plt.errorbar(
    energies_valid,
    tot_values_valid,
    yerr=tot_errors,
    fmt='o',
    capsize=4,
    label='ToT data with error (FWHM/2.355)'
)
plt.plot(E_fit, ToT_fit, '-', label=f'Fit: ToT = {a:.2f}·(E − {threshold_energy})^{b:.2f}')
plt.xlabel("Energy (keV)")
plt.ylabel("ToT (at peak)")
plt.title("ToT vs Energy Calibration (with FWHM-based Error Bars)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("tot_energy_calibration_with_errorbars.png", dpi=300)
plt.show()

# Print result
print(f"Calibration Fit: ToT = {a:.3f} · (E − {threshold_energy})^{b:.3f}")
print("Plot saved as: tot_energy_calibration_with_errorbars.png")
