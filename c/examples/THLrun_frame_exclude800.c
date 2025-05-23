#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <string.h>
#include <unistd.h>
#include <katherine/katherine.h>
#include <hdf5.h>
#include <math.h>

static const char *remote_addr = "192.168.1.218"; //Device IP address
typedef struct katherine_px_f_event_itot px_t; //ACQ mode (Modes in px.h) Here we import all modes

// Global variables
#define SENSOR_WIDTH 256
#define SENSOR_HEIGHT 256
static uint64_t pixel_counts[SENSOR_HEIGHT][SENSOR_WIDTH] = {0};
static uint64_t n_hits = 0;
static uint16_t event_count = 0;
static uint8_t hit_count = 0;

// THL/DAC settings

#define MAX_COARSE 15 //Vthreshold_coarse DAC limit
#define MAX_FINE 511 //Vthreshold_fine DAC limit
#define FINE_STEP_MV 0.5 //Vthreshold_fine step in mV
#define COARSE_STEP_MV 80.0 //Vthreshold_coarse step in mV
#define MAX_THRESHOLD_MV ((MAX_COARSE * COARSE_STEP_MV) + (MAX_FINE * FINE_STEP_MV))

#define THL_MIN_MV 1000.0  // Start at 100 mV to avoid noise edge
#define THL_MAX_MV 1000.0 // Conservative max voltage
#define THL_STEP_MV 100.0  // Step in threshold voltage

#define FRAMES_PER_THL 1

// HDF5 File Structure
typedef struct {
    hid_t file_id;
    hid_t pixel_datatype;
    hid_t pixel_dataset;
    hid_t thl_dataset;    // Dataset to store THL scan results
    float current_bias;
    int current_thl;
} H5FileManager;

// Data Structure for HDF5
typedef struct {
    int x;
    int y;
    //uint64_t toa;
    //uint8_t ftoa;
    //uint16_t tot;
    uint16_t integral_tot;
    uint16_t event_count;
    uint8_t hit_count;
    int thl;
} PixelHit;

// THL scan result structure
typedef struct {
    int thl;
    int frame_idx;
    uint16_t event_count;
    uint8_t hit_count;
    //uint64_t hits;
} THLScanPoint;

static H5FileManager h5_manager = {-1, -1, -1, -1};

// Function prototypes
void configure(katherine_config_t *config, int thl_value);
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
void run_thl_scan(katherine_device_t *device);
void run_acquisition(katherine_device_t *device, const katherine_config_t *config);
// Add a global counter to track actual measurement points
static int thl_measurement_index = 0;
static int total_thl_measurements = 0;

// ***MUST BE FIXED! Wring indexing!***
void initialize_thl_scan_counter() {
    thl_measurement_index = 0;
    // Calculate exact number of steps
    total_thl_measurements = (int)((THL_MAX_MV - THL_MIN_MV) / THL_STEP_MV) + 1;
    printf("Total THL measurements: %d (from %.1f to %.1f mV in %.1f mV steps)\n",
           total_thl_measurements, THL_MIN_MV, THL_MAX_MV, THL_STEP_MV);
}

// HDF5 Initialization and Setup
hid_t create_pixel_datatype() {
    hid_t pixel_type = H5Tcreate(H5T_COMPOUND, sizeof(PixelHit));
    H5Tinsert(pixel_type, "x", HOFFSET(PixelHit, x), H5T_NATIVE_INT);
    H5Tinsert(pixel_type, "y", HOFFSET(PixelHit, y), H5T_NATIVE_INT);
    //H5Tinsert(pixel_type, "toa", HOFFSET(PixelHit, toa), H5T_NATIVE_UINT64);
    //H5Tinsert(pixel_type, "ftoa", HOFFSET(PixelHit, ftoa), H5T_NATIVE_UINT8);
    //H5Tinsert(pixel_type, "tot", HOFFSET(PixelHit, tot), H5T_NATIVE_UINT16);
    H5Tinsert(pixel_type, "hit_count", HOFFSET(PixelHit, hit_count), H5T_NATIVE_UINT8);
    H5Tinsert(pixel_type, "event_count", HOFFSET(PixelHit, event_count), H5T_NATIVE_UINT16);
    H5Tinsert(pixel_type, "integral_tot", HOFFSET(PixelHit, integral_tot), H5T_NATIVE_UINT16);
    H5Tinsert(pixel_type, "thl", HOFFSET(PixelHit, thl), H5T_NATIVE_INT);
    return pixel_type;
}

hid_t create_thl_scan_datatype() {
    hid_t thl_type = H5Tcreate(H5T_COMPOUND, sizeof(THLScanPoint));
    H5Tinsert(thl_type, "thl", HOFFSET(THLScanPoint, thl), H5T_NATIVE_INT);
    H5Tinsert(thl_type, "frame_idx", HOFFSET(THLScanPoint, frame_idx), H5T_NATIVE_INT);
    H5Tinsert(thl_type, "hit_count", HOFFSET(PixelHit, hit_count), H5T_NATIVE_UINT8);
    H5Tinsert(thl_type, "event_count", HOFFSET(PixelHit, event_count), H5T_NATIVE_UINT16);
    H5Tinsert(thl_type, "integral_tot", HOFFSET(PixelHit, integral_tot), H5T_NATIVE_UINT16);
    return thl_type;
}

void initialize_h5_file() {
    // Create filename with timestamp
    char filename[128];
    time_t now;
    time(&now);
    struct tm *timeinfo = localtime(&now);
    strftime(filename, sizeof(filename), "thl_calibration_%Y%m%d_%H%M%S.h5", timeinfo);

    // Create file
    hid_t plist_id = H5Pcreate(H5P_FILE_ACCESS);
    H5Pset_libver_bounds(plist_id, H5F_LIBVER_LATEST, H5F_LIBVER_LATEST);
    h5_manager.file_id = H5Fcreate(filename, H5F_ACC_TRUNC, H5P_DEFAULT, plist_id);
    H5Pclose(plist_id);

    if (h5_manager.file_id < 0) {
        printf("Failed to create HDF5 file: %s\n", filename);
        return;
    }

    h5_manager.pixel_datatype = create_pixel_datatype();
    hsize_t initial_dims[1] = {0};
    hsize_t max_dims[1] = {H5S_UNLIMITED};
    hid_t dataspace_id = H5Screate_simple(1, initial_dims, max_dims);

    hid_t plist = H5Pcreate(H5P_DATASET_CREATE);
    hsize_t chunk_dims[1] = {1000};
    H5Pset_chunk(plist, 1, chunk_dims);

    h5_manager.pixel_dataset = H5Dcreate(h5_manager.file_id, "/pixel_hits", h5_manager.pixel_datatype, 
                                       dataspace_id, H5P_DEFAULT, plist, H5P_DEFAULT);
    
    hid_t thl_datatype = create_thl_scan_datatype();
    int num_thl_points = total_thl_measurements;
    printf("Creating THL dataset with %d slots (indices 0-%d)\n", 
        num_thl_points, num_thl_points-1);
    hsize_t thl_dims[1] = {num_thl_points};
    hid_t thl_dataspace = H5Screate_simple(1, thl_dims, NULL);
    
    h5_manager.thl_dataset = H5Dcreate(h5_manager.file_id, "/thl_scan", thl_datatype, 
                                     thl_dataspace, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);

    hid_t attr_space = H5Screate(H5S_SCALAR);
    hid_t attr;
    
    attr = H5Acreate(h5_manager.file_id, "thl_start_mv", H5T_NATIVE_DOUBLE, attr_space, H5P_DEFAULT, H5P_DEFAULT);
    double thl_start = THL_MIN_MV;
    H5Awrite(attr, H5T_NATIVE_DOUBLE, &thl_start);
    H5Aclose(attr);
    
    attr = H5Acreate(h5_manager.file_id, "thl_end_mv", H5T_NATIVE_DOUBLE, attr_space, H5P_DEFAULT, H5P_DEFAULT);
    double thl_end = THL_MAX_MV;
    H5Awrite(attr, H5T_NATIVE_DOUBLE, &thl_end);
    H5Aclose(attr);
    
    attr = H5Acreate(h5_manager.file_id, "thl_step_mv", H5T_NATIVE_DOUBLE, attr_space, H5P_DEFAULT, H5P_DEFAULT);
    double thl_step = THL_STEP_MV;
    H5Awrite(attr, H5T_NATIVE_DOUBLE, &thl_step);
    H5Aclose(attr);
    
    attr = H5Acreate(h5_manager.file_id, "frames_per_thl", H5T_NATIVE_INT, attr_space, H5P_DEFAULT, H5P_DEFAULT);
    int frames_per_thl = FRAMES_PER_THL;
    H5Awrite(attr, H5T_NATIVE_INT, &frames_per_thl);
    H5Aclose(attr);

    // Close resources
    H5Sclose(attr_space);
    H5Tclose(thl_datatype);
    H5Sclose(thl_dataspace);
    H5Pclose(plist);
    H5Sclose(dataspace_id);
    h5_manager.current_thl = 0;
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
        //pixel_hits[i].toa = dpx[i].toa;
        //pixel_hits[i].ftoa = dpx[i].ftoa;
        //pixel_hits[i].tot = dpx[i].tot;
        pixel_hits[i].hit_count = dpx[i].hit_count;
        pixel_hits[i].event_count = dpx[i].event_count;
        pixel_hits[i].integral_tot = dpx[i].integral_tot;
        pixel_hits[i].thl = h5_manager.current_thl;
    }

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

    PixelHit *all_pixels = malloc(SENSOR_WIDTH * SENSOR_HEIGHT * sizeof(PixelHit));
    size_t index = 0;

    for (int y = 0; y < SENSOR_HEIGHT; ++y) {
        for (int x = 0; x < SENSOR_WIDTH; ++x) {
            all_pixels[index].x = x;
            all_pixels[index].y = y;
            //all_pixels[index].toa = 0;
            //all_pixels[index].ftoa = 0;
            //all_pixels[index].tot = 0;
            all_pixels[index].hit_count = 0;
            all_pixels[index].event_count = 0;
            all_pixels[index].integral_tot = 0;
            all_pixels[index].thl = h5_manager.current_thl;
            index++;
        }
    }

    // Write all pixels to the dataset
    filespace = H5Dget_space(h5_manager.pixel_dataset);
    H5Sget_simple_extent_dims(filespace, current_dims, NULL);

    new_size[0] = current_dims[0] + SENSOR_WIDTH * SENSOR_HEIGHT;
    H5Dset_extent(h5_manager.pixel_dataset, new_size);

    start[0] = current_dims[0];
    count_hslab[0] = SENSOR_WIDTH * SENSOR_HEIGHT;
    memspace = H5Screate_simple(1, count_hslab, NULL);
    
    filespace = H5Dget_space(h5_manager.pixel_dataset);
    H5Sselect_hyperslab(filespace, H5S_SELECT_SET, start, NULL, count_hslab, NULL);
    H5Dwrite(h5_manager.pixel_dataset, h5_manager.pixel_datatype, memspace, filespace, H5P_DEFAULT, all_pixels);

    free(all_pixels);
    H5Sclose(memspace);
    H5Sclose(filespace);
}

void write_thl_scan_point(double thl_mv, uint16_t hits) {
    if (h5_manager.thl_dataset < 0) return;
    if (thl_measurement_index >= total_thl_measurements) {
    printf("Error: Index %d >= dataset size %d (max index is %d)\n",
           thl_measurement_index, 
           total_thl_measurements,
           total_thl_measurements-1);
    return;
}

    printf("Writing THL %.1f mV at index %d/%d\n", 
           thl_mv, thl_measurement_index, total_thl_measurements-1);

    THLScanPoint point = {
        .thl = (int)(thl_mv),
        .event_count = event_count,
        .hit_count = hit_count
    };

    hsize_t start[1] = {thl_measurement_index};
    hsize_t count[1] = {1};
    
    hid_t dataspace = H5Dget_space(h5_manager.thl_dataset);
    H5Sselect_hyperslab(dataspace, H5S_SELECT_SET, start, NULL, count, NULL);
    
    hid_t memspace = H5Screate_simple(1, count, NULL);
    H5Dwrite(h5_manager.thl_dataset, create_thl_scan_datatype(), memspace, dataspace, H5P_DEFAULT, &point);
    
    H5Sclose(memspace);
    H5Sclose(dataspace);
    
    thl_measurement_index++;

    if (total_thl_measurements <= 0) {
    printf("CRITICAL ERROR: total_thl_measurements=%d (Did you call initialize_thl_scan_counter()?)\n",
           total_thl_measurements);
    return;
}
}

void close_h5_file() {
    if (h5_manager.thl_dataset >= 0) {
        H5Dclose(h5_manager.thl_dataset);
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
    // Reset file
    h5_manager.file_id = -1;
    h5_manager.pixel_dataset = -1;
    h5_manager.pixel_datatype = -1;
    h5_manager.thl_dataset = -1;
    h5_manager.current_bias = 0.0;
    h5_manager.current_thl = 0;
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
    
    // Run THL scan
    run_thl_scan(&device);

    // Closing device
    katherine_device_fini(&device);

    close_h5_file(); 
    return 0;
}

void configure(katherine_config_t *config, int thl_value) {
    // For now, these constants are hard-coded. (Used from krun)
    config->bias_id                 = 0;
    config->acq_time                = 1e8;
    config->no_frames               = 1;
    config->bias                    = 155; // V

    config->delayed_start           = false;

    config->start_trigger.enabled           = false;
    config->start_trigger.channel           = 0;
    config->start_trigger.use_falling_edge  = false;
    config->stop_trigger.enabled            = false;
    config->stop_trigger.channel            = 0;
    config->stop_trigger.use_falling_edge   = false;

    config->gray_disable            = true;
    config->polarity_holes          = true;

    config->phase                   = PHASE_1;
    config->freq                    = FREQ_40;

    config->dacs.named.Ibias_Preamp_ON       = 128;
    config->dacs.named.Ibias_Preamp_OFF      = 8;
    config->dacs.named.VPReamp_NCAS          = 128;
    config->dacs.named.Ibias_Ikrum           = 15;
    config->dacs.named.Vfbk                  = 164;
    config->dacs.named.Vthreshold_fine       = thl_value;  // THL value we're testing
    config->dacs.named.Vthreshold_coarse     = 7;
    config->dacs.named.Ibias_DiscS1_ON       = 100;
    config->dacs.named.Ibias_DiscS1_OFF      = 8;
    config->dacs.named.Ibias_DiscS2_ON       = 128;
    config->dacs.named.Ibias_DiscS2_OFF      = 8;
    config->dacs.named.Ibias_PixelDAC        = 100;
    config->dacs.named.Ibias_TPbufferIn      = 128;
    config->dacs.named.Ibias_TPbufferOut     = 128;
    config->dacs.named.VTP_coarse            = 128;
    config->dacs.named.VTP_fine              = 256;
    config->dacs.named.Ibias_CP_PLL          = 128;
    config->dacs.named.PLL_Vcntrl            = 128;

    int res = katherine_px_config_load_bmc_file(&config->pixel_config, "chipconfig_D4-W0005.bmc");
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

void digital_test(katherine_device_t *device) {
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
    printf("Started frame %d at THL=%d.\n", frame_idx, h5_manager.current_thl);
}

katherine_frame_info_t last_frame_info = {0};
void frame_ended(void *user_ctx, int frame_idx, bool completed, const katherine_frame_info_t *info) {
    // Save frame info for THL scan
    const double recv_perc = 100. * info->received_pixels / info->sent_pixels;
    n_hits = info->received_pixels;
    printf("\n");
    printf("Ended frame %d at THL=%d.\n", frame_idx, h5_manager.current_thl);
    printf(" - Pixels received: %lu\n", info->received_pixels);
    printf(" - tpx3->katherine lost %lu pixels\n", info->lost_pixels);
    printf(" - katherine->pc sent %lu pixels\n", info->sent_pixels);
    printf(" - state: %s\n", (completed ? "completed" : "not completed"));
    // Store THL scan point
    write_thl_scan_point(h5_manager.current_thl, n_hits);
    
    // Store last frame info
    memcpy(&last_frame_info, info, sizeof(katherine_frame_info_t));
}

pixels_received(void *user_ctx, const void *px, size_t count)
{
        const px_t *dpx = (const px_t *) px;
    for (size_t i = 0; i < count; ++i) {
        printf("%d\t%d\t%lu\t%d\t%d\n", dpx[i].coord.x, dpx[i].coord.y, dpx[i].integral_tot, dpx[i].hit_count, dpx[i].event_count);
    }
}

void reset_pixel_counts() {
    memset(pixel_counts, 0, sizeof(pixel_counts));
    n_hits = 0;
}

void run_acquisition(katherine_device_t *device, const katherine_config_t *config) {
    // Acquisition setup
    katherine_acquisition_t acq;
    int res = katherine_acquisition_init(&acq, device, NULL, 
                                         KATHERINE_MD_SIZE * 34952533, 
                                         sizeof(px_t) * 65536, 500, 30000);
    if (res != 0) {
        printf("Cannot initialize acquisition.\n");
        return;
    }

    // Set acquisition handlers
    acq.handlers.frame_started = frame_started;
    acq.handlers.frame_ended = frame_ended;
    acq.handlers.pixels_received = pixels_received;

    // Begin acquisition
    res = katherine_acquisition_begin(&acq, config, 
                                      READOUT_SEQUENTIAL, 
                                      ACQUISITION_MODE_EVENT_ITOT, 
                                      true, true);
    if (res != 0) {
        printf("Cannot begin acquisition.\n");
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
}

void run_thl_scan(katherine_device_t *device) {
    initialize_thl_scan_counter();
    initialize_h5_file();

    for (double thl_mv = THL_MIN_MV; thl_mv <= THL_MAX_MV; thl_mv += THL_STEP_MV) {
        if (thl_mv >= 800.0 && thl_mv <= 840.0) {
            printf("Skipping voltage range 800-840 mV (current target: %.1f mV)\n", thl_mv);
            continue;
        }
        int coarse;
        int fine;
        double actual_voltage;

        coarse = (int)(thl_mv / COARSE_STEP_MV);
        double remaining_mv = thl_mv - (coarse * COARSE_STEP_MV);
        fine = (int)(remaining_mv / FINE_STEP_MV + 0.5);

        if (coarse > MAX_COARSE) {
            coarse = MAX_COARSE;
            remaining_mv = thl_mv - (coarse * COARSE_STEP_MV);
            fine = (int)(remaining_mv / FINE_STEP_MV + 0.5);
        }
        if (fine > MAX_FINE) fine = MAX_FINE;
        if (fine < 0) fine = 0;
        actual_voltage = (coarse * COARSE_STEP_MV) + (fine * FINE_STEP_MV);


        printf("\nVoltage scan: target=%.1f mV → actual=%.1f mV (coarse=%d, fine=%d)\n", 
               thl_mv, actual_voltage, coarse, fine);
        
        h5_manager.current_thl = actual_voltage;
        
        katherine_config_t config;
        configure(&config, fine);
        config.dacs.named.Vthreshold_coarse = coarse;



        uint64_t total_hits = 0;
        for (int frame = 0; frame < FRAMES_PER_THL; frame++) {
            printf("Frame %d/%d for %.1f mV\n", frame + 1, FRAMES_PER_THL, actual_voltage);
            reset_pixel_counts();
            run_acquisition(device, &config);
            total_hits += n_hits;
            usleep(100000);
        }
    
        write_thl_scan_point(actual_voltage, total_hits);
    }
}