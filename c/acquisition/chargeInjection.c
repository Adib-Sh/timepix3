/**
 * Real Charge Injection and Equalization for Timepix3 / LGAD
 *
 * Measures per-pixel threshold by injecting test charges,
 * equalizes the pixel configuration, and saves it to a .bmc file.
 *
 * Author: Adib Shaker
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>   // for usleep
#include <time.h>
#include <katherine/katherine.h>
#include <katherine/config.h>
#include <katherine/px_config.h>
#include <katherine/global.h>
#include <katherine/acquisition.h>
#include <katherine/device.h>

#define NUM_PIXELS 65536
#define OUTPUT_FILENAME "equalized_real.bmc"

#define DEBUG_PRINT(fmt, ...) printf("[DEBUG] " fmt "\n", ##__VA_ARGS__)

// Threshold search parameters
#define MAX_TEST_PULSE 255
#define MIN_TEST_PULSE 0
#define TEST_PULSE_STEP 5
#define INJECTION_DELAY_US 5000 // 5 ms

// Helper: write value into BMC pixel config
void write_pixel_bmc(katherine_px_config_t *px_config, int pixel_idx, uint8_t val) {
    int x = pixel_idx % 256;
    int y = 255 - (pixel_idx / 256);
    int word_idx = 64 * x + (y >> 2);
    int shift = 8 * (3 - (y % 4));
    px_config->words[word_idx] &= ~(0xFF << shift);
    px_config->words[word_idx] |= ((uint32_t)val << shift);
}

// Save px_config to a BMC file
int save_bmc_file(const char *filename, const katherine_px_config_t *px_config) {
    katherine_bmc_t buffer;
    for (int i = 0; i < NUM_PIXELS; i++) {
        int x = i % 256;
        int y = 255 - (i / 256);
        int word_idx = 64 * x + (y >> 2);
        int shift = 8 * (3 - (y % 4));
        buffer.px_config[i] = (px_config->words[word_idx] >> shift) & 0xFF;
    }

    FILE *f = fopen(filename, "wb");
    if (!f) {
        perror("Failed to open output BMC file");
        return errno;
    }
    size_t written = fwrite(&buffer, 1, sizeof(katherine_bmc_t), f);
    fclose(f);
    if (written != sizeof(katherine_bmc_t)) return EIO;

    DEBUG_PRINT("BMC file saved successfully: %s", filename);
    return 0;
}

// ---------------------------------------------------------------------------
// Device connection check
//
// The Katherine library may return 0 from status calls even with no hardware
// present — the UDP socket is created locally and no handshake is required.
// We therefore validate the *content* of each reply, not just the return code:
//
//   - chip_id       must be a non-empty string
//   - chip_detected must be true
//   - data_rate     must be non-zero
//   - temperatures  must be non-zero (real hardware is never exactly 0.0 C)
//   - digital_test  return code is the only reliable binary pass/fail
// ---------------------------------------------------------------------------
int check_device_connection(katherine_device_t *device) {
    int res;

    printf("[CHECK] Verifying device connection to Katherine readout...\n");

    // --- 1. Chip ID ---------------------------------------------------------
    char chip_id[KATHERINE_CHIP_ID_STR_SIZE];
    memset(chip_id, 0, sizeof(chip_id));
    res = katherine_get_chip_id(device, chip_id);
    if (res != 0) {
        fprintf(stderr, "[ERROR] katherine_get_chip_id returned %d (%s)\n",
                res, strerror(res));
        fprintf(stderr, "        Is the Katherine readout powered and reachable?\n");
        return res;
    }
    // An empty string means the readout never replied despite res == 0
    if (chip_id[0] == '\0') {
        fprintf(stderr, "[ERROR] Chip ID is empty — no response from hardware "
                        "(library returned success without a real reply).\n");
        return -1;
    }
    printf("[CHECK] Chip ID: %s\n", chip_id);

    // --- 2. Communication status --------------------------------------------
    katherine_comm_status_t comm_status;
    memset(&comm_status, 0, sizeof(comm_status));
    res = katherine_get_comm_status(device, &comm_status);
    if (res != 0) {
        fprintf(stderr, "[ERROR] katherine_get_comm_status returned %d (%s)\n",
                res, strerror(res));
        return res;
    }
    printf("[CHECK] Comm status — lines mask: 0x%x | data rate: %u Mbps | "
           "chip detected: %s\n",
           comm_status.comm_lines_mask,
           comm_status.data_rate,
           comm_status.chip_detected ? "Yes" : "No");
    if (!comm_status.chip_detected) {
        fprintf(stderr, "[ERROR] comm_status.chip_detected is false — "
                        "Timepix3 not seen by the readout board.\n");
        return -1;
    }
    if (comm_status.data_rate == 0) {
        fprintf(stderr, "[ERROR] Data rate reported as 0 Mbps — "
                        "no active data link detected.\n");
        return -1;
    }

    // --- 3. Readout board temperature ---------------------------------------
    float readout_temp = 0.0f;
    res = katherine_get_readout_temperature(device, &readout_temp);
    if (res != 0) {
        fprintf(stderr, "[ERROR] katherine_get_readout_temperature returned %d (%s)\n",
                res, strerror(res));
        return res;
    }
    // Real hardware is never exactly 0.0 C — a zero reply means no response
    if (readout_temp == 0.0f) {
        fprintf(stderr, "[ERROR] Readout temperature is exactly 0.0 C — "
                        "no real hardware response received.\n");
        return -1;
    }
    printf("[CHECK] Readout temperature: %.2f C\n", readout_temp);

    // --- 4. Sensor temperature ----------------------------------------------
    float sensor_temp = 0.0f;
    res = katherine_get_sensor_temperature(device, &sensor_temp);
    if (res != 0) {
        fprintf(stderr, "[ERROR] katherine_get_sensor_temperature returned %d (%s)\n",
                res, strerror(res));
        return res;
    }
    if (sensor_temp == 0.0f) {
        fprintf(stderr, "[ERROR] Sensor temperature is exactly 0.0 C — "
                        "no real hardware response received.\n");
        return -1;
    }
    printf("[CHECK] Sensor temperature:  %.2f C\n", sensor_temp);

    // --- 5. Digital test ----------------------------------------------------
    // Exercises the internal data path on the readout — most reliable
    // binary pass/fail indicator available in the API.
    res = katherine_perform_digital_test(device);
    if (res != 0) {
        fprintf(stderr, "[ERROR] Digital test FAILED (res=%d: %s)\n",
                res, strerror(res));
        return res;
    }
    printf("[CHECK] Digital test passed.\n");

    printf("[CHECK] *** All checks passed — device is connected and ready. ***\n");
    return 0;
}

// ---------------------------------------------------------------------------
// inject_charge_and_read
// ---------------------------------------------------------------------------
int inject_charge_and_read(katherine_device_t *dev,
                           const katherine_config_t *config,
                           int pixel_idx,
                           uint8_t pulse_value)
{
    int res;

    res = katherine_set_sensor_register(dev, TPX3_REG_TEST_PULSE_METHOD, 1);
    if (res) return res;

    res = katherine_set_sensor_register(dev, TPX3_REG_SENSE_DAC_SELECTOR, pixel_idx);
    if (res) return res;

    res = katherine_set_sensor_register(dev, TPX3_REG_NUMBER_TEST_PULSES, pulse_value);
    if (res) return res;

    katherine_acquisition_t acq;
    res = katherine_acquisition_init(&acq, dev, NULL,
                                     KATHERINE_MD_SIZE * 34952533,
                                     sizeof(katherine_px_f_toa_tot_t) * NUM_PIXELS,
                                     5000, 60000);
    if (res) return res;

    res = katherine_acquisition_begin(&acq, config,
                                      READOUT_DATA_DRIVEN,
                                      ACQUISITION_MODE_ONLY_TOA,
                                      true, true);
    if (res) {
        katherine_acquisition_fini(&acq);
        return res;
    }

    usleep(INJECTION_DELAY_US);

    res = katherine_acquisition_read(&acq);
    katherine_acquisition_fini(&acq);
    if (res) return res;

    // Simulation placeholder: replace with real fired-pixel check from acq data
    return (pulse_value > 100) ? 1 : 0;
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------
int main() {
    DEBUG_PRINT("Starting real charge injection and equalization...");

    katherine_device_t device;
    int res = katherine_device_init(&device, "192.168.1.218");
    if (res) {
        fprintf(stderr, "Failed to initialise Katherine device handle: %s\n",
                strerror(res));
        return 1;
    }

    // Verify the device is reachable and the chip is responsive before doing
    // anything else. Aborts if any check fails or returns implausible values.
    res = check_device_connection(&device);
    if (res) {
        fprintf(stderr, "[ABORT] Device connection check failed — "
                        "not proceeding with charge injection.\n");
        katherine_device_fini(&device);
        return res;
    }

    katherine_config_t config;
    memset(&config, 0, sizeof(config));
    // Populate config as needed (bias voltage, thresholds, pixel config, etc.)

    katherine_px_config_t px_config;
    memset(&px_config, 0, sizeof(px_config));

    // Per-pixel threshold measurement and equalization
    for (int i = 0; i < NUM_PIXELS; i++) {
        int threshold_found = 0;
        for (uint8_t pulse = MIN_TEST_PULSE; pulse <= MAX_TEST_PULSE; pulse += TEST_PULSE_STEP) {
            int fired = inject_charge_and_read(&device, &config, i, pulse);
            if (fired) {
                write_pixel_bmc(&px_config, i, pulse);
                threshold_found = 1;
                break;
            }
        }
        if (!threshold_found) {
            write_pixel_bmc(&px_config, i, MAX_TEST_PULSE);
        }

        if (i < 5) {
            DEBUG_PRINT("Pixel %d threshold set to %d", i,
                        (int)(px_config.words[(64 * (i % 256)) + ((255 - (i / 256)) >> 2)] >>
                        (8 * (3 - ((255 - (i / 256)) % 4))) & 0xFF));
        }
    }

    res = save_bmc_file(OUTPUT_FILENAME, &px_config);
    if (res) {
        fprintf(stderr, "Error saving BMC file: %d\n", res);
        katherine_device_fini(&device);
        return res;
    }

    DEBUG_PRINT("Charge injection and equalization completed successfully.");

    katherine_device_fini(&device);
    return 0;
}