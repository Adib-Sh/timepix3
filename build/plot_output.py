import numpy as np
import matplotlib.pyplot as plt

data = np.loadtxt('output.txt', skiprows=1)

# Extract columns
x = data[:, 0]  # X column
y = data[:, 1]  # Y column
toa = data[:, 2]  # ToA column
ftoa = data[:, 3]  # fToA column
tot = data[:, 4]  # TOT column

# Plot 2D hitmap
plt.hist2d(x, y, bins=[256, 256], cmap='viridis')
plt.colorbar(label='Number of hits')
plt.xlabel('X')
plt.ylabel('Y')
plt.title('2D Hitmap of Particle Hits')
plt.show()

plt.hist(tot, bins=100, color='blue', alpha=0.7)
plt.xlabel('TOT (Time over Threshold)')
plt.ylabel('Counts')
plt.title('TOT Distribution')
plt.show()

# Scatter plot of ToA vs TOT
plt.scatter(toa, tot, s=1, alpha=0.5)
plt.xlabel('ToA (Time of Arrival)')
plt.ylabel('TOT (Time over Threshold)')
plt.title('ToA vs TOT')
plt.show()

from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(x, y, tot, c=tot, cmap='viridis', s=1)
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('TOT')
plt.title('3D Plot of X, Y, and TOT')
plt.show()