#ifndef TPX3H5LIB_H
#define TPX3H5LIB_H

#include <hdf5.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

typedef struct {
    int x, y;
    uint64_t toa;
    uint8_t ftoa;
    uint16_t tot;
    uint32_t hit_count;
} PixelHit;

typedef struct {
    hid_t file_id;
    hid_t datatype;
    hid_t dataset;
    hsize_t current_size;
} Tpx3H5Writer;


//Create HDF5 datatype for PixelHit

static hid_t tpx3h5_create_datatype() {
    hid_t dtype = H5Tcreate(H5T_COMPOUND, sizeof(PixelHit));
    H5Tinsert(dtype, "x", HOFFSET(PixelHit, x), H5T_NATIVE_INT);
    H5Tinsert(dtype, "y", HOFFSET(PixelHit, y), H5T_NATIVE_INT);
    H5Tinsert(dtype, "toa", HOFFSET(PixelHit, toa), H5T_NATIVE_UINT64);
    H5Tinsert(dtype, "ftoa", HOFFSET(PixelHit, ftoa), H5T_NATIVE_UINT8);
    H5Tinsert(dtype, "tot", HOFFSET(PixelHit, tot), H5T_NATIVE_UINT16);
    H5Tinsert(dtype, "hit_count", HOFFSET(PixelHit, hit_count), H5T_NATIVE_UINT32);
    return dtype;
}


//Initialize HDF5 writer with filename and dataset

static int tpx3h5_init(Tpx3H5Writer *writer, const char *filename, const char *dataset_name) {
    writer->current_size = 0;

    hid_t plist_id = H5Pcreate(H5P_FILE_ACCESS);
    H5Pset_libver_bounds(plist_id, H5F_LIBVER_LATEST, H5F_LIBVER_LATEST);
    writer->file_id = H5Fcreate(filename, H5F_ACC_TRUNC, H5P_DEFAULT, plist_id);
    H5Pclose(plist_id);
    if (writer->file_id < 0) return -1;

    writer->datatype = tpx3h5_create_datatype();

    hsize_t initial_dims[1] = {0};
    hsize_t max_dims[1] = {H5S_UNLIMITED};
    hsize_t chunk_dims[1] = {1024};
    hid_t dataspace_id = H5Screate_simple(1, initial_dims, max_dims);
    hid_t dcpl = H5Pcreate(H5P_DATASET_CREATE);
    H5Pset_chunk(dcpl, 1, chunk_dims);

    writer->dataset = H5Dcreate(writer->file_id, dataset_name, writer->datatype, dataspace_id,
                                H5P_DEFAULT, dcpl, H5P_DEFAULT);

    H5Sclose(dataspace_id);
    H5Pclose(dcpl);

    return (writer->dataset < 0) ? -2 : 0;
}


//Add or append PixelHit data to dataset

static int tpx3h5_append(Tpx3H5Writer *writer, const void *data, size_t count) {
    if (writer->dataset < 0) return -1;

    hsize_t new_size = writer->current_size + count;
    H5Dset_extent(writer->dataset, &new_size);

    hid_t filespace = H5Dget_space(writer->dataset);
    hsize_t start[1] = {writer->current_size};
    hsize_t count_dims[1] = {count};
    H5Sselect_hyperslab(filespace, H5S_SELECT_SET, start, NULL, count_dims, NULL);

    hid_t memspace = H5Screate_simple(1, count_dims, NULL);
    H5Dwrite(writer->dataset, writer->datatype, memspace, filespace, H5P_DEFAULT, data);

    H5Sclose(memspace);
    H5Sclose(filespace);

    writer->current_size = new_size;
    return 0;
}


//Close all open files

static void tpx3h5_close(Tpx3H5Writer *writer) {
    if (writer->dataset >= 0) H5Dclose(writer->dataset);
    if (writer->datatype >= 0) H5Tclose(writer->datatype);
    if (writer->file_id >= 0) H5Fclose(writer->file_id);
    writer->dataset = writer->datatype = writer->file_id = -1;
    writer->current_size = 0;
}

#endif