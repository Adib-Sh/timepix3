import ctypes
from pathlib import Path
from enum import Enum
import numpy as np

class FileFormat(Enum):
    BMC = "bmc"  # BurdaMan format
    BPC = "bpc"  # Pixet format

class KatherinePixelConfig:
    def __init__(self):
        # 65536 bytes for 256x256 pixel configuration
        self.words = (ctypes.c_uint32 * (65536 // 4))()
    
    @property
    def array(self) -> np.ndarray:
        """Convert the pixel configuration to a 256x256 numpy array."""
        # Create a view of the raw buffer as bytes
        raw_bytes = (ctypes.c_uint8 * 65536).from_buffer(self.words)
        return np.frombuffer(raw_bytes, dtype=np.uint8).reshape(256, 256)

class PixelConfigLoader:
    """Python wrapper for Katherine pixel configuration loading."""
    
    def __init__(self):
        self.px_config = KatherinePixelConfig()
    
    def load_file(self, file_path: str | Path, format: FileFormat) -> np.ndarray:
        """
        Load pixel configuration from a file.
        
        Args:
            file_path: Path to the configuration file
            format: File format (BMC or BPC)
            
        Returns:
            numpy.ndarray: 256x256 array containing the pixel configuration
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file size is incorrect
            IOError: If there's an error reading the file
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        expected_size = 65536  # Both formats use 256x256 pixels
        
        try:
            with open(file_path, "rb") as f:
                data = f.read()
                if len(data) != expected_size:
                    raise ValueError(
                        f"Invalid file size. Expected {expected_size} bytes, "
                        f"got {len(data)} bytes"
                    )
                
                # Reset pixel configuration
                ctypes.memset(self.px_config.words, 0, 65536)
                
                if format == FileFormat.BMC:
                    self._load_bmc_data(data)
                else:
                    self._load_bpc_data(data)
                    
                return self.px_config.array
                
        except IOError as e:
            raise IOError(f"Error reading file: {e}")
    
    def _load_bmc_data(self, data: bytes):
        """Load BurdaMan format data."""
        dest = (ctypes.c_uint32 * (65536 // 4)).from_buffer_copy(self.px_config.words)
        
        for i in range(65536):
            x = i % 256
            y = 255 - i // 256
            dest[(64 * x) + (y >> 2)] |= data[i] << (8 * (3 - (y % 4)))
            
        # Copy back to pixel config
        ctypes.memmove(self.px_config.words, dest, 65536)
    
    def _load_bpc_data(self, data: bytes):
        """Load Pixet format data."""
        dest = (ctypes.c_uint32 * (65536 // 4)).from_buffer_copy(self.px_config.words)
        reverse_array = bytes([0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15])
        
        for i in range(65536):
            y = i // 256
            x = i % 256
            val = (data[i] & 0x21) | (reverse_array[((data[i] & 0x1E) >> 1)] << 1)
            
            y = 255 - y
            dest[(64 * x) + (y >> 2)] |= val << (8 * (3 - (y % 4)))
            
        # Copy back to pixel config
        ctypes.memmove(self.px_config.words, dest, 65536)

if __name__ == "__main__":
    loader = PixelConfigLoader()
    try:
        config = loader.load_file("chipconfig.bmc", FileFormat.BMC)
        print(f"Standalone test: Configuration loaded successfully {config.shape}")
    except Exception as e:
        print(f"Standalone test failed: {e}")