import ctypes
from cdevice_ctypes import KatherineDevice
from cconfig_ctypes import KatherineConfig, KatherineAcquisitionMode, KatherineReadoutType

# Load the shared library
lib_path = "libkatherine.so"  # Adjust the path as needed
katherine_lib = ctypes.CDLL(lib_path)

# Define structures
class KatherineCoord(ctypes.Structure):
    _fields_ = [("x", ctypes.c_uint8),
                ("y", ctypes.c_uint8)]

class KatherinePxFToaTot(ctypes.Structure):
    _fields_ = [("coord", KatherineCoord),
                ("ftoa", ctypes.c_uint8),
                ("toa", ctypes.c_uint64),
                ("tot", ctypes.c_uint16)]

class KatherinePxToaTot(ctypes.Structure):
    _fields_ = [("coord", KatherineCoord),
                ("toa", ctypes.c_uint64),
                ("hit_count", ctypes.c_uint8),
                ("tot", ctypes.c_uint16)]

class KatherinePxFToaOnly(ctypes.Structure):
    _fields_ = [("coord", KatherineCoord),
                ("ftoa", ctypes.c_uint8),
                ("toa", ctypes.c_uint64)]

class KatherinePxToaOnly(ctypes.Structure):
    _fields_ = [("coord", KatherineCoord),
                ("toa", ctypes.c_uint64),
                ("hit_count", ctypes.c_uint8)]

class KatherinePxFEventItot(ctypes.Structure):
    _fields_ = [("coord", KatherineCoord),
                ("hit_count", ctypes.c_uint8),
                ("event_count", ctypes.c_uint16),
                ("integral_tot", ctypes.c_uint16)]

class KatherinePxEventItot(ctypes.Structure):
    _fields_ = [("coord", KatherineCoord),
                ("event_count", ctypes.c_uint16),
                ("integral_tot", ctypes.c_uint16)]

class KatherineFrameInfoTimeSplit(ctypes.Structure):
    _fields_ = [("msb", ctypes.c_uint32),
                ("lsb", ctypes.c_uint32)]

class KatherineFrameInfoTime(ctypes.Union):
    _fields_ = [("b", KatherineFrameInfoTimeSplit),
                ("d", ctypes.c_uint64)]

class KatherineFrameInfo(ctypes.Structure):
    _fields_ = [("received_pixels", ctypes.c_uint64),
                ("sent_pixels", ctypes.c_uint64),
                ("lost_pixels", ctypes.c_uint64),
                ("start_time", KatherineFrameInfoTime),
                ("end_time", KatherineFrameInfoTime),
                ("start_time_observed", ctypes.c_time_t),
                ("end_time_observed", ctypes.c_time_t)]

class KatherineAcquisitionHandlers(ctypes.Structure):
    _fields_ = [
        ("pixels_received", ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t)),
        ("frame_started", ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int)),
        ("frame_ended", ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int, ctypes.c_bool, ctypes.POINTER(KatherineFrameInfo))),
        ("data_received", ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t))
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

# Define enums
class KatherineReadoutType(ctypes.c_int):
    READOUT_SEQUENTIAL = 0
    READOUT_DATA_DRIVEN = 1

class KatherineAcquisitionState(ctypes.c_int):
    ACQUISITION_NOT_STARTED = 0
    ACQUISITION_RUNNING = 1
    ACQUISITION_SUCCEEDED = 2
    ACQUISITION_TIMED_OUT = 3

# Define function prototypes
katherine_acquisition_init = katherine_lib.katherine_acquisition_init
katherine_acquisition_init.argtypes = [ctypes.POINTER(KatherineAcquisition), ctypes.POINTER(KatherineDevice), ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_int, ctypes.c_int]
katherine_acquisition_init.restype = ctypes.c_int

katherine_acquisition_begin = katherine_lib.katherine_acquisition_begin
katherine_acquisition_begin.argtypes = [
    ctypes.POINTER(KatherineAcquisition),
    ctypes.POINTER(KatherineConfig),
    ctypes.c_char,
    ctypes.c_int,
    ctypes.c_bool,
    ctypes.c_bool
]
katherine_acquisition_begin.restype = ctypes.c_int

katherine_acquisition_abort = katherine_lib.katherine_acquisition_abort
katherine_acquisition_abort.argtypes = [ctypes.POINTER(KatherineAcquisition)]
katherine_acquisition_abort.restype = ctypes.c_int

katherine_acquisition_read = katherine_lib.katherine_acquisition_read
katherine_acquisition_read.argtypes = [ctypes.POINTER(KatherineAcquisition)]
katherine_acquisition_read.restype = ctypes.c_int

katherine_acquisition_fini = katherine_lib.katherine_acquisition_fini
katherine_acquisition_fini.argtypes = [ctypes.POINTER(KatherineAcquisition)]
katherine_acquisition_fini.restype = None

# Python wrapper for acquisition
class Acquisition:
    def __init__(self, device, md_buffer_size, pixel_buffer_size, report_timeout, fail_timeout):
        self._acquisition = KatherineAcquisition()
        print("Initializing acquisition...")

        # Initialize buffers
        self._acquisition.md_buffer = (ctypes.c_char * md_buffer_size)()
        self._acquisition.pixel_buffer = (ctypes.c_char * pixel_buffer_size)()

        # Initialize handlers
        self._acquisition.handlers = KatherineAcquisitionHandlers(
            pixels_received=ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t)(self.pixels_received),
            frame_started=ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int)(self.frame_started),
            frame_ended=ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int, ctypes.c_bool, ctypes.POINTER(KatherineFrameInfo))(self.frame_ended),
            data_received=ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t)(self.data_received)
        )

        res = katherine_acquisition_init(ctypes.byref(self._acquisition), ctypes.byref(device._device), None, md_buffer_size, pixel_buffer_size, report_timeout, fail_timeout)
        if res != 0:
            print(f"Failed to initialize acquisition: {res}")
            raise RuntimeError(f"Failed to initialize acquisition: {res}")
        print("Acquisition initialized successfully!")

    def begin(self, config, readout_type, acq_mode, fast_vco_enabled, decode_data=True):
        print("Starting acquisition...")
        res = katherine_acquisition_begin(
            ctypes.byref(self._acquisition),
            config.get_c_config(),  # Pass the underlying C structure
            readout_type.value,
            acq_mode.value,
            fast_vco_enabled,
            decode_data
        )
        if res != 0:
            print(f"Failed to start acquisition: {res}")
            raise RuntimeError(f"Failed to start acquisition: {res}")
        print("Acquisition started successfully!")

    def pixels_received(self, user_ctx, pixel_buffer, pixel_count):
        print(f"Pixels received: {pixel_count}")

    def frame_started(self, user_ctx, frame_index):
        print(f"Frame started: {frame_index}")

    def frame_ended(self, user_ctx, frame_index, aborted, frame_info):
        print(f"Frame ended: {frame_index}, aborted: {aborted}")

    def data_received(self, user_ctx, data, size):
        print(f"Data received: {size} bytes")

    def read(self):
        print("Reading acquisition data...")
        res = katherine_acquisition_read(ctypes.byref(self._acquisition))
        if res != 0:
            print(f"Failed to read acquisition data: {res}")
            raise RuntimeError(f"Failed to read acquisition data: {res}")
        print("Acquisition data read successfully!")

    def abort(self):
        print("Aborting acquisition...")
        res = katherine_acquisition_abort(ctypes.byref(self._acquisition))
        if res != 0:
            print(f"Failed to abort acquisition: {res}")
            raise RuntimeError(f"Failed to abort acquisition: {res}")
        print("Acquisition aborted successfully!")

    def __del__(self):
        if hasattr(self, "_acquisition"):
            print("Finalizing acquisition...")
            katherine_acquisition_fini(ctypes.byref(self._acquisition))
            print("Acquisition finalized successfully!")