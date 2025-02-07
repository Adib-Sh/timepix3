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

// Global variables for configuration and modes
static uint64_t n_hits; //
#define SENSOR_WIDTH 256
#define SENSOR_HEIGHT 256

typedef struct {
    float bias_voltage;
    unsigned long long total_hits;
    int frame_count;
    float total_duration;
    float throughput;
    unsigned long lost_pixels;
    unsigned long sent_pixels;
    unsigned long received_pixels;
} BiasPointData;

static uint64_t pixel_counts[SENSOR_HEIGHT][SENSOR_WIDTH] = {0}; 
static hid_t file_id = -1; // HDF5 file identifier, initialized to invalid
static int current_voltage_index = 0; 

// Function prototypes
void configure(katherine_config_t *config);
void frame_started(void *user_ctx, int frame_idx);
void frame_ended(void *user_ctx, int frame_idx, bool completed, const katherine_frame_info_t *info);
void pixels_received(void *user_ctx, const void *px, size_t count);
void get_chip_id(katherine_device_t *device);
void get_comm_status(katherine_device_t *device);
void get_readout_temp(katherine_device_t *device);
void get_sensor_temp(katherine_device_t *device);
void digital_test(katherine_device_t *device);
void adc_voltage(katherine_device_t *device);
void run_acquisition(katherine_device_t *dev, const katherine_config_t *c);
void set_bias(katherine_device_t *device, unsigned char bias_id, float bias_value);
void ramp_bias(katherine_device_t *device, katherine_config_t *config, float start_bias, float end_bias, float bias_step);
void run_acquisition_at_bias(katherine_device_t *dev, const katherine_config_t *c, float bias_value);


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
        if (res == 0) break; // Success
        printf("Connection failed: %s. Retrying... (%d attempts left)\n", strerror(res), retries);
        sleep(1); // Wait before retrying
        retries--;
    }
    if (res != 0) {
        printf("Cannot initialize device after multiple attempts.\n");
        exit(6);
    }
    printf("Connected successfully.\n");

    
    // enable_scanning_modes(); // enabling scan modes
    get_comm_status(&device);
    get_chip_id(&device);
    get_readout_temp(&device);
    get_sensor_temp(&device);
    digital_test(&device);
    adc_voltage(&device);  
    ramp_bias(&device, &c, 120.0, 240.0, 30.0);


    // Closing device
    katherine_device_fini(&device);

    // Close HDF5 file after acquisition
    if (file_id >= 0) {
        H5Fclose(file_id); 
    }
    return 0;
}


void configure(katherine_config_t *config) {
    // For now, these constants are hard-coded. (Used from krun)
    config->bias_id                 = 0;
    config->acq_time                = 5e8; // ns
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
static float current_bias_voltage = 0.0;

void pixels_received(void *user_ctx, const void *px, size_t count) {
    n_hits += count;
    const px_t *dpx = (const px_t *) px;

    // Prepare data for writing
    int *data = malloc(count * 6 * sizeof(int)); // 6 columns: X, Y, ToA, fToA, ToT, hit count
    for (size_t i = 0; i < count; ++i) {
        data[i * 6 + 0] = dpx[i].coord.x;
        data[i * 6 + 1] = dpx[i].coord.y;
        data[i * 6 + 2] = (int)dpx[i].toa;
        data[i * 6 + 3] = dpx[i].ftoa;
        data[i * 6 + 4] = dpx[i].tot;
        data[i * 6 + 5] = pixel_counts[dpx[i].coord.y][dpx[i].coord.x]++;

        // Update the count for this pixel
        if (dpx[i].coord.x < SENSOR_WIDTH && dpx[i].coord.y < SENSOR_HEIGHT) {
            pixel_counts[dpx[i].coord.y][dpx[i].coord.x]++;
        }
    }

    if (file_id < 0) {
        printf("Invalid HDF5 file ID. Cannot write pixel data.\n");
        free(data);
        return;
    }

    // Create a group for the bias voltage with a more precise naming
    char group_name[64];
    snprintf(group_name, sizeof(group_name), "/bias_%.2fV", current_bias_voltage);
    hid_t group_id = H5Gopen(file_id, group_name, H5P_DEFAULT);
    if (group_id < 0) {
        group_id = H5Gcreate(file_id, group_name, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
    }

    // Unique dataset name per frame
    static int frame_counter = 0;
    char dataset_name[64];
    snprintf(dataset_name, sizeof(dataset_name), "frame_pixel_data_%d", frame_counter++);

    hid_t dataset_id = H5Dopen(group_id, dataset_name, H5P_DEFAULT);
    if (dataset_id < 0) {
        hsize_t initial_dims[2] = {0, 5};
        hsize_t max_dims[2] = {H5S_UNLIMITED, 5};
        hid_t dataspace_id = H5Screate_simple(2, initial_dims, max_dims);
        
        hid_t plist_id = H5Pcreate(H5P_DATASET_CREATE);
        hsize_t chunk_dims[2] = {1000, 5};
        H5Pset_chunk(plist_id, 2, chunk_dims);

        dataset_id = H5Dcreate(group_id, dataset_name, H5T_NATIVE_INT, 
                               dataspace_id, H5P_DEFAULT, plist_id, H5P_DEFAULT);
        
        H5Pclose(plist_id);
        H5Sclose(dataspace_id);
    }

    // Extend dataset to accommodate new data
    hid_t filespace_id = H5Dget_space(dataset_id);
    hsize_t current_dims[2];
    H5Sget_simple_extent_dims(filespace_id, current_dims, NULL);

    hsize_t new_dims[2] = {current_dims[0] + count, 5};
    H5Dset_extent(dataset_id, new_dims);

    H5Sclose(filespace_id);
    filespace_id = H5Dget_space(dataset_id);

    // Write data
    hsize_t start[2] = {current_dims[0], 0};
    hsize_t count_hslab[2] = {count, 5};
    hid_t memspace_id = H5Screate_simple(2, count_hslab, NULL);

    H5Sselect_hyperslab(filespace_id, H5S_SELECT_SET, start, NULL, count_hslab, NULL);
    H5Dwrite(dataset_id, H5T_NATIVE_INT, memspace_id, filespace_id, H5P_DEFAULT, data);

    free(data);
    H5Sclose(memspace_id);
    H5Sclose(filespace_id);
    H5Dclose(dataset_id);
    H5Gclose(group_id);
}

void reset_pixel_counts() {

    memset(pixel_counts, 0, sizeof(pixel_counts));
}

void run_acquisition_at_bias(katherine_device_t *dev, const katherine_config_t *c, float bias_value) {
    // Reset pixel counts for new acquisition
    reset_pixel_counts();
    
    // Create dataset in advance
    char group_name[64];
    snprintf(group_name, sizeof(group_name), "/voltage_%03d", current_voltage_index);
    
    // Ensure group exists
    hid_t group_id = H5Gopen(file_id, group_name, H5P_DEFAULT);
    if (group_id < 0) {
        printf("Failed to open group %s\n", group_name);
        return;
    }
    
    // Create initial dataset
    hsize_t initial_dims[2] = {0, 5};
    hsize_t max_dims[2] = {H5S_UNLIMITED, 5};
    hid_t dataspace_id = H5Screate_simple(2, initial_dims, max_dims);
    
    hid_t plist_id = H5Pcreate(H5P_DATASET_CREATE);
    hsize_t chunk_dims[2] = {1000, 5};
    H5Pset_chunk(plist_id, 2, chunk_dims);

    hid_t dataset_id = H5Dcreate(group_id, "frame_pixel_data", H5T_NATIVE_INT, 
                                 dataspace_id, H5P_DEFAULT, plist_id, H5P_DEFAULT);
    
    H5Dclose(dataset_id);
    H5Pclose(plist_id);
    H5Sclose(dataspace_id);
    H5Gclose(group_id);
    
    // Run acquisition
    int res;
    katherine_acquisition_t acq;
    
    res = katherine_acquisition_init(&acq, dev, NULL, KATHERINE_MD_SIZE * 34952533, sizeof(px_t) * 65536, 500, 30000);
    if (res != 0) {
        printf("Cannot initialize acquisition at bias %.2fV.\n", bias_value);
        printf("Reason: %s\n", strerror(res));
        exit(3);
    }

    acq.handlers.frame_started = frame_started;
    acq.handlers.frame_ended = frame_ended;
    acq.handlers.pixels_received = pixels_received;

    res = katherine_acquisition_begin(&acq, c, READOUT_DATA_DRIVEN, ACQUISITION_MODE_TOA_TOT, true, true);
    if (res != 0) {
        printf("Cannot begin acquisition at bias %.2fV.\n", bias_value);
        printf("Reason: %s\n", strerror(res));
        exit(4);
    }

    printf("Acquisition started at bias %.2fV.\n", bias_value);

    time_t tic = time(NULL);
    res = katherine_acquisition_read(&acq);
    if (res != 0) {
        printf("Cannot read acquisition data at bias %.2fV.\n", bias_value);
        printf("Reason: %s\n", strerror(res));
        exit(5);
    }
    time_t toc = time(NULL);

    double duration = difftime(toc, tic);
    printf("\n");
    printf("Acquisition completed at bias %.2fV:\n", bias_value);
    printf(" - state: %s\n", katherine_str_acquisition_status(acq.state));
    printf(" - received %d complete frames\n", acq.completed_frames);
    printf(" - dropped %zu measurement data\n", acq.dropped_measurement_data);
    printf(" - total hits: %lu\n", n_hits);
    printf(" - total duration: %f s\n", duration);
    printf(" - throughput: %f hits/s\n", (n_hits / duration));

    katherine_acquisition_fini(&acq);
}

void ramp_bias(katherine_device_t *device, katherine_config_t *config, float start_bias, float end_bias, float bias_step) {
    // Create HDF5 file with latest interface
    hid_t plist_id = H5Pcreate(H5P_FILE_ACCESS);
    H5Pset_libver_bounds(plist_id, H5F_LIBVER_LATEST, H5F_LIBVER_LATEST);
    
    char filename[100];
    time_t now;
    time(&now);
    struct tm *timeinfo = localtime(&now);
    strftime(filename, sizeof(filename), "bias_ramp_%Y%m%d_%H%M%S.h5", timeinfo);
    
    hid_t file_id = H5Fcreate(filename, H5F_ACC_TRUNC, H5P_DEFAULT, plist_id);
    H5Pclose(plist_id);
    
    if (file_id < 0) {
        printf("Failed to create HDF5 file: %s\n", filename);
        return;
    }

    // Create compound datatype for bias point data
    hid_t bias_datatype = H5Tcreate(H5T_COMPOUND, sizeof(BiasPointData));
    H5Tinsert(bias_datatype, "bias_voltage", HOFFSET(BiasPointData, bias_voltage), H5T_NATIVE_FLOAT);
    H5Tinsert(bias_datatype, "total_hits", HOFFSET(BiasPointData, total_hits), H5T_NATIVE_ULLONG);
    H5Tinsert(bias_datatype, "frame_count", HOFFSET(BiasPointData, frame_count), H5T_NATIVE_INT);
    H5Tinsert(bias_datatype, "total_duration", HOFFSET(BiasPointData, total_duration), H5T_NATIVE_FLOAT);
    H5Tinsert(bias_datatype, "throughput", HOFFSET(BiasPointData, throughput), H5T_NATIVE_FLOAT);
    H5Tinsert(bias_datatype, "lost_pixels", HOFFSET(BiasPointData, lost_pixels), H5T_NATIVE_ULONG);
    H5Tinsert(bias_datatype, "sent_pixels", HOFFSET(BiasPointData, sent_pixels), H5T_NATIVE_ULONG);
    H5Tinsert(bias_datatype, "received_pixels", HOFFSET(BiasPointData, received_pixels), H5T_NATIVE_ULONG);

    // Create extensible dataset for bias points
    hsize_t initial_dims[1] = {0};
    hsize_t max_dims[1] = {H5S_UNLIMITED};
    hid_t dataspace_id = H5Screate_simple(1, initial_dims, max_dims);
    if (dataspace_id < 0) {
        printf("Failed to create dataspace.\n");
        H5Fclose(file_id);
        return;
    }
    
    hid_t plist = H5Pcreate(H5P_DATASET_CREATE);
    hsize_t chunk_dims[1] = {1};
    H5Pset_chunk(plist, 1, chunk_dims);
    
    hid_t dataset_id = H5Dcreate(file_id, "bias_ramp_data", bias_datatype, dataspace_id, H5P_DEFAULT, plist, H5P_DEFAULT);
    if (dataset_id < 0) {
        printf("Failed to create dataset.\n");
        H5Sclose(dataspace_id);
        H5Fclose(file_id);
        return;
    }

    // Store ramp parameters as attributes in root group
    hid_t root_group = H5Gopen(file_id, "/", H5P_DEFAULT);
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

    // Determine ramping direction and step
    float step = (start_bias <= end_bias) ? fabs(bias_step) : -fabs(bias_step);
    float current_voltage = start_bias;
    hsize_t current_index = 0;

    while ((step > 0 && current_voltage <= end_bias) || 
           (step < 0 && current_voltage >= end_bias)) {
        
        // Set global current bias voltage for pixel data grouping
        current_bias_voltage = current_voltage;
        
        // Reset last frame info
        memset(&last_frame_info, 0, sizeof(katherine_frame_info_t));

        // Set bias and run acquisition
        set_bias(device, 0, current_voltage);
        config->bias = current_voltage;
        usleep(500000); // Stabilization delay

        // Prepare acquisition
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

        // Time acquisition
        time_t tic = time(NULL);
        res = katherine_acquisition_read(&acq);
        time_t toc = time(NULL);

        // Prepare data point using last_frame_info
        BiasPointData point_data = {
            .bias_voltage = current_voltage,
            .total_hits = n_hits,
            .frame_count = acq.completed_frames,
            .total_duration = difftime(toc, tic),
            .throughput = n_hits / difftime(toc, tic),
            .lost_pixels = last_frame_info.lost_pixels,
            .sent_pixels = last_frame_info.sent_pixels,
            .received_pixels = last_frame_info.received_pixels
        };

        // Extend dataset
        hsize_t new_size[1] = {current_index + 1};
        H5Dset_extent(dataset_id, new_size);
        
        // Write data
        hid_t filespace = H5Dget_space(dataset_id);
        hsize_t start[1] = {current_index};
        hsize_t count[1] = {1};
        hid_t memspace = H5Screate_simple(1, count, NULL);
        
        H5Sselect_hyperslab(filespace, H5S_SELECT_SET, start, NULL, count, NULL);
        H5Dwrite(dataset_id, bias_datatype, memspace, filespace, H5P_DEFAULT, &point_data);
        
        // Cleanup
        H5Sclose(memspace);
        H5Sclose(filespace);
        katherine_acquisition_fini(&acq);
        
        current_index++;
        current_voltage += step;
    }

    // Close resources
    H5Dclose(dataset_id);
    H5Pclose(plist);
    H5Sclose(dataspace_id);
    H5Fclose(file_id);

    printf("Bias ramping and acquisition sequence completed\n");
}