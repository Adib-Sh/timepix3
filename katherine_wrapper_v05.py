import ctypes
from ctypes import CFUNCTYPE, c_void_p, c_char_p, c_size_t, c_int, c_bool
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
    """Get the chip ID of the device"""
    chip_id = ctypes.create_string_buffer(16)
    result = libkatherine.katherine_get_chip_id(ctypes.byref(device), chip_id)
    if result == 0:
        return chip_id.value.decode()
    raise RuntimeError(f"Failed to get chip ID. Error code: {result}")


# Function to get readout status
def get_readout_status(device):
    """Get the readout status of the device"""
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
    """Finalize the Katherine device"""
    result = libkatherine.katherine_device_fini(ctypes.byref(device))
    if result != 0:
        raise RuntimeError(f"Error closing device connection! Error code: {result}")
    print("Device connection closed successfully.")



class KatherineTrigger(ctypes.Structure):
    """Representation of katherine_trigger_t"""
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


class KatherineBmcPixel(ctypes.Structure):
    """Representation of katherine_bmc_px_t"""
    _fields_ = [
        ('value', ctypes.c_ubyte)
    ]

class KatherineBmc(ctypes.Structure):
    """Representation of katherine_bmc_t"""
    _fields_ = [('px_config', KatherineBmcPixel * 65536)]

class KatherineBpcPixel(ctypes.Structure):
    """Representation of katherine_bpc_px_t"""
    _fields_ = [('value', ctypes.c_ubyte)]

class KatherineBpc(ctypes.Structure):
    """Representation of katherine_bpc_t"""
    _fields_ = [('px_config', KatherineBpcPixel * 65536)]


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

class KatherineDACs(ctypes.Union):
    """Representation of katherine_dacs_t (Union with array and named fields)"""
    _fields_ = [
        ('array', ctypes.c_uint16 * 18),
        ('named', KatherineDacsNamed)
    ]
    
class KatherinePixelConfig(ctypes.Structure):
    """Representation of katherine_px_config_t"""
    _fields_ = [('words', ctypes.c_uint32 * 16384)]

    def load_bmc_file(self, file_path):
        """Load BMC configuration from a file"""
        result = libkatherine.katherine_px_config_load_bmc_file(ctypes.byref(self), file_path.encode('utf-8'))
        if result != 0:
            raise RuntimeError(f"Failed to load BMC file. Error code: {result}")
    
    def load_bmc_data(self, bmc):
        """Load BMC configuration from a KatherineBmc instance"""
        if not isinstance(bmc, KatherineBmc):
            raise TypeError("bmc must be an instance of KatherineBmc")
        result = libkatherine.katherine_px_config_load_bmc_data(ctypes.byref(self), ctypes.byref(bmc))
        if result != 0:
            raise RuntimeError(f"Failed to load BMC data. Error code: {result}")
    
    def load_bpc_file(self, file_path):
        """Load BPC configuration from a file"""
        result = libkatherine.katherine_px_config_load_bpc_file(ctypes.byref(self), file_path.encode('utf-8'))
        if result != 0:
            raise RuntimeError(f"Failed to load BPC file. Error code: {result}")
    
    def load_bpc_data(self, bpc):
        """Load BPC configuration from a KatherineBpc instance"""
        if not isinstance(bpc, KatherineBpc):
            raise TypeError("bpc must be an instance of KatherineBpc")
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

# Define the acquisition handlers
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
    for i in range(count):
        pixel = pixels[i]
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

    
class KatherineConfig(ctypes.Structure):
    """Python representation of katherine_config_t structure"""
    _fields_ = [
        ('pixel_config', KatherinePixelConfig),
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
        ("handlers", KatherineAcquisitionHandlers),  # Valid ctypes.Structure
        ("current_frame_info", KatherineFrameInfo),  # Valid ctypes.Structure
        ("last_toa_offset", ctypes.c_uint64)
    ]


def run_acquisition(device, config):
    # Initialize the acquisition structure
    acq = KatherineAcquisition()
    result = libkatherine.katherine_acquisition_init(ctypes.byref(acq), ctypes.byref(device), None, 1024 * 1024, 65536, 500, 10000)
    if result != 0:
        raise RuntimeError(f"Failed to initialize acquisition. Error code: {result}")
    print("Acquisition initialized.")

    # Set the handlers
    handlers = KatherineAcquisitionHandlers()
    handlers.pixels_received = PIXELS_RECEIVED_FUNC(lambda *args: print("Pixels received"))
    handlers.frame_started = FRAME_STARTED_FUNC(lambda *args: print("Frame started"))
    handlers.frame_ended = FRAME_ENDED_FUNC(lambda *args: print("Frame ended"))
    handlers.data_received = DATA_RECEIVED_FUNC(lambda *args: print("Data received"))

    acq.handlers = handlers

    # Begin the acquisition
    result = libkatherine.katherine_acquisition_begin(ctypes.byref(acq), ctypes.byref(config), READOUT_DATA_DRIVEN, ACQUISITION_MODE_TOA_TOT, True, True)
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
    finally:
        finalize_device(device)





