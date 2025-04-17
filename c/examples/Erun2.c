#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <string.h>
#include <unistd.h>
#include <katherine/katherine.h>
#include <hdf5.h>



static const char *remote_addr = "192.168.1.218"; //Device IP address
typedef katherine_px_f_toa_tot_t px_t; //ACQ mode (Modes in px.h) Here we import all modes

// Global variables for configuration and modes
static uint64_t n_hits; //
static hid_t hdf5_file_id = -1; // HDF5 file identifier, initialized to invalid

//scan modes. NOT READY YET!
/*
static bool energy_spectrum_enabled = false;
static bool position_sensitive_enabled = false;
static bool time_resolved_enabled = false;
static bool triggered_acquisition_enabled = false;
static bool pulse_height_analysis_enabled = false;
static bool coincidence_detection_enabled = false;
static bool dead_time_measurement_enabled = false;
static bool calibration_scan_enabled = false;
*/

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
void enable_scanning_modes();
//void process_energy_spectrum(const px_t *px, size_t count);
//void process_position_sensitive(const px_t *px, size_t count);
//void process_time_resolved(const px_t *px, size_t count);
//void process_triggered_acquisition(const px_t *px, size_t count);
//void process_pulse_height_analysis(const px_t *px, size_t count);
//void process_coincidence_detection(const px_t *px, size_t count);
//void process_dead_time_measurement(const px_t *px, size_t count);
//void process_calibration_scan(const px_t *px, size_t count);

int main(int argc, char *argv[]) {
    // Loading config
    katherine_config_t c; 
    configure(&c);

    // Initializing device
    int res;
    katherine_device_t device; 

    // Creating an HDF5 file
    hdf5_file_id = H5Fcreate("Fe55-184V.h5", H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);
    if (hdf5_file_id < 0) {
        printf("Failed to create HDF5 file.\n");
        exit(7);
    }

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
        H5Fclose(hdf5_file_id); // Close HDF5 file before exiting
        exit(6);
    }
    printf("Connected successfully.\n");

    
    // enable_scanning_modes(); // enabling scan modes
    get_comm_status(&device);
    get_chip_id(&device);
    get_readout_temp(&device);
    get_sensor_temp(&device);
    digital_test(&device);
    adc_voltage(&device);//check if bias is set before adc
    run_acquisition(&device, &c);

    // Closing device
    katherine_device_fini(&device);

    // Close HDF5 file after acquisition
    if (hdf5_file_id >= 0) {
        H5Fclose(hdf5_file_id); 
    }
    return 0;
}


void configure(katherine_config_t *config) {
    // For now, these constants are hard-coded. (Used from krun)
    config->bias_id                 = 0;
    config->acq_time                = 10e9; // ns
    config->no_frames               = 1;
    config->bias                    = 184; // V

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


void frame_started(void *user_ctx, int frame_idx) {
    n_hits = 0;

    printf("Started frame %d.\n", frame_idx);

    // Ensure the HDF5 file is valid
    if (hdf5_file_id < 0) {
        printf("Invalid HDF5 file ID. Cannot create group for frame %d.\n", frame_idx);
        return;
    }

    // Create a group for this frame
    char group_name[64];
    snprintf(group_name, sizeof(group_name), "/frame_%d", frame_idx);

    hid_t group_id;
    if (H5Lexists(hdf5_file_id, group_name, H5P_DEFAULT) > 0) {
        group_id = H5Gopen(hdf5_file_id, group_name, H5P_DEFAULT);
    } else {
        group_id = H5Gcreate(hdf5_file_id, group_name, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
    }

    if (group_id < 0) {
        printf("Failed to create/open group for frame %d.\n", frame_idx);
        return;
    }

    // Create a dataset for pixel data
    hsize_t dims[2] = {0, 5}; // Initial size (0 rows, 5 columns: X, Y, ToA, fToA, ToT)
    hsize_t max_dims[2] = {H5S_UNLIMITED, 5}; // Allow unlimited rows
    hid_t dataspace_id = H5Screate_simple(2, dims, max_dims);
    if (dataspace_id < 0) {
        printf("Failed to create dataspace for frame %d.\n", frame_idx);
        H5Gclose(group_id);
        return;
    }

    // Enable chunking for the dataset
    hid_t plist_id = H5Pcreate(H5P_DATASET_CREATE);
    if (plist_id < 0) {
        printf("Failed to create property list for frame %d.\n", frame_idx);
        H5Sclose(dataspace_id);
        H5Gclose(group_id);
        return;
    }

    hsize_t chunk_dims[2] = {1000, 5}; // Chunk size: 1000 rows, 5 columns
    H5Pset_chunk(plist_id, 2, chunk_dims);

    // Create the dataset
    hid_t dataset_id = H5Dcreate(group_id, "pixel_data", H5T_NATIVE_INT, dataspace_id, H5P_DEFAULT, plist_id, H5P_DEFAULT);
    if (dataset_id < 0) {
        printf("Failed to create dataset for frame %d.\n", frame_idx);
        H5Pclose(plist_id);
        H5Sclose(dataspace_id);
        H5Gclose(group_id);
        return;
    }

    // Close file
    H5Pclose(plist_id);
    H5Sclose(dataspace_id);
    H5Dclose(dataset_id);
    H5Gclose(group_id);
}

void frame_ended(void *user_ctx, int frame_idx, bool completed, const katherine_frame_info_t *info) {
    const double recv_perc = 100. * info->received_pixels / info->sent_pixels;

    printf("\n");
    printf("Ended frame %d.\n", frame_idx);
    printf(" - tpx3->katherine lost %lu pixels\n", info->lost_pixels);
    printf(" - katherine->pc sent %lu pixels\n", info->sent_pixels);
    printf(" - katherine->pc received %lu pixels\n", info->received_pixels);
    printf(" - state: %s\n", (completed ? "completed" : "not completed"));
    printf(" - start time: %lu\n", info->start_time.d);
    printf(" - end time: %lu\n", info->end_time.d);

    // Ensure the HDF5 file is valid
    if (hdf5_file_id < 0) {
        printf("Invalid HDF5 file ID. Cannot write frame summary.\n");
        return;
    }

    // Write frame summary as attributes
    char group_name[64];
    snprintf(group_name, sizeof(group_name), "/frame_%d", frame_idx);
    hid_t group_id = H5Gopen(hdf5_file_id, group_name, H5P_DEFAULT);
    if (group_id < 0) {
        printf("Failed to open group for frame %d.\n", frame_idx);
        return;
    }

    // Write attributes
    hid_t attribute_id = H5Acreate(group_id, "lost_pixels", H5T_NATIVE_ULONG, H5Screate(H5S_SCALAR), H5P_DEFAULT, H5P_DEFAULT);
    if (attribute_id >= 0) {
        H5Awrite(attribute_id, H5T_NATIVE_ULONG, &info->lost_pixels);
        H5Aclose(attribute_id);
    }

    attribute_id = H5Acreate(group_id, "sent_pixels", H5T_NATIVE_ULONG, H5Screate(H5S_SCALAR), H5P_DEFAULT, H5P_DEFAULT);
    if (attribute_id >= 0) {
        H5Awrite(attribute_id, H5T_NATIVE_ULONG, &info->sent_pixels);
        H5Aclose(attribute_id);
    }

    attribute_id = H5Acreate(group_id, "received_pixels", H5T_NATIVE_ULONG, H5Screate(H5S_SCALAR), H5P_DEFAULT, H5P_DEFAULT);
    if (attribute_id >= 0) {
        H5Awrite(attribute_id, H5T_NATIVE_ULONG, &info->received_pixels);
        H5Aclose(attribute_id);
    }

    attribute_id = H5Acreate(group_id, "state", H5T_C_S1, H5Screate(H5S_SCALAR), H5P_DEFAULT, H5P_DEFAULT);
    if (attribute_id >= 0) {
        const char *state_str = completed ? "completed" : "not completed";
        H5Awrite(attribute_id, H5T_C_S1, state_str);
        H5Aclose(attribute_id);
    }

    H5Gclose(group_id);
}

void pixels_received(void *user_ctx, const void *px, size_t count) {

    //CHECK MASKING AT crd.h
    n_hits += count;

    const px_t *dpx = (const px_t *) px;

    // Prepare data for writing
    int *data = malloc(count * 5 * sizeof(int)); // 5 columns: X, Y, ToA, fToA, ToT
    for (size_t i = 0; i < count; ++i) {
        data[i * 5 + 0] = dpx[i].coord.x;
        data[i * 5 + 1] = dpx[i].coord.y;
        data[i * 5 + 2] = dpx[i].toa;
        data[i * 5 + 3] = dpx[i].ftoa;
        data[i * 5 + 4] = dpx[i].tot;
    }

    // Ensure the HDF5 file is valid
    if (hdf5_file_id < 0) {
        printf("Invalid HDF5 file ID. Cannot write pixel data.\n");
        free(data);
        return;
    }

    // Get the current dataset dimensions
    char group_name[64];
    snprintf(group_name, sizeof(group_name), "/frame_%d", 0); // Assuming frame 0 for simplicity
    hid_t group_id = H5Gopen(hdf5_file_id, group_name, H5P_DEFAULT);
    if (group_id < 0) {
        printf("Failed to open group: %s\n", group_name);
        free(data);
        return;
    }

    hid_t dataset_id = H5Dopen(group_id, "pixel_data", H5P_DEFAULT);
    if (dataset_id < 0) {
        printf("Failed to open dataset: pixel_data\n");
        H5Gclose(group_id);
        free(data);
        return;
    }

    hid_t filespace_id = H5Dget_space(dataset_id);
    if (filespace_id < 0) {
        printf("Failed to get filespace for dataset.\n");
        H5Dclose(dataset_id);
        H5Gclose(group_id);
        free(data);
        return;
    }

    // Get the current dimensions of the dataset
    hsize_t current_dims[2];
    H5Sget_simple_extent_dims(filespace_id, current_dims, NULL);

    // Extend the dataset to accommodate new data
    hsize_t new_dims[2] = {current_dims[0] + count, 5};
    H5Dset_extent(dataset_id, new_dims);

    // Reopen the filespace to reflect the new dimensions
    H5Sclose(filespace_id);
    filespace_id = H5Dget_space(dataset_id);
    if (filespace_id < 0) {
        printf("Failed to get updated filespace for dataset.\n");
        H5Dclose(dataset_id);
        H5Gclose(group_id);
        free(data);
        return;
    }

    // Select the hyperslab for writing
    hsize_t start[2] = {current_dims[0], 0}; // Start at the end of the existing data
    hsize_t count_hslab[2] = {count, 5};     // Write `count` rows and 5 columns
    hid_t memspace_id = H5Screate_simple(2, count_hslab, NULL);
    if (memspace_id < 0) {
        printf("Failed to create memory space.\n");
        H5Sclose(filespace_id);
        H5Dclose(dataset_id);
        H5Gclose(group_id);
        free(data);
        return;
    }

    // Select the hyperslab in the dataset's filespace
    if (H5Sselect_hyperslab(filespace_id, H5S_SELECT_SET, start, NULL, count_hslab, NULL) < 0) {
        printf("Failed to select hyperslab for writing.\n");
        H5Sclose(memspace_id);
        H5Sclose(filespace_id);
        H5Dclose(dataset_id);
        H5Gclose(group_id);
        free(data);
        return;
    }

    // Write the data
    if (H5Dwrite(dataset_id, H5T_NATIVE_INT, memspace_id, filespace_id, H5P_DEFAULT, data) < 0) {
        printf("Failed to write data to dataset.\n");
    }

    // Free resources
    free(data);
    H5Sclose(memspace_id);
    H5Sclose(filespace_id);
    H5Dclose(dataset_id);
    H5Gclose(group_id);

    /* EDIT LATER
    // Process additional scanning modes if enabled
    if (energy_spectrum_enabled) process_energy_spectrum(dpx, count);
    if (position_sensitive_enabled) process_position_sensitive(dpx, count);
    if (time_resolved_enabled) process_time_resolved(dpx, count);
    if (triggered_acquisition_enabled) process_triggered_acquisition(dpx, count);
    if (pulse_height_analysis_enabled) process_pulse_height_analysis(dpx, count);
    if (coincidence_detection_enabled) process_coincidence_detection(dpx, count);
    if (dead_time_measurement_enabled) process_dead_time_measurement(dpx, count);
    if (calibration_scan_enabled) process_calibration_scan(dpx, count);
    */
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

    // Write chip ID as an attribute to the root group
    hid_t root_group_id = H5Gopen(hdf5_file_id, "/", H5P_DEFAULT);
    if (root_group_id < 0) {
        printf("Failed to open root group.\n");
        return;
    }

    hid_t attribute_id = H5Acreate(root_group_id, "chip_id", H5T_C_S1, H5Screate(H5S_SCALAR), H5P_DEFAULT, H5P_DEFAULT);
    if (attribute_id >= 0) {
        H5Awrite(attribute_id, H5T_C_S1, chip_id);
        H5Aclose(attribute_id);
    }

    H5Gclose(root_group_id);
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
        exit(10);
    }
    printf("ADC voltage: %f\n", voltage);

}

void run_acquisition(katherine_device_t *dev, const katherine_config_t *c) {
    int res;
    katherine_acquisition_t acq;

    res = katherine_acquisition_init(&acq, dev, NULL, KATHERINE_MD_SIZE * 34952533, sizeof(px_t) * 65536, 500, 30000); // 30-second timeout
    if (res != 0) {
        printf("Cannot initialize acquisition. Is the configuration valid?\n");
        printf("Reason: %s\n", strerror(res));
        exit(3);
    }

    acq.handlers.frame_started = frame_started;
    acq.handlers.frame_ended = frame_ended;
    acq.handlers.pixels_received = pixels_received;

    res = katherine_acquisition_begin(&acq, c, READOUT_DATA_DRIVEN, ACQUISITION_MODE_TOA_TOT, true, true);
    if (res != 0) {
        printf("Cannot begin acquisition.\n");
        printf("Reason: %s\n", strerror(res));
        exit(4);
    }

    printf("Acquisition started.\n");

    time_t tic = time(NULL);
    res = katherine_acquisition_read(&acq);
    if (res != 0) {
        printf("Cannot read acquisition data.\n");
        printf("Reason: %s\n", strerror(res));
        exit(5);
    }
    time_t toc = time(NULL);

    double duration = difftime(toc, tic);
    printf("\n");
    printf("Acquisition completed:\n");
    printf(" - state: %s\n", katherine_str_acquisition_status(acq.state));
    printf(" - received %d complete frames\n", acq.completed_frames);
    printf(" - dropped %zu measurement data\n", acq.dropped_measurement_data);
    printf(" - total hits: %lu\n", n_hits);
    printf(" - total duration: %f s\n", duration);
    printf(" - throughput: %f hits/s\n", (n_hits / duration));

    katherine_acquisition_fini(&acq);
}

void enable_scanning_modes() {
    char input[10];
/*
    printf("Enable Energy Spectrum Scanning? (y/n): ");
    fgets(input, sizeof(input), stdin);
    energy_spectrum_enabled = (input[0] == 'y' || input[0] == 'Y');

    printf("Enable Position-Sensitive Scanning? (y/n): ");
    fgets(input, sizeof(input), stdin);
    position_sensitive_enabled = (input[0] == 'y' || input[0] == 'Y');

    printf("Enable Time-Resolved Scanning? (y/n): ");
    fgets(input, sizeof(input), stdin);
    time_resolved_enabled = (input[0] == 'y' || input[0] == 'Y');

    printf("Enable Triggered Acquisition? (y/n): ");
    fgets(input, sizeof(input), stdin);
    triggered_acquisition_enabled = (input[0] == 'y' || input[0] == 'Y');

    printf("Enable Pulse Height Analysis? (y/n): ");
    fgets(input, sizeof(input), stdin);
    pulse_height_analysis_enabled = (input[0] == 'y' || input[0] == 'Y');

    printf("Enable Coincidence Detection? (y/n): ");
    fgets(input, sizeof(input), stdin);
    coincidence_detection_enabled = (input[0] == 'y' || input[0] == 'Y');

    printf("Enable Dead Time Measurement? (y/n): ");
    fgets(input, sizeof(input), stdin);
    dead_time_measurement_enabled = (input[0] == 'y' || input[0] == 'Y');

    printf("Enable Calibration Scan? (y/n): ");
    fgets(input, sizeof(input), stdin);
    calibration_scan_enabled = (input[0] == 'y' || input[0] == 'Y');
*/
}


//EDIT ACQ MODES

/*
void process_energy_spectrum(const px_t *px, size_t count) {
    static int energy_histogram[256] = {0}; // Assuming 8-bit ToT values
    for (size_t i = 0; i < count; ++i) {
        energy_histogram[px[i].tot]++;
    }

    // Ensure the HDF5 file is valid
    if (hdf5_file_id < 0) {
        printf("Invalid HDF5 file ID. Cannot write energy spectrum data.\n");
        return;
    }

    // Check if the group already exists
    const char *group_name = "/energy_spectrum";
    hid_t group_id;
    if (H5Lexists(hdf5_file_id, group_name, H5P_DEFAULT) > 0) {
        group_id = H5Gopen(hdf5_file_id, group_name, H5P_DEFAULT);
    } else {
        group_id = H5Gcreate(hdf5_file_id, group_name, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
    }

    if (group_id < 0) {
        printf("Failed to create/open group for energy spectrum.\n");
        return;
    }

    // Create a dataset for the histogram
    hsize_t dims[1] = {256};
    hid_t dataspace_id = H5Screate_simple(1, dims, NULL);
    if (dataspace_id < 0) {
        printf("Failed to create dataspace for energy spectrum.\n");
        H5Gclose(group_id);
        return;
    }

    // Check if the dataset already exists
    const char *dataset_name = "histogram";
    hid_t dataset_id;
    if (H5Lexists(group_id, dataset_name, H5P_DEFAULT) > 0) {
        dataset_id = H5Dopen(group_id, dataset_name, H5P_DEFAULT);
    } else {
        dataset_id = H5Dcreate(group_id, dataset_name, H5T_NATIVE_INT, dataspace_id, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
    }

    if (dataset_id < 0) {
        printf("Failed to create/open dataset for energy spectrum.\n");
        H5Sclose(dataspace_id);
        H5Gclose(group_id);
        return;
    }

    // Write the histogram data
    if (H5Dwrite(dataset_id, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT, energy_histogram) < 0) {
        printf("Failed to write energy spectrum data.\n");
    }

    // Close resources
    H5Dclose(dataset_id);
    H5Sclose(dataspace_id);
    H5Gclose(group_id);
}

void process_position_sensitive(const px_t *px, size_t count) {
    static int position_map[256][256] = {0}; // Assuming 256x256 pixel detector
    for (size_t i = 0; i < count; ++i) {
        position_map[px[i].coord.x][px[i].coord.y]++;
    }

    // Ensure the HDF5 file is valid
    if (hdf5_file_id < 0) {
        printf("Invalid HDF5 file ID. Cannot write position-sensitive data.\n");
        return;
    }

    // Check if the group already exists
    const char *group_name = "/position_sensitive";
    hid_t group_id;
    if (H5Lexists(hdf5_file_id, group_name, H5P_DEFAULT) > 0) {
        group_id = H5Gopen(hdf5_file_id, group_name, H5P_DEFAULT);
    } else {
        group_id = H5Gcreate(hdf5_file_id, group_name, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
    }

    if (group_id < 0) {
        printf("Failed to create/open group for position-sensitive data.\n");
        return;
    }

    // Create a dataset for the position map
    hsize_t dims[2] = {256, 256};
    hid_t dataspace_id = H5Screate_simple(2, dims, NULL);
    if (dataspace_id < 0) {
        printf("Failed to create dataspace for position-sensitive data.\n");
        H5Gclose(group_id);
        return;
    }

    // Check if the dataset already exists
    const char *dataset_name = "map";
    hid_t dataset_id;
    if (H5Lexists(group_id, dataset_name, H5P_DEFAULT) > 0) {
        dataset_id = H5Dopen(group_id, dataset_name, H5P_DEFAULT);
    } else {
        dataset_id = H5Dcreate(group_id, dataset_name, H5T_NATIVE_INT, dataspace_id, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
    }

    if (dataset_id < 0) {
        printf("Failed to create/open dataset for position-sensitive data.\n");
        H5Sclose(dataspace_id);
        H5Gclose(group_id);
        return;
    }

    // Write the position map data
    if (H5Dwrite(dataset_id, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT, position_map) < 0) {
        printf("Failed to write position-sensitive data.\n");
    }

    // Close resources
    H5Dclose(dataset_id);
    H5Sclose(dataspace_id);
    H5Gclose(group_id);
}

void process_time_resolved(const px_t *px, size_t count) {
    static int time_histogram[1000] = {0}; // Assuming 1000 time bins
    for (size_t i = 0; i < count; ++i) {
        int time_bin = px[i].toa % 1000; // Example: Bin by modulo 1000
        time_histogram[time_bin]++;
    }

    // Ensure the HDF5 file is valid
    if (hdf5_file_id < 0) {
        printf("Invalid HDF5 file ID. Cannot write time-resolved data.\n");
        return;
    }

    // Check if the group already exists
    const char *group_name = "/time_resolved";
    hid_t group_id;
    if (H5Lexists(hdf5_file_id, group_name, H5P_DEFAULT) > 0) {
        group_id = H5Gopen(hdf5_file_id, group_name, H5P_DEFAULT);
    } else {
        group_id = H5Gcreate(hdf5_file_id, group_name, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
    }

    if (group_id < 0) {
        printf("Failed to create/open group for time-resolved data.\n");
        return;
    }

    // Create a dataset for the time histogram
    hsize_t dims[1] = {1000};
    hid_t dataspace_id = H5Screate_simple(1, dims, NULL);
    if (dataspace_id < 0) {
        printf("Failed to create dataspace for time-resolved data.\n");
        H5Gclose(group_id);
        return;
    }

    // Check if the dataset already exists
    const char *dataset_name = "histogram";
    hid_t dataset_id;
    if (H5Lexists(group_id, dataset_name, H5P_DEFAULT) > 0) {
        dataset_id = H5Dopen(group_id, dataset_name, H5P_DEFAULT);
    } else {
        dataset_id = H5Dcreate(group_id, dataset_name, H5T_NATIVE_INT, dataspace_id, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
    }

    if (dataset_id < 0) {
        printf("Failed to create/open dataset for time-resolved data.\n");
        H5Sclose(dataspace_id);
        H5Gclose(group_id);
        return;
    }

    // Write the time histogram data
    if (H5Dwrite(dataset_id, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT, time_histogram) < 0) {
        printf("Failed to write time-resolved data.\n");
    }

    // Close resources
    H5Dclose(dataset_id);
    H5Sclose(dataspace_id);
    H5Gclose(group_id);
}

void process_triggered_acquisition(const px_t *px, size_t count) {
    // Implement triggered acquisition logic here
    // Example: Check for external triggers and start/stop acquisition
    // This would require additional hardware support for triggers

    // Write triggered acquisition data to the HDF5 file
    hid_t group_id = H5Gcreate(hdf5_file_id, "/triggered_acquisition", H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
    if (group_id < 0) {
        printf("Failed to create HDF5 group for triggered acquisition.\n");
        return;
    }

    // Write a placeholder message
    const char *message = "Triggered acquisition is enabled but not implemented in this example.";
    hid_t dataspace_id = H5Screate(H5S_SCALAR);
    hid_t attribute_id = H5Acreate(group_id, "message", H5T_C_S1, dataspace_id, H5P_DEFAULT, H5P_DEFAULT);
    H5Awrite(attribute_id, H5T_C_S1, message);

    // Close resources
    H5Aclose(attribute_id);
    H5Sclose(dataspace_id);
    H5Gclose(group_id);
}

void process_pulse_height_analysis(const px_t *px, size_t count) {
    // Implement pulse height analysis here
    // Example: Analyze the ToT values to infer pulse heights

    // Write pulse height analysis data to the HDF5 file
    hid_t group_id = H5Gcreate(hdf5_file_id, "/pulse_height_analysis", H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
    if (group_id < 0) {
        printf("Failed to create HDF5 group for pulse height analysis.\n");
        return;
    }

    // Write a placeholder message
    const char *message = "Pulse height analysis is enabled but not implemented in this example.";
    hid_t dataspace_id = H5Screate(H5S_SCALAR);
    hid_t attribute_id = H5Acreate(group_id, "message", H5T_C_S1, dataspace_id, H5P_DEFAULT, H5P_DEFAULT);
    H5Awrite(attribute_id, H5T_C_S1, message);

    // Close resources
    H5Aclose(attribute_id);
    H5Sclose(dataspace_id);
    H5Gclose(group_id);
}

void process_coincidence_detection(const px_t *px, size_t count) {
    // Implement coincidence detection here
    // Example: Check for hits within a short time window

    // Write coincidence detection data to the HDF5 file
    hid_t group_id = H5Gcreate(hdf5_file_id, "/coincidence_detection", H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
    if (group_id < 0) {
        printf("Failed to create HDF5 group for coincidence detection.\n");
        return;
    }

    // Write a placeholder message
    const char *message = "Coincidence detection is enabled but not implemented in this example.";
    hid_t dataspace_id = H5Screate(H5S_SCALAR);
    hid_t attribute_id = H5Acreate(group_id, "message", H5T_C_S1, dataspace_id, H5P_DEFAULT, H5P_DEFAULT);
    H5Awrite(attribute_id, H5T_C_S1, message);

    // Close resources
    H5Aclose(attribute_id);
    H5Sclose(dataspace_id);
    H5Gclose(group_id);
}

void process_dead_time_measurement(const px_t *px, size_t count) {
    // Implement dead time measurement here
    // Example: Analyze the time intervals between hits

    // Write dead time measurement data to the HDF5 file
    hid_t group_id = H5Gcreate(hdf5_file_id, "/dead_time_measurement", H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
    if (group_id < 0) {
        printf("Failed to create HDF5 group for dead time measurement.\n");
        return;
    }

    // Write a placeholder message
    const char *message = "Dead time measurement is enabled but not implemented in this example.";
    hid_t dataspace_id = H5Screate(H5S_SCALAR);
    hid_t attribute_id = H5Acreate(group_id, "message", H5T_C_S1, dataspace_id, H5P_DEFAULT, H5P_DEFAULT);
    H5Awrite(attribute_id, H5T_C_S1, message);

    // Close resources
    H5Aclose(attribute_id);
    H5Sclose(dataspace_id);
    H5Gclose(group_id);
}

void process_calibration_scan(const px_t *px, size_t count) {
    // Implement calibration scan here
    // Example: Adjust detector settings based on known energy sources

    // Write calibration scan data to the HDF5 file
    hid_t group_id = H5Gcreate(hdf5_file_id, "/calibration_scan", H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
    if (group_id < 0) {
        printf("Failed to create HDF5 group for calibration scan.\n");
        return;
    }

    // Write a placeholder message
    const char *message = "Calibration scan is enabled but not implemented in this example.";
    hid_t dataspace_id = H5Screate(H5S_SCALAR);
    hid_t attribute_id = H5Acreate(group_id, "message", H5T_C_S1, dataspace_id, H5P_DEFAULT, H5P_DEFAULT);
    H5Awrite(attribute_id, H5T_C_S1, message);

    // Close resources
    H5Aclose(attribute_id);
    H5Sclose(dataspace_id);
    H5Gclose(group_id);
}
*/