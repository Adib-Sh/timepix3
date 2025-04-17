#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import h5py

file_name = 'pixel_data_20250223_034233.h5'

with h5py.File(file_name, 'r') as file:
    for key in file.keys():
        if 'pixel_hits' in file[key]:
            dataset = file[key]['pixel_hits']
            total_count = sum(entry[5] for entry in dataset) 
            print(f"Total count for dataset '{key}': {total_count}")