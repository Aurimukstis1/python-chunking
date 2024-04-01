import random
from perlin_noise import PerlinNoise
import arcade
import multiprocessing as mp
import numpy as np
import queue
import time
import os
import json
from numba import jit
from addons import default_terraingen as TERRAINGEN
import pickle

# display settings
WIDTH, HEIGHT = 1280, 720
SCREEN_SIZE = (WIDTH, HEIGHT)


with open('config/default.json', 'r') as file:
    defaultconfig_data = json.load(file)

world_chunk_size_x = defaultconfig_data["world_chunk_size_x"]
world_chunk_size_y = defaultconfig_data["world_chunk_size_y"]
_range = defaultconfig_data["_range"]
CHUNK_SIZE = defaultconfig_data["CHUNK_SIZE"]
TILE_SIZE = defaultconfig_data["TILE_SIZE"]
CHUNK_FULLSIZE = TILE_SIZE*CHUNK_SIZE


class Tile(arcade.SpriteSolidColor):
    def __init__(self, input_screenx, input_screeny, input_data, input_water_data):
        # Convert color values to integers
        color_value = int(input_data)
        super().__init__(TILE_SIZE, TILE_SIZE, (color_value, color_value, color_value))
        self.data:       int = input_data
        self.water_data: int = input_water_data
        self.center_x:   int = input_screenx+(int(TILE_SIZE/2))
        self.center_y:   int = input_screeny+(int(TILE_SIZE/2))
    
    def to_dict(self):
        return {
            'data': self.data,
            'water_data': self.water_data,
            'center_x': self.center_x,
            'center_y': self.center_y
        }


class Chunk():
    def __init__(self, input_chunkx, input_chunky):
        self.chunkx: int = input_chunkx
        self.chunky: int = input_chunky
        self.tiles: list = []

    def create(self, input_data, input_water_data, spritelist):
        for localx in range(CHUNK_SIZE):
            screenx = (localx+CHUNK_SIZE*self.chunkx)*TILE_SIZE
            for localy in range(CHUNK_SIZE):
                screeny = (localy+CHUNK_SIZE*self.chunky)*TILE_SIZE
                tile = Tile(screenx, screeny, input_data[localx][localy], input_water_data[localx][localy])
                self.tiles.append(tile)
                spritelist.append(tile)

    def to_dict(self):
        return {
            'chunkx': self.chunkx,
            'chunky': self.chunky,
            'tiles': [tile.to_dict() for tile in self.tiles]
        }


class World:
    def __init__(self, width, height, grid_sprite_list):
        self.width = width
        self.height = height
        self.chunks = []
        self.chunk_generated_coordinate_list = set(())
        self.grid_sprite_list = grid_sprite_list

        self.task_queue = mp.Queue()
        self.done_queue = mp.Queue()

        self.NUMBER_OF_PROCESSES = 8

        # perlin generator settings
        self.seed = random.randint(0, 1000000)
        self.noise_profile1 = PerlinNoise(octaves=2, seed=self.seed)
        self.noise_profile2 = PerlinNoise(octaves=8, seed=self.seed)
        self.noise_profile3 = PerlinNoise(octaves=64, seed=self.seed)
        self.noise_profile4 = PerlinNoise(octaves=128, seed=self.seed)

        # Start the processes
        for i in range(self.NUMBER_OF_PROCESSES):
            mp.Process(target=TERRAINGEN.perlin_worker, args=(
                self.task_queue,
                self.done_queue,
                self.noise_profile1,
                self.noise_profile2,
                self.noise_profile3,
                self.noise_profile4
            )).start()

    def request_chunks(self, chunk_coord_list):
        for coords in chunk_coord_list:
            print(f"Requested chunk: {coords}")
            self.task_queue.put(coords)

    def get_chunks(self):
        try:
            for i in range(self.NUMBER_OF_PROCESSES):  # This determines the max number of chunks to try and load per frame
                chunkx, chunky, data, water_data = self.done_queue.get(block=False)
                extracted_chunk = Chunk(chunkx, chunky)
                data = data.tolist()
                water_data = water_data.tolist()
                extracted_chunk.create(data, water_data, self.grid_sprite_list)
                self.chunks.append(extracted_chunk)
                print(f"Got back chunk: ({chunkx},{chunky})")
        except queue.Empty:
            return

    def cleanup(self):
        # Cleanup the worker processes.
        # Otherwise, they will be left orphaned (and that wouldn't be very nice.)
        for i in range(self.NUMBER_OF_PROCESSES):
            self.task_queue.put('STOP')

    def save_world(self):
        for i in range(self.NUMBER_OF_PROCESSES):
            self.task_queue.put('STOP')

        with open('chunkdata/world.data','wb') as f:
            world_data_dictionary = {
                "seed": self.seed,
                "noise_profile1": self.noise_profile1.__dict__,
                "noise_profile2": self.noise_profile2.__dict__,
                "noise_profile3": self.noise_profile3.__dict__,
                "noise_profile4": self.noise_profile4.__dict__,
                "width": self.width,
                "height": self.height,
                "chunk_generated_coordinate_list": list(self.chunk_generated_coordinate_list),
                "chunks": []
            }

            for chunk in self.chunks:
                world_data_dictionary["chunks"].append(chunk.to_dict())

            pickle.dump(world_data_dictionary, f)

            print("Saved world successfuly.")


class Game(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_chunk_x = 0
        self.mouse_chunk_y = 0
        self.background_color = arcade.color.BLACK
        self.grid_sprite_list = arcade.SpriteList()

        arcade.enable_timings(100)

        self.world = World(world_chunk_size_x, world_chunk_size_y, self.grid_sprite_list)

    def on_update(self, dt):
        self.world.get_chunks()

        stuff_to_gen = set(())
    
        for chunkx in range(self.mouse_chunk_x-_range, self.mouse_chunk_x+_range):
            for chunky in range(self.mouse_chunk_y-_range, self.mouse_chunk_y+_range):
                if (chunkx,chunky) not in self.world.chunk_generated_coordinate_list:
                    stuff_to_gen.add((chunkx,chunky))
                    self.world.chunk_generated_coordinate_list.add((chunkx,chunky))

        self.world.request_chunks(stuff_to_gen)
        if stuff_to_gen:
            print(f"Requesting chunks: {stuff_to_gen}")

    def on_draw(self):
        self.clear()

        self.grid_sprite_list.draw()

        #for chunk in self.world.chunks:
        #   arcade.draw_rectangle_outline((chunk.x*TILE_SIZE*CHUNK_SIZE)+((TILE_SIZE*CHUNK_SIZE)/2),(chunk.y*TILE_SIZE*CHUNK_SIZE)+((TILE_SIZE*CHUNK_SIZE)/2),CHUNK_SIZE*TILE_SIZE,CHUNK_SIZE*TILE_SIZE,(10,10,10),1,0)

        arcade.draw_circle_filled(self.mouse_x, self.mouse_y, 5, arcade.color.GREEN_YELLOW)
        arcade.draw_text(f"mouse_x: {self.mouse_x}", self.mouse_x+10, self.mouse_y, arcade.color.GREEN, 12, 100, "left", "calibri")
        arcade.draw_text(f"mouse_y: {self.mouse_y}", self.mouse_x+10, self.mouse_y-15, arcade.color.GREEN, 12, 100, "left", "calibri")
        arcade.draw_text(f"fps: {int(arcade.get_fps(10))}", self.mouse_x+10, self.mouse_y-30, arcade.color.GREEN, 12, 100, "left", "calibri")
        arcade.draw_text(f"chunk_x: {self.mouse_chunk_x}", self.mouse_x+10, self.mouse_y-45, arcade.color.GREEN, 12, 100, "left", "calibri")
        arcade.draw_text(f"chunk_y: {self.mouse_chunk_y}", self.mouse_x+10, self.mouse_y-60, arcade.color.GREEN, 12, 100, "left", "calibri")
        arcade.draw_text(f"_range: {_range}", self.mouse_x+10, self.mouse_y-75, arcade.color.AZURE, 12, 100, "left", "calibri")

        arcade.draw_rectangle_outline(self.mouse_chunk_x*CHUNK_FULLSIZE, self.mouse_chunk_y*CHUNK_FULLSIZE, CHUNK_FULLSIZE*(_range*2), CHUNK_FULLSIZE*(_range*2), arcade.color.AZURE, 1, 0)

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

        self.mouse_chunk_x = x // CHUNK_FULLSIZE
        self.mouse_chunk_y = y // CHUNK_FULLSIZE

    def on_mouse_press(self, x, y, button, modifiers):
        saving_json = open("chunkdata\world.json", "a")

    def cleanup(self):
        self.world.save_world()


def main():
    game = Game(WIDTH, HEIGHT, "arcadev")
    arcade.run()
    game.cleanup()


if __name__ == "__main__":
    main()