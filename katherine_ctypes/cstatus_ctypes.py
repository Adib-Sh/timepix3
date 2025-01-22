import ctypes
from cdevice_ctypes import KatherineDevice  # Import KatherineDevice

# Load the shared library
lib_path = "libkatherine.so"  # Adjust the path as needed
katherine_lib = ctypes.CDLL(lib_path)

# Define structures
class KatherineReadoutStatus(ctypes.Structure):
    _fields_ = []  # Opaque structure, no fields are exposed

class KatherineCommStatus(ctypes.Structure):
    _fields_ = [
        ("comm_lines_mask", ctypes.c_uint32),
        ("data_rate", ctypes.c_float),
        ("chip_detected", ctypes.c_bool),
    ]

# Define function prototypes
katherine_get_chip_id = katherine_lib.katherine_get_chip_id
katherine_get_chip_id.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.c_char_p]
katherine_get_chip_id.restype = ctypes.c_int

katherine_get_readout_status = katherine_lib.katherine_get_readout_status
katherine_get_readout_status.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.POINTER(KatherineReadoutStatus)]
katherine_get_readout_status.restype = ctypes.c_int

katherine_get_comm_status = katherine_lib.katherine_get_comm_status
katherine_get_comm_status.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.POINTER(KatherineCommStatus)]
katherine_get_comm_status.restype = ctypes.c_int

katherine_get_readout_temperature = katherine_lib.katherine_get_readout_temperature
katherine_get_readout_temperature.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.POINTER(ctypes.c_float)]
katherine_get_readout_temperature.restype = ctypes.c_int

katherine_get_sensor_temperature = katherine_lib.katherine_get_sensor_temperature
katherine_get_sensor_temperature.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.POINTER(ctypes.c_float)]
katherine_get_sensor_temperature.restype = ctypes.c_int

katherine_perform_digital_test = katherine_lib.katherine_perform_digital_test
katherine_perform_digital_test.argtypes = [ctypes.POINTER(KatherineDevice)]
katherine_perform_digital_test.restype = ctypes.c_int

katherine_get_adc_voltage = katherine_lib.katherine_get_adc_voltage
katherine_get_adc_voltage.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.c_ubyte, ctypes.POINTER(ctypes.c_float)]
katherine_get_adc_voltage.restype = ctypes.c_int

# Python wrapper for status
class Status:
    def __init__(self, device):
        self._device = device
        print("Status object created successfully!")

    def get_chip_id(self):
        print("Attempting to retrieve chip ID...")
        chip_id = ctypes.create_string_buffer(16)  # Buffer size of 16
        result = katherine_get_chip_id(ctypes.byref(self._device._device), chip_id)
        if result == 0:
            print("Chip ID retrieved successfully!")
            return chip_id.value.decode()
        print(f"Failed to get chip ID. Error code: {result}")
        raise RuntimeError(f"Failed to get chip ID. Error code: {result}")

    def get_readout_status(self):
        print("Attempting to retrieve readout status...")
        readout_status = KatherineReadoutStatus()
        result = katherine_get_readout_status(ctypes.byref(self._device._device), ctypes.byref(readout_status))
        if result != 0:
            print(f"Failed to get readout status. Error code: {result}")
            raise RuntimeError(f"Failed to get readout status. Error code: {result}")
        print("Readout status retrieved successfully!")
        return readout_status

    def get_comm_status(self):
        print("Attempting to retrieve communication status...")
        comm_status = KatherineCommStatus()
        result = katherine_get_comm_status(ctypes.byref(self._device._device), ctypes.byref(comm_status))
        if result == 0:
            print(f"Comm Status: Comm Lines Mask {comm_status.comm_lines_mask}, Data Rate {comm_status.data_rate}, "
                  f"Chip Detected {comm_status.chip_detected}")
            return comm_status
        print(f"Failed to get communication status. Error code: {result}")
        raise RuntimeError(f"Failed to get communication status. Error code: {result}")

    def get_temperatures(self):
        print("Attempting to retrieve temperatures...")
        readout_temp = ctypes.c_float()
        sensor_temp = ctypes.c_float()

        result = katherine_get_readout_temperature(ctypes.byref(self._device._device), ctypes.byref(readout_temp))
        if result == 0:
            print(f"Readout Temperature: {readout_temp.value} °C")
        else:
            print("Error retrieving readout temperature.")

        result = katherine_get_sensor_temperature(ctypes.byref(self._device._device), ctypes.byref(sensor_temp))
        if result == 0:
            print(f"Sensor Temperature: {sensor_temp.value} °C")
        else:
            print("Error retrieving sensor temperature.")

        return readout_temp.value, sensor_temp.value

    def perform_digital_test(self):
        print("Performing digital test...")
        result = katherine_perform_digital_test(ctypes.byref(self._device._device))
        if result == 0:
            print("Digital test passed.")
        else:
            print("Digital test failed.")
        return result

    def get_adc_voltage(self, channel_id=0):
        print(f"Attempting to retrieve ADC voltage for channel {channel_id}...")
        adc_voltage = ctypes.c_float()
        result = katherine_get_adc_voltage(ctypes.byref(self._device._device), channel_id, ctypes.byref(adc_voltage))
        if result == 0:
            print(f"ADC Voltage: {adc_voltage.value} V")
            return adc_voltage.value
        print(f"Failed to get ADC voltage. Error code: {result}")
        raise RuntimeError(f"Failed to get ADC voltage. Error code: {result}")