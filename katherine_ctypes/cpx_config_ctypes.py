import ctypes

# Load the shared library
lib_path = "/home/adisha/git/libkatherine/build/libkatherine.so"  # Adjust the path as needed
libkatherine = ctypes.CDLL(lib_path)

# Define the KatherineBMC and KatherineBPC structures
class KatherineBMC(ctypes.Structure):
    _fields_ = [("px_config", ctypes.c_uint8 * 65536)]

class KatherineBPC(ctypes.Structure):
    _fields_ = [("px_config", ctypes.c_uint8 * 65536)]

# Define the KatherinePxConfig class
class KatherinePxConfig(ctypes.Structure):
    _fields_ = [("words", ctypes.c_uint32 * 16384)]

    def load_bmc_file(self, file_path):
        """
        Load pixel configuration from a BMC file.
        :param file_path: Path to the BMC file.
        """
        result = libkatherine.katherine_px_config_load_bmc_file(ctypes.byref(self), file_path.encode('utf-8'))
        if result != 0:
            raise RuntimeError(f"Failed to load BMC file. Error code: {result}")

    def load_bmc_data(self, bmc):
        """
        Load pixel configuration from BMC data.
        :param bmc: An instance of KatherineBMC.
        """
        if not isinstance(bmc, KatherineBMC):
            raise TypeError("bmc must be an instance of KatherineBMC")
        result = libkatherine.katherine_px_config_load_bmc_data(ctypes.byref(self), ctypes.byref(bmc))
        if result != 0:
            raise RuntimeError(f"Failed to load BMC data. Error code: {result}")

    def load_bpc_file(self, file_path):
        """
        Load pixel configuration from a BPC file.
        :param file_path: Path to the BPC file.
        """
        result = libkatherine.katherine_px_config_load_bpc_file(ctypes.byref(self), file_path.encode('utf-8'))
        if result != 0:
            raise RuntimeError(f"Failed to load BPC file. Error code: {result}")

    def load_bpc_data(self, bpc):
        """
        Load pixel configuration from BPC data.
        :param bpc: An instance of KatherineBPC.
        """
        if not isinstance(bpc, KatherineBPC):
            raise TypeError("bpc must be an instance of KatherineBPC")
        result = libkatherine.katherine_px_config_load_bpc_data(ctypes.byref(self), ctypes.byref(bpc))
        if result != 0:
            raise RuntimeError(f"Failed to load BPC data. Error code: {result}")