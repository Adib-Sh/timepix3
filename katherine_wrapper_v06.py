import ctypes
from ctypes import CFUNCTYPE, c_void_p, c_char_p, c_size_t, c_int, c_bool, c_float, c_ubyte, c_uint16, c_uint32, c_uint64, c_double, c_char
import os
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

class KatherineBMC(ctypes.Structure):
    _fields_ = [("px_config", ctypes.c_ubyte * 65536)]

class KatherineBPC(ctypes.Structure):
    _fields_ = [("px_config", ctypes.c_ubyte * 65536)]

class KatherinePxConfig(ctypes.Structure):
    _fields_ = [("words", ctypes.c_uint32 * 16384)]

    def load_bmc_file(self, file_path):
        result = libkatherine.katherine_px_config_load_bmc_file(ctypes.byref(self), file_path.encode('utf-8'))
        if result != 0:
            raise RuntimeError(f"Failed to load BMC file. Error code: {result}")

    def load_bmc_data(self, bmc):
        if not isinstance(bmc, KatherineBMC):
            raise TypeError("bmc must be an instance of KatherineBMC")
        result = libkatherine.katherine_px_config_load_bmc_data(ctypes.byref(self), ctypes.byref(bmc))
        if result != 0:
            raise RuntimeError(f"Failed to load BMC data. Error code: {result}")

    def load_bpc_file(self, file_path):
        result = libkatherine.katherine_px_config_load_bpc_file(ctypes.byref(self), file_path.encode('utf-8'))
        if result != 0:
            raise RuntimeError(f"Failed to load BPC file. Error code: {result}")

    def load_bpc_data(self, bpc):
        if not isinstance(bpc, KatherineBPC):
            raise TypeError("bpc must be an instance of KatherineBPC")
        result = libkatherine.katherine_px_config_load_bpc_data(ctypes.byref(self), ctypes.byref(bpc))
        if result != 0:
            raise RuntimeError(f"Failed to load BPC data. Error code: {result}")

class KatherineFrameInfoTimeSplit(ctypes.Structure):
    _fields_ = [
        ("msb", ctypes.c_uint32),
        ("lsb", ctypes.c_uint32)
    ]

class KatherineFrameInfoTime(ctypes.Union):
    _fields_ = [
        ("b", KatherineFrameInfoTimeSplit),
        ("d", ctypes.c_uint64)
    ]

class KatherineFrameInfo(ctypes.Structure):
    _fields_ = [
        ("received_pixels", ctypes.c_uint64),
        ("sent_pixels", ctypes.c_uint64),
        ("lost_pixels", ctypes.c_uint64),
        ("start_time", KatherineFrameInfoTime),
        ("end_time", KatherineFrameInfoTime),
        ("start_time_observed", ctypes.c_time_t),
        ("end_time_observed", ctypes.c_time_t)
    ]

# Define the function types for the handlers
PIXELS_RECEIVED_FUNC = CFUNCTYPE(None, c_void_p, c_void_p, c_size_t)
FRAME_STARTED_FUNC = CFUNCTYPE(None, c_void_p, c_int)
FRAME_ENDED_FUNC = CFUNCTYPE(None, c_void_p, c_int, c_bool, c_void_p)
DATA_RECEIVED_FUNC = CFUNCTYPE(None, c_void_p, c_char_p, c_size_t)

# Define the acquisition handlers structure
class KatherineAcquisitionHandlers(ctypes.Structure):
    _fields_ = [
        ("pixels_received", PIXELS_RECEIVED_FUNC),
        ("frame_started", FRAME_STARTED_FUNC),
        ("frame_ended", FRAME_ENDED_FUNC),
        ("data_received", DATA_RECEIVED_FUNC)
    ]

class KatherineAcquisition(ctypes.Structure):
    _fields_ = [
        ("device", ctypes.POINTER(KatherineDevice)),
        ("user_ctx", ctypes.c_void_p),
        ("state", ctypes.c_char),
        ("aborted", ctypes.c_bool),
        ("readout_mode", ctypes.c_char),
        ("acq_mode", ctypes.c_char),
        ("fast_vco_enabled", ctypes.c_bool),
        ("md_buffer", ctypes.POINTER(ctypes.c_char)),
        ("md_buffer_size", ctypes.c_size_t),
        ("decode_data", ctypes.c_bool),
        ("pixel_buffer", ctypes.POINTER(ctypes.c_char)),
        ("pixel_buffer_size", ctypes.c_size_t),
        ("pixel_buffer_valid", ctypes.c_size_t),
        ("pixel_buffer_max_valid", ctypes.c_size_t),
        ("requested_frames", ctypes.c_int),
        ("requested_frame_duration", ctypes.c_double),
        ("completed_frames", ctypes.c_int),
        ("dropped_measurement_data", ctypes.c_size_t),
        ("acq_start_time", ctypes.c_time_t),
        ("report_timeout", ctypes.c_int),
        ("fail_timeout", ctypes.c_int),
        ("handlers", KatherineAcquisitionHandlers),
        ("current_frame_info", KatherineFrameInfo),
        ("last_toa_offset", ctypes.c_uint64)
    ]

# Default handler functions
def default_pixels_received(user_ctx, pixels, count):
    print(f"Received {count} pixels.")
    pixel_array = ctypes.cast(pixels, ctypes.POINTER(ctypes.c_uint64))
    for i in range(count):
        pixel = pixel_array[i]
        print(f"Pixel {i}: {pixel}")

def default_frame_started(user_ctx, frame_idx):
    print(f"Frame {frame_idx} started.")

def default_frame_ended(user_ctx, frame_idx, completed, frame_info):
    print(f"Frame {frame_idx} ended.")
    if completed:
        print("Frame completed successfully.")
    else:
        print("Frame did not complete.")
    print(f"Received pixels: {frame_info.received_pixels}")
    print(f"Sent pixels: {frame_info.sent_pixels}")
    print(f"Lost pixels: {frame_info.lost_pixels}")
    print(f"Start time: {frame_info.start_time}")
    print(f"End time: {frame_info.end_time}")

def default_data_received(user_ctx, data, size):
    print(f"Received {size} bytes of raw data.")

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
        return chip_id.value.decode()
    raise RuntimeError(f"Failed to get chip ID. Error code: {result}")

# Function to get readout status
def get_readout_status(device):
    readout_status = KatherineReadoutStatus()
    result = libkatherine.katherine_get_readout_status(ctypes.byref(device), ctypes.byref(readout_status))
    if result != 0:
        raise RuntimeError(f"Failed to get readout status. Error code: {result}")
    return readout_status

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
    if result != 0:
        raise RuntimeError(f"Error closing device connection! Error code: {result}")
    print("Device connection closed successfully.")

class KatherineTrigger(ctypes.Structure):
    _fields_ = [
        ('enabled', ctypes.c_bool),
        ('channel', ctypes.c_char),
        ('use_falling_edge', ctypes.c_bool)
    ]

    def __init__(self):
        super().__init__()
        self.enabled = False
        self.channel = 0
        self.use_falling_edge = False

class KatherinePhase(IntEnum):
    PHASE_1 = 0
    PHASE_2 = 1
    PHASE_4 = 2
    PHASE_8 = 3
    PHASE_16 = 4

class KatherineFreq(IntEnum):
    FREQ_40 = 1
    FREQ_80 = 2
    FREQ_160 = 3

class KatherineDacsNamed(ctypes.Structure):
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

class KatherineDACs(ctypes.Union):
    _fields_ = [
        ('array', ctypes.c_uint16 * 18),
        ('named', KatherineDacsNamed)
    ]

class KatherineConfig(ctypes.Structure):
    _fields_ = [
        ('pixel_config', KatherinePxConfig),
        ('bias_id', ctypes.c_ubyte),
        ('acq_time', ctypes.c_double),  # ns
        ('no_frames', ctypes.c_int),
        ('bias', ctypes.c_float),
        ('start_trigger', KatherineTrigger),
        ('delayed_start', ctypes.c_bool),
        ('stop_trigger', KatherineTrigger),
        ('gray_disable', ctypes.c_bool),
        ('polarity_holes', ctypes.c_bool),
        ('phase', ctypes.c_int),
        ('freq', ctypes.c_int),
        ('dacs', KatherineDACs)
    ]

    def __init__(self):
        super().__init__()
        self.bias_id = 0
        self.acq_time = 1000.0  # 1 microsecond default
        self.no_frames = 1
        self.bias = 0.0
        self.start_trigger = KatherineTrigger()
        self.delayed_start = False
        self.stop_trigger = KatherineTrigger()
        self.gray_disable = False
        self.polarity_holes = False
        self.phase = KatherinePhase.PHASE_1
        self.freq = KatherineFreq.FREQ_40
        self.dacs = KatherineDACs()

# Define constants for readout mode
READOUT_SEQUENTIAL = 0
READOUT_DATA_DRIVEN = 1

# Define constants for acquisition mode
ACQUISITION_MODE_TOA_TOT = 0  # Time-of-Arrival and Time-over-Threshold
ACQUISITION_MODE_ONLY_TOA = 1  # Only Time-of-Arrival
ACQUISITION_MODE_EVENT_ITOT = 2  # Event-driven Time-over-Threshold

def run_acquisition(device, config):
    # Initialize the acquisition structure
    acq = KatherineAcquisition()
    result = libkatherine.katherine_acquisition_init(ctypes.byref(acq), ctypes.byref(device), None, 1024 * 1024, 65536, 500, 10000)
    if result != 0:
        raise RuntimeError(f"Failed to initialize acquisition. Error code: {result}")
    print("Acquisition initialized.")

    # Set the handlers
    handlers = KatherineAcquisitionHandlers()
    handlers.pixels_received = PIXELS_RECEIVED_FUNC(default_pixels_received)
    handlers.frame_started = FRAME_STARTED_FUNC(default_frame_started)
    handlers.frame_ended = FRAME_ENDED_FUNC(default_frame_ended)
    handlers.data_received = DATA_RECEIVED_FUNC(default_data_received)

    acq.handlers = handlers

    # Begin the acquisition
    result = libkatherine.katherine_acquisition_begin(
        ctypes.byref(acq), 
        ctypes.byref(config), 
        READOUT_DATA_DRIVEN,  # Use the defined constant
        ACQUISITION_MODE_TOA_TOT,  # Use the defined constant
        True,  # fast_vco_enabled
        True   # decode_data
    )
    if result != 0:
        raise RuntimeError(f"Failed to begin acquisition. Error code: {result}")
    print("Acquisition started.")

    # Read acquisition data
    result = libkatherine.katherine_acquisition_read(ctypes.byref(acq))
    if result != 0:
        raise RuntimeError(f"Failed to read acquisition data. Error code: {result}")

    # Print acquisition results
    print("\nAcquisition completed:")
    print(f" - state: {libkatherine.katherine_str_acquisition_status(acq.state)}")
    print(f" - received {acq.completed_frames} complete frames")
    print(f" - dropped {acq.dropped_measurement_data} measurement data")

    # Finalize the acquisition
    libkatherine.katherine_acquisition_fini(ctypes.byref(acq))

# Main logic
if __name__ == "__main__":
    device_ip = b"192.168.1.218"  # Device IP address
    bmc_file_path = './chipconfig.bmc'
    device = None  # Initialize device to None

    try:
        device = initialize_device(device_ip)
        # Create and configure device settings
        config = KatherineConfig()
        config.pixel_config.load_bmc_file(bmc_file_path)

        # Set DAC values (as in the C example)
        config.dacs.named.Ibias_Preamp_ON = 128
        config.dacs.named.Ibias_Preamp_OFF = 8
        config.dacs.named.VPReamp_NCAS = 128
        config.dacs.named.Ibias_Ikrum = 15
        config.dacs.named.Vfbk = 164
        config.dacs.named.Vthreshold_fine = 476
        config.dacs.named.Vthreshold_coarse = 8
        config.dacs.named.Ibias_DiscS1_ON = 100
        config.dacs.named.Ibias_DiscS1_OFF = 8
        config.dacs.named.Ibias_DiscS2_ON = 128
        config.dacs.named.Ibias_DiscS2_OFF = 8
        config.dacs.named.Ibias_PixelDAC = 128
        config.dacs.named.Ibias_TPbufferIn = 128
        config.dacs.named.Ibias_TPbufferOut = 128
        config.dacs.named.VTP_coarse = 128
        config.dacs.named.VTP_fine = 256
        config.dacs.named.Ibias_CP_PLL = 128
        config.dacs.named.PLL_Vcntrl = 128

        # Set other configuration parameters
        config.bias_id = 0
        config.acq_time = 10e9  # 10 seconds in nanoseconds
        config.no_frames = 1
        config.bias = 230.0  # 230 V
        config.delayed_start = False
        config.start_trigger.enabled = False
        config.start_trigger.channel = 0
        config.start_trigger.use_falling_edge = False
        config.stop_trigger.enabled = False
        config.stop_trigger.channel = 0
        config.stop_trigger.use_falling_edge = False
        config.gray_disable = False
        config.polarity_holes = False
        config.phase = KatherinePhase.PHASE_1
        config.freq = KatherineFreq.FREQ_40

        chip_id = get_chip_id(device)
        print(f"Device Serial Number (Chip ID): {chip_id}")
        get_readout_status(device)
        get_comm_status(device)
        get_temperatures(device)
        perform_digital_test(device)
        get_adc_voltage(device)

        run_acquisition(device, config)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if device is not None:  # Check if device is defined before finalizing
            finalize_device(device)