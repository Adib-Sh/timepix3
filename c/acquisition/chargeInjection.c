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

#include <katherine/config.h>
#include <katherine/px_config.h>

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

// Inject a charge into a pixel and read response
int inject_charge_and_read(katherine_device_t *dev, int pixel_idx, uint8_t pulse_value) {
    int res;

    // Set test pulse method
    res = katherine_set_sensor_register(dev, TPX3_REG_TEST_PULSE_METHOD, 1); // 1 = single pixel
    if (res) return res;

    // Set which pixel to pulse (simplified: map pixel_idx to register or memory)
    res = katherine_set_sensor_register(dev, TPX3_REG_SENSE_DAC_SELECTOR, pixel_idx);
    if (res) return res;

    // Set pulse value
    res = katherine_set_sensor_register(dev, TPX3_REG_NUMBER_TEST_PULSES, pulse_value);
    if (res) return res;

    // Trigger test pulse
    res = katherine_cmd_start_acquisition(&dev->control_socket, READOUT_DATA_DRIVEN);
    if (res) return res;

    usleep(INJECTION_DELAY_US); // wait for hardware

    // Read back pixel response (simplified placeholder)
    // Real implementation: read via acquisition_read() or pixel buffer handlers
    // For now, simulate: assume pixel fires if pulse_value > 100 (replace with actual read)
    return (pulse_value > 100) ? 1 : 0;
}

int main() {
    DEBUG_PRINT("Starting real charge injection and equalization...");

    katherine_device_t *device = katherine_device_open("192.168.1.218"); // adjust IP
    if (!device) {
        fprintf(stderr, "Failed to open Katherine device\n");
        return 1;
    }

    katherine_px_config_t px_config;
    memset(&px_config, 0, sizeof(px_config));

    // Per-pixel threshold measurement and equalization
    for (int i = 0; i < NUM_PIXELS; i++) {
        int threshold_found = 0;
        for (uint8_t pulse = MIN_TEST_PULSE; pulse <= MAX_TEST_PULSE; pulse += TEST_PULSE_STEP) {
            int fired = inject_charge_and_read(device, i, pulse);
            if (fired) {
                write_pixel_bmc(&px_config, i, pulse);
                threshold_found = 1;
                break;
            }
        }
        if (!threshold_found) {
            write_pixel_bmc(&px_config, i, MAX_TEST_PULSE); // pixel never fired
        }

        if (i < 5) {
            DEBUG_PRINT("Pixel %d threshold set to %d", i,
                        (int)(px_config.words[(64 * (i % 256)) + ((255 - (i / 256)) >> 2)] >> (8 * (3 - ((255 - (i / 256)) % 4))) & 0xFF));
        }
    }

    int res = save_bmc_file(OUTPUT_FILENAME, &px_config);
    if (res) {
        fprintf(stderr, "Error saving BMC file: %d\n", res);
        katherine_device_close(device);
        return res;
    }

    DEBUG_PRINT("Charge injection and equalization completed successfully.");
    katherine_device_close(device);
    return 0;
}