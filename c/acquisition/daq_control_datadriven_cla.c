#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <string.h>
#include <unistd.h>
#include <katherine/katherine.h>
#include <hdf5.h>
#include <argp.h>

// CLA structs and parsing
const char *argp_program_version = "DAQ_Control 1.0";
const char *argp_program_bug_address = "<ad6224sh@lu.se>";
static char doc[] = "DAQ_Control — Timepix3 Acquisition Tool for Katherine with HDF5 functionally enabled";
static char args_doc[] = "[OPTIONS]";

/* Command line options */
static struct argp_option options[] = {
    {"bias",             'b', "VOLTAGE",    0, "Set bias voltage (default: 155)"},
    {"frames",           'f', "NUM",        0, "Number of frames (default: 1)"},
    {"config",           'c', "FILE",       0, "Path to pixel config .bmc file (default: chipconfig_D4-W0005.bmc)"},
    {"address",          'a', "IP",         0, "IP address of the device (default: 192.168.1.218)"},
    {"output",           'o', "FILE",       0, "Output HDF5 file name (default: pixel_data_YYYYMMDD_HHMMSS.h5)"},
    {"acqtime",          't', "TIME",       0, "Acquisition time in nanoseconds (default: 1e9)"},
    {"polarity",         'p', "MODE",       0, "Polarity mode: 0=electrons, 1=holes (default: 1)"},
    {"frequency",        'F', "FREQ",       0, "Clock frequency (10, 20, 40, 80) (default: 40)"},
    {"vth-fine",         'v', "VALUE",      0, "Vthreshold_fine DAC value (default: 442)"},
    {"vth-coarse",       'V', "VALUE",      0, "Vthreshold_coarse DAC value (default: 7)"},
    {"acq-mode",         'm', "MODE",       0, "Acquisition mode (0=TOA, 1=TOA_TOT, 2=EVENT_ITOT) (default: 1)"},
    {"help",             'h', 0,            0, "Display this help and exit"},
    {"detailed-help",    'H', 0,            0, "Display detailed help information about parameters"},
    {0}
};

// Command line arguments structure
struct arguments {
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
};

// Default values
#define DEFAULT_BIAS 155
#define DEFAULT_FRAMES 1
#define DEFAULT_CONFIG "chipconfig_D4-W0005.bmc"
#define DEFAULT_ADDRESS "192.168.1.218"
#define DEFAULT_ACQTIME 1e9
#define DEFAULT_POLARITY 1
#define DEFAULT_FREQUENCY 40
#define DEFAULT_VTH_FINE 424
#define DEFAULT_VTH_COARSE 7
#define DEFAULT_ACQ_MODE 1

// Function to display detailed help information
void display_detailed_help() {
    printf("\nDETAILED HELP INFORMATION\n");
    printf("=========================\n\n");
    
        printf("  Acquires Timepix3 hit data for a specified duration and writes it to an HDF5 file.\n\n");
    printf("COMMAND LINE OPTIONS:\n");
    printf("  -b, --bias=VOLTAGE          Set the bias voltage for the Timepix3 sensor (default: 155 V).\n");
    printf("  -f, --frames=NUM            Set the number of frames to acquire (default: 1).\n");
    printf("  -c, --config=FILE           Path to the pixel configuration file in .bmc format (default: chipconfig_D4-W0005.bmc).\n");
    printf("  -a, --address=IP            IP address of the Timepix3 device (default: 192.168.1.218).\n"); 
    printf("  -o, --output=FILE           Output HDF5 file name (default: pixel_data_YYYYMMDD_HHMMSS.h5).\n");
    printf("  -t, --acqtime=TIME          Acquisition time in nanoseconds (default: 1e9).\n");
    printf("  -p, --polarity=MODE       Polarity mode: 0 for electrons, 1 for holes (default: 1).\n");
    printf("  -F, --frequency=FREQ        Clock frequency in MHz (40, 80, 160) (default: 40).\n");
    printf("  -v, --vth-fine=VALUE        Vthreshold_fine DAC value (default: 442).\n");
    printf("  -V, --vth-coarse=VALUE      Vthreshold_coarse DAC value (default: 7).\n");
    printf("  -m, --acq-mode=MODE         Acquisition mode: 0 for TOA, 1 for TOA_TOT, 2 for EVENT_ITOT (default: 1).\n");
    printf("  -h, --help                  Display this help message and exit.\n");
    printf("  -H, --detailed-help         Display detailed help information about parameters.\n\n");

    printf("ADDITIONAL INFORMATION:\n");
    printf("  The program uses the Katherine library to interface with the Timepix3 device and acquire pixel hit data.\n");
    printf("  The acquired data is stored in an HDF5 file with a dataset containing pixel hits.\n");
    printf("  The program supports different acquisition modes and clock frequencies.\n");
    printf("  The output file name can be customized, or a default name based on the current date and time will be generated.\n");
    printf("  The program can be run with default settings or with custom parameters specified via command line options.\n\n");

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
    struct arguments *args = state->input;
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
            if (                args->frequency != 40 && args->frequency != 80 && args->frequency != 160) {
                fprintf(stderr, "Invalid frequency: %d. Must be 40, 80, or 160 MHz.\n", args->frequency);
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

void print_active_settings(const struct arguments *args) {
    printf("\nACTIVE ACQUISITION SETTINGS:\n");
    printf("---------------------------\n");
    printf("Bias voltage:       %d V\n", args->bias);
    printf("Number of frames:   %d\n", args->frames);
    printf("Config file:        %s\n", args->config_file);
    printf("Device IP address:  %s\n", args->ip_address);
    printf("Acquisition time:   %.2e seconds\n", args->acq_time);
    printf("Polarity mode:      %s\n", args->polarity ? "Holes" : "Electrons");
    printf("Clock frequency:    %d MHz\n", args->frequency);
    printf("Vthreshold fine:    %d\n", args->vth_fine);
    printf("Vthreshold coarse:  %d\n", args->vth_coarse);
    printf("\n");
}

static const char *remote_addr = DEFAULT_ADDRESS; //Device IP address
typedef katherine_px_f_toa_tot_t px_t; //ACQ mode (Modes in px.h)

// Global variables
#define SENSOR_WIDTH 256
#define SENSOR_HEIGHT 256
static uint64_t pixel_counts[SENSOR_HEIGHT][SENSOR_WIDTH] = {0};
static uint64_t n_hits = 0;

// HDF5 File Structure
typedef struct {
    hid_t file_id;
    hid_t pixel_datatype;
    hid_t pixel_dataset;
    float current_bias;
} H5FileManager;

// Data Structure for HDF5
typedef struct {
    int x;
    int y;
    uint64_t toa;
    uint8_t ftoa;
    uint16_t tot;
    uint32_t hit_count;
} PixelHit;

static H5FileManager h5_manager = {-1, -1, -1};

// Function prototypes
void configure(katherine_config_t *config, const struct arguments *args);
void frame_started(void *user_ctx, int frame_idx);
void frame_ended(void *user_ctx, int frame_idx, bool completed, const katherine_frame_info_t *info);
void pixels_received(void *user_ctx, const void *px, size_t count);
void get_chip_id(katherine_device_t *device);
void get_comm_status(katherine_device_t *device);
void get_readout_temp(katherine_device_t *device);
void get_sensor_temp(katherine_device_t *device);
void digital_test(katherine_device_t *device);
void adc_voltage(katherine_device_t *device);
void reset_pixel_counts();
void run_acquisition(katherine_device_t *device, const katherine_config_t *config, const struct arguments *args);
void enable_scanning_modes();

// HDF5 Initialization and Setup
hid_t create_pixel_datatype() {
    hid_t pixel_type = H5Tcreate(H5T_COMPOUND, sizeof(PixelHit));
    H5Tinsert(pixel_type, "x", HOFFSET(PixelHit, x), H5T_NATIVE_INT);
    H5Tinsert(pixel_type, "y", HOFFSET(PixelHit, y), H5T_NATIVE_INT);
    H5Tinsert(pixel_type, "toa", HOFFSET(PixelHit, toa), H5T_NATIVE_UINT64);
    H5Tinsert(pixel_type, "ftoa", HOFFSET(PixelHit, ftoa), H5T_NATIVE_UINT8);
    H5Tinsert(pixel_type, "tot", HOFFSET(PixelHit, tot), H5T_NATIVE_UINT16);
    H5Tinsert(pixel_type, "hit_count", HOFFSET(PixelHit, hit_count), H5T_NATIVE_UINT32);
    return pixel_type;
}

void initialize_h5_file(const struct arguments *args) {
    char filename[128];
    
    if (args->output_file) {
        strncpy(filename, args->output_file, sizeof(filename));
    } else {
        time_t now;
        time(&now);
        struct tm *timeinfo = localtime(&now);
        strftime(filename, sizeof(filename), "ToTdata_datadriven_%Y%m%d_%H%M%S.h5", timeinfo);
    }

    // Create file
    hid_t plist_id = H5Pcreate(H5P_FILE_ACCESS);
    H5Pset_libver_bounds(plist_id, H5F_LIBVER_LATEST, H5F_LIBVER_LATEST);
    h5_manager.file_id = H5Fcreate(filename, H5F_ACC_TRUNC, H5P_DEFAULT, plist_id);
    H5Pclose(plist_id);

    if (h5_manager.file_id < 0) {
        printf("Failed to create HDF5 file: %s\n", filename);
        return;
    }

    // Create datatype
    h5_manager.pixel_datatype = create_pixel_datatype();

    // Create dataset for all pixel hits
    hsize_t initial_dims[1] = {0};
    hsize_t max_dims[1] = {H5S_UNLIMITED};
    hid_t dataspace_id = H5Screate_simple(1, initial_dims, max_dims);

    hid_t plist = H5Pcreate(H5P_DATASET_CREATE);
    hsize_t chunk_dims[1] = {1000};
    H5Pset_chunk(plist, 1, chunk_dims);

    h5_manager.pixel_dataset = H5Dcreate(h5_manager.file_id, "/pixel_hits", h5_manager.pixel_datatype, 
                                         dataspace_id, H5P_DEFAULT, plist, H5P_DEFAULT);

    // Close resources
    H5Pclose(plist);
    H5Sclose(dataspace_id);
}

void write_pixel_hits(const px_t *dpx, size_t count) {
    if (h5_manager.pixel_dataset < 0) return;

    // Init pixel hits
    PixelHit *pixel_hits = malloc(count * sizeof(PixelHit));
    
    for (size_t i = 0; i < count; ++i) {
        int x = dpx[i].coord.x;
        int y = dpx[i].coord.y;
        
        // Verify coordinates are within bounds
        if (x < 0 || x >= SENSOR_WIDTH || y < 0 || y >= SENSOR_HEIGHT) {
            printf("Warning: Pixel coordinates out of bounds: (%d, %d)\n", x, y);
            continue;
        }
        
        // Increment the hit count for this pixel location
        pixel_counts[y][x]++;
        
        // Populate the hit data structure
        pixel_hits[i].x = x;
        pixel_hits[i].y = y;
        pixel_hits[i].toa = dpx[i].toa;
        pixel_hits[i].ftoa = dpx[i].ftoa;
        pixel_hits[i].tot = dpx[i].tot;
        pixel_hits[i].hit_count = pixel_counts[y][x]; // Store the current count
    }

    // Get current dataset dims
    hid_t filespace = H5Dget_space(h5_manager.pixel_dataset);
    hsize_t current_dims[1];
    H5Sget_simple_extent_dims(filespace, current_dims, NULL);

    // Extend dataset
    hsize_t new_size[1] = {current_dims[0] + count};
    H5Dset_extent(h5_manager.pixel_dataset, new_size);

    // Write data
    hsize_t start[1] = {current_dims[0]};
    hsize_t count_hslab[1] = {count};
    hid_t memspace = H5Screate_simple(1, count_hslab, NULL);
    
    filespace = H5Dget_space(h5_manager.pixel_dataset);
    H5Sselect_hyperslab(filespace, H5S_SELECT_SET, start, NULL, count_hslab, NULL);
    H5Dwrite(h5_manager.pixel_dataset, h5_manager.pixel_datatype, memspace, filespace, H5P_DEFAULT, pixel_hits);

    // Close
    free(pixel_hits);
    H5Sclose(memspace);
    H5Sclose(filespace);
}

void close_h5_file() {
    if (h5_manager.pixel_dataset >= 0) {
        H5Dclose(h5_manager.pixel_dataset);
    }
    if (h5_manager.pixel_datatype >= 0) {
        H5Tclose(h5_manager.pixel_datatype);
    }
    if (h5_manager.file_id >= 0) {
        H5Fclose(h5_manager.file_id);
    }
    // Reset file
    h5_manager.file_id = -1;
    h5_manager.pixel_dataset = -1;
    h5_manager.pixel_datatype = -1;
    h5_manager.current_bias = 0.0;
}

int main(int argc, char *argv[]) {
    // Parse command line arguments
    struct arguments arguments = {
        .bias = DEFAULT_BIAS,
        .frames = DEFAULT_FRAMES,
        .config_file = DEFAULT_CONFIG,
        .ip_address = DEFAULT_ADDRESS,
        .output_file = NULL,
        .acq_time = DEFAULT_ACQTIME,
        .polarity = DEFAULT_POLARITY,
        .frequency = DEFAULT_FREQUENCY,
        .vth_fine = DEFAULT_VTH_FINE,
        .vth_coarse = DEFAULT_VTH_COARSE,
        .acq_mode = DEFAULT_ACQ_MODE
    };
    
    // Initialize argp parser
    static struct argp argp = { options, parse_opt, args_doc, doc };
    
    // Parse arguments
    argp_parse(&argp, argc, argv, 0, 0, &arguments);

    // Handle help options
    if (arguments.show_detailed_help) {
        display_detailed_help();
        exit(0);
    }
    
    // Update remote_addr from arguments
    remote_addr = arguments.ip_address;
    // Loading config
    katherine_config_t c; 
    configure(&c, &arguments);

    // Initializing device
    int res;
    katherine_device_t device; 

    // Retry mechanism for connection
    int retries = 3;
    while (retries > 0) {
        printf("Attempting to connect to device at %s...\n", remote_addr);
        res = katherine_device_init(&device, remote_addr);
        if (res == 0) break; // Connected. No retry
        printf("Connection failed: %s. Retrying... (%d attempts left)\n", strerror(res), retries);
        sleep(1); // Wait before retrying
        retries--;
    }
    if (res != 0) {
        printf("Cannot initialize device after multiple attempts.\n");
        exit(6);
    }
    printf("Connected successfully.\n");

    get_comm_status(&device);
    get_chip_id(&device);
    get_readout_temp(&device);
    get_sensor_temp(&device);
    digital_test(&device);
    adc_voltage(&device);
    print_active_settings(&arguments);
    run_acquisition(&device, &c, &arguments);


    // Closing device
    katherine_device_fini(&device);

    close_h5_file(); 
    return 0;
}


void configure(katherine_config_t *config, const struct arguments *args) {
    config->bias_id = 0;
    config->acq_time = args->acq_time;
    config->no_frames = args->frames;
    config->bias = args->bias;
    
    config->delayed_start = false;
    
    config->start_trigger.enabled = false;
    config->start_trigger.channel = 0;
    config->start_trigger.use_falling_edge = false;
    config->stop_trigger.enabled = false;
    config->stop_trigger.channel = 0;
    config->stop_trigger.use_falling_edge = false;
    
    config->gray_disable = true;
    config->polarity_holes = args->polarity;
    
    config->phase = PHASE_1;
    switch (args->frequency) {
        case 40: config->freq = FREQ_40; break;
        case 80: config->freq = FREQ_80; break;
        case 160: config->freq = FREQ_160; break;
        default:
            printf("Invalid frequency %d, using default 40 MHz\n", args->frequency);
            config->freq = FREQ_40;
            break;
    }
    
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
        printf("Cannot load pixel configuration from %s.\n", args->config_file);
        printf("Reason: %s\n", strerror(res));
        exit(1);
    }
}

void get_chip_id(katherine_device_t *device) {
    char chip_id[KATHERINE_CHIP_ID_STR_SIZE];
    int res = katherine_get_chip_id(device, chip_id);
    if (res != 0) {
        printf("Cannot get chip ID. Is Timepix3 connected to the readout?\n");
        printf("Reason: %s\n", strerror(res));
        exit(2);
    }

    printf("Chip ID: %s\n", chip_id);
}

void get_comm_status(katherine_device_t *device) {
    katherine_comm_status_t comm_status;
    int res = katherine_get_comm_status(device, &comm_status);
    if (res != 0) {
        printf("cannot get comm status.\n");
        printf("Reason: %s\n", strerror(res));
        exit(8);
    }
    printf("Comm Status:\n");
    printf("  Communication Lines Mask: 0x%x\n", comm_status.comm_lines_mask);
    printf("  Data Rate: %u Mbps\n", comm_status.data_rate);
    printf("  Chip Detected: %s\n", comm_status.chip_detected ? "Yes" : "No");
}

void get_readout_temp(katherine_device_t *device) {
    float temperature;
    int res = katherine_get_readout_temperature(device, &temperature);
    if (res != 0) {
        printf("cannot get readout temperature.\n");
        printf("Reason: %s\n", strerror(res));
        exit(8);
    }
    printf("Readout temperature: %.2f°C\n", temperature);

}

void get_sensor_temp(katherine_device_t *device) {
    float temperature;
    int res = katherine_get_sensor_temperature(device, &temperature);
    if (res != 0) {
        printf("cannot get sensor temperature.\n");
        printf("Reason: %s\n", strerror(res));
        exit(9);
    }
    printf("Sensor temperature: %.2f°C\n", temperature);

}

void digital_test(katherine_device_t *device)  {
    int res = katherine_perform_digital_test(device);
    if (res != 0) {
        printf("Digital test failed!\n");
        printf("Reason: %s\n", strerror(res));
        exit(10);
    }
    printf("Digital test passed.\n");

}

void adc_voltage(katherine_device_t *device) {
    float voltage;
    int res = katherine_get_adc_voltage(device,0, &voltage);
    if (res != 0) {
        printf("ADC voltage test failed!\n");
        printf("Reason: %s\n", strerror(res));
        exit(11);
    }
    printf("ADC voltage: %f\n", voltage);

}

void frame_started(void *user_ctx, int frame_idx) {
    n_hits = 0;

    printf("Started frame %d.\n", frame_idx);

}

katherine_frame_info_t last_frame_info = {0};
void frame_ended(void *user_ctx, int frame_idx, bool completed, const katherine_frame_info_t *info) {
    // Existing frame_ended logic
    const double recv_perc = 100. * info->received_pixels / info->sent_pixels;

    printf("\n");
    printf("Ended frame %d.\n", frame_idx);
    printf(" - tpx3->katherine lost %lu pixels\n", info->lost_pixels);
    printf(" - katherine->pc sent %lu pixels\n", info->sent_pixels);
    printf(" - katherine->pc received %lu pixels\n", info->received_pixels);
    printf(" - state: %s\n", (completed ? "completed" : "not completed"));
    printf(" - start time: %lu\n", info->start_time.d);
    printf(" - end time: %lu\n", info->end_time.d);

    // Store last frame info
    memcpy(&last_frame_info, info, sizeof(katherine_frame_info_t));
}

void pixels_received(void *user_ctx, const void *px, size_t count) {
    const px_t *dpx = (const px_t *) px;
    
    write_pixel_hits(dpx, count);
}

void reset_pixel_counts() {
    memset(pixel_counts, 0, sizeof(pixel_counts));
    n_hits = 0;
}

void run_acquisition(katherine_device_t *device, const katherine_config_t *config, const struct arguments *args) {
    initialize_h5_file(args);
    
    katherine_acquisition_t acq;
    int res = katherine_acquisition_init(&acq, device, NULL, 
                                     KATHERINE_MD_SIZE * 34952533, 
                                     sizeof(px_t) * 65536, 5000, 60000);
    if (res != 0) {
        printf("Cannot initialize acquisition.\n");
        return;
    }

    acq.handlers.frame_started = frame_started;
    acq.handlers.frame_ended = frame_ended;
    acq.handlers.pixels_received = pixels_received;

    katherine_acquisition_mode_t acq_mode;
    switch (args->acq_mode) {
        case 0: acq_mode = ACQUISITION_MODE_TOA_TOT; break;
        case 1: acq_mode = ACQUISITION_MODE_ONLY_TOA; break;
        case 2: acq_mode = ACQUISITION_MODE_EVENT_ITOT; break;
        default:
            printf("Invalid acquisition mode %d, using default TOA_TOT\n", args->acq_mode);
            acq_mode = ACQUISITION_MODE_TOA_TOT;
            break;
    }

    res = katherine_acquisition_begin(&acq, config, 
                                  READOUT_DATA_DRIVEN, 
                                  acq_mode, 
                                  true, true);
    if (res != 0) {
        printf("Cannot begin acquisition .\n");
        katherine_acquisition_fini(&acq);
        return;
    }

    // Read acquisition data
    res = katherine_acquisition_read(&acq);
    if (res != 0) {
        printf("Cannot read acquisition data.\n");
        katherine_acquisition_fini(&acq);
        return;
    }

    // Finalize acquisition
    katherine_acquisition_fini(&acq);
    close_h5_file();
    printf("Acquisition completed\n");
}