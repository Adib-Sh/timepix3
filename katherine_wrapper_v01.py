import ctypes
import os
from enum import Enum


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
check_function_exists(libkatherine, 'katherine_device_init')
check_function_exists(libkatherine, 'katherine_get_chip_id')
check_function_exists(libkatherine, 'katherine_get_readout_status')
check_function_exists(libkatherine, 'katherine_get_comm_status')
check_function_exists(libkatherine, 'katherine_get_readout_temperature')
check_function_exists(libkatherine, 'katherine_get_sensor_temperature')
check_function_exists(libkatherine, 'katherine_perform_digital_test')
check_function_exists(libkatherine, 'katherine_get_adc_voltage')
check_function_exists(libkatherine, 'katherine_device_fini')


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


# Main logic
device_ip = b"192.168.1.218"  # Device IP address

try:
    device = initialize_device(device_ip)
    get_chip_id(device)
    get_readout_status(device)
    get_comm_status(device)
    get_temperatures(device)
    perform_digital_test(device)
    get_adc_voltage(device)
finally:
    finalize_device(device)
