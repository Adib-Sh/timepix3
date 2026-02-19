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
static char doc[] = "DAQ_Control — Timepix3 Acquisition Tool for Katherine with HDF5 functionally enabled (Data-driven and Frame modes)";
static char args_doc[] = "[OPTIONS]";

/* Command line options */
static struct argp_option options[] = {
    {"bias",             'b', "VOLTAGE",    0, "Set bias voltage (default: 155)"},
    {"frames",           'f', "NUM",        0, "Number of frames (default: 1)"},
    {"config",           'c', "FILE",       0, "Path to pixel config .bmc file (default: chipconfig_D4-W0005.bmc)"},
    {"address",          'a', "IP",         0, "IP address of the device (default: 192.168.1.218)"},
    {"output",           'o', "FILE",       0, "Output HDF5 file name (default: auto-generated with timestamp)"},
    {"acqtime",          't', "TIME",       0, "Acquisition time in nanoseconds (default: 1e9)"},
    {"polarity",         'p', "MODE",       0, "Polarity mode: 0=electrons, 1=holes (default: 1)"},
    {"frequency",        'F', "FREQ",       0, "Clock frequency (40, 80, 160) (default: 40)"},
    {"vth-fine",         'v', "VALUE",      0, "Vthreshold_fine DAC value (default: 424)"},
    {"vth-coarse",       'V', "VALUE",      0, "Vthreshold_coarse DAC value (default: 7)"},
    {"acq-mode",         'm', "MODE",       0, "Acquisition mode (0=TOA_TOT, 1=TOA, 2=EVENT_ITOT) (default: 1)"},
    {"readout-mode",     'r', "MODE",       0, "Readout mode (0=data-driven, 1=frame) (default: 0)"},
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
    int readout_mode;
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
#define DEFAULT_READOUT_MODE 0


void display_detailed_help() {
    printf("\nDETAILED HELP INFORMATION\n");
    printf("=========================\n\n");
    
    printf("  Acquires Timepix3 hit data for a specified duration and writes it to an HDF5 file.\n");
    printf("  Supports both data-driven and frame-based readout modes.\n\n");
    
    printf("COMMAND LINE OPTIONS:\n");
    printf("  -b, --bias=VOLTAGE          Set the bias voltage for the Timepix3 sensor (default: 155 V).\n");
    printf("  -f, --frames=NUM            Set the number of frames to acquire (default: 1).\n");
    printf("  -c, --config=FILE           Path to the pixel configuration file in .bmc format (default: chipconfig_D4-W0005.bmc).\n");
    printf("  -a, --address=IP            IP address of the Timepix3 device (default: 192.168.1.218).\n"); 
    printf("  -o, --output=FILE           Output HDF5 file name (default: auto-generated with timestamp).\n");
    printf("  -t, --acqtime=TIME          Acquisition time in seconds (default: 1e9).\n");
    printf("  -p, --polarity=MODE         Polarity mode: 0 for electrons, 1 for holes (default: 1).\n");
    printf("  -F, --frequency=FREQ        Clock frequency in MHz (40, 80, 160) (default: 40).\n");
    printf("  -v, --vth-fine=VALUE        Vthreshold_fine DAC value (default: 424).\n");
    printf("  -V, --vth-coarse=VALUE      Vthreshold_coarse DAC value (default: 7).\n");
    printf("  -m, --acq-mode=MODE         Acquisition mode: 0 for TOA_TOT, 1 for TOA, 2 for EVENT_ITOT (default: 1).\n");
    printf("  -r, --readout-mode=MODE     Readout mode: 0 for data-driven, 1 for frame (default: 0).\n");
    printf("  -h, --help                  Display this help message and exit.\n");
    printf("  -H, --detailed-help         Display detailed help information about parameters.\n\n");

    printf("READOUT MODES:\n");
    printf("  0 = Data-driven: Continuous readout with TOA/TOT data\n");
    printf("  1 = Frame: Sequential readout with integrated data per frame\n\n");

    printf("ACQUISITION MODES:\n");
    printf("  0 = TOA_TOT: Time of Arrival and Time over Threshold\n");
    printf("  1 = TOA: Time of Arrival only (default)\n");
    printf("  2 = EVENT_ITOT: Event counting with integral Time over Threshold\n\n");
    
    printf("CLOCK FREQUENCIES:\n");
    printf("  40 = 40 MHz (default)\n");
    printf("  80 = 80 MHz\n");
    printf("  160 = 160 MHz\n\n");
    
    printf("POLARITY MODES:\n");
    printf("  0 = Electrons\n");
    printf("  1 = Holes (default)\n\n");
    
    printf("THRESHOLD SETTINGS:\n");
    printf("  Vthreshold_fine (default: 424)\n");
    printf("    - Valid range: 0-1023\n");
    printf("    - Lower values = higher sensitivity\n");
    printf("  Vthreshold_coarse (default: 7)\n");
    printf("    - Valid range: 0-15\n");
    printf("    - Lower values = higher sensitivity\n\n");
    
    printf("EXAMPLES:\n");
    printf("  Run data-driven mode with default settings:\n");
    printf("    ./erun3\n\n");
    
    printf("  Run frame mode with 5 frames:\n");
    printf("    ./erun3 -r 1 -f 5\n\n");
    
    printf("  Run with 200V bias voltage and EVENT_ITOT mode:\n");
    printf("    ./erun3 -b 200 -m 2\n\n");
    
    printf("  Run frame mode with custom config and output file:\n");
    printf("    ./erun3 -r 1 -c my_config.bmc -o my_data.h5\n\n");
    
    printf("  Run with different frequency and readout mode:\n");
    printf("    ./erun3 -F 80 -r 1 -m 2\n\n");
    
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
            if (args->frequency != 40 && args->frequency != 80 && args->frequency != 160) {
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
                fprintf(stderr, "Invalid acquisition mode: %d. Using default (1=TOA).\n", args->acq_mode);
                args->acq_mode = 1; // Reset to default
            }
            break;
        case 'r':
            args->readout_mode = atoi(arg);
            // Validate readout mode
            if (args->readout_mode < 0 || args->readout_mode > 1) {
                fprintf(stderr, "Invalid readout mode: %d. Using default (0=data-driven).\n", args->readout_mode);
                args->readout_mode = 0; // Reset to default
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
    printf("Readout mode:       %s\n", args->readout_mode ? "Frame" : "Data-driven");
    printf("Bias voltage:       %d V\n", args->bias);
    printf("Number of frames:   %d\n", args->frames);
    printf("Config file:        %s\n", args->config_file);
    printf("Device IP address:  %s\n", args->ip_address);
    printf("Acquisition time:   %.2e seconds\n", args->acq_time);
    printf("Polarity mode:      %s\n", args->polarity ? "Holes" : "Electrons");
    printf("Clock frequency:    %d MHz\n", args->frequency);
    printf("Vthreshold fine:    %d\n", args->vth_fine);
    printf("Vthreshold coarse:  %d\n", args->vth_coarse);
    const char *acq_modes[] = {"TOA_TOT", "TOA", "EVENT_ITOT"};
    printf("Acquisition mode:   %s\n", acq_modes[args->acq_mode]);
    printf("\n");
}

static const char *remote_addr = DEFAULT_ADDRESS; //Device IP address
typedef katherine_px_f_toa_tot_t px_t; //ACQ mode (Modes in px.h)

// Global variables
#define SENSOR_WIDTH 256
#define SENSOR_HEIGHT 256
static uint64_t pixel_counts[SENSOR_HEIGHT][SENSOR_WIDTH] = {0};
static uint64_t n_hits = 0;

// Frame mode specific variables
static void *frame_pixels = NULL;
static size_t frame_pixel_count = 0;
static size_t frame_pixel_capacity = 0;
static uint16_t pixel_count = 0;
static uint32_t event_count = 0;
static uint16_t integral_tot = 0;

// HDF5 File Structure
typedef struct {
    hid_t file_id;
    hid_t pixel_datatype;
    hid_t pixel_dataset;
    float current_bias;
} H5FileManager;

// Data Structure for HDF5 - Data-driven mode
typedef struct {
    int x;
    int y;
    uint64_t toa;
    uint8_t ftoa;
    uint16_t tot;
    uint32_t hit_count;
} PixelHitDataDriven;

// Data Structure for HDF5 - Frame mode
typedef struct {
    int x;
    int y;
    uint16_t integral_tot;
    uint16_t event_count;
    uint8_t hit_count;
} PixelHitFrame;


static H5FileManager h5_manager = {-1, -1, -1};
static struct arguments *global_args = NULL;

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

// HDF5 Functions for Data-driven mode
hid_t create_pixel_datatype_datadriven() {
    hid_t pixel_type = H5Tcreate(H5T_COMPOUND, sizeof(PixelHitDataDriven));
    H5Tinsert(pixel_type, "x", HOFFSET(PixelHitDataDriven, x), H5T_NATIVE_INT);
    H5Tinsert(pixel_type, "y", HOFFSET(PixelHitDataDriven, y), H5T_NATIVE_INT);
    H5Tinsert(pixel_type, "toa", HOFFSET(PixelHitDataDriven, toa), H5T_NATIVE_UINT64);
    H5Tinsert(pixel_type, "ftoa", HOFFSET(PixelHitDataDriven, ftoa), H5T_NATIVE_UINT8);
    H5Tinsert(pixel_type, "tot", HOFFSET(PixelHitDataDriven, tot), H5T_NATIVE_UINT16);
    H5Tinsert(pixel_type, "hit_count", HOFFSET(PixelHitDataDriven, hit_count), H5T_NATIVE_UINT32);
    return pixel_type;
}

// HDF5 Functions for Frame mode
hid_t create_pixel_datatype_frame() {
    hid_t pixel_type = H5Tcreate(H5T_COMPOUND, sizeof(PixelHitFrame));
    H5Tinsert(pixel_type, "x", HOFFSET(PixelHitFrame, x), H5T_NATIVE_INT);
    H5Tinsert(pixel_type, "y", HOFFSET(PixelHitFrame, y), H5T_NATIVE_INT);
    H5Tinsert(pixel_type, "hit_count", HOFFSET(PixelHitFrame, hit_count), H5T_NATIVE_UINT8);
    H5Tinsert(pixel_type, "event_count", HOFFSET(PixelHitFrame, event_count), H5T_NATIVE_UINT16);
    H5Tinsert(pixel_type, "integral_tot", HOFFSET(PixelHitFrame, integral_tot), H5T_NATIVE_UINT16);
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
        if (args->readout_mode == 0) {
            strftime(filename, sizeof(filename), "ToTdata_datadriven_%Y%m%d_%H%M%S.h5", timeinfo);
        } else {
            strftime(filename, sizeof(filename), "ToTdata_frame_%Y%m%d_%H%M%S.h5", timeinfo);
        }
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

    // Create datatype based on readout mode
    if (args->readout_mode == 0) {
        h5_manager.pixel_datatype = create_pixel_datatype_datadriven();
    } else {
        h5_manager.pixel_datatype = create_pixel_datatype_frame();
    }

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
    
    printf("Initialized HDF5 file: %s\n", filename);
}
// Add a global counter for sequential hit numbering
static uint64_t global_hit_counter = 0;

void write_pixel_hits_datadriven(const katherine_px_f_toa_tot_t *dpx, size_t count) {
    if (h5_manager.pixel_dataset < 0) return;

    // Init pixel hits
    PixelHitDataDriven *pixel_hits = malloc(count * sizeof(PixelHitDataDriven));
    
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
        
        // Increment global hit counter
        global_hit_counter++;
        n_hits++;
        
        // Populate the hit data structure
        pixel_hits[i].x = x;
        pixel_hits[i].y = y;
        pixel_hits[i].toa = dpx[i].toa;
        pixel_hits[i].ftoa = dpx[i].ftoa;
        pixel_hits[i].tot = dpx[i].tot;
        
        // OPTION 1: Use global sequential hit number
        pixel_hits[i].hit_count = global_hit_counter;
        
        // OPTION 2: Use per-pixel hit count (uncomment to use instead)
        // pixel_hits[i].hit_count = pixel_counts[y][x];
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

// Add reset function for new acquisitions
void reset_pixel_counts() {
    memset(pixel_counts, 0, sizeof(pixel_counts));
    n_hits = 0;
    global_hit_counter = 0;  // Add this line
}



void write_pixel_hits_frame(const struct katherine_px_f_event_itot *dpx, size_t count) {
    if (h5_manager.pixel_dataset < 0) return;

    // Init pixel hits
    PixelHitFrame *pixel_hits = malloc(count * sizeof(PixelHitFrame));
    
    for (size_t i = 0; i < count; ++i) {
        int x = dpx[i].coord.x;
        int y = dpx[i].coord.y;
        
        // Verify coordinates are within bounds
        if (x < 0 || x >= SENSOR_WIDTH || y < 0 || y >= SENSOR_HEIGHT) {
            printf("Warning: Pixel coordinates out of bounds: (%d, %d)\n", x, y);
            continue;
        }
                
        // Populate the hit data structure
        pixel_hits[i].x = x;
        pixel_hits[i].y = y;
        pixel_hits[i].integral_tot = dpx[i].integral_tot;
        pixel_hits[i].event_count = dpx[i].event_count;
        pixel_hits[i].hit_count = frame_pixel_count;
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
        .acq_mode = DEFAULT_ACQ_MODE,
        .readout_mode = DEFAULT_READOUT_MODE,
        .custom_output_file = 0,
        .show_detailed_help = 0
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
    global_hit_counter = 0;
    printf("Started frame %d.\n", frame_idx);
}

katherine_frame_info_t last_frame_info = {0};
void frame_ended(void *user_ctx, int frame_idx, bool completed, const katherine_frame_info_t *info) {
    if (global_args && global_args->readout_mode == 1) {
        // Frame mode: Write all collected pixels to HDF5
        if (frame_pixel_count > 0) {
            write_pixel_hits_frame((const struct katherine_px_f_event_itot *)frame_pixels, frame_pixel_count);
            printf("Wrote %zu pixels to HDF5 file\n", frame_pixel_count);
        }
        event_count = info->received_pixels;
    }

    const double recv_perc = 100. * info->received_pixels / info->sent_pixels;

    printf("\n");
    printf("Ended frame %d.\n", frame_idx);
    printf(" - tpx3->katherine lost %lu pixels\n", info->lost_pixels);
    printf(" - katherine->pc sent %lu pixels\n", info->sent_pixels);
    printf(" - katherine->pc received %lu pixels\n", info->received_pixels);
    printf(" - state: %s\n", (completed ? "completed" : "not completed"));
    printf(" - start time: %lu\n", info->start_time.d);
    printf(" - end time: %lu\n", info->end_time.d);
    
    if (global_args && global_args->readout_mode == 1) {
        printf(" - Events: %u\n", event_count);
        printf(" - Integral TOT: %u\n", integral_tot);
    }

    // Store last frame info
    memcpy(&last_frame_info, info, sizeof(katherine_frame_info_t));
}

void pixels_received(void *user_ctx, const void *px, size_t count) {
    if (!global_args) return;
    
    if (global_args->readout_mode == 0) {
        // Data-driven mode
        const katherine_px_f_toa_tot_t *dpx = (const katherine_px_f_toa_tot_t *) px;
        write_pixel_hits_datadriven(dpx, count);
    } else {
        // Frame mode
        const struct katherine_px_f_event_itot *dpx = (const struct katherine_px_f_event_itot *)px;
        
        // Ensure we have enough capacity
        if (frame_pixel_count + count > frame_pixel_capacity) {
            frame_pixel_capacity = (frame_pixel_count + count) * 2; // Double the capacity
            frame_pixels = realloc(frame_pixels, frame_pixel_capacity * sizeof(struct katherine_px_f_event_itot));
            if (!frame_pixels) {
                printf("Error: Failed to allocate memory for frame pixels\n");
                return;
            }
        }
        
        // Copy pixels to frame buffer
        memcpy((char*)frame_pixels + frame_pixel_count * sizeof(struct katherine_px_f_event_itot), 
               dpx, count * sizeof(struct katherine_px_f_event_itot));
        frame_pixel_count += count;
    }
}

void run_acquisition(katherine_device_t *device, const katherine_config_t *config, const struct arguments *args) {
    initialize_h5_file(args);
    
    katherine_acquisition_t acq;
    size_t pixel_size = (args->readout_mode == 0) ? sizeof(katherine_px_f_toa_tot_t) : sizeof(struct katherine_px_f_event_itot);
    
    int res = katherine_acquisition_init(&acq, device, NULL, 
                                     KATHERINE_MD_SIZE * 34952533, 
                                     pixel_size * 65536, 5000, 60000);
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
            printf("Using default TOA_ToT\n");
            acq_mode = ACQUISITION_MODE_TOA_TOT;
            break;
    }

    katherine_readout_type_t readout_mode = (args->readout_mode == 0) ? 
                                           READOUT_DATA_DRIVEN : READOUT_SEQUENTIAL;

    res = katherine_acquisition_begin(&acq, config, 
                                  readout_mode, 
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
    printf("Acquisition completed\n");
}