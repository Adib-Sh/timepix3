#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <string.h>
#include <unistd.h>
#include <katherine/katherine.h>
#include <hdf5.h>
#include <math.h>

static const char *remote_addr = "192.168.1.218"; // Device IP address
typedef katherine_px_f_toa_tot_t px_t; // ACQ mode (Modes in px.h)

// Global variables
#define SENSOR_WIDTH 256
#define SENSOR_HEIGHT 256
static uint64_t pixel_counts[SENSOR_HEIGHT][SENSOR_WIDTH] = {0};
static uint64_t n_hits = 0;

// Bias voltage scan settings
#define BIAS_START 80.0f    // Start bias value (V)
#define BIAS_END 100.0f     // End bias value (V)
#define BIAS_STEP 5.0f      // Bias step size (V)
#define FRAMES_PER_BIAS 1   // Number of frames per bias point
#define ACQ_TIME 1e8       // 100ms acquisition time
#define BIAS_ID 0          // Bias channel ID

// HDF5 File Structure
typedef struct {
    hid_t file_id;
    hid_t pixel_datatype;
    hid_t pixel_dataset;
    hid_t bias_dataset;
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
    float bias;
} PixelHit;

// Bias scan result structure
typedef struct {
    float bias;
    int frame_idx;
    uint64_t hits;
} BiasScanPoint;

static H5FileManager h5_manager = {-1, -1, -1, -1};

// Function prototypes
void configure(katherine_config_t *config, float bias_value);
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
void set_bias(katherine_device_t *device, unsigned char bias_id, float bias_value);
void run_bias_scan(katherine_device_t *device);
void run_acquisition(katherine_device_t *device, const katherine_config_t *config);

// HDF5 Initialization and Setup
hid_t create_pixel_datatype() {
    hid_t pixel_type = H5Tcreate(H5T_COMPOUND, sizeof(PixelHit));
    H5Tinsert(pixel_type, "x", HOFFSET(PixelHit, x), H5T_NATIVE_INT);
    H5Tinsert(pixel_type, "y", HOFFSET(PixelHit, y), H5T_NATIVE_INT);
    H5Tinsert(pixel_type, "toa", HOFFSET(PixelHit, toa), H5T_NATIVE_UINT64);
    H5Tinsert(pixel_type, "ftoa", HOFFSET(PixelHit, ftoa), H5T_NATIVE_UINT8);
    H5Tinsert(pixel_type, "tot", HOFFSET(PixelHit, tot), H5T_NATIVE_UINT16);
    H5Tinsert(pixel_type, "hit_count", HOFFSET(PixelHit, hit_count), H5T_NATIVE_UINT32);
    H5Tinsert(pixel_type, "bias", HOFFSET(PixelHit, bias), H5T_NATIVE_FLOAT);
    return pixel_type;
}

hid_t create_bias_scan_datatype() {
    hid_t bias_type = H5Tcreate(H5T_COMPOUND, sizeof(BiasScanPoint));
    H5Tinsert(bias_type, "bias", HOFFSET(BiasScanPoint, bias), H5T_NATIVE_FLOAT);
    H5Tinsert(bias_type, "frame_idx", HOFFSET(BiasScanPoint, frame_idx), H5T_NATIVE_INT);
    H5Tinsert(bias_type, "hits", HOFFSET(BiasScanPoint, hits), H5T_NATIVE_UINT64);
    return bias_type;
}

void initialize_h5_file() {
    // Create filename with timestamp
    char filename[128];
    time_t now;
    time(&now);
    struct tm *timeinfo = localtime(&now);
    strftime(filename, sizeof(filename), "bias_scan_%Y%m%d_%H%M%S.h5", timeinfo);

    // Create file
    hid_t plist_id = H5Pcreate(H5P_FILE_ACCESS);
    H5Pset_libver_bounds(plist_id, H5F_LIBVER_LATEST, H5F_LIBVER_LATEST);
    h5_manager.file_id = H5Fcreate(filename, H5F_ACC_TRUNC, H5P_DEFAULT, plist_id);
    H5Pclose(plist_id);

    if (h5_manager.file_id < 0) {
        printf("Failed to create HDF5 file: %s\n", filename);
        return;
    }

    // Create datatype for pixel hits
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

    // Create dataset for bias scan results
    hid_t bias_datatype = create_bias_scan_datatype();
    
    // Calculate number of bias points
    int num_bias_points = ((BIAS_END - BIAS_START) / BIAS_STEP + 1) * FRAMES_PER_BIAS;
    hsize_t bias_dims[1] = {num_bias_points};
    hid_t bias_dataspace = H5Screate_simple(1, bias_dims, NULL);
    
    h5_manager.bias_dataset = H5Dcreate(h5_manager.file_id, "/bias_scan", bias_datatype, 
                                       bias_dataspace, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
    
    // Store bias scan parameters as attributes
    hid_t attr_space = H5Screate(H5S_SCALAR);
    hid_t attr;
    
    attr = H5Acreate(h5_manager.file_id, "bias_start", H5T_NATIVE_FLOAT, attr_space, H5P_DEFAULT, H5P_DEFAULT);
    float bias_start = BIAS_START;
    H5Awrite(attr, H5T_NATIVE_FLOAT, &bias_start);
    H5Aclose(attr);
    
    attr = H5Acreate(h5_manager.file_id, "bias_end", H5T_NATIVE_FLOAT, attr_space, H5P_DEFAULT, H5P_DEFAULT);
    float bias_end = BIAS_END;
    H5Awrite(attr, H5T_NATIVE_FLOAT, &bias_end);
    H5Aclose(attr);
    
    attr = H5Acreate(h5_manager.file_id, "bias_step", H5T_NATIVE_FLOAT, attr_space, H5P_DEFAULT, H5P_DEFAULT);
    float bias_step = BIAS_STEP;
    H5Awrite(attr, H5T_NATIVE_FLOAT, &bias_step);
    H5Aclose(attr);
    
    attr = H5Acreate(h5_manager.file_id, "frames_per_bias", H5T_NATIVE_INT, attr_space, H5P_DEFAULT, H5P_DEFAULT);
    int frames_per_bias = FRAMES_PER_BIAS;
    H5Awrite(attr, H5T_NATIVE_INT, &frames_per_bias);
    H5Aclose(attr);

    // Close resources
    H5Sclose(attr_space);
    H5Tclose(bias_datatype);
    H5Sclose(bias_dataspace);
    H5Pclose(plist);
    H5Sclose(dataspace_id);
    
    // Initialize current bias value
    h5_manager.current_bias = BIAS_START;
}

void write_pixel_hits(const px_t *dpx, size_t count) {
    if (h5_manager.pixel_dataset < 0) return;

    PixelHit *pixel_hits = malloc(count * sizeof(PixelHit));
    for (size_t i = 0; i < count; ++i) {
        int x = dpx[i].coord.x;
        int y = dpx[i].coord.y;
        
        if (x < 0 || x >= SENSOR_WIDTH || y < 0 || y >= SENSOR_HEIGHT) {
            printf("Warning: Pixel coordinates out of bounds: (%d, %d)\n", x, y);
            continue;
        }
        
        pixel_counts[y][x]++;
        
        pixel_hits[i].x = x;
        pixel_hits[i].y = y;
        pixel_hits[i].toa = dpx[i].toa;
        pixel_hits[i].ftoa = dpx[i].ftoa;
        pixel_hits[i].tot = dpx[i].tot;
        pixel_hits[i].hit_count = pixel_counts[y][x];
        pixel_hits[i].bias = h5_manager.current_bias;
    }

    // Write the hits
    hid_t filespace = H5Dget_space(h5_manager.pixel_dataset);
    hsize_t current_dims[1];
    H5Sget_simple_extent_dims(filespace, current_dims, NULL);

    hsize_t new_size[1] = {current_dims[0] + count};
    H5Dset_extent(h5_manager.pixel_dataset, new_size);

    hsize_t start[1] = {current_dims[0]};
    hsize_t count_hslab[1] = {count};
    hid_t memspace = H5Screate_simple(1, count_hslab, NULL);
    
    filespace = H5Dget_space(h5_manager.pixel_dataset);
    H5Sselect_hyperslab(filespace, H5S_SELECT_SET, start, NULL, count_hslab, NULL);
    H5Dwrite(h5_manager.pixel_dataset, h5_manager.pixel_datatype, memspace, filespace, H5P_DEFAULT, pixel_hits);

    free(pixel_hits);
    H5Sclose(memspace);
    H5Sclose(filespace);
}

void write_bias_scan_point(float bias, int frame_idx, uint64_t hits) {
    if (h5_manager.bias_dataset < 0) return;
    
    BiasScanPoint point;
    point.bias = bias;
    point.frame_idx = frame_idx;
    point.hits = hits;
    
    int bias_index = ((bias - BIAS_START) / BIAS_STEP) * FRAMES_PER_BIAS + frame_idx;
    
    hsize_t start[1] = {bias_index};
    hsize_t count[1] = {1};
    
    hid_t dataspace = H5Dget_space(h5_manager.bias_dataset);
    H5Sselect_hyperslab(dataspace, H5S_SELECT_SET, start, NULL, count, NULL);
    
    hid_t memspace = H5Screate_simple(1, count, NULL);
    
    H5Dwrite(h5_manager.bias_dataset, h5_manager.pixel_datatype, memspace, dataspace, H5P_DEFAULT, &point);
    
    H5Sclose(memspace);
    H5Sclose(dataspace);
}

void close_h5_file() {
    if (h5_manager.bias_dataset >= 0) {
        H5Dclose(h5_manager.bias_dataset);
    }
    if (h5_manager.pixel_dataset >= 0) {
        H5Dclose(h5_manager.pixel_dataset);
    }
    if (h5_manager.pixel_datatype >= 0) {
        H5Tclose(h5_manager.pixel_datatype);
    }
    if (h5_manager.file_id >= 0) {
        H5Fclose(h5_manager.file_id);
    }
    h5_manager.file_id = -1;
    h5_manager.pixel_dataset = -1;
    h5_manager.pixel_datatype = -1;
    h5_manager.bias_dataset = -1;
    h5_manager.current_bias = 0.0;
}

int main(int argc, char *argv[]) {
    // Initializing device
    int res;
    katherine_device_t device; 

    // Retry mechanism for connection
    int retries = 3;
    while (retries > 0) {
        printf("Attempting to connect to device at %s...\n", remote_addr);
        res = katherine_device_init(&device, remote_addr);
        if (res == 0) break;
        printf("Connection failed: %s. Retrying... (%d attempts left)\n", strerror(res), retries);
        sleep(1);
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
    
    // Run bias scan
    run_bias_scan(&device);

    // Closing device
    katherine_device_fini(&device);

    close_h5_file(); 
    return 0;
}

void configure(katherine_config_t *config, float bias_value) {
    config->bias_id = 0;
    config->acq_time = ACQ_TIME;
    config->no_frames = 1;
    config->bias = bias_value;

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
    config->dacs.named.Vthreshold_fine = 476;
    config->dacs.named.Vthreshold_coarse = 8;
    config->dacs.named.Ibias_DiscS1_ON = 100;
    config->dacs.named.Ibias_DiscS1_OFF = 8;
    config->dacs.named.Ibias_DiscS2_ON = 128;
    config->dacs.named.Ibias_DiscS2_OFF = 8;
    config->dacs.named.Ibias_PixelDAC = 128;
    config->dacs.named.Ibias_TPbufferIn = 128;
    config->dacs.named.Ibias_TPbufferOut = 128;
    config->dacs.named.VTP_coarse = 128;
    config->dacs.named.VTP_fine = 256;
    config->dacs.named.Ibias_CP_PLL = 128;
    config->dacs.named.PLL_Vcntrl = 128;

    int res = katherine_px_config_load_bmc_file(&config->pixel_config, "chipconfig.bmc");
    if (res != 0) {
        printf("Cannot load pixel configuration. Does the file exist?\n");
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

void set_bias(katherine_device_t *device, unsigned char bias_id, float bias_value) {
    int retries = 3;
    while (retries > 0) {
        int res = katherine_set_bias(device, bias_id, bias_value);
        if (res == 0) {
            printf("Bias set at: %.2fV\n", bias_value);
            return;
        }
        printf("Setting bias failed at %.2fV! Retrying... (%d attempts left)\n", bias_value, retries);
        usleep(500000);
        retries--;
    }
    printf("Setting bias failed at %.2fV after multiple attempts.\n", bias_value);
    exit(12);
}

void run_bias_scan(katherine_device_t *device) {
    printf("\n=== Starting Bias Voltage Scan ===\n");
    printf("Range: %.1fV to %.1fV in %.1fV steps\n", BIAS_START, BIAS_END, BIAS_STEP);
    
    initialize_h5_file();
    
    for (float bias = BIAS_START; bias <= BIAS_END; bias += BIAS_STEP) {
        printf("\n=== Setting bias to %.1fV ===\n", bias);
        
        // Set the bias voltage
        set_bias(device, BIAS_ID, bias);
        h5_manager.current_bias = bias;
        
        // Configure remaining parameters
        katherine_config_t config;
        configure(&config, bias);
        
        for (int frame = 0; frame < FRAMES_PER_BIAS; frame++) {
            printf("Frame %d/%d at %.1fV\n", frame+1, FRAMES_PER_BIAS, bias);
            reset_pixel_counts();
            run_acquisition(device, &config);
            usleep(100000);
        }
    }
    
    printf("\n=== Bias Scan Complete ===\n");
}

void run_acquisition(katherine_device_t *device, const katherine_config_t *config) {
    katherine_acquisition_t acq;
    int res = katherine_acquisition_init(&acq, device, NULL, 
                                         KATHERINE_MD_SIZE * 34952533, 
                                         sizeof(px_t) * 65536, 500, 30000);
    if (res != 0) {
        printf("Cannot initialize acquisition.\n");
        return;
    }

    acq.handlers.frame_started = frame_started;
    acq.handlers.frame_ended = frame_ended;
    acq.handlers.pixels_received = pixels_received;

    res = katherine_acquisition_begin(&acq, config, 
                                      READOUT_DATA_DRIVEN, 
                                      ACQUISITION_MODE_TOA_TOT, 
                                      true, true);
    if (res != 0) {
        printf("Cannot begin acquisition.\n");
        katherine_acquisition_fini(&acq);
        return;
    }

    res = katherine_acquisition_read(&acq);
    if (res != 0) {
        printf("Cannot read acquisition data.\n");
        katherine_acquisition_fini(&acq);
        return;
    }

    katherine_acquisition_fini(&acq);
}

void frame_started(void *user_ctx, int frame_idx) {
    n_hits = 0;
    printf("Started frame %d at bias=%.1fV.\n", frame_idx, h5_manager.current_bias);
}

katherine_frame_info_t last_frame_info = {0};
void frame_ended(void *user_ctx, int frame_idx, bool completed, const katherine_frame_info_t *info) {
    n_hits = info->received_pixels;
    
    printf("\n");
    printf("Ended frame %d at bias=%.1fV.\n", frame_idx, h5_manager.current_bias);
    printf(" - Pixels received: %lu\n", info->received_pixels);
    printf(" - tpx3->katherine lost %lu pixels\n", info->lost_pixels);
    printf(" - katherine->pc sent %lu pixels\n", info->sent_pixels);
    
    write_bias_scan_point(h5_manager.current_bias, frame_idx, n_hits);
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