/**
 * chargeInjection_step1.c
 *
 * Step 1 of the High-Low THL equalization pipeline.
 *
 * Purpose:
 *   Inject a SINGLE fixed charge into ALL pixels simultaneously and record
 *   which pixels respond. Results are saved to:
 *     - injection_result.bmc  : pixel config used (trim=7 + test-enable on
 *                               all pixels) — serves as the neutral baseline
 *                               config for subsequent equalization steps.
 *     - injection_result.txt  : human-readable hit map: total counts, list of
 *                               fired pixels (x, y, hit_count), and a summary.
 *
 * Tunable parameters (top of file):
 *   INJECT_VTP_FINE        — test pulse amplitude   (0–511)
 *   INJECT_VTHRESHOLD_FINE — global discriminator threshold (0–511)
 *   INJECT_NUM_PULSES      — how many pulses to fire per acquisition
 *
 * All other logic (device init, callbacks, BMC helpers) is unchanged from
 * chargeInjection.c so this file slots cleanly into the existing build.
 *
 * Author: Adib Shaker
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
/* No <math.h> dependency — isqrt() used instead to avoid linking -lm */
#include <katherine/katherine.h>
#include <katherine/config.h>
#include <katherine/px_config.h>
#include <katherine/global.h>
#include <katherine/acquisition.h>
#include <katherine/device.h>

/* =========================================================================
 * Pixel type
 * ====================================================================== */
typedef katherine_px_f_toa_tot_t px_t;

/* =========================================================================
 * *** TUNABLE PARAMETERS — adjust these before each run ***
 * ====================================================================== */
#define INJECT_VTP_FINE          500   /* Test pulse amplitude    (0–511)  */
#define INJECT_VTHRESHOLD_FINE   0   /* Global threshold THL    (0–511)  */
#define INJECT_VTHRESHOLD_COARSE   0   /* Coarse threshold — usually fixed */
#define INJECT_NUM_PULSES        10000   /* Pulses fired per acquisition     */

/* =========================================================================
 * Constants
 * ====================================================================== */
static const char *REMOTE_ADDR = "192.168.1.218";

#define SENSOR_WIDTH    256
#define SENSOR_HEIGHT   256
#define NUM_PIXELS      (SENSOR_WIDTH * SENSOR_HEIGHT)   /* 65 536 */

#define NEUTRAL_TRIM    1    /* Midpoint of 4-bit trim range (0–15).
                              * Gives equal headroom for correction in both
                              * directions during later equalization steps. */

#define OUTPUT_BMC_FILE  "injection_result.bmc"
#define OUTPUT_TXT_FILE  "injection_result.txt"

/* Acquisition buffer sizes */
#define ACQ_MD_SLOTS    (KATHERINE_MD_SIZE * 4096)
#define ACQ_PIXEL_SLOTS (sizeof(px_t) * NUM_PIXELS * 2)

/* Wait after acquisition_begin before reading — lets pulses propagate */
#define INJECTION_DELAY_US  5000   /* 5 ms */

#define DEBUG_PRINT(fmt, ...) printf("[DEBUG] " fmt "\n", ##__VA_ARGS__)

/* =========================================================================
 * Global hit map — written by pixels_received(), cleared before each run.
 * ====================================================================== */
static uint64_t g_hit_map[SENSOR_HEIGHT][SENSOR_WIDTH];

/* Forward declaration */
void write_pixel_bmc(katherine_px_config_t *px_config, int pixel_idx, uint8_t val);
uint8_t read_pixel_bmc(const katherine_px_config_t *px_config, int pixel_idx);

/* =========================================================================
 * Callbacks
 * ====================================================================== */

void frame_started(void *user_ctx, int frame_idx)
{
    printf("  [ACQ] Frame %d started.\n", frame_idx);
}

void frame_ended(void *user_ctx, int frame_idx, bool completed,
                 const katherine_frame_info_t *info)
{
    printf("  [ACQ] Frame %d ended — received: %lu  lost: %lu  state: %s\n",
           frame_idx,
           info->received_pixels,
           info->lost_pixels,
           completed ? "completed" : "not completed");
}

void pixels_received(void *user_ctx, const void *px, size_t count)
{
    const px_t *dpx = (const px_t *)px;
    for (size_t i = 0; i < count; i++) {
        int x = dpx[i].coord.x;
        int y = dpx[i].coord.y;
        if (x >= 0 && x < SENSOR_WIDTH && y >= 0 && y < SENSOR_HEIGHT) {
            g_hit_map[y][x]++;
        } else {
            printf("  [WARN] Out-of-bounds pixel: (%d, %d)\n", x, y);
        }
    }
}

/*
 * data_received — the library calls this for every raw UDP packet with NO
 * NULL check. Must be registered or acquisition_read() will segfault.
 * We discard the raw bytes — decoded pixels arrive via pixels_received().
 */
void data_received(void *user_ctx, const char *data, size_t size)
{
    (void)user_ctx; (void)data; (void)size;
}

/* =========================================================================
 * BMC helpers
 *
 * Pixel byte layout (8 bits):
 *   [7]   — unused
 *   [6]   — unused
 *   [5]   — test-enable  (1 = pixel receives test pulses)
 *   [4]   — mask         (1 = pixel is disabled / masked)
 *   [3:0] — trim value   (0–15)
 * ====================================================================== */

void write_pixel_bmc(katherine_px_config_t *px_config, int pixel_idx, uint8_t val)
{
    int col      = pixel_idx % 256;
    int row      = 255 - (pixel_idx / 256);
    int word_idx = 64 * col + (row >> 2);
    int shift    = 8 * (3 - (row % 4));
    px_config->words[word_idx] &= ~((uint32_t)0xFF << shift);
    px_config->words[word_idx] |=  ((uint32_t)val  << shift);
}

uint8_t read_pixel_bmc(const katherine_px_config_t *px_config, int pixel_idx)
{
    int col      = pixel_idx % 256;
    int row      = 255 - (pixel_idx / 256);
    int word_idx = 64 * col + (row >> 2);
    int shift    = 8 * (3 - (row % 4));
    return (uint8_t)((px_config->words[word_idx] >> shift) & 0xFF);
}

int save_bmc_file(const char *filename, const katherine_px_config_t *px_config)
{
    katherine_bmc_t buffer;
    for (int i = 0; i < NUM_PIXELS; i++) {
        buffer.px_config[i] = read_pixel_bmc(px_config, i);
    }
    FILE *f = fopen(filename, "wb");
    if (!f) { perror("[ERROR] Failed to open BMC file"); return errno; }
    size_t written = fwrite(&buffer, 1, sizeof(katherine_bmc_t), f);
    fclose(f);
    if (written != sizeof(katherine_bmc_t)) {
        fprintf(stderr, "[ERROR] Short write to %s\n", filename);
        return EIO;
    }
    printf("[OUT] BMC saved: %s\n", filename);
    return 0;
}

/* =========================================================================
 * isqrt — integer square root, no <math.h> / -lm required.
 * Returns floor(sqrt(n)) for any uint64_t n.
 * ====================================================================== */
static uint64_t isqrt(uint64_t n)
{
    if (n == 0) return 0;
    uint64_t x = n;
    uint64_t y = (x + 1) / 2;
    while (y < x) { x = y; y = (x + n / x) / 2; }
    return x;
}

/* =========================================================================
 * save_txt_file
 *
 * Writes a human-readable summary of the hit map to a .txt file:
 *   - Run parameters
 *   - Total fired pixels and total hit count
 *   - Per-pixel lines for every pixel that fired: X  Y  HITS
 *   - Pixels that did NOT fire are noted in the summary count only
 * ====================================================================== */
int save_txt_file(const char *filename, int vtp_fine, int vth_fine,
                  int vth_coarse, int num_pulses)
{
    FILE *f = fopen(filename, "w");
    if (!f) { perror("[ERROR] Failed to open TXT file"); return errno; }

    /* --- Header --------------------------------------------------------- */
    fprintf(f, "=============================================================\n");
    fprintf(f, "  Timepix3 / Katherine — Single Charge Injection Result\n");
    fprintf(f, "=============================================================\n");
    fprintf(f, "  VTP_fine             : %d\n", vtp_fine);
    fprintf(f, "  Vthreshold_fine      : %d\n", vth_fine);
    fprintf(f, "  Vthreshold_coarse    : %d\n", vth_coarse);
    fprintf(f, "  Number of pulses     : %d\n", num_pulses);
    fprintf(f, "  Trim (all pixels)    : %d (neutral midpoint)\n", NEUTRAL_TRIM);
    fprintf(f, "-------------------------------------------------------------\n\n");

    /* --- Count statistics ----------------------------------------------- */
    uint64_t total_hits   = 0;
    int      fired_pixels = 0;
    uint64_t max_hits     = 0;
    uint64_t min_hits_fired = UINT64_MAX;

    for (int y = 0; y < SENSOR_HEIGHT; y++) {
        for (int x = 0; x < SENSOR_WIDTH; x++) {
            uint64_t h = g_hit_map[y][x];
            if (h > 0) {
                fired_pixels++;
                total_hits += h;
                if (h > max_hits)        max_hits = h;
                if (h < min_hits_fired)  min_hits_fired = h;
            }
        }
    }

    /* Mean (integer: total_hits / fired_pixels) */
    uint64_t mean_hits = (fired_pixels > 0) ? (total_hits / (uint64_t)fired_pixels) : 0;

    /* Variance and std dev — computed in integer arithmetic, no -lm needed.
     * Uses sum of squared deviations from mean, divided by (n-1). */
    uint64_t sum_sq_diff = 0;
    if (fired_pixels > 1) {
        for (int y = 0; y < SENSOR_HEIGHT; y++) {
            for (int x = 0; x < SENSOR_WIDTH; x++) {
                uint64_t h = g_hit_map[y][x];
                if (h > 0) {
                    uint64_t diff = (h >= mean_hits) ? (h - mean_hits)
                                                     : (mean_hits - h);
                    sum_sq_diff += diff * diff;
                }
            }
        }
    }
    uint64_t variance  = (fired_pixels > 1) ? sum_sq_diff / (uint64_t)(fired_pixels - 1) : 0;
    uint64_t std_hits  = isqrt(variance);

    fprintf(f, "SUMMARY\n");
    fprintf(f, "  Total pixels         : %d\n",  NUM_PIXELS);
    fprintf(f, "  Fired pixels         : %d  (%.2f%%)\n",
            fired_pixels, 100.0 * fired_pixels / NUM_PIXELS);
    fprintf(f, "  Silent pixels        : %d  (%.2f%%)\n",
            NUM_PIXELS - fired_pixels,
            100.0 * (NUM_PIXELS - fired_pixels) / NUM_PIXELS);
    fprintf(f, "  Total hits           : %lu\n", (unsigned long)total_hits);
    if (fired_pixels > 0) {
        fprintf(f, "  Hit count per fired pixel:\n");
        fprintf(f, "    min  = %lu\n", (unsigned long)min_hits_fired);
        fprintf(f, "    max  = %lu\n", (unsigned long)max_hits);
        fprintf(f, "    mean = %lu  (integer)\n", (unsigned long)mean_hits);
        fprintf(f, "    std  = %lu  (integer floor)\n", (unsigned long)std_hits);
    }
    fprintf(f, "\n-------------------------------------------------------------\n");
    fprintf(f, "FIRED PIXELS  (X  Y  HITS)\n");
    fprintf(f, "-------------------------------------------------------------\n");

    /* --- Per-pixel fired list ------------------------------------------- */
    for (int y = 0; y < SENSOR_HEIGHT; y++) {
        for (int x = 0; x < SENSOR_WIDTH; x++) {
            if (g_hit_map[y][x] > 0) {
                fprintf(f, "%3d  %3d  %lu\n",
                        x, y, (unsigned long)g_hit_map[y][x]);
            }
        }
    }

    fprintf(f, "\n=============================================================\n");
    fprintf(f, "  END OF REPORT\n");
    fprintf(f, "=============================================================\n");

    fclose(f);
    printf("[OUT] TXT saved: %s\n", filename);
    return 0;
}

/* =========================================================================
 * configure
 *
 * Sets all DACs. All 65 536 pixels are configured with:
 *   - trim = NEUTRAL_TRIM (7) — midpoint, no correction applied yet
 *   - test-enable bit SET    — pixel receives internal test pulses
 *   - mask bit CLEAR         — pixel is active
 *
 * Pixel byte value = (1 << 5) | NEUTRAL_TRIM = 0x27
 * ====================================================================== */
void configure(katherine_config_t *config, int vtp_fine,
               int vthreshold_fine, int vthreshold_coarse)
{
    memset(config, 0, sizeof(*config));

    config->bias_id                          = 1;
    config->acq_time                         = 1e9;   /* 100 ms — confirmed (units: nanoseconds) */
    config->no_frames                        = 1;
    config->bias                             = 100;   /* sensor bias voltage */

    config->delayed_start                    = false;

    config->start_trigger.enabled            = false;
    config->start_trigger.channel            = 0;
    config->start_trigger.use_falling_edge   = false;
    config->stop_trigger.enabled             = false;
    config->stop_trigger.channel             = 0;
    config->stop_trigger.use_falling_edge    = false;

    config->gray_disable                     = true;
    config->polarity_holes                   = false;
    config->phase                            = PHASE_1;
    config->freq                             = FREQ_40;

    /* DAC values */
    config->dacs.named.Ibias_Preamp_ON       = 128;
    config->dacs.named.Ibias_Preamp_OFF      = 8;
    config->dacs.named.VPReamp_NCAS          = 128;
    config->dacs.named.Ibias_Ikrum           = 15;
    config->dacs.named.Vfbk                  = 164;
    config->dacs.named.Vthreshold_fine       = vthreshold_fine;
    config->dacs.named.Vthreshold_coarse     = vthreshold_coarse;
    config->dacs.named.Ibias_DiscS1_ON       = 100;
    config->dacs.named.Ibias_DiscS1_OFF      = 8;
    config->dacs.named.Ibias_DiscS2_ON       = 128;
    config->dacs.named.Ibias_DiscS2_OFF      = 8;
    config->dacs.named.Ibias_PixelDAC        = 100;
    config->dacs.named.Ibias_TPbufferIn      = 128;
    config->dacs.named.Ibias_TPbufferOut     = 128;
    config->dacs.named.VTP_coarse            = 128;
    config->dacs.named.VTP_fine              = vtp_fine;
    config->dacs.named.Ibias_CP_PLL          = 128;
    config->dacs.named.PLL_Vcntrl            = 128;

    /*
     * Per-pixel config: trim=7 + test-enable.
     *
     * Byte = (test_enable << 5) | trim
     *      = (1 << 5) | 7
     *      = 0x27
     *
     * This is the NEUTRAL baseline — equal trim headroom in both directions,
     * test pulse routing enabled for every pixel.
     */
    const uint8_t pixel_byte = (uint8_t)((1u << 5) | (NEUTRAL_TRIM & 0x0F));
    memset(&config->pixel_config, 0, sizeof(config->pixel_config));
    for (int i = 0; i < NUM_PIXELS; i++) {
        write_pixel_bmc(&config->pixel_config, i, pixel_byte);
    }

    printf("[CFG] VTP_fine=%d  Vth_fine=%d  Vth_coarse=%d  trim=%d (all pixels)\n",
           vtp_fine, vthreshold_fine, vthreshold_coarse, NEUTRAL_TRIM);
}

/* =========================================================================
 * Device info helpers
 * ====================================================================== */

void get_chip_id(katherine_device_t *device)
{
    char chip_id[KATHERINE_CHIP_ID_STR_SIZE];
    int res = katherine_get_chip_id(device, chip_id);
    if (res != 0) {
        printf("Cannot get chip ID.\nReason: %s\n", strerror(res)); exit(2);
    }
    printf("Chip ID: %s\n", chip_id);
}

void get_comm_status(katherine_device_t *device)
{
    katherine_comm_status_t s;
    int res = katherine_get_comm_status(device, &s);
    if (res != 0) {
        printf("Cannot get comm status.\nReason: %s\n", strerror(res)); exit(8);
    }
    printf("Comm Status: lines=0x%x  rate=%u Mbps  chip=%s\n",
           s.comm_lines_mask, s.data_rate, s.chip_detected ? "Yes" : "No");
}

void get_readout_temp(katherine_device_t *device)
{
    float t;
    int res = katherine_get_readout_temperature(device, &t);
    if (res != 0) {
        printf("Cannot get readout temperature.\nReason: %s\n", strerror(res)); exit(8);
    }
    printf("Readout temperature: %.2f C\n", t);
}

void get_sensor_temp(katherine_device_t *device)
{
    float t;
    int res = katherine_get_sensor_temperature(device, &t);
    if (res != 0) {
        printf("Cannot get sensor temperature.\nReason: %s\n", strerror(res)); exit(9);
    }
    printf("Sensor temperature: %.2f C\n", t);
}

void digital_test(katherine_device_t *device)
{
    int res = katherine_perform_digital_test(device);
    if (res != 0) {
        printf("Digital test failed!\nReason: %s\n", strerror(res)); exit(10);
    }
    printf("Digital test passed.\n");
}

void adc_voltage(katherine_device_t *device)
{
    float v;
    int res = katherine_get_adc_voltage(device, 0, &v);
    if (res != 0) {
        printf("ADC voltage test failed!\nReason: %s\n", strerror(res)); exit(11);
    }
    printf("ADC voltage: %.4f V\n", v);
}

/* =========================================================================
 * run_single_injection
 *
 * Fires a single fixed-charge injection burst at ALL pixels simultaneously
 * and records which pixels responded in g_hit_map[][].
 *
 * Steps:
 *   1. Configure chip (DACs + all-pixel trim=7/test-enable)
 *   2. Set TPX3_REG_TEST_PULSE_METHOD = 1  (internal generator)
 *   3. Set TPX3_REG_NUMBER_TEST_PULSES     (how many pulses to fire)
 *   4. Init acquisition handle (once)
 *   5. Begin acquisition with internal test pulse trigger
 *   6. Wait for pulses to propagate
 *   7. Read data → pixels_received() fills g_hit_map
 *   8. Fini acquisition handle
 * ====================================================================== */
int run_single_injection(katherine_device_t *device)
{
    printf("\n=== Single Charge Injection ===\n");
    printf("  VTP_fine             : %d\n", INJECT_VTP_FINE);
    printf("  Vthreshold_fine      : %d\n", INJECT_VTHRESHOLD_FINE);
    printf("  Vthreshold_coarse    : %d\n", INJECT_VTHRESHOLD_COARSE);
    printf("  Num pulses           : %d\n", INJECT_NUM_PULSES);
    printf("  Trim (all pixels)    : %d\n\n", NEUTRAL_TRIM);

    katherine_config_t config;
    configure(&config,
              INJECT_VTP_FINE,
              INJECT_VTHRESHOLD_FINE,
              INJECT_VTHRESHOLD_COARSE);

    int res;

    /* ------------------------------------------------------------------ *
     * NOTE: TPX3_REG_TEST_PULSE_METHOD and TPX3_REG_NUMBER_TEST_PULSES   *
     * are intentionally NOT written here.                                 *
     *                                                                     *
     * With the internal generator (method=1), writing                    *
     * TPX3_REG_NUMBER_TEST_PULSES arms and fires the pulses immediately.  *
     * If that happens before acquisition_begin(), the acquisition window  *
     * is not yet open and every hit is dropped.                           *
     *                                                                     *
     * Both register writes are deferred to after acquisition_begin()      *
     * so the pulses fire into an already-open window.                     *
     * ------------------------------------------------------------------ */

    /* --- Initialise acquisition handle ---------------------------------- */
    katherine_acquisition_t acq;
    res = katherine_acquisition_init(&acq, device, NULL,
                                     ACQ_MD_SLOTS,
                                     ACQ_PIXEL_SLOTS,
                                     500,    /* report period ms */
                                     30000); /* timeout ms       */
    if (res != 0) {
        fprintf(stderr, "[ERROR] katherine_acquisition_init: %s\n", strerror(res));
        return res;
    }

    memset(&acq.handlers, 0, sizeof(acq.handlers));
    acq.handlers.pixels_received = pixels_received;
    acq.handlers.frame_started   = frame_started;
    acq.handlers.frame_ended     = frame_ended;
    acq.handlers.data_received   = data_received;

    memset(g_hit_map, 0, sizeof(g_hit_map));

    /* --- Open the acquisition window first ------------------------------ */
    res = katherine_acquisition_begin(&acq, &config,
                                      READOUT_DATA_DRIVEN,
                                      ACQUISITION_MODE_TOA_TOT,
                                      false,
                                      true);
    if (res != 0) {
        fprintf(stderr, "[ERROR] katherine_acquisition_begin: %s\n", strerror(res));
        katherine_acquisition_fini(&acq);
        return res;
    }

    /* --- NOW arm the internal pulse generator — window is open ---------- *
     *                                                                      *
     * Order matters:                                                       *
     *   1. Set method=1 first   → selects internal generator              *
     *   2. Set pulse count      → this arms + fires the burst             *
     *                                                                      *
     * The 100 ms acq_time gives plenty of room for INJECT_NUM_PULSES      *
     * to complete before acquisition_read() drains the buffer.            *
     * ------------------------------------------------------------------  */
    res = katherine_set_sensor_register(device, TPX3_REG_TEST_PULSE_METHOD, 1);
    if (res != 0) {
        fprintf(stderr, "[ERROR] TPX3_REG_TEST_PULSE_METHOD: %s\n", strerror(res));
        katherine_acquisition_abort(&acq);
        katherine_acquisition_fini(&acq);
        return res;
    }

    res = katherine_set_sensor_register(device, TPX3_REG_NUMBER_TEST_PULSES,
                                        INJECT_NUM_PULSES);
    if (res != 0) {
        fprintf(stderr, "[ERROR] TPX3_REG_NUMBER_TEST_PULSES: %s\n", strerror(res));
        katherine_acquisition_abort(&acq);
        katherine_acquisition_fini(&acq);
        return res;
    }

    /* --- Wait for the burst to complete before draining the buffer ------ */
    printf("  Waiting %d µs for pulses to propagate...\n", INJECTION_DELAY_US);
    usleep(INJECTION_DELAY_US);

    /* --- Read data — pixels_received() fills g_hit_map ------------------ */
    res = katherine_acquisition_read(&acq);
    if (res != 0) {
        fprintf(stderr, "[ERROR] katherine_acquisition_read: %s\n", strerror(res));
        katherine_acquisition_fini(&acq);
        return res;
    }

    katherine_acquisition_fini(&acq);

    int fired = 0;
    uint64_t total_hits = 0;
    for (int y = 0; y < SENSOR_HEIGHT; y++) {
        for (int x = 0; x < SENSOR_WIDTH; x++) {
            if (g_hit_map[y][x] > 0) {
                fired++;
                total_hits += g_hit_map[y][x];
            }
        }
    }
    printf("\n[INJ] Done. Fired pixels: %d / %d  |  Total hits: %lu\n\n",
           fired, NUM_PIXELS, (unsigned long)total_hits);

    res = save_bmc_file(OUTPUT_BMC_FILE, &config.pixel_config);
    if (res != 0) {
        fprintf(stderr, "[ERROR] Failed to save BMC file.\n");
        return res;
    }

    res = save_txt_file(OUTPUT_TXT_FILE,
                        INJECT_VTP_FINE,
                        INJECT_VTHRESHOLD_FINE,
                        INJECT_VTHRESHOLD_COARSE,
                        INJECT_NUM_PULSES);
    if (res != 0) {
        fprintf(stderr, "[ERROR] Failed to save TXT file.\n");
        return res;
    }

    return 0;
}

/* =========================================================================
 * main
 * ====================================================================== */
int main(void)
{
    DEBUG_PRINT("chargeInjection_step1 starting...");

    int res;
    katherine_device_t device;

    /* Connection with retry */
    int retries = 3;
    while (retries > 0) {
        printf("Attempting to connect to %s...\n", REMOTE_ADDR);
        res = katherine_device_init(&device, REMOTE_ADDR);
        if (res == 0) break;
        printf("Connection failed: %s. Retrying... (%d left)\n",
               strerror(res), --retries);
        sleep(1);
    }
    if (res != 0) {
        fprintf(stderr, "[ERROR] Cannot connect after %d attempts.\n", 3);
        return 1;
    }
    printf("Connected successfully.\n\n");

    /* Hardware checks */
    get_comm_status(&device);
    get_chip_id(&device);
    get_readout_temp(&device);
    get_sensor_temp(&device);
    digital_test(&device);
    adc_voltage(&device);

    /* Single injection */
    res = run_single_injection(&device);
    if (res != 0) {
        fprintf(stderr, "[ERROR] Injection failed: %s\n", strerror(res));
    }

    katherine_device_fini(&device);

    printf("\nDone. Outputs:\n");
    printf("  %s  — pixel config (trim=7 baseline)\n", OUTPUT_BMC_FILE);
    printf("  %s  — hit map with statistics\n",        OUTPUT_TXT_FILE);

    return (res == 0) ? 0 : 1;
}