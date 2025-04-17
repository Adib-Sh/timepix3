# TPX3H5LIB

## Overview

`tpx3h5lib` is a lightweight C library for efficiently storing Timepix3 detector data in HDF5 format. It provides a simple interface for creating, appending to, and managing HDF5 files specifically tailored for Timepix3 pixel hit data.

## Features

- Simple API with just three main functions
- Efficient storage of Timepix3 pixel hit data
- Support for unlimited dataset sizes with chunking
- Thread-safe data appending
- Stores complete pixel information including coordinates, timing, and hit counts

## Data Structure

The library uses a standardized `PixelHit` structure for storing detector data:

```c
typedef struct {
    int x, y;           // Pixel coordinates
    uint64_t toa;       // Time of Arrival
    uint8_t ftoa;       // Fine Time of Arrival
    uint16_t tot;       // Time over Threshold
    uint32_t hit_count; // Running hit counter for this pixel
} PixelHit;
```

## API Reference

### Initialization

```c
int tpx3h5_init(Tpx3H5Writer *writer, const char *filename, const char *dataset_name);
```

Creates a new HDF5 file and initializes a dataset for storing pixel hits.

- `writer`: Pointer to a `Tpx3H5Writer` structure
- `filename`: Path to the HDF5 file to create
- `dataset_name`: Name of the dataset within the HDF5 file (typically "/pixel_hits")
- Returns: 0 on success, negative values on error

### Appending Data

```c
int tpx3h5_append(Tpx3H5Writer *writer, const void *data, size_t count);
```

Appends pixel hit data to the dataset.

- `writer`: Pointer to an initialized `Tpx3H5Writer` structure
- `data`: Array of `PixelHit` structures
- `count`: Number of pixel hits to append
- Returns: 0 on success, negative values on error

### Cleanup

```c
void tpx3h5_close(Tpx3H5Writer *writer);
```

Closes all open HDF5 handles and releases resources.

- `writer`: Pointer to a `Tpx3H5Writer` structure

## Example Usage

### Basic Example

```c
#include "tpx3h5lib.h"

int main() {
    // Initialize writer
    Tpx3H5Writer writer;
    tpx3h5_init(&writer, "pixel_data.h5", "/pixel_hits");
    
    // Create some sample data
    PixelHit hits[2];
    hits[0] = (PixelHit){10, 20, 12345678, 5, 100, 1};
    hits[1] = (PixelHit){11, 21, 12345680, 7, 120, 1};
    
    // Append data
    tpx3h5_append(&writer, hits, 2);
    
    // Clean up
    tpx3h5_close(&writer);
    return 0;
}
```

### Integration with Erun3

The Erun3 data acquisition tool uses tpx3h5lib to store pixel data from a Timepix3 detector:

```c
void pixels_received(void *ctx, const void *px, size_t count) {
    const px_t *dpx = (const px_t *) px;
    PixelHit *hits = malloc(count * sizeof(PixelHit));
    
    for (size_t i = 0; i < count; ++i) {
        int x = dpx[i].coord.x;
        int y = dpx[i].coord.y;
        if (x < 0 || x >= SENSOR_WIDTH || y < 0 || y >= SENSOR_HEIGHT) continue;
        pixel_counts[y][x]++;
        
        hits[i] = (PixelHit){
            x, y, 
            dpx[i].toa, dpx[i].ftoa, dpx[i].tot,
            pixel_counts[y][x]
        };
    }
    
    tpx3h5_append(&h5writer, hits, count);
    free(hits);
}
```

## Working with HDF5 Files

### Reading Data in Python

```python
import h5py
import numpy as np
import matplotlib.pyplot as plt

# Open the file
with h5py.File('pixel_data.h5', 'r') as f:
    # Get the dataset
    hits = f['/pixel_hits'][:]
    
    # Create hit map
    hit_map = np.zeros((256, 256))
    for hit in hits:
        hit_map[hit['y'], hit['x']] += 1
    
    # Visualize
    plt.imshow(hit_map, cmap='viridis')
    plt.colorbar(label='Hits')
    plt.title('Timepix3 Hit Map')
    plt.show()
```

### Reading Data in C/C++

```c
#include <hdf5.h>
#include "tpx3h5lib.h"

void read_data(const char *filename) {
    hid_t file_id = H5Fopen(filename, H5F_ACC_RDONLY, H5P_DEFAULT);
    hid_t dataset = H5Dopen(file_id, "/pixel_hits", H5P_DEFAULT);
    
    // Get dataset size
    hid_t dataspace = H5Dget_space(dataset);
    hsize_t dims[1];
    H5Sget_simple_extent_dims(dataspace, dims, NULL);
    
    // Allocate memory for data
    PixelHit *hits = malloc(dims[0] * sizeof(PixelHit));
    
    // Create datatype
    hid_t dtype = tpx3h5_create_datatype();
    
    // Read data
    H5Dread(dataset, dtype, H5S_ALL, H5S_ALL, H5P_DEFAULT, hits);
    
    // Process data
    for (size_t i = 0; i < dims[0]; i++) {
        printf("Hit at (%d,%d) TOA=%lu TOT=%u Count=%u\n", 
               hits[i].x, hits[i].y, hits[i].toa, 
               hits[i].tot, hits[i].hit_count);
    }
    
    // Clean up
    free(hits);
    H5Tclose(dtype);
    H5Sclose(dataspace);
    H5Dclose(dataset);
    H5Fclose(file_id);
}
```

## Performance Considerations

- The library uses HDF5 chunking for efficient data appending
- Default chunk size is 1024 records
- For very high data rates, consider increasing the chunk size

## Building with tpx3h5lib

### Including in Your Project

Simply include the header file in your C project:

```c
#include "tpx3h5lib.h"
```

### Compilation

Make sure to link against the HDF5 library:

```bash
gcc -o myprogram myprogram.c -lhdf5
```

## License

[Add appropriate license information]

## Contact

[Add contact information]