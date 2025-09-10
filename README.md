# Katherine THL Calibration Repository

A comprehensive toolkit for performing Threshold Level (THL) calibration scans on Timepix3 detectors using the Katherine acquisition library.

## Repository Structure

```
katherine-thl-calibration/
├── README.md
├── CMakeLists.txt
├── chipconfig_D4-W0005.bmc                       # Chip configuration file
├── c/
│   ├── acquisition/
│   │   ├── daq_thlscan_datadriven.c              # Data-driven mode with full THL scan
│   │   ├── daq_thlscan_datadriven_exclude800.c   # Data-driven mode excluding 810-845mV
│   │   └── daq_thlscan_frame_exclude800.c        # Frame mode excluding 810-845mV
│   ├── katherine_headers/
│   │   └── [Katherine library headers]
│   └── src/
│       └── [libkatherine source files]
```

## Overview

This repository contains three different implementations for performing THL (Threshold Level) calibration scans on Timepix3 detectors:

### 1. Data-Driven Mode (Full Scan) - `daq_thlscan_datadriven.c`
- **Voltage Range**: 820-1200 mV
- **Step Size**: 5.0 mV
- **Acquisition Mode**: `READOUT_DATA_DRIVEN` with `ACQUISITION_MODE_TOA_TOT`
- **Features**: 
  - Complete THL scan dataset creation
  - Writes both individual hits and full pixel matrix to HDF5
  - Includes comprehensive THL scan results tracking

### 2. Data-Driven Mode (Excluded Range) - `daq_thlscan_datadriven_exclude800.c`
- **Voltage Range**: 600-950 mV (excludes 810-845 mV)
- **Step Size**: 2.0 mV
- **Acquisition Mode**: `READOUT_DATA_DRIVEN` with `ACQUISITION_MODE_TOA_TOT`
- **Features**: 
  - Skips problematic voltage range (810-845 mV)
  - Longer acquisition time (500ms vs 100ms)
  - Simplified HDF5 output structure

### 3. Frame Mode (Excluded Range) - `daq_thlscan_frame_exclude800.c`
- **Voltage Range**: 300-1200 mV (excludes 810-845 mV)
- **Step Size**: 2.0 mV
- **Acquisition Mode**: `READOUT_SEQUENTIAL` with `ACQUISITION_MODE_EVENT_ITOT`
- **Features**: 
  - Uses frame-based readout instead of data-driven
  - Collects integral TOT, event count, and hit count
  - Different pixel data structure optimized for frame mode

## Prerequisites

### System Requirements
- Linux-based system
- CMake 3.10 or higher
- GCC compiler with C99 support
- HDF5 development libraries
- Katherine library and headers

### Dependencies
```bash
# Ubuntu/Debian
sudo apt-get install cmake build-essential libhdf5-dev

# CentOS/RHEL
sudo yum install cmake gcc hdf5-devel
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

### 4. Build the Project
```bash
make
```

This will generate three executables:
- `daq_thlscan_datadriven`
- `daq_thlscan_datadriven_exclude800`
- `daq_thlscan_frame_exclude800`

## Configuration Files

### Pixel Configuration File
The `chipconfig_D4-W0005.bmc` file contains the pixel configuration for the specific Timepix3 chip. This file must be present in the same directory as the executables or update the path in the source code:

```c
// Update this line in the configure() function if needed
int res = katherine_px_config_load_bmc_file(&config->pixel_config, "chipconfig_D4-W0005.bmc");
```

### Device Configuration
By default, the device IP address is set to `192.168.1.218`. Update the `remote_addr` variable in the source files if your device uses a different address:

```c
static const char *remote_addr = "192.168.1.218";
```

## Running the Programs

### Basic Usage
```bash
# Run data-driven mode with full scan
./daq_thlscan_datadriven

# Run data-driven mode excluding problematic range
./daq_thlscan_datadriven_exclude800

# Run frame mode excluding problematic range
./daq_thlscan_frame_exclude800
```

### Program Flow
1. **Device Connection**: Attempts connection with 3 retries
2. **Device Diagnostics**: Checks communication status, chip ID, temperatures
3. **Digital Test**: Verifies device functionality
4. **THL Scan**: Performs threshold scan across specified voltage range
5. **Data Storage**: Saves results to timestamped HDF5 files

## Output Files

### HDF5 File Structure
The programs generate HDF5 files with the following naming conventions:
- Data-driven (full): `thl_calibration_YYYYMMDD_HHMMSS.h5`
- Data-driven (excluded): `thlscan_datadriven_YYYYMMDD_HHMMSS.h5`
- Frame mode: `thlscan_frame_YYYYMMDD_HHMMSS.h5`

### Dataset Structure

#### Data-Driven Mode
```
/pixel_hits - Individual pixel hits with fields:
├── x, y          # Pixel coordinates
├── toa           # Time of arrival
├── ftoa          # Fine time of arrival
├── tot           # Time over threshold
├── hit_count     # Number of hits per pixel
└── thl           # THL voltage value

/thl_scan - Scan summary with fields:
├── thl           # THL voltage
├── frame_idx     # Frame index
└── hits          # Total hits for this THL value
```

#### Frame Mode
```
/pixel_hits - Frame-based pixel data with fields:
├── x, y          # Pixel coordinates
├── integral_tot  # Integrated time over threshold
├── event_count   # Number of events
├── hit_count     # Number of hits
└── thl           # THL voltage value
```

### File Attributes
Each HDF5 file includes metadata attributes:
- `thl_start_mv`: Starting voltage in mV
- `thl_end_mv`: Ending voltage in mV
- `thl_step_mv`: Step size in mV
- `frames_per_thl`: Number of frames per THL point

## THL Voltage Calculation

The programs convert voltage values to DAC settings using:
- **Coarse DAC**: 80.0 mV steps (0-15 range)
- **Fine DAC**: 0.5 mV steps (0-511 range)
- **Total voltage**: `(coarse × 80.0) + (fine × 0.5)` mV

## Troubleshooting

### Common Issues

1. **Device Connection Failed**
   - Verify network connectivity to device IP
   - Check if device is powered on
   - Ensure no firewall blocking communication

2. **Chip Configuration Load Failed**
   - Verify `chipconfig_D4-W0005.bmc` file exists
   - Check file permissions
   - Ensure correct file path in source code

3. **HDF5 File Creation Failed**
   - Check disk space availability
   - Verify write permissions in current directory
   - Ensure HDF5 libraries are properly installed

4. **Digital Test Failed**
   - Check Timepix3 chip connection
   - Verify power supply stability
   - Review communication status output

### Debug Output
All programs provide verbose output including:
- Connection attempts and status
- Device diagnostics (temperatures, communication status)
- Frame-by-frame acquisition progress
- Pixel hit statistics
- Voltage conversion details

## Customization

### Modifying Scan Parameters
Key parameters can be adjusted in the source code:

```c
// Voltage range and steps
#define THL_MIN_MV 600.0    // Starting voltage
#define THL_MAX_MV 950.0    // Ending voltage  
#define THL_STEP_MV 2.0     // Step size

// Acquisition settings
#define FRAMES_PER_THL 1    // Frames per voltage point
config->acq_time = 5e8;     // Acquisition time (500ms)
```

### Adding Custom DAC Settings
The `configure()` function contains all DAC settings that can be customized for your specific detector configuration.

## Performance Considerations

- **Data-driven mode**: More efficient for high hit rate scenarios
- **Frame mode**: Better for analyzing spatial distributions
- **Acquisition time**: Balance between statistics and scan duration
- **Step size**: Smaller steps provide higher resolution but longer scan times

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