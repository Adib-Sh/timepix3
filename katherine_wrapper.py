import ctypes
import os
import time
from enum import Enum


# For debug: check function available !!!!!!!(REMOVE LATER)!!!!!!!
def check_function_exists(lib, func_name):
    try:
        getattr(lib, func_name)
        print(f"Function {func_name} is available.")
    except AttributeError:
        raise RuntimeError(f"Function {func_name} not found in library.")




# path to the libkatherine.so and check file
library_path = './build/libkatherine.so'
if not os.path.isfile(library_path):
    raise FileNotFoundError(f"Library not found: {library_path}")

# Load .so
try:
    libkatherine = ctypes.CDLL(library_path)
    print(f"Successfully loaded library: {library_path}")
except OSError as e:
    raise RuntimeError(f"Failed to load the library: {library_path}") from e



# !!!!!!!(REMOVE LATER)!!!!!!! Check atherine_device_init
check_function_exists(libkatherine, 'katherine_device_init')
check_function_exists(libkatherine, 'katherine_px_config_load_bmc_file')
check_function_exists(libkatherine, 'katherine_px_config_load_bpc_file')


# Functions in udp_nix.h
class SockaddrIn(ctypes.Structure):
    _fields_ = [
        ("sin_family", ctypes.c_short),
        ("sin_port", ctypes.c_ushort),
        ("sin_addr", ctypes.c_uint),
        ("sin_zero", ctypes.c_ubyte * 8)
    ]

class KatherineUdp(ctypes.Structure):
    _fields_ = [
        ("sock", ctypes.c_int),
        ("addr_local", SockaddrIn),
        ("addr_remote", SockaddrIn),
        ("mutex", ctypes.c_void_p)
    ]

# Functions in device.h
class KatherineDevice(ctypes.Structure):
    _fields_ = [
        ("control_socket", KatherineUdp),
        ("data_socket", KatherineUdp)
    ]

# Functions in status.h
class KatherineReadoutStatus(ctypes.Structure):
    _fields_ = [
        ("hw_type", ctypes.c_int),
        ("hw_revision", ctypes.c_int),
        ("hw_serial_number", ctypes.c_int),
        ("fw_version", ctypes.c_int)
    ]

class KatherineCommStatus(ctypes.Structure):
    _fields_ = [
        ("comm_lines_mask", ctypes.c_uint8),
        ("data_rate", ctypes.c_uint32),
        ("chip_detected", ctypes.c_bool)
    ]

# Functions in px_config.h
class KatherinePxConfig(ctypes.Structure):
    _fields_ = [("words", ctypes.c_uint32 * 16384)]

# Functions in px.h
class KatherineCoord(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_uint8),
        ("y", ctypes.c_uint8)
    ]

class KatherinePxFToAToT(ctypes.Structure):
    _fields_ = [
        ("coord", KatherineCoord),
        ("ftoa", ctypes.c_uint8),
        ("toa", ctypes.c_uint64),
        ("tot", ctypes.c_uint16)
    ]

class KatherinePxToAToT(ctypes.Structure):
    _fields_ = [
        ("coord", KatherineCoord),
        ("toa", ctypes.c_uint64),
        ("hit_count", ctypes.c_uint8),
        ("tot", ctypes.c_uint16)
    ]

class KatherinePxFToAOnly(ctypes.Structure):
    _fields_ = [
        ("coord", KatherineCoord),
        ("ftoa", ctypes.c_uint8),
        ("toa", ctypes.c_uint64)
    ]

class KatherinePxToAOnly(ctypes.Structure):
    _fields_ = [
        ("coord", KatherineCoord),
        ("toa", ctypes.c_uint64),
        ("hit_count", ctypes.c_uint8)
    ]

class KatherinePxFEventITot(ctypes.Structure):
    _fields_ = [
        ("coord", KatherineCoord),
        ("hit_count", ctypes.c_uint8),
        ("event_count", ctypes.c_uint16),
        ("integral_tot", ctypes.c_uint16)
    ]

class KatherinePxEventITot(ctypes.Structure):
    _fields_ = [
        ("coord", KatherineCoord),
        ("event_count", ctypes.c_uint16),
        ("integral_tot", ctypes.c_uint16)
    ]
    
# Functions in config.h
class KatherineTrigger(ctypes.Structure):
    _fields_ = [
        ("enabled", ctypes.c_bool),
        ("channel", ctypes.c_char),
        ("use_falling_edge", ctypes.c_bool)
    ]

class KatherineDacsNamed(ctypes.Structure):
    _fields_ = [
        ("Ibias_Preamp_ON", ctypes.c_uint16),
        ("Ibias_Preamp_OFF", ctypes.c_uint16),
        ("VPReamp_NCAS", ctypes.c_uint16),
        ("Ibias_Ikrum", ctypes.c_uint16),
        ("Vfbk", ctypes.c_uint16),
        ("Vthreshold_fine", ctypes.c_uint16),
        ("Vthreshold_coarse", ctypes.c_uint16),
        ("Ibias_DiscS1_ON", ctypes.c_uint16),
        ("Ibias_DiscS1_OFF", ctypes.c_uint16),
        ("Ibias_DiscS2_ON", ctypes.c_uint16),
        ("Ibias_DiscS2_OFF", ctypes.c_uint16),
        ("Ibias_PixelDAC", ctypes.c_uint16),
        ("Ibias_TPbufferIn", ctypes.c_uint16),
        ("Ibias_TPbufferOut", ctypes.c_uint16),
        ("VTP_coarse", ctypes.c_uint16),
        ("VTP_fine", ctypes.c_uint16),
        ("Ibias_CP_PLL", ctypes.c_uint16),
        ("PLL_Vcntrl", ctypes.c_uint16)
    ]

class KatherineDacs(ctypes.Structure):
    _fields_ = [
        ("array", ctypes.c_uint16 * 18),
        ("named", KatherineDacsNamed)
    ]

class KatherineAcquisitionMode(ctypes.c_int):
    TOA_TOT = 0
    ONLY_TOA = 1
    EVENT_ITOT = 2

class KatherinePhase(ctypes.c_int):
    PHASE_1 = 0
    PHASE_2 = 1
    PHASE_4 = 2
    PHASE_8 = 3
    PHASE_16 = 4

class KatherineFreq(ctypes.c_int):
    FREQ_40 = 1
    FREQ_80 = 2
    FREQ_160 = 3

class KatherineConfig(ctypes.Structure):
    _fields_ = [
        ("pixel_config", KatherinePxConfig),
        ("bias_id", ctypes.c_ubyte),
        ("acq_time", ctypes.c_double),
        ("no_frames", ctypes.c_int),
        ("bias", ctypes.c_float),
        ("start_trigger", KatherineTrigger),
        ("delayed_start", ctypes.c_bool),
        ("stop_trigger", KatherineTrigger),
        ("gray_disable", ctypes.c_bool),
        ("polarity_holes", ctypes.c_bool),
        ("phase", KatherinePhase),
        ("freq", KatherineFreq), 
        ("dacs", KatherineDacs)
    ]



# Define the function prototypes
# Device init
libkatherine.katherine_device_init.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.c_char_p]
libkatherine.katherine_device_init.restype = ctypes.c_int
libkatherine.katherine_device_fini.argtypes = [ctypes.POINTER(KatherineDevice)]
libkatherine.katherine_device_fini.restype = ctypes.c_int

# Chip ID
libkatherine.katherine_get_chip_id.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.c_char_p]
libkatherine.katherine_get_chip_id.restype = ctypes.c_int

# Get status
libkatherine.katherine_get_readout_status.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.POINTER(KatherineReadoutStatus)]
libkatherine.katherine_get_readout_status.restype = ctypes.c_int

# Get communications status
libkatherine.katherine_get_comm_status.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.POINTER(KatherineCommStatus)]
libkatherine.katherine_get_comm_status.restype = ctypes.c_int

# Get readout temperature
libkatherine.katherine_get_readout_temperature.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.POINTER(ctypes.c_float)]
libkatherine.katherine_get_readout_temperature.restype = ctypes.c_int

# Get sensor temperature
libkatherine.katherine_get_sensor_temperature.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.POINTER(ctypes.c_float)]
libkatherine.katherine_get_sensor_temperature.restype = ctypes.c_int

# Get ADC voltage
libkatherine.katherine_get_adc_voltage.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.c_uint8, ctypes.POINTER(ctypes.c_float)]
libkatherine.katherine_get_adc_voltage.restype = ctypes.c_int

# Pixel config
libkatherine.katherine_px_config_load_bmc_file.argtypes = [ctypes.POINTER(KatherinePxConfig), ctypes.c_char_p]
libkatherine.katherine_px_config_load_bmc_file.restype = ctypes.c_int

libkatherine.katherine_px_config_load_bpc_file.argtypes = [ctypes.POINTER(KatherinePxConfig), ctypes.c_char_p]
libkatherine.katherine_px_config_load_bpc_file.restype = ctypes.c_int

# Configure the device with a given configuration
libkatherine.katherine_configure.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.POINTER(KatherineConfig)]
libkatherine.katherine_configure.restype = ctypes.c_int

# Set pixel configuration
libkatherine.katherine_set_all_pixel_config.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.POINTER(KatherinePxConfig)]
libkatherine.katherine_set_all_pixel_config.restype = ctypes.c_int

# Set acquisition time
libkatherine.katherine_set_acq_time.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.c_double]
libkatherine.katherine_set_acq_time.restype = ctypes.c_int

# Set acquisition mode
libkatherine.katherine_set_acq_mode.argtypes = [ctypes.POINTER(KatherineDevice), KatherineAcquisitionMode, ctypes.c_bool]
libkatherine.katherine_set_acq_mode.restype = ctypes.c_int

# Set number of frames
libkatherine.katherine_set_no_frames.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.c_int]
libkatherine.katherine_set_no_frames.restype = ctypes.c_int

# Set bias voltage
libkatherine.katherine_set_bias.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.c_ubyte, ctypes.c_float]
libkatherine.katherine_set_bias.restype = ctypes.c_int

# Set sequence readout start
libkatherine.katherine_set_seq_readout_start.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.c_int]
libkatherine.katherine_set_seq_readout_start.restype = ctypes.c_int

# Acquisition setup
libkatherine.katherine_acquisition_setup.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.POINTER(KatherineTrigger), ctypes.c_bool, ctypes.POINTER(KatherineTrigger)]
libkatherine.katherine_acquisition_setup.restype = ctypes.c_int

# Set sensor register
libkatherine.katherine_set_sensor_register.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.c_char, ctypes.c_int32]
libkatherine.katherine_set_sensor_register.restype = ctypes.c_int

# Update sensor registers
libkatherine.katherine_update_sensor_registers.argtypes = [ctypes.POINTER(KatherineDevice)]
libkatherine.katherine_update_sensor_registers.restype = ctypes.c_int

# Output block config update
libkatherine.katherine_output_block_config_update.argtypes = [ctypes.POINTER(KatherineDevice)]
libkatherine.katherine_output_block_config_update.restype = ctypes.c_int

# Set timer
libkatherine.katherine_timer_set.argtypes = [ctypes.POINTER(KatherineDevice)]
libkatherine.katherine_timer_set.restype = ctypes.c_int

# Set DACs
libkatherine.katherine_set_dacs.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.POINTER(KatherineDacs)]
libkatherine.katherine_set_dacs.restype = ctypes.c_int


# Digital test
libkatherine.katherine_perform_digital_test.argtypes = [ctypes.POINTER(KatherineDevice)]
libkatherine.katherine_perform_digital_test.restype = ctypes.c_int


# Initialize px_config test
def load_bmc_config(file_path):
    px_config = KatherinePxConfig()
    result = libkatherine.katherine_px_config_load_bmc_file(ctypes.byref(px_config), file_path.encode())
    if result == 0:
        print(f"BMC configuration loaded successfully from {file_path}.")
    else:
        print(f"Failed to load BMC configuration from {file_path}. Error code: {result}")
    return px_config

def load_bpc_config(file_path):
    px_config = KatherinePxConfig()
    result = libkatherine.katherine_px_config_load_bpc_file(ctypes.byref(px_config), file_path.encode())
    if result == 0:
        print(f"BPC configuration loaded successfully from {file_path}.")
    else:
        print(f"Failed to load BPC configuration from {file_path}. Error code: {result}")
        return px_config



# Connect to the device
device = KatherineDevice()
config = KatherineConfig()
device_ip = b"192.168.1.218"  # Device IP address
bmc_file = "bmc_file.bmc" # Add config file path
px_config_bmc = load_bmc_config(bmc_file)

# Initialize the device
result = libkatherine.katherine_device_init(ctypes.byref(device), device_ip)
if result != 0:
    print(f"Failed to initialize device!")
else:
    print("Failed to initialize device!")

    # Get the chip ID 
    chip_id = ctypes.create_string_buffer(16)
    result = libkatherine.katherine_get_chip_id(ctypes.byref(device), chip_id)
    if result == 0:
        print(f"Device Serial Number (Chip ID): {chip_id.value.decode()}")
    else:
        print(f"Failed to get chip ID. Error code: {result}")

    # Get Readout Status
    readout_status = KatherineReadoutStatus()
    result = libkatherine.katherine_get_readout_status(ctypes.byref(device), ctypes.byref(readout_status))
    if result == 0:
        print(f"Readout Status: HW Type {readout_status.hw_type}, HW Revision {readout_status.hw_revision}, "
              f"Serial Number {readout_status.hw_serial_number}, FW Version {readout_status.fw_version}")
    else:
        print(f"Failed to get readout status. Error code: {result}")

    # Get Comm Status
    comm_status = KatherineCommStatus()
    result = libkatherine.katherine_get_comm_status(ctypes.byref(device), ctypes.byref(comm_status))
    if result == 0:
        print(f"Comm Status: Comm Lines Mask {comm_status.comm_lines_mask}, Data Rate {comm_status.data_rate}, "
              f"Chip Detected {comm_status.chip_detected}")
    else:
        print(f"Failed to get communication status. Error code: {result}")

    # Get Readout Temperature
    readout_temp = ctypes.c_float()
    result = libkatherine.katherine_get_readout_temperature(ctypes.byref(device), ctypes.byref(readout_temp))
    if result == 0:
        print(f"Readout Temperature: {readout_temp.value} °C")
    else:
        print("Error retrieving readout temperature.")

    # Get Sensor Temperature
    sensor_temp = ctypes.c_float()
    result = libkatherine.katherine_get_sensor_temperature(ctypes.byref(device), ctypes.byref(sensor_temp))
    if result == 0:
        print(f"Sensor Temperature: {sensor_temp.value} °C")
    else:
        print("Error retrieving sensor temperature.")

    # Digital Test
    result = libkatherine.katherine_perform_digital_test(ctypes.byref(device))
    if result == 0:
        print("Digital test passed.")
    else:
        print("Digital test failed.")

    # Get ADC Voltage 
    adc_voltage = ctypes.c_float()
    result = libkatherine.katherine_get_adc_voltage(ctypes.byref(device), 0, ctypes.byref(adc_voltage))
    if result == 0:
        print(f"ADC Voltage: {adc_voltage.value} V")
    else:
        print(f"Failed to get ADC voltage. Error code: {result}")

    # Configure the device
    result = libkatherine.katherine_configure(ctypes.byref(device), ctypes.byref(config))
    if result == 0:
        print("Device configured successfully.")
    else:
        print(f"Failed to configure device. Error code: {result}")
# Clean up and finalize the device connection
libkatherine.katherine_device_fini(ctypes.byref(device))
