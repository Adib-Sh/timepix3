import ctypes
from enum import IntEnum
from cpx_config_ctypes import KatherinePxConfig

# Load the shared library
lib_path = "/home/adisha/git/libkatherine/build/libkatherine.so"  # Adjust the path as needed
katherine_lib = ctypes.CDLL(lib_path)

# Define structures
class KatherineTrigger(ctypes.Structure):
    _fields_ = [("enabled", ctypes.c_bool),
                ("channel", ctypes.c_char),
                ("use_falling_edge", ctypes.c_bool)]

class KatherineDacs(ctypes.Structure):
    _fields_ = [("array", ctypes.c_uint16 * 18)]

class KatherineConfig(ctypes.Structure):
    _fields_ = [("pixel_config", ctypes.c_void_p),  # Use c_void_p for pixel_config
                ("bias_id", ctypes.c_ubyte),
                ("acq_time", ctypes.c_double),
                ("no_frames", ctypes.c_int),
                ("bias", ctypes.c_float),
                ("start_trigger", KatherineTrigger),
                ("delayed_start", ctypes.c_bool),
                ("stop_trigger", KatherineTrigger),
                ("gray_disable", ctypes.c_bool),
                ("polarity_holes", ctypes.c_bool),
                ("phase", ctypes.c_int),
                ("freq", ctypes.c_int),
                ("dacs", KatherineDacs)]

# Define enums
class KatherineAcquisitionMode(IntEnum):
    TOA_TOT = 0
    ONLY_TOA = 1
    EVENT_ITOT = 2

class KatherineReadoutType(IntEnum):
    READOUT_SEQUENTIAL = 0
    READOUT_DATA_DRIVEN = 1

# Python wrapper for configuration
class Config:
    def __init__(self):
        self._config = KatherineConfig()
        self._px_config = KatherinePxConfig()  # Store the pixel config separately
        self._config.pixel_config = ctypes.cast(ctypes.pointer(self._px_config), ctypes.c_void_p)  # Cast to c_void_p

    @property
    def bias_id(self):
        return self._config.bias_id

    @bias_id.setter
    def bias_id(self, value):
        self._config.bias_id = value

    @property
    def acq_time(self):
        return self._config.acq_time

    @acq_time.setter
    def acq_time(self, value):
        self._config.acq_time = value

    @property
    def no_frames(self):
        return self._config.no_frames

    @no_frames.setter
    def no_frames(self, value):
        self._config.no_frames = value

    @property
    def bias(self):
        return self._config.bias

    @bias.setter
    def bias(self, value):
        self._config.bias = value

    @property
    def delayed_start(self):
        return self._config.delayed_start

    @delayed_start.setter
    def delayed_start(self, value):
        self._config.delayed_start = value

    @property
    def start_trigger(self):
        return self._config.start_trigger

    @property
    def stop_trigger(self):
        return self._config.stop_trigger

    @property
    def gray_disable(self):
        return self._config.gray_disable

    @gray_disable.setter
    def gray_disable(self, value):
        self._config.gray_disable = value

    @property
    def polarity_holes(self):
        return self._config.polarity_holes

    @polarity_holes.setter
    def polarity_holes(self, value):
        self._config.polarity_holes = value

    @property
    def phase(self):
        return self._config.phase

    @phase.setter
    def phase(self, value):
        self._config.phase = value

    @property
    def freq(self):
        return self._config.freq

    @freq.setter
    def freq(self, value):
        self._config.freq = value

    @property
    def dacs(self):
        return self._config.dacs

    def load_bmc_file(self, file_path):
        """
        Load pixel configuration from a BMC file.
        :param file_path: Path to the BMC file.
        """
        self._px_config.load_bmc_file(file_path)

    def get_c_config(self):
        """
        Get the underlying C structure (KatherineConfig).
        :return: A pointer to the KatherineConfig structure.
        """
        return ctypes.byref(self._config)