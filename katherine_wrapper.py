import ctypes
import os
import time

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

# Define the function prototypes
libkatherine.katherine_device_init.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.c_char_p]
libkatherine.katherine_device_init.restype = ctypes.c_int

# Chip ID
libkatherine.katherine_get_chip_id.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.c_char_p]
libkatherine.katherine_get_chip_id.restype = ctypes.c_int

# Get status
libkatherine.katherine_get_readout_status.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.POINTER(ctypes.c_int)]
libkatherine.katherine_get_readout_status.restype = ctypes.c_int
# Get communications status
libkatherine.katherine_get_comm_status.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.POINTER(ctypes.c_int)]
libkatherine.katherine_get_comm_status.restype = ctypes.c_int
# Get readout temperature
libkatherine.katherine_get_readout_temperature.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.POINTER(ctypes.c_float)]
libkatherine.katherine_get_readout_temperature.restype = ctypes.c_int
# Get sensor temperature
libkatherine.katherine_get_sensor_temperature.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.POINTER(ctypes.c_float)]
libkatherine.katherine_get_sensor_temperature.restype = ctypes.c_int
# Digital test
libkatherine.katherine_perform_digital_test.argtypes = [ctypes.POINTER(KatherineDevice)]
libkatherine.katherine_perform_digital_test.restype = ctypes.c_int

# Connect to the device
device = KatherineDevice()
device_ip = b"192.168.1.218"  # Device IP address

# Initialize the device
result = libkatherine.katherine_device_init(ctypes.byref(device), device_ip)
if result != 0:
    print(f"Failed to initialize device!")
else:
    print("Device initialized successfully.")

    # Get the chip ID 
    chip_id = ctypes.create_string_buffer(16)
    result = libkatherine.katherine_get_chip_id(ctypes.byref(device), chip_id)
    if result == 0:
        print(f"Device Serial Number (Chip ID): {chip_id.value.decode()}")
    else:
        print(f"Failed to get chip ID. Error code: {result}")

    # Get Readout Status
    readout_status = ctypes.c_int()
    result = libkatherine.katherine_get_readout_status(ctypes.byref(device), ctypes.byref(readout_status))
    if result == 0:
        print(f"Readout Status: {readout_status.value}")
    else:
        print("Error retrieving readout status.")

    # Get Comm Status
    comm_status = ctypes.c_int()
    result = libkatherine.katherine_get_comm_status(ctypes.byref(device), ctypes.byref(comm_status))
    if result == 0:
        print(f"Comm Status: {comm_status.value}")
    else:
        print("Error retrieving communication status.")

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

    # Perform Digital Test
    result = libkatherine.katherine_perform_digital_test(ctypes.byref(device))
    if result == 0:
        print("Digital test passed.")
    else:
        print("Digital test failed.")

# Clean up and finalize the device connection
libkatherine.katherine_device_fini(ctypes.byref(device))
