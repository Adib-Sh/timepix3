import ctypes

# Load the shared library
lib_path = "/home/adisha/git/libkatherine/build/libkatherine.so"  # Adjust the path as needed
katherine_lib = ctypes.CDLL(lib_path)

# Define the katherine_device_t structure
class KatherineDevice(ctypes.Structure):
    _fields_ = []  # Opaque structure, no fields are exposed

# Define function prototypes
katherine_device_init = katherine_lib.katherine_device_init
katherine_device_init.argtypes = [ctypes.POINTER(KatherineDevice), ctypes.c_char_p]
katherine_device_init.restype = ctypes.c_int

katherine_device_fini = katherine_lib.katherine_device_fini
katherine_device_fini.argtypes = [ctypes.POINTER(KatherineDevice)]
katherine_device_fini.restype = None

# Python wrapper for the device
class Device:
    def __init__(self, addr):
        self._device = KatherineDevice()
        print(f"Initializing device with address: {addr}")
        res = katherine_device_init(ctypes.byref(self._device), addr.encode())
        if res != 0:
            print(f"Failed to initialize device: {res}")
            raise OSError(f"Failed to initialize device: {res}")
        print("Device initialized successfully!")

    def __del__(self):
        if hasattr(self, "_device"):
            print("Finalizing device")
            katherine_device_fini(ctypes.byref(self._device))
            print("Device finalized successfully!")