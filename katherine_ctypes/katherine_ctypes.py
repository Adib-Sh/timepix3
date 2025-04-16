# katherine_ctypes.py
from timeit import default_timer as timer
from cdevice_ctypes import Device
from cstatus_ctypes import Status
from cconfig_ctypes import Config, KatherineAcquisitionMode, KatherineReadoutType, KatherineTrigger, KatherineDacs
from cacquisition_ctypes import Acquisition
from cpx_config_ctypes import KatherinePxConfig

# Example usage
if __name__ == "__main__":
    try:
        # Initialize device
        device = Device("192.168.1.218")

        # Create Status object
        status = Status(device)

        # Get chip ID
        chip_id = status.get_chip_id()
        print(f"Chip ID: {chip_id}")

        # Get readout status
        readout_status = status.get_readout_status()

        # Get communication status
        comm_status = status.get_comm_status()

        # Get temperatures
        readout_temp, sensor_temp = status.get_temperatures()

        # Perform digital test
        status.perform_digital_test()

        # Get ADC voltage
        adc_voltage = status.get_adc_voltage(channel_id=0)

        config = Config()
        config.bias_id = 0
        config.acq_time = 10e9  # 10 seconds in nanoseconds
        config.no_frames = 1
        config.bias = 230  # 230 V
        config.delayed_start = False
        config.start_trigger.enabled = False
        config.stop_trigger.enabled = False
        config.gray_disable = False
        config.polarity_holes = False
        config.phase = 1  # Example value, adjust as needed
        config.freq = 40  # Example value, adjust as needed

        # Load BMC file
        bmc_file_path = "chipconfig.bmc"  # Path to your BMC file
        config.load_bmc_file(bmc_file_path)
        print("BMC file loaded successfully!")

        print("Config object created successfully!")

        # Create Acquisition object
        acquisition = Acquisition(device, md_buffer_size=34952533 * 6, pixel_buffer_size=65536 * 8, report_timeout=500, fail_timeout=10000)
        print("Acquisition object created successfully!")

        # Start acquisition
        acquisition.begin(
            config,
            readout_type=KatherineReadoutType.READOUT_DATA_DRIVEN,  # Use the enum value
            acq_mode=KatherineAcquisitionMode.TOA_TOT,  # Use the enum value
            fast_vco_enabled=True,
            decode_data=True  # Added decode_data parameter
        )
        print("Acquisition started!")

        # Read acquisition data
        acquisition.read()
        print("Acquisition data read!")

        # Abort acquisition
        acquisition.abort()
        print("Acquisition aborted!")

        # Explicitly finalize the device
        del device
        print("Device explicitly finalized.")
    except Exception as e:
        print(f"Error: {e}")