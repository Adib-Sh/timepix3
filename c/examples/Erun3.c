#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <string.h>
#include <unistd.h>
#include <argp.h>
#include <katherine/katherine.h>
#include "tpx3h5lib.h"

static const char *remote_addr = "192.168.1.218";
typedef katherine_px_f_toa_tot_t px_t;
#define SENSOR_WIDTH 256
#define SENSOR_HEIGHT 256
static uint64_t pixel_counts[SENSOR_HEIGHT][SENSOR_WIDTH] = {0};

// CLA structs and parsing
const char *argp_program_version = "Erun3 1.0";
const char *argp_program_bug_address = "<your_email@example.com>";
static char doc[] = "Erun3 — Timepix3 HDF5 Acquisition Tool";
static struct argp_option options[] = {
    {"bias",  'b', "VOLTAGE", 0, "Set bias voltage (default: 155)"},
    {"frames",'f', "NUM",     0, "Number of frames (default: 1)"},
    {"config",'c', "FILE",    0, "Path to pixel config .bmc file (default: chipconfig_D4-W0005.bmc)"},
    {0}
};

typedef struct {
    int bias;
    int frames;
    char *config_file;
} arguments_t;

static error_t parse_opt(int key, char *arg, struct argp_state *state) {
    arguments_t *args = state->input;
    switch (key) {
        case 'b': args->bias = atoi(arg); break;
        case 'f': args->frames = atoi(arg); break;
        case 'c': args->config_file = arg; break;
        default: return ARGP_ERR_UNKNOWN;
    }
    return 0;
}

static struct argp argp = { options, parse_opt, 0, doc };

// Acquisition globals
static Tpx3H5Writer h5writer;

// Katherine config
void configure(katherine_config_t *config, int bias, int frames, const char *config_file) {
    config->bias = bias;
    config->no_frames = frames;
    config->acq_time = 1e10;
    config->bias_id = 0;
    config->delayed_start = false;
    config->start_trigger.enabled = false;
    config->stop_trigger.enabled = false;
    config->gray_disable = true;
    config->polarity_holes = true;
    config->phase = PHASE_1;
    config->freq = FREQ_40;

    config->dacs.named.Ibias_Preamp_ON = 128;
    config->dacs.named.Ibias_Preamp_OFF = 8;
    config->dacs.named.VPReamp_NCAS = 128;
    config->dacs.named.Ibias_Ikrum = 15;
    config->dacs.named.Vfbk = 164;
    config->dacs.named.Vthreshold_fine = 442;
    config->dacs.named.Vthreshold_coarse = 7;
    config->dacs.named.Ibias_DiscS1_ON = 100;
    config->dacs.named.Ibias_DiscS1_OFF = 8;
    config->dacs.named.Ibias_DiscS2_ON = 128;
    config->dacs.named.Ibias_DiscS2_OFF = 8;
    config->dacs.named.Ibias_PixelDAC = 100;
    config->dacs.named.Ibias_TPbufferIn = 128;
    config->dacs.named.Ibias_TPbufferOut = 128;
    config->dacs.named.VTP_coarse = 128;
    config->dacs.named.VTP_fine = 256;
    config->dacs.named.Ibias_CP_PLL = 128;
    config->dacs.named.PLL_Vcntrl = 128;

    int res = katherine_px_config_load_bmc_file(&config->pixel_config, config_file);
    if (res != 0) {
        printf("Cannot load pixel configuration: %s\n", config_file);
        exit(1);
    }
}

// Callback implementations
void pixels_received(void *ctx, const void *px, size_t count) {
    const px_t *dpx = (const px_t *) px;
    PixelHit *hits = malloc(count * sizeof(PixelHit));
    for (size_t i = 0; i < count; ++i) {
        int x = dpx[i].coord.x;
        int y = dpx[i].coord.y;
        if (x < 0 || x >= SENSOR_WIDTH || y < 0 || y >= SENSOR_HEIGHT) continue;
        pixel_counts[y][x]++;
        hits[i] = (PixelHit){x, y, dpx[i].toa, dpx[i].ftoa, dpx[i].tot, pixel_counts[y][x]};
    }
    tpx3h5_append(&h5writer, hits, count);
    free(hits);
}

void frame_started(void *ctx, int frame_idx) {
    printf("Started frame %d\n", frame_idx);
}

void frame_ended(void *ctx, int frame_idx, bool completed, const katherine_frame_info_t *info) {
    printf("Ended frame %d: %lu pixels received\n", frame_idx, info->received_pixels);
}

void run_acquisition(katherine_device_t *device, const katherine_config_t *config) {
    katherine_acquisition_t acq;
    katherine_acquisition_init(&acq, device, NULL,
        KATHERINE_MD_SIZE * 34952533, sizeof(px_t) * 65536, 500, 30000);

    acq.handlers.frame_started = frame_started;
    acq.handlers.frame_ended = frame_ended;
    acq.handlers.pixels_received = pixels_received;

    katherine_acquisition_begin(&acq, config, READOUT_DATA_DRIVEN, ACQUISITION_MODE_TOA_TOT, true, true);
    katherine_acquisition_read(&acq);
    katherine_acquisition_fini(&acq);
}

int main(int argc, char *argv[]) {
    arguments_t args = {155, 1, "chipconfig_D4-W0005.bmc"};
    argp_parse(&argp, argc, argv, 0, 0, &args);

    katherine_config_t c;
    configure(&c, args.bias, args.frames, args.config_file);

    katherine_device_t device;
    if (katherine_device_init(&device, remote_addr) != 0) {
        printf("Failed to initialize device\n");
        return 1;
    }

    char h5name[128];
    time_t now = time(NULL);
    strftime(h5name, sizeof(h5name), "pixel_data_%Y%m%d_%H%M%S.h5", localtime(&now));
    tpx3h5_init(&h5writer, h5name, "/pixel_hits");

    run_acquisition(&device, &c);

    tpx3h5_close(&h5writer);
    katherine_device_fini(&device);
    return 0;
}
