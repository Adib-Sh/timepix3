# Daq_control_CLA - Timepix3 Data Acquisition Tool

A command-line data acquisition tool for Timepix3 detectors using the Katherine library with comprehensive HDF5 data storage and configurable acquisition parameters.

## Repository Structure

```
timepix3/
├── README.md                               # This file
├── CMakeLists.txt                          # Main CMake configuration
├── chipconfig_D4-W0005.bmc                 # Chip configuration file
├── build/                                  # Build directory (created during build)
└── c/
    ├── acquisition/
    │   ├── daq_control_datadriven_cla.c    # Data-driven acquisition mode
    ├── include/                            # Katherine library header files
    │   └── katherine/
    │       ├── katherine.h
    │       ├── px.h
    │       └── [other headers...]
    └── src/                                # libkatherine source files
        ├── device.c
        ├── acquisition.c
        ├── config.c
        └── [other source files...]         # Build directory (created during build)
```

## Features

- **Command-Line Interface**: Full argument parsing with comprehensive help system
- **Multiple Acquisition Modes**: TOA, TOA_TOT, and EVENT_ITOT modes
- **HDF5 Data Storage**: Real-time storage of pixel hit data with metadata
- **Configurable Parameters**: Bias voltage, thresholds, clock frequency, and timing settings
- **Real-time Monitoring**: Device status, temperature, and communication monitoring
- **Pixel Hit Tracking**: Individual pixel hit counting with coordinates and timing
- **Robust Error Handling**: Connection retry mechanisms and comprehensive error reporting
- **Automatic File Naming**: Timestamp-based output file generation

## Prerequisites

### System Requirements
- Linux-based system (Ubuntu 18.04+ recommended)
- CMake 3.10 or higher
- GCC compiler with C11 support
- Network connection to Timepix3 device

### Dependencies
- **libkatherine**: Timepix3 control library
- **HDF5**: High-performance data storage library
- **argp**: GNU argument parsing library (usually included in glibc)
- **Standard C libraries**: stdlib, stdio, time, string, unistd

### Installing Dependencies

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install cmake gcc build-essential
sudo apt install libhdf5-dev hdf5-tools
sudo apt install libargp-dev  # If not included in your libc
```

#### CentOS/RHEL:
```bash
sudo yum install cmake gcc make
sudo yum install hdf5-devel hdf5-tools
```

## Building the Project

### 1. Clone/Download the Source
```bash
# If using git
git clone https://github.com/Adib-Sh/timepix3.git
cd timepix3

# Or simply download the source files to a directory
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
- **Location**: Must be accessible from the executable directory or specify full path
- **Format**: Binary configuration file specific to your Timepix3 chip
- **Usage**: Loaded automatically during initialization

### Default Configuration Parameters
```
Bias voltage:       155 V
Number of frames:   1
Acquisition time:   1e9 seconds
Polarity:           Holes (1)
Clock frequency:    40 MHz
Vthreshold fine:    424
Vthreshold coarse:  7
Device IP:           <your_device_ip>
Acquisition mode:   TOA_TOT (1)
```

## Usage

### Basic Usage
```bash
# Run with default settings
./daq_control_datadriven_cla

# Run with custom bias voltage and frames
./daq_control_datadriven_cla -b 200 -f 10

# Run with custom configuration file and output
./daq_control_datadriven_cla -c my_config.bmc -o my_data.h5
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--bias` | `-b` | Set bias voltage (V) | 155 |
| `--frames` | `-f` | Number of frames | 1 |
| `--config` | `-c` | Path to .bmc config file | chipconfig_D4-W0005.bmc |
| `--address` | `-a` | Device IP address | 192.168.1.218 |
| `--output` | `-o` | Output HDF5 file name | Auto-generated |
| `--acqtime` | `-t` | Acquisition time (seconds) | 1e9 |
| `--polarity` | `-p` | Polarity mode (0=electrons, 1=holes) | 1 |
| `--frequency` | `-F` | Clock frequency (10, 20, 40, 80 MHz) | 40 |
| `--vth-fine` | `-v` | Fine threshold DAC value | 424 |
| `--vth-coarse` | `-V` | Coarse threshold DAC value | 7 |
| `--acq-mode` | `-m` | Acquisition mode (0,1,2) | 1 |
| `--help` | `-h` | Display help message | - |
| `--detailed-help` | `-H` | Display detailed help | - |

### Acquisition Modes
- **Mode 0**: TOA_TOT - Time of Arrival and Time over Threshold
- **Mode 1**: ONLY_TOA - Time of Arrival only (default)
- **Mode 2**: EVENT_ITOT - Event counting with integral Time over Threshold

### Example Commands
```bash
# High sensitivity with lower thresholds
./daq_control_datadriven_cla -v 400 -V 5 -b 180

# 80 MHz operation with electron polarity
./daq_control_datadriven_cla -F 80 -p 0

# Long acquisition with custom output file
./daq_control_datadriven_cla -t 3600 -o long_measurement.h5

# Event counting mode with multiple frames
./daq_control_datadriven_cla -m 2 -f 100 -t 10
```

### Help System
```bash
# Basic help
./daq_control_datadriven_cla -h

# Detailed help with examples and parameter explanations
./daq_control_datadriven_cla -H
```

## Output Files

### File Format and Structure
- **Format**: HDF5 (.h5)
- **Default Naming**: `ToTdata_datadriven_YYYYMMDD_HHMMSS.h5`
- **Dataset Structure**:
  ```
  /pixel_hits
  ├── x           (int)      - Pixel X coordinate (0-255)
  ├── y           (int)      - Pixel Y coordinate (0-255)
  ├── toa         (uint64)   - Time of Arrival
  ├── ftoa        (uint8)    - Fine Time of Arrival
  ├── tot         (uint16)   - Time over Threshold
  └── hit_count   (uint32)   - Cumulative hits per pixel
  ```

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

## System Monitoring

The program provides comprehensive device monitoring:
- **Chip ID verification**
- **Communication status and data rates**
- **Readout and sensor temperature monitoring**
- **ADC voltage readings**
- **Digital connectivity tests**

## Troubleshooting

### Common Issues

#### 1. Connection Failed
```
Attempting to connect to device at 192.168.1.218...
Connection failed: Connection refused. Retrying... (2 attempts left)
```
**Solutions**:
- Verify device IP address with `-a` option
- Check network connectivity and cables
- Ensure device is powered on
- Check firewall settings

#### 2. Configuration File Not Found
```
Cannot load pixel configuration from chipconfig_D4-W0005.bmc.
```
**Solutions**:
- Verify config file exists and is readable
- Use `-c` option to specify full path
- Check file permissions

#### 3. HDF5 File Creation Failed
```
Failed to create HDF5 file: ToTdata_datadriven_YYYYMMDD_HHMMSS.h5
```
**Solutions**:
- Check available disk space
- Verify write permissions in directory
- Use `-o` option to specify different location

#### 4. Invalid Parameters
```
Invalid frequency: 50. Must be 10, 20, 40, or 80 MHz.
Invalid acquisition mode: 3. Using default (1=TOA_TOT).
```
**Solutions**:
- Check parameter ranges in detailed help (`-H`)
- Use valid values as specified in documentation

### Debug Information
The program displays extensive status information:
```
Chip ID: W0005_D4
Comm Status:
  Communication Lines Mask: 0xff
  Data Rate: 5120 Mbps
  Chip Detected: Yes
Readout temperature: 45.2°C
Sensor temperature: 23.8°C
Digital test passed.
ADC voltage: 1.234000
```

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
- Data-driven acquisition modes
- HDF5 data storage
- Real-time monitoring
- Network retry mechanismspixel)