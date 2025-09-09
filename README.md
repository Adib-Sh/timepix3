# Timepix3 DAQ Control System

A comprehensive data acquisition control system for Timepix3 detectors using the Katherine library, supporting both data-driven and frame-based acquisition modes with HDF5 data storage.

## Repository Structure

```
timepix3-daq/
├── README.md                           # This file
├── CMakeLists.txt                      # Main CMake configuration
├── chipconfig_D4-W0005.bmc            # Chip configuration file
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
Frames:            1
Acquisition time:   1e10 seconds (continuous)
Polarity:          Holes (1)
Clock frequency:    40 MHz
Vthreshold fine:    442
Vthreshold coarse:  7
Device IP:         192.168.1.218
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

## Repository Structure

```
timepix3-daq/
├── README.md                           # This file
├── CMakeLists.txt                      # Main CMake configuration
├── chipconfig_D4-W0005.bmc            # Chip configuration file
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
git clone <your-repository-url>
cd timepix3-daq
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
make -j$(nproc)
```

### Alternative Build Method (if using custom Makefile):
```bash
# From the root directory
make clean
make all
```

## Configuration Files

### Chip Configuration File
The `chipconfig_D4-W0005.bmc` file contains pixel-specific configuration settings:
- **Location**: Must be in the same directory as the executable or specify full path
- **Format**: Binary configuration file specific to your Timepix3 chip
- **Usage**: Automatically loaded during initialization

### Default Configuration Parameters
```c
Bias voltage:       155 V
Frames:            1
Acquisition time:   1e10 seconds (continuous)
Polarity:          Holes (1)
Clock frequency:    40 MHz
Vthreshold fine:    442
Vthreshold coarse:  7
Device IP:         192.168.1.218
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
  └── hit_count (cumulative hits per pixel)
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

### Sensor Specifications
- **Dimensions**: 256 × 256 pixels
- **Pixel size**: 55 μm × 55 μm
- **Active area**: 14.08 mm × 14.08 mm

## Network Configuration

### Device Connection
- **Default IP**: 192.168.1.218
- **Protocol**: TCP/IP
- **Port**: Standard Katherine protocol ports
- **Timeout**: 30 seconds for connection attempts
- **Retry**: 3 automatic retry attempts

### Network Setup
Ensure your system can reach the device:
```bash
ping 192.168.1.218
```

## Troubleshooting

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
    .bias = 155,                    // Bias voltage
    .frames = 1,                    // Number of frames
    .acq_time = 1e10,              // Acquisition time
    .polarity = 1,                 // 1=holes, 0=electrons
    .frequency = 40,               // Clock frequency (MHz)
    .vth_fine = 442,              // Fine threshold
    .vth_coarse = 7,              // Coarse threshold
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
#### Python Example - Data-driven mode:
```python
import h5py
import numpy as np

# Open data-driven file
with h5py.File('ToTdata_datadriven_20241209_143022.h5', 'r') as f:
    pixel_hits = f['pixel_hits'][:]
    
    # Extract data
    x_coords = pixel_hits['x']
    y_coords = pixel_hits['y']
    toa_data = pixel_hits['toa']
    tot_data = pixel_hits['tot']
    ftoa_data = pixel_hits['ftoa']
```

#### Python Example - Frame-based mode:
```python
import h5py
import numpy as np

# Open frame-based file
with h5py.File('ToTdata_frame_20241209_143022.h5', 'r') as f:
    pixel_hits = f['pixel_hits'][:]
    
    # Extract data
    x_coords = pixel_hits['x']
    y_coords = pixel_hits['y']
    integral_tot = pixel_hits['integral_tot']
    event_count = pixel_hits['event_count']
```

#### MATLAB Example:
```matlab
% Read data-driven HDF5 file
filename_dd = 'ToTdata_datadriven_20241209_143022.h5';
x_dd = h5read(filename_dd, '/pixel_hits/x');
y_dd = h5read(filename_dd, '/pixel_hits/y');
toa = h5read(filename_dd, '/pixel_hits/toa');
tot = h5read(filename_dd, '/pixel_hits/tot');

% Read frame-based HDF5 file
filename_fb = 'ToTdata_frame_20241209_143022.h5';
x_fb = h5read(filename_fb, '/pixel_hits/x');
y_fb = h5read(filename_fb, '/pixel_hits/y');
integral_tot = h5read(filename_fb, '/pixel_hits/integral_tot');
event_count = h5read(filename_fb, '/pixel_hits/event_count');
```

## Performance Considerations

### Data Rates
- **Typical rates**: 10⁶ - 10⁷ hits/second
- **Storage**: ~50 bytes per hit in HDF5 format
- **Memory usage**: Configurable buffers (default: 34MB metadata, 4MB pixel data)

### Optimization Tips
- Use SSD storage for high-rate applications
- Monitor system memory usage during long acquisitions
- Adjust buffer sizes based on expected data rates
- Consider data compression for long-term storage

## License

This project uses the Katherine library for Timepix3 control. Please ensure compliance with all applicable licenses.

## Support and Contributing

### Reporting Issues
Please include the following information:
- System specifications
- Error messages (full output)
- Network configuration
- Device model and firmware version

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

### Sensor Specifications
- **Dimensions**: 256 × 256 pixels
- **Pixel size**: 55 μm × 55 μm
- **Active area**: 14.08 mm × 14.08 mm

## Network Configuration

### Device Connection
- **Default IP**: 192.168.1.218
- **Protocol**: TCP/IP
- **Port**: Standard Katherine protocol ports
- **Timeout**: 30 seconds for connection attempts
- **Retry**: 3 automatic retry attempts

### Network Setup
Ensure your system can reach the device:
```bash
ping 192.168.1.218
```

## Troubleshooting

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
    .bias = 155,                    // Bias voltage
    .frames = 1,                    // Number of frames
    .acq_time = 1e10,              // Acquisition time
    .polarity = 1,                 // 1=holes, 0=electrons
    .frequency = 40,               // Clock frequency (MHz)
    .vth_fine = 442,              // Fine threshold
    .vth_coarse = 7,              // Coarse threshold
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
#### Python Example:
```python
import h5py
import numpy as np

# Open file
with h5py.File('ToTdata_datadriven_20241209_143022.h5', 'r') as f:
    pixel_hits = f['pixel_hits'][:]
    
    # Extract data
    x_coords = pixel_hits['x']
    y_coords = pixel_hits['y']
    toa_data = pixel_hits['toa']
    tot_data = pixel_hits['tot']
```

#### MATLAB Example:
```matlab
% Read HDF5 file
filename = 'ToTdata_datadriven_20241209_143022.h5';
x = h5read(filename, '/pixel_hits/x');
y = h5read(filename, '/pixel_hits/y');
toa = h5read(filename, '/pixel_hits/toa');
tot = h5read(filename, '/pixel_hits/tot');
```

## Performance Considerations

### Data Rates
- **Typical rates**: 10⁶ - 10⁷ hits/second
- **Storage**: ~50 bytes per hit in HDF5 format
- **Memory usage**: Configurable buffers (default: 34MB metadata, 4MB pixel data)

### Optimization Tips
- Use SSD storage for high-rate applications
- Monitor system memory usage during long acquisitions
- Adjust buffer sizes based on expected data rates
- Consider data compression for long-term storage

## License

This project uses the Katherine library for Timepix3 control. Please ensure compliance with all applicable licenses.

## Support and Contributing

### Reporting Issues
Please include the following information:
- System specifications
- Error messages (full output)
- Network configuration
- Device model and firmware version

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
- Network retry mechanisms