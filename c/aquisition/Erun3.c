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
const char *argp_program_bug_address = "<ad6224sh@lu.se>";
static char doc[] = "Erun3 — Timepix3 Acquisition Tool for Katherine with HDF5 functionally enabled";
static char args_doc[] = "[OPTIONS]";

static struct argp_option options[] = {
    {"bias",             'b', "VOLTAGE",    0, "Set bias voltage (default: 155)"},
    {"frames",           'f', "NUM",        0, "Number of frames (default: 1)"},
    {"config",           'c', "FILE",       0, "Path to pixel config .bmc file (default: chipconfig_D4-W0005.bmc)"},
    {"address",          'a', "IP",         0, "IP address of the device (default: 192.168.1.218)"},
    {"output",           'o', "FILE",       0, "Output HDF5 file name (default: pixel_data_YYYYMMDD_HHMMSS.h5)"},
    {"acqtime",          't', "TIME",       0, "Acquisition time in seconds (default: 1e10)"},
    {"polarity",         'p', "MODE",       0, "Polarity mode: 0=electrons, 1=holes (default: 1)"},
    {"frequency",        'F', "FREQ",       0, "Clock frequency (10, 20, 40, 80) (default: 40)"},
    {"vth-fine",         'v', "VALUE",      0, "Vthreshold_fine DAC value (default: 442)"},
    {"vth-coarse",       'V', "VALUE",      0, "Vthreshold_coarse DAC value (default: 7)"},
    {"acq-mode",         'm', "MODE",       0, "Acquisition mode (0=TOA, 1=TOA_TOT, 2=EVENT_ITOT) (default: 1)"},
    {"help",             'h', 0,            0, "Display this help and exit"},
    {"detailed-help",    'H', 0,            0, "Display detailed help information about parameters"},
    {0}
};

typedef struct {
    int bias;
    int frames;
    char *config_file;
    char *ip_address;
    char *output_file;
    double acq_time;
    int polarity;
    int custom_output_file;
    int frequency;
    int vth_fine;
    int vth_coarse;
    int acq_mode;
    int show_detailed_help;
} arguments_t;

// Function to display detailed help information
void display_detailed_help() {
    printf("\nDETAILED HELP INFORMATION\n");
    printf("=========================\n\n");
    
    printf("ACQUISITION MODES:\n");
    printf("  0 = TOA_TOT_EVENT: Time of Arrival, Time over Threshold, and Event counting (default)\n");
    printf("  1 = TOA: Time of Arrival only\n");
    printf("  2 = EVENT_ITOT: Event counting with integral Time over Threshold\n\n");
    
    printf("CLOCK FREQUENCIES:\n");
    printf("  40 = 40 MHz (default)\n");
    printf("  80 = 80 MHz\n");
    printf("  160 = 160 MHz\n\n");
    
    printf("POLARITY MODES:\n");
    printf("  0 = Electrons\n");
    printf("  1 = Holes (default)\n\n");
    
    printf("THRESHOLD SETTINGS:\n");
    printf("  Vthreshold_fine (default: 442)\n");
    printf("    - Valid range: 0-1023\n");
    printf("    - Lower values = higher sensitivity\n");
    printf("  Vthreshold_coarse (default: 7)\n");
    printf("    - Valid range: 0-15\n");
    printf("    - Lower values = higher sensitivity\n\n");
    
    printf("EXAMPLES:\n");
    printf("  Run with default settings:\n");
    printf("    ./erun3\n\n");
    
    printf("  Run with 200V bias voltage and 10 frames:\n");
    printf("    ./erun3 -b 200 -f 10\n\n");
    
    printf("  Run with custom config file and output file:\n");
    printf("    ./erun3 -c my_config.bmc -o my_data.h5\n\n");
    
    printf("  Run with different frequency and acquisition mode:\n");
    printf("    ./erun3 -F 80 -m 0\n\n");
    
    printf("  Run with custom threshold settings:\n");
    printf("    ./erun3 -v 430 -V 6\n\n");
    
    exit(0);
}

static error_t parse_opt(int key, char *arg, struct argp_state *state) {
    arguments_t *args = state->input;
    switch (key) {
        case 'b': args->bias = atoi(arg); break;
        case 'f': args->frames = atoi(arg); break;
        case 'c': args->config_file = arg; break;
        case 'a': args->ip_address = arg; break;
        case 'o': 
            args->output_file = arg; 
            args->custom_output_file = 1;
            break;
        case 't': args->acq_time = atof(arg); break;
        case 'p': args->polarity = atoi(arg); break;
        case 'F': 
            args->frequency = atoi(arg); 
            // Validate frequency
            if (args->frequency != 10 && args->frequency != 20 && 
                args->frequency != 40 && args->frequency != 80) {
                fprintf(stderr, "Invalid frequency: %d. Must be 10, 20, 40, or 80 MHz.\n", args->frequency);
                args->frequency = 40; // Reset to default
            }
            break;
        case 'v': args->vth_fine = atoi(arg); break;
        case 'V': args->vth_coarse = atoi(arg); break;
        case 'm': 
            args->acq_mode = atoi(arg);
            // Validate acquisition mode
            if (args->acq_mode < 0 || args->acq_mode > 2) {
                fprintf(stderr, "Invalid acquisition mode: %d. Using default (1=TOA_TOT).\n", args->acq_mode);
                args->acq_mode = 1; // Reset to default
            }
            break;
        case 'h': 
            argp_state_help(state, stdout, ARGP_HELP_STD_HELP);
            exit(0);
            break;
        case 'H': 
            args->show_detailed_help = 1;
            break;
        default: return ARGP_ERR_UNKNOWN;
    }
    return 0;
}

static struct argp argp = { options, parse_opt, args_doc, doc };

// Acquisition globals
static Tpx3H5Writer h5writer;

// Katherine config
void configure(katherine_config_t *config, arguments_t *args) {
    config->bias = args->bias;
    config->no_frames = args->frames;
    config->acq_time = args->acq_time;
    config->bias_id = 0;
    config->delayed_start = false;
    config->start_trigger.enabled = false;
    config->stop_trigger.enabled = false;
    config->gray_disable = true;
    config->polarity_holes = args->polarity;
    
    // Set frequency based on argument
    switch (args->frequency) {
        case 40: config->freq = FREQ_40; break;
        case 80: config->freq = FREQ_80; break;
        case 160: config->freq = FREQ_160; break;
        default: config->freq = FREQ_40; break;
    }
    
    config->phase = PHASE_1;

    config->dacs.named.Ibias_Preamp_ON = 128;
    config->dacs.named.Ibias_Preamp_OFF = 8;
    config->dacs.named.VPReamp_NCAS = 128;
    config->dacs.named.Ibias_Ikrum = 15;
    config->dacs.named.Vfbk = 164;
    config->dacs.named.Vthreshold_fine = args->vth_fine;
    config->dacs.named.Vthreshold_coarse = args->vth_coarse;
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

    int res = katherine_px_config_load_bmc_file(&config->pixel_config, args->config_file);
    if (res != 0) {
        printf("Cannot load pixel configuration: %s\n", args->config_file);
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

void run_acquisition(katherine_device_t *device, const katherine_config_t *config, int acq_mode) {
    katherine_acquisition_t acq;
    katherine_acquisition_init(&acq, device, NULL,
        KATHERINE_MD_SIZE * 34952533, sizeof(px_t) * 65536, 500, 30000);

    acq.handlers.frame_started = frame_started;
    acq.handlers.frame_ended = frame_ended;
    acq.handlers.pixels_received = pixels_received;

    // Set acquisition mode based on argument
    katherine_acquisition_mode_t mode;
    switch (acq_mode) {
        case 0: mode = ACQUISITION_MODE_TOA_TOT; break;
        case 1: mode = ACQUISITION_MODE_ONLY_TOA; break;
        case 2: mode = ACQUISITION_MODE_EVENT_ITOT; break;
        default: mode = ACQUISITION_MODE_TOA_TOT; break;
    }

    katherine_acquisition_begin(&acq, config, READOUT_DATA_DRIVEN, mode, true, true);
    katherine_acquisition_read(&acq);
    katherine_acquisition_fini(&acq);
}

// Function to print active settings
void print_active_settings(arguments_t *args) {
    printf("\nACTIVE ACQUISITION SETTINGS:\n");
    printf("---------------------------\n");
    printf("Bias voltage:       %d V\n", args->bias);
    printf("Number of frames:   %d\n", args->frames);
    printf("Config file:        %s\n", args->config_file);
    printf("Device IP address:  %s\n", args->ip_address);
    printf("Output file:        %s\n", args->output_file);
    printf("Acquisition time:   %.2e seconds\n", args->acq_time);
    printf("Polarity mode:      %s\n", args->polarity ? "Holes" : "Electrons");
    printf("Clock frequency:    %d MHz\n", args->frequency);
    printf("Vthreshold fine:    %d\n", args->vth_fine);
    printf("Vthreshold coarse:  %d\n", args->vth_coarse);
    
    const char *acq_mode_str;
    switch (args->acq_mode) {
        case 0: acq_mode_str = "TOA"; break;
        case 1: acq_mode_str = "TOA_TOT"; break;
        case 2: acq_mode_str = "EVENT_ITOT"; break;
        default: acq_mode_str = "Unknown"; break;
    }
    printf("Acquisition mode:   %s\n", acq_mode_str);
    printf("\n");
}

int main(int argc, char *argv[]) {
    // Set default arguments
    arguments_t args = {
        .bias = 155,
        .frames = 1,
        .config_file = "chipconfig_D4-W0005.bmc",
        .ip_address = (char*)remote_addr,
        .output_file = NULL,
        .acq_time = 1e10,
        .polarity = 1,
        .custom_output_file = 0,
        .frequency = 40,
        .vth_fine = 442,
        .vth_coarse = 7,
        .acq_mode = 0,  // TOA_TOT
        .show_detailed_help = 0
    };
    
    // Parse command line arguments
    argp_parse(&argp, argc, argv, 0, 0, &args);
    
    // Show detailed help if requested
    if (args.show_detailed_help) {
        display_detailed_help();
    }
    
    // Generate default output filename if not provided
    char h5name[128];
    if (!args.custom_output_file) {
        time_t now = time(NULL);
        strftime(h5name, sizeof(h5name), "pixel_data_%Y%m%d_%H%M%S.h5", localtime(&now));
        args.output_file = h5name;
    }
    
    // Print active settings (only if running acquisition)
    print_active_settings(&args);
    
    katherine_config_t c;
    configure(&c, &args);

    katherine_device_t device;
    if (katherine_device_init(&device, args.ip_address) != 0) {
        printf("Failed to initialize device\n");
        return 1;
    }

    tpx3h5_init(&h5writer, args.output_file, "/pixel_hits");

    run_acquisition(&device, &c, args.acq_mode);

    tpx3h5_close(&h5writer);
    katherine_device_fini(&device);
    return 0;
}