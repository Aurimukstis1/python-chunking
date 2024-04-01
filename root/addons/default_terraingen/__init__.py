__version__ = '0.0.1'
configfile_name = "default_terraingen.json"
defaultconf_name = "default.json"

import os
import time
import numpy as np
import json
import random
from perlin_noise import PerlinNoise
from numba import jit

try:
    with open(f"config/{configfile_name}", 'r') as file:
        print(f"[{time.ctime()}]#Info: Config file {configfile_name} succesfully found...")
        data_configured = json.load(file)

    with open(f"config/{defaultconf_name}", 'r') as file:
        print(f"[{time.ctime()}]#Info: Config file {defaultconf_name} succesfully found...")
        data_default = json.load(file)

    CHUNK_SIZE = data_default['CHUNK_SIZE']
    world_chunk_size_x = data_default['world_chunk_size_x']
    world_chunk_size_y = data_default['world_chunk_size_y']

    noise1_weight = data_configured['noise1_weight']
    noise2_weight = data_configured['noise2_weight']
    noise3_weight = data_configured['noise3_weight']
    noise4_weight = data_configured['noise4_weight']

    final_weight = data_configured['final_weight']

except FileNotFoundError:
    print(f"[{time.ctime()}]#Error: Config file {configfile_name} not found...")

def perlin_worker(input_queue, output_queue, noise1, noise2, noise3, noise4):
    for chunkx, chunky in iter(input_queue.get, 'STOP'):
        data = np.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=np.int8)
        water_data = np.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=np.int8)

        for localx in range(CHUNK_SIZE):
            scaled_x = (localx/CHUNK_SIZE + chunkx)/world_chunk_size_x

            for localy in range(CHUNK_SIZE):
                scaled_y = (localy/CHUNK_SIZE + chunky)/world_chunk_size_y

                noise_val = noise1([scaled_x, scaled_y])
                noise_val += noise2_weight * noise2([scaled_x, scaled_y])
                noise_val += noise3_weight * noise3([scaled_x, scaled_y])
                noise_val += noise4_weight * noise4([scaled_x, scaled_y])
                noise_val *= final_weight

                data[localx][localy] = min(255, max(1, noise_val))
                water_data[localx][localy] = 0

        output_queue.put((chunkx, chunky, data, water_data))
