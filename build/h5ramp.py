import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors

file_name = 'bias_ramp_20250406_050343.h5'

COLUMN_NAMES = ['X', 'Y', 'ToA', 'fToA', 'ToT', 'Pixel_C']

with h5py.File(file_name, 'r') as file:
    print("Keys: %s" % file.keys())
    a_group_key = list(file.keys())[12]

    print(type(file[a_group_key])) 
    fig1 = plt.figure(figsize=(15, 7))
    ax1 = fig1.add_subplot(projection='3d')
    data = list(file[a_group_key]['pixel_hits'])
    
    x = [data[i][0] for i in range(len(data)-1)]
    y = [data[i][1] for i in range(len(data)-1)]
    #ToA = [data[i][2] for i in range(len(data)-1)]
    #fToA = [data[i][3] for i in range(len(data)-1)]
    #ToT = [data[i][4] for i in range(len(data)-1)]
    count = [data[i][2] for i in range(len(data)-1)]
    
    '''
    norm = colors.Normalize(vmin=min(ToA), vmax=max(ToA))
    c = np.array(ToA)
    p = ax1.scatter(x, y, ToA, c=c, cmap='magma', norm=norm)
    fig1.colorbar(p, ax=ax1)
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_zlabel('ToA')
    ax1.set_title('ToA over Sensor Spatial X-Y')
    plt.show()
    
    
    fig2 = plt.figure(figsize=(15, 7))
    ax2 = fig2.add_subplot(projection='3d')
    norm = colors.Normalize(vmin=min(ToT), vmax=max(ToT))
    c = np.array(ToT)
    p = ax2.scatter(x, y, ToT, c=c, cmap='magma', norm=norm)
    fig2.colorbar(p, ax=ax2)
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    ax2.set_zlabel('ToT')
    ax2.set_title('ToT over Sensor Spatial X-Y')
    plt.show()
    '''
    
    fig3 = plt.figure(figsize=(15, 7))
    ax3 = fig3.add_subplot(projection='3d')
    norm = colors.Normalize(vmin=min(count), vmax=max(count))
    c = np.array(count)
    p = ax3.scatter(x, y, count, c=c, cmap='magma', norm=norm)
    fig3.colorbar(p, ax=ax3)
    ax3.set_xlabel('X')
    ax3.set_ylabel('Y')
    ax3.set_zlabel('Pixel Count')
    ax3.set_title('Individual Pixel Hit Count on Sensor Spatial X-Y')
    plt.show()
