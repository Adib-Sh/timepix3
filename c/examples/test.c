#include <stdio.h>      // printf, sprintf
#include <string.h>     // strchr
#include <stdlib.h>     // abort
#include <katherine/katherine.h>
#include <katherine/status.h>
#include <katherine/device.h>

static const char *address = "192.168.1.218";

static void log_timestamp(const char *message) {
    time_t rawtime;
    struct tm *timeinfo;
    char buffer[80];

    time(&rawtime);
    timeinfo = localtime(&rawtime);

    strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", timeinfo);
    printf("[%s] %s\n", buffer, message);
}

static void display_device_status(katherine_device_t *device) {
    katherine_readout_status_t readout_status;
    katherine_comm_status_t comm_status;
    float readout_temp, sensor_temp;

    int res = katherine_get_readout_status(device, &readout_status);
    if (res == 0) {
        printf("Readout Status: HW Type: %d, HW Revision: %d, Serial: %d, FW Version: %d\n",
               readout_status.hw_type, readout_status.hw_revision, readout_status.hw_serial_number,
               readout_status.fw_version);
    } else {
        printf("Error retrieving readout status.\n");
    }

    res = katherine_get_comm_status(device, &comm_status);
    if (res == 0) {
        printf("Comm Status: Line Mask: 0x%x, Data Rate: %.2f, Chip Detected: %d\n",
               comm_status.comm_lines_mask, comm_status.data_rate, comm_status.chip_detected);
    } else {
        printf("Error retrieving communication status.\n");
    }

    res = katherine_get_readout_temperature(device, &readout_temp);
    if (res == 0) {
        printf("Readout Temperature: %.2f °C\n", readout_temp);
    } else {
        printf("Error retrieving readout temperature.\n");
    }

    res = katherine_get_sensor_temperature(device, &sensor_temp);
    if (res == 0) {
        printf("Sensor Temperature: %.2f °C\n", sensor_temp);
    } else {
        printf("Error retrieving sensor temperature.\n");
    }

    res = katherine_perform_digital_test(device);
    if (res == 0) {
        printf("Digital test passed.\n");
    } else {
        printf("Digital test failed.\n");
    }
}

int main() {
    log_timestamp("Starting status test");

    int res;
    katherine_device_t device;

    // Initialize device with the specific IP address
    res = katherine_device_init(&device, address);
    if (res) {
        printf("Failed to initialize device at address %s.\n", address);
        return 1;
    }

    // Display the device status
    display_device_status(&device);

    // Clean up and finalize the device connection
    katherine_device_fini(&device);

    log_timestamp("Status test completed");

    return 0;
}
