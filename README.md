# Timepix3 DAQ Control System

A comprehensive data acquisition control system for Timepix3 detectors using the Katherine library, supporting both data-driven and frame-based acquisition modes with HDF5 data storage.

## Repository Structure

```
timepix3-daq/
├── README.md                           # This file
├── CMakeLists.txt                      # Main CMake configuration
├── chipconfig_D4-W0005.bmc             # Chip configuration file
├── build/                              # Build directory (created during build)
└── c/
    ├── acquisition/
    │   ├── daq_control_datadriven.c    # Data-driven acquisition mode
    │   └── daq_control_frame.c         # Frame-based acquisition mode
    ├── katherine_headers/              # Katherine library header files
    │   └── katherine/
    │       ├── katherine.h
    │       ├── px.h
    │       └── [other headers...]
    └── src/                           # libkatherine source files
        ├── device.c
        ├── acquisition.c
        ├── config.c
        └── [other source files...]
```

## Features

- **Dual Acquisition Modes**: Support for both data-driven and frame-based acquisition
- **HDF5 Data Storage**: Efficient storage of pixel hit data with metadata
- **Real-time Monitoring**: Temperature, voltage, and communication status monitoring
- **Configurable Parameters**: Flexible bias voltage, threshold, and timing settings
- **Error Handling**: Robust connection retry mechanisms and error reporting
- **Pixel Hit Counting**: Track hit counts per pixel location
- **Timestamping**: Automatic filename generation with timestamps

## Prerequisites

### System Requirements
- Linux-based system (Ubuntu 18.04+ recommended)
- CMake 3.10 or higher
- GCC compiler with C11 support
- Network connection to Timepix3 device

### Dependencies
- **libkatherine**: Timepix3 control library
- **HDF5**: High-performance data storage library
- **Standard C libraries**: stdlib, stdio, time, string, unistd

### Installing Dependencies

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install cmake gcc build-essential
sudo apt install libhdf5-dev hdf5-tools
```

#### CentOS/RHEL:
```bash
sudo yum install cmake gcc make
sudo yum install hdf5-devel hdf5-tools
```

## Building the Project

### 1. Clone the Repository
```bash
git clone https://github.com/Adib-Sh/timepix3.git
cd timepix3
```

### 2. Create Build Directory
```bash
mkdir build
cd build
```

### 3. Configure with CMake
```bash
cmake ..
```

### 4. Compile the Project
```bash
make
```

## Configuration Files

### Chip Configuration File
The `chipconfig_D4-W0005.bmc` file contains pixel-specific configuration settings:
- **Location**: Must be in the same directory as the executable (build) or specify full path
- **Format**: Binary configuration file specific to your Timepix3 chip
- **Usage**: Automatically loaded during initialization

### Default Configuration Parameters
```c
Bias voltage:       155 V
Frames:             1
Acquisition time:   1e10 seconds (continuous)
Polarity:           Holes (1)
Clock frequency:    40 MHz
Vthreshold fine:    442
Vthreshold coarse:  7
Device IP:          <your_device_ip>
```

## Usage

### Data-Driven Acquisition Mode
```bash
./daq_control_datadriven
```

This mode:
- Continuously acquires pixel hits as they occur
- Stores data in real-time to HDF5 format
- Provides immediate feedback on hit rates
- Suitable for low to medium rate applications

### Frame-Based Acquisition Mode
```bash
./daq_control_frame
```

This mode:
- Acquires data in discrete time frames
- Better for high-rate applications
- Provides frame-by-frame statistics
- More suitable for timing-critical measurements

### Output Files
- **Format**: HDF5 (.h5)
- **Naming**: `ToTdata_datadriven_YYYYMMDD_HHMMSS.h5`
- **Structure**:
  ```
  /pixel_hits
  ├── x (pixel x-coordinate)
  ├── y (pixel y-coordinate)  
  ├── toa (time of arrival)
  ├── ftoa (fine time of arrival)
  ├── tot (time over threshold)
  └── hit_count (cumulative hits per # Timepix3 DAQ Control System

A comprehensive data acquisition control system for Timepix3 detectors using the Katherine library, supporting both data-driven and frame-based acquisition modes with HDF5 data storage.


## Data Structure

### PixelHit Structure
```c
typedef struct {
    int x;              // Pixel X coordinate (0-255)
    int y;              // Pixel Y coordinate (0-255)
    uint64_t toa;       // Time of Arrival
    uint8_t ftoa;       // Fine Time of Arrival
    uint16_t tot;       // Time over Threshold
    uint32_t hit_count; // Hit count for this pixel
} PixelHit;
```


### Common Issues

#### 1. Connection Failed
```
Connection failed: Connection refused. Retrying...
```
**Solutions**:
- Check device IP address and network connectivity
- Verify device is powered on and network cable connected
- Check firewall settings
- Ensure no other software is accessing the device

#### 2. Configuration File Not Found
```
Cannot load pixel configuration: chipconfig_D4-W0005.bmc
```
**Solutions**:
- Verify config file exists in executable directory
- Check file permissions (readable)
- Use absolute path to config file

#### 3. HDF5 File Creation Failed
```
Failed to create HDF5 file: ToTdata_datadriven_YYYYMMDD_HHMMSS.h5
```
**Solutions**:
- Check disk space availability
- Verify write permissions in current directory
- Ensure HDF5 library is properly installed

#### 4. Digital Test Failed
```
Digital test failed!
```
**Solutions**:
- Check device connection stability
- Verify device is not overheating
- Try power cycling the device
- Check for hardware issues

### Debug Information
The system provides comprehensive status information:
- Chip ID verification
- Communication status
- Temperature monitoring (readout and sensor)
- ADC voltage readings
- Digital test results

## Advanced Configuration

### Modifying Acquisition Parameters
Edit the default values in the main function:
```c
arguments_t args = {
    .bias = 155,         // Bias voltage
    .frames = 1,         // Number of frames
    .acq_time = 1e10,    // Acquisition time
    .polarity = 1,       // 1=holes, 0=electrons
    .frequency = 40,     // Clock frequency (MHz)
    .vth_fine = 442,     // Fine threshold
    .vth_coarse = 7,     // Coarse threshold
};
```

### DAC Settings
The system includes comprehensive DAC configuration:
- Preamp bias currents
- Discriminator settings
- Feedback voltage
- PLL control
- Test pulse settings

## Data Analysis

### Reading HDF5 Files

#### Basic Python Example - Data-driven mode:
```python
import h5py
import numpy as np
import matplotlib.pyplot as plt

# Load and analyze data-driven file
with h5py.File('ToTdata_datadriven_20241209_143022.h5', 'r') as f:
    hits = f['pixel_hits'][:]

# Extract data
x_coords = hits['x']
y_coords = hits['y']
toa_data = hits['toa']
tot_data = hits['tot']

# Create 256x256 hit count map
hit_count_map = np.zeros((256, 256), dtype=int)
np.add.at(hit_count_map, (y_coords, x_coords), 1)

# Basic visualization
plt.figure(figsize=(12, 5))

# Hit map
plt.subplot(121)
plt.imshow(hit_count_map, origin='lower', cmap='inferno')
plt.title('Pixel Hit Count Map')
plt.colorbar(label='Hits')

# ToT histogram
plt.subplot(122)
plt.hist(tot_data, bins=50, alpha=0.7, color='cyan')
plt.xlabel('Time-over-Threshold (ToT)')
plt.ylabel('Count')
plt.title('ToT Energy Spectrum')
plt.yscale('log')

plt.tight_layout()
plt.show()

print(f"Total hits: {len(hits):,}")
print(f"Active pixels: {np.sum(hit_count_map > 0):,}/65536")
print(f"Mean ToT: {np.mean(tot_data):.2f}")
```

#### Basic Python Example - Frame-based mode:
```python
import h5py
import numpy as np
import matplotlib.pyplot as plt

# Load and analyze frame-based file
with h5py.File('ToTdata_frame_20241209_143022.h5', 'r') as f:
    hits = f['pixel_hits'][:]

# Extract data
x_coords = hits['x']
y_coords = hits['y']
integral_tot = hits['integral_tot']
event_count = hits['event_count']

# Create 32x32 binned analysis
hist, xedges, yedges = np.histogram2d(
    x_coords, y_coords, bins=32, range=[[0, 255], [0, 255]]
)

# Visualization
plt.figure(figsize=(12, 5))

# Binned hit map
plt.subplot(121)
plt.imshow(hist.T, origin='lower', extent=[0, 255, 0, 255], cmap='inferno')
plt.title('32×32 Binned Hit Map')
plt.colorbar(label='Hits')

# Integral ToT distribution
plt.subplot(122)
plt.hist(integral_tot, bins=50, alpha=0.7, color='orange')
plt.xlabel('Integral ToT')
plt.ylabel('Count')
plt.title('Integral ToT Distribution')

plt.tight_layout()
plt.show()

print(f"Total events: {len(hits):,}")
print(f"Mean integral ToT: {np.mean(integral_tot):.2f}")
```

## Copyright Attribution
© Adib Shaker, MAX IV, Lund University 2025, All rights reserved.

This project is built on the [libkatherine](https://github.com/petrmanek/libkatherine) library developed by **Petr Mánek**. The original library is provided under the MIT License.

### Required Citation

If you use this DAQ control system or the underlying libkatherine library in your academic work, please cite this and the libkatherine:

```bibtex
  @THESIS{Manek2018_CUNI,
    author={P. Mánek},
    title={A system for 3D localization of gamma sources using Timepix3-based Compton cameras},
    year={2018},
    institution={Faculty of Mathematics and Physics, Charles University},
    type={Master's thesis}
  } 
```

### License
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)


### Acknowledgments

- [**Petr Mánek**](https://github.com/petrmanek/libkatherine/tree/master?tab=readme-ov-file)
- [**CERN and the Medipix Collaboration**](https://kt.cern/technologies/timepix3)
- [**Katherine Readout System**](https://iopscience.iop.org/article/10.1088/1748-0221/20/06/C06077)


## Support and Contributing

### Reporting Issues
Please include the following information:
- System specifications
- Error messages (full output)
- Network configuration
- Sensor and Chip ID

### Development
- Follow C11 coding standards
- Include proper error handling
- Update documentation for new features
- Test thoroughly before submitting changes

## Changelog

### Version 1.0
- Initial release
- Data-driven and frame-based acquisition modes
- HDF5 data storage
- Real-time monitoring
- Network retry mechanismspixel)

