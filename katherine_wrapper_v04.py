import ctypes
import os
from enum import Enum
from enum import IntEnum

# Function to check if a function exists in the shared library
def check_function_exists(lib, func_name):
    try:
        getattr(lib, func_name)
        print(f"Function {func_name} is available.")
    except AttributeError:
        raise RuntimeError(f"Function {func_name} not found in library.")


# Load library
library_path = './build/libkatherine.so'
if not os.path.isfile(library_path):
    raise FileNotFoundError(f"Library not found: {library_path}")

try:
    libkatherine = ctypes.CDLL(library_path)
    print(f"Successfully loaded library: {library_path}")
except OSError as e:
    raise RuntimeError(f"Failed to load the library: {library_path}") from e


# Check required functions
#Device.h
check_function_exists(libkatherine, 'katherine_device_init')
check_function_exists(libkatherine, 'katherine_device_fini')

#Status.h
check_function_exists(libkatherine, 'katherine_get_chip_id')
check_function_exists(libkatherine, 'katherine_get_readout_status')
check_function_exists(libkatherine, 'katherine_get_comm_status')
check_function_exists(libkatherine, 'katherine_get_readout_temperature')
check_function_exists(libkatherine, 'katherine_get_sensor_temperature')
check_function_exists(libkatherine, 'katherine_perform_digital_test')
check_function_exists(libkatherine, 'katherine_get_adc_voltage')

#Px_config.h
check_function_exists(libkatherine, 'katherine_px_config_load_bmc_file')
check_function_exists(libkatherine, 'katherine_px_config_load_bpc_file')
check_function_exists(libkatherine, 'katherine_px_config_load_bmc_data')
check_function_exists(libkatherine, 'katherine_px_config_load_bpc_data')

#Acquisition.h
check_function_exists(libkatherine, 'katherine_acquisition_init')
check_function_exists(libkatherine, 'katherine_acquisition_fini')
check_function_exists(libkatherine, 'katherine_acquisition_begin')
check_function_exists(libkatherine, 'katherine_acquisition_abort')
check_function_exists(libkatherine, 'katherine_acquisition_read')
check_function_exists(libkatherine, 'katherine_str_acquisition_status')

#Config.h
check_function_exists(libkatherine, 'katherine_configure')
check_function_exists(libkatherine, 'katherine_set_all_pixel_config')
check_function_exists(libkatherine, 'katherine_set_acq_time')
check_function_exists(libkatherine, 'katherine_set_acq_mode')
check_function_exists(libkatherine, 'katherine_set_no_frames')
check_function_exists(libkatherine, 'katherine_set_bias')
check_function_exists(libkatherine, 'katherine_set_seq_readout_start')
check_function_exists(libkatherine, 'katherine_acquisition_setup')
check_function_exists(libkatherine, 'katherine_set_sensor_register')
check_function_exists(libkatherine, 'katherine_update_sensor_registers')
check_function_exists(libkatherine, 'katherine_output_block_config_update')
check_function_exists(libkatherine, 'katherine_timer_set')
check_function_exists(libkatherine, 'katherine_set_dacs')

#Udp.h
check_function_exists(libkatherine, 'katherine_udp_init')
check_function_exists(libkatherine, 'katherine_udp_fini')
check_function_exists(libkatherine, 'katherine_udp_send_exact')
check_function_exists(libkatherine, 'katherine_udp_recv_exact')
check_function_exists(libkatherine, 'katherine_udp_recv')
check_function_exists(libkatherine, 'katherine_udp_mutex_lock')
check_function_exists(libkatherine, 'katherine_udp_mutex_unlock')


# Define structures for communication with the library
class SockaddrIn(ctypes.Structure):
    _fields_ = [
        ("sin_family", ctypes.c_short),
        ("sin_port", ctypes.c_ushort),
        ("sin_addr", ctypes.c_uint),
        ("sin_zero", ctypes.c_ubyte * 8)
    ]


class KatherineDevice(ctypes.Structure):
    _fields_ = [
        ("control_socket", SockaddrIn),
        ("data_socket", SockaddrIn)
    ]


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

# Structures for BMC and BPC configuration
class KatherineBMC(ctypes.Structure):
    _fields_ = [("px_config", ctypes.c_ubyte * 65536)]


class KatherineBPC(ctypes.Structure):
    _fields_ = [("px_config", ctypes.c_ubyte * 65536)]


# Define KatherinePxConfig structure
class KatherinePxConfig(ctypes.Structure):
    _fields_ = [("words", ctypes.c_uint32 * 16384)]


# Function to initialize the device
def initialize_device(device_ip):
    device = KatherineDevice()
    result = libkatherine.katherine_device_init(ctypes.byref(device), device_ip)
    if result != 0:
        raise RuntimeError(f"Failed to initialize device. Error code: {result}")
    print("Device initialized successfully.")
    return device


# Function to get chip ID
def get_chip_id(device):
    chip_id = ctypes.create_string_buffer(16)
    result = libkatherine.katherine_get_chip_id(ctypes.byref(device), chip_id)
    if result == 0:
        print(f"Device Serial Number (Chip ID): {chip_id.value.decode()}")
    else:
        print(f"Failed to get chip ID. Error code: {result}")


# Function to get readout status
def get_readout_status(device):
    readout_status = KatherineReadoutStatus()
    result = libkatherine.katherine_get_readout_status(ctypes.byref(device), ctypes.byref(readout_status))
    if result == 0:
        print(f"Readout Status: HW Type {readout_status.hw_type}, HW Revision {readout_status.hw_revision}, "
              f"Serial Number {readout_status.hw_serial_number}, FW Version {readout_status.fw_version}")
    else:
        print(f"Failed to get readout status. Error code: {result}")


# Function to get communication status
def get_comm_status(device):
    comm_status = KatherineCommStatus()
    result = libkatherine.katherine_get_comm_status(ctypes.byref(device), ctypes.byref(comm_status))
    if result == 0:
        print(f"Comm Status: Comm Lines Mask {comm_status.comm_lines_mask}, Data Rate {comm_status.data_rate}, "
              f"Chip Detected {comm_status.chip_detected}")
    else:
        print(f"Failed to get communication status. Error code: {result}")


# Function to get readout and sensor temperatures
def get_temperatures(device):
    readout_temp = ctypes.c_float()
    sensor_temp = ctypes.c_float()

    result = libkatherine.katherine_get_readout_temperature(ctypes.byref(device), ctypes.byref(readout_temp))
    if result == 0:
        print(f"Readout Temperature: {readout_temp.value} °C")
    else:
        print("Error retrieving readout temperature.")

    result = libkatherine.katherine_get_sensor_temperature(ctypes.byref(device), ctypes.byref(sensor_temp))
    if result == 0:
        print(f"Sensor Temperature: {sensor_temp.value} °C")
    else:
        print("Error retrieving sensor temperature.")


# Function to perform digital test
def perform_digital_test(device):
    result = libkatherine.katherine_perform_digital_test(ctypes.byref(device))
    if result == 0:
        print("Digital test passed.")
    else:
        print("Digital test failed.")


# Function to get ADC voltage
def get_adc_voltage(device):
    adc_voltage = ctypes.c_float()
    result = libkatherine.katherine_get_adc_voltage(ctypes.byref(device), 0, ctypes.byref(adc_voltage))
    if result == 0:
        print(f"ADC Voltage: {adc_voltage.value} V")
    else:
        print(f"Failed to get ADC voltage. Error code: {result}")


# Function to finalize the device
def finalize_device(device):
    result = libkatherine.katherine_device_fini(ctypes.byref(device))
    if result == 0:
        print("Device connection closed successfully.")
    else:
        print(f"Error closing device connection! Error code: {result}")


# Function to load BMC file
def load_bmc_file(device, file_path):
    px_config = KatherinePxConfig()  # Create a new instance of the structure
    result = libkatherine.katherine_px_config_load_bmc_file(ctypes.byref(px_config), file_path.encode('utf-8'))
    if result == 0:
        print("BMC file loaded successfully.")
    else:
        print(f"Failed to load BMC file. Error code: {result}")


# Function to load BPC file
def load_bpc_file(device, file_path):
    px_config = KatherinePxConfig()  # Create a new instance of the structure
    result = libkatherine.katherine_px_config_load_bpc_file(ctypes.byref(px_config), file_path.encode('utf-8'))
    if result == 0:
        print("BPC file loaded successfully.")
    else:
        print(f"Failed to load BPC file. Error code: {result}")


class KatherineTrigger(ctypes.Structure):
    """Representation of katherine_trigger_t"""
    _fields_ = [
        ('enabled', ctypes.c_bool),          # bool in C corresponds to c_bool in ctypes
        ('channel', ctypes.c_char),         # char in C corresponds to c_char in ctypes
        ('use_falling_edge', ctypes.c_bool) # bool in C corresponds to c_bool in ctypes
    ]

class KatherinePhase(IntEnum):
    """Enum for katherine_phase_t"""
    PHASE_1 = 0
    PHASE_2 = 1
    PHASE_4 = 2
    PHASE_8 = 3
    PHASE_16 = 4

class KatherineFreq(IntEnum):
    """Enum for katherine_freq_t"""
    FREQ_40 = 1
    FREQ_80 = 2
    FREQ_160 = 3

class KatherineDacsNamed(ctypes.Structure):
    """Representation of katherine_dacs_named_t"""
    _fields_ = [
        ('Ibias_Preamp_ON', ctypes.c_uint16),
        ('Ibias_Preamp_OFF', ctypes.c_uint16),
        ('VPReamp_NCAS', ctypes.c_uint16),
        ('Ibias_Ikrum', ctypes.c_uint16),
        ('Vfbk', ctypes.c_uint16),
        ('Vthreshold_fine', ctypes.c_uint16),
        ('Vthreshold_coarse', ctypes.c_uint16),
        ('Ibias_DiscS1_ON', ctypes.c_uint16),
        ('Ibias_DiscS1_OFF', ctypes.c_uint16),
        ('Ibias_DiscS2_ON', ctypes.c_uint16),
        ('Ibias_DiscS2_OFF', ctypes.c_uint16),
        ('Ibias_PixelDAC', ctypes.c_uint16),
        ('Ibias_TPbufferIn', ctypes.c_uint16),
        ('Ibias_TPbufferOut', ctypes.c_uint16),
        ('VTP_coarse', ctypes.c_uint16),
        ('VTP_fine', ctypes.c_uint16),
        ('Ibias_CP_PLL', ctypes.c_uint16),
        ('PLL_Vcntrl', ctypes.c_uint16)
    ]

class KatherineDacs(ctypes.Union):
    """Representation of katherine_dacs_t (Union with array and named fields)"""
    _fields_ = [
        ('array', ctypes.c_uint16 * 18),  # Array of 18 uint16_t values
        ('named', KatherineDacsNamed)     # Named struct
    ]
    
class KatherinePixelConfig(ctypes.Structure):
    """Representation of katherine_px_config_t"""
    # You'll need to define the fields based on the C structure
    pass
'''
class KatherineConfig(ctypes.Structure):
    """Python representation of katherine_config_t structure"""
    _fields_ = [
        ('pixel_config', KatherinePixelConfig),
        ('bias_id', ctypes.c_ubyte),
        ('acq_time', ctypes.c_double),  # ns
        ('no_frames', ctypes.c_int),
        ('bias', ctypes.c_float),
        ('start_trigger', ctypes.c_int),  # katherine_trigger_t enum
        ('delayed_start', ctypes.c_bool),
        ('stop_trigger', ctypes.c_int),   # katherine_trigger_t enum
        ('gray_disable', ctypes.c_bool),
        ('polarity_holes', ctypes.c_bool),
        ('phase', KatherinePhase),
        ('freq', KatherineFreq),
        ('dacs', KatherineDACs)
    ]

    def __init__(self):
        super().__init__()
        # Initialize with default values if needed
        self.bias_id = 0
        self.acq_time = 1000.0  # 1 microsecond default
        self.no_frames = 1
        self.bias = 0.0
        self.start_trigger = 0  # Default trigger type
        self.delayed_start = False
        self.stop_trigger = 0   # Default trigger type
        self.gray_disable = False
        self.polarity_holes = False

'''
# Main logic
device_ip = b"192.168.1.218"  # Device IP address
bmc_file_path = './chipconfig.bmc'
try:
    device = initialize_device(device_ip)
    load_bmc_file(device, bmc_file_path)
    get_chip_id(device)
    get_readout_status(device)
    get_comm_status(device)
    get_temperatures(device)
    perform_digital_test(device)
    get_adc_voltage(device)






finally:
    finalize_device(device)
