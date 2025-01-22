import ctypes
from typing import List, Optional, Union


# Load the shared library
libkatherine = ctypes.CDLL('./build/libkatherine.so')


# Define C types and structures that are used in the functions

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


class KatherineDacs(ctypes.Union):
    _fields_ = [
        ("array", ctypes.c_uint16 * 18),
        ("named", KatherineDacsNamed)
    ]


class KatherineConfig(ctypes.Structure):
    _fields_ = [
        ("pixel_config", ctypes.POINTER(ctypes.c_void_p)),  # Placeholder for pixel config struct
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
        ("dacs", KatherineDacs)
    ]


class KatherineDevice:
    def __init__(self, device_pointer: ctypes.POINTER(ctypes.c_void_p)):
        self.device = device_pointer

    def configure(self, config: KatherineConfig) -> int:
        return libkatherine.katherine_configure(self.device, ctypes.byref(config))

    def set_all_pixel_config(self, px_config: ctypes.POINTER(ctypes.c_void_p)) -> int:
        return libkatherine.katherine_set_all_pixel_config(self.device, px_config)

    def set_acq_time(self, ns: float) -> int:
        return libkatherine.katherine_set_acq_time(self.device, ns)

    def set_acq_mode(self, acq_mode: int, fast_vco_enabled: bool) -> int:
        return libkatherine.katherine_set_acq_mode(self.device, acq_mode, fast_vco_enabled)

    def set_no_frames(self, no_frames: int) -> int:
        return libkatherine.katherine_set_no_frames(self.device, no_frames)

    def set_bias(self, bias_id: int, bias_value: float) -> int:
        return libkatherine.katherine_set_bias(self.device, bias_id, bias_value)

    def set_seq_readout_start(self, arg: int) -> int:
        return libkatherine.katherine_set_seq_readout_start(self.device, arg)

    def acquisition_setup(self, start_trigger: KatherineTrigger, delayed_start: bool, end_trigger: KatherineTrigger) -> int:
        return libkatherine.katherine_acquisition_setup(self.device, ctypes.byref(start_trigger), delayed_start, ctypes.byref(end_trigger))

    def set_sensor_register(self, reg_idx: int, reg_value: int) -> int:
        return libkatherine.katherine_set_sensor_register(self.device, reg_idx, reg_value)

    def update_sensor_registers(self) -> int:
        return libkatherine.katherine_update_sensor_registers(self.device)

    def output_block_config_update(self) -> int:
        return libkatherine.katherine_output_block_config_update(self.device)

    def timer_set(self) -> int:
        return libkatherine.katherine_timer_set(self.device)

    def set_dacs(self, dacs: KatherineDacs) -> int:
        return libkatherine.katherine_set_dacs(self.device, ctypes.byref(dacs))