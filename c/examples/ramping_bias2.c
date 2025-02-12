#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <string.h>
#include <unistd.h>
#include <katherine/katherine.h>
#include <hdf5.h>
#include <math.h>




static const char *remote_addr = "192.168.1.218"; //Device IP address
typedef katherine_px_f_toa_tot_t px_t; //ACQ mode (Modes in px.h) Here we import all modes

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

static H5FileManager h5_manager = {-1, -1, -1, 0.0};


// Function prototypes
void configure(katherine_config_t *config);
void get_chip_id(katherine_device_t *device);
void get_comm_status(katherine_device_t *device);
void get_readout_temp(katherine_device_t *device);
void get_sensor_temp(katherine_device_t *device);
void digital_test(katherine_device_t *device);
void adc_voltage(katherine_device_t *device);
void set_bias(katherine_device_t *device, unsigned char bias_id, float bias_value);
void reset_pixel_counts();
void frame_started(void *user_ctx, int frame_idx);
void frame_ended(void *user_ctx, int frame_idx, bool completed, const katherine_frame_info_t *info);
void pixels_received(void *user_ctx, const void *px, size_t count);
void ramp_bias(katherine_device_t *device, katherine_config_t *config, float start_bias, float end_bias, float bias_step);
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

void initialize_h5_file(float start_bias, float end_bias, float bias_step) {
    // Create filename with timetamp
    char filename[128];
    time_t now;
    time(&now);
    struct tm *timeinfo = localtime(&now);
    strftime(filename, sizeof(filename), "pixel_data_%Y%m%d_%H%M%S.h5", timeinfo);

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

    // Store ramp parameters
    hid_t root_group = H5Gopen(h5_manager.file_id, "/", H5P_DEFAULT);
    hid_t attr_space = H5Screate(H5S_SCALAR);
    
    hid_t attr_id;
    attr_id = H5Acreate(root_group, "start_bias", H5T_NATIVE_FLOAT, attr_space, H5P_DEFAULT, H5P_DEFAULT);
    H5Awrite(attr_id, H5T_NATIVE_FLOAT, &start_bias);
    H5Aclose(attr_id);
    
    attr_id = H5Acreate(root_group, "end_bias", H5T_NATIVE_FLOAT, attr_space, H5P_DEFAULT, H5P_DEFAULT);
    H5Awrite(attr_id, H5T_NATIVE_FLOAT, &end_bias);
    H5Aclose(attr_id);
    
    attr_id = H5Acreate(root_group, "bias_step", H5T_NATIVE_FLOAT, attr_space, H5P_DEFAULT, H5P_DEFAULT);
    H5Awrite(attr_id, H5T_NATIVE_FLOAT, &bias_step);
    H5Aclose(attr_id);
    
    H5Sclose(attr_space);
    H5Gclose(root_group);
}

void prepare_bias_dataset(float bias_voltage) {
    // Close opened dataset if exists
    if (h5_manager.pixel_dataset >= 0) {
        H5Dclose(h5_manager.pixel_dataset);
    }

    // Create group for current (or whatever the starting point is) bias voltage
    char group_name[64];
    snprintf(group_name, sizeof(group_name), "/bias_%.2fV", bias_voltage);
    hid_t group_id = H5Gcreate(h5_manager.file_id, group_name, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);

    // Create dataset
    hsize_t initial_dims[1] = {0};
    hsize_t max_dims[1] = {H5S_UNLIMITED};
    hid_t dataspace_id = H5Screate_simple(1, initial_dims, max_dims);

    hid_t plist = H5Pcreate(H5P_DATASET_CREATE);
    hsize_t chunk_dims[1] = {1000};
    H5Pset_chunk(plist, 1, chunk_dims);

    h5_manager.pixel_dataset = H5Dcreate(group_id, "pixel_hits", h5_manager.pixel_datatype, 
                                         dataspace_id, H5P_DEFAULT, plist, H5P_DEFAULT);

    // Store current bias
    h5_manager.current_bias = bias_voltage;

    // Close
    H5Pclose(plist);
    H5Sclose(dataspace_id);
    H5Gclose(group_id);
}

void write_pixel_hits(const px_t *dpx, size_t count) {
    if (h5_manager.pixel_dataset < 0) return;

    // Init pixel hits
    PixelHit *pixel_hits = malloc(count * sizeof(PixelHit));
    
    for (size_t i = 0; i < count; ++i) {
        pixel_hits[i].x = dpx[i].coord.x;
        pixel_hits[i].y = dpx[i].coord.y;
        pixel_hits[i].toa = dpx[i].toa;
        pixel_hits[i].ftoa = dpx[i].ftoa;
        pixel_hits[i].tot = dpx[i].tot;
        pixel_hits[i].hit_count = pixel_counts[dpx[i].coord.y][dpx[i].coord.x]++;
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
    // Loading config
    katherine_config_t c; 
    configure(&c);

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
    ramp_bias(&device, &c, -190.0, -100.0, 2.0);


    // Closing device
    katherine_device_fini(&device);

    close_h5_file(); 
    return 0;
}

void configure(katherine_config_t *config) {
    // For now, these constants are hard-coded. (Used from krun)
    config->bias_id                 = 0;
    config->acq_time                = 1e8; // ns
    config->no_frames               = 1;
    config->bias                    = 270; // V

    config->delayed_start           = false;

    config->start_trigger.enabled           = false;
    config->start_trigger.channel           = 0;
    config->start_trigger.use_falling_edge  = false;
    config->stop_trigger.enabled            = false;
    config->stop_trigger.channel            = 0;
    config->stop_trigger.use_falling_edge   = false;

    config->gray_disable            = false;
    config->polarity_holes          = false;

    config->phase                   = PHASE_1;
    config->freq                    = FREQ_40;

    config->dacs.named.Ibias_Preamp_ON       = 128;
    config->dacs.named.Ibias_Preamp_OFF      = 8;
    config->dacs.named.VPReamp_NCAS          = 128;
    config->dacs.named.Ibias_Ikrum           = 15;
    config->dacs.named.Vfbk                  = 164;
    config->dacs.named.Vthreshold_fine       = 476;
    config->dacs.named.Vthreshold_coarse     = 8;
    config->dacs.named.Ibias_DiscS1_ON       = 100;
    config->dacs.named.Ibias_DiscS1_OFF      = 8;
    config->dacs.named.Ibias_DiscS2_ON       = 128;
    config->dacs.named.Ibias_DiscS2_OFF      = 8;
    config->dacs.named.Ibias_PixelDAC        = 128;
    config->dacs.named.Ibias_TPbufferIn      = 128;
    config->dacs.named.Ibias_TPbufferOut     = 128;
    config->dacs.named.VTP_coarse            = 128;
    config->dacs.named.VTP_fine              = 256;
    config->dacs.named.Ibias_CP_PLL          = 128;
    config->dacs.named.PLL_Vcntrl            = 128;

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
        usleep(500000); // Wait before retrying
        retries--;
    }
    printf("Setting bias failed at %.2fV after multiple attempts.\n", bias_value);
    exit(12);
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

void ramp_bias(katherine_device_t *device, katherine_config_t *config, float start_bias, float end_bias, float bias_step) {
    // Initialize HDF5 file with ramp parameters
    initialize_h5_file(start_bias, end_bias, bias_step);

    // Determine ramping direction and step
    float step = (start_bias <= end_bias) ? fabs(bias_step) : -fabs(bias_step);
    float current_voltage = start_bias;

    while ((step > 0 && current_voltage <= end_bias) || 
           (step < 0 && current_voltage >= end_bias)) {
        
        // Prepare dataset for this bias voltage
        prepare_bias_dataset(current_voltage);
        
        // Reset pixel counts
        reset_pixel_counts();

        // Set bias and run acquisition
        set_bias(device, 0, current_voltage);
        config->bias = current_voltage;
        usleep(500000); // Waiting delay time before the next voltage

        // Acquisition setup
        katherine_acquisition_t acq;
        int res = katherine_acquisition_init(&acq, device, NULL, 
                                             KATHERINE_MD_SIZE * 34952533, 
                                             sizeof(px_t) * 65536, 500, 30000);
        if (res != 0) {
            printf("Cannot initialize acquisition at bias %.2fV.\n", current_voltage);
            break;
        }

        // Set acquisition handlers
        acq.handlers.frame_started = frame_started;
        acq.handlers.frame_ended = frame_ended;
        acq.handlers.pixels_received = pixels_received;

        // Begin acquisition
        res = katherine_acquisition_begin(&acq, config, 
                                          READOUT_DATA_DRIVEN, 
                                          ACQUISITION_MODE_TOA_TOT, 
                                          true, true);
        if (res != 0) {
            printf("Cannot begin acquisition at bias %.2fV.\n", current_voltage);
            katherine_acquisition_fini(&acq);
            break;
        }

        // Read acquisition data
        res = katherine_acquisition_read(&acq);
        if (res != 0) {
            printf("Cannot read acquisition data at bias %.2fV.\n", current_voltage);
            katherine_acquisition_fini(&acq);
            break;
        }

        // Finalize acquisition
        katherine_acquisition_fini(&acq);
        
        // Move to next voltage
        current_voltage += step;
    }

    // Close HDF5 file
    close_h5_file();

    printf("Bias ramping and acquisition sequence completed\n");
}