import random
from perlin_noise import PerlinNoise
import arcade
import multiprocessing as mp
import numpy as np
import queue
import time

# display settings
WIDTH, HEIGHT = 1280, 720
SCREEN_SIZE = (WIDTH, HEIGHT)


# world/chunk/tile settings
world_chunk_size_x = 128
world_chunk_size_y = 128
CHUNK_SIZE = 8
TILE_SIZE = 4
CHUNK_FULLSIZE = CHUNK_SIZE*TILE_SIZE
_range = 4


def perlin_worker(input_queue, output_queue, noise1, noise2, noise3, noise4):
    for chunkx, chunky in iter(input_queue.get, 'STOP'):
        data = np.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=np.int8)
        water_data = np.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=np.int8)
        for localx in range(CHUNK_SIZE):
            scaled_x = (localx/CHUNK_SIZE + chunkx)/world_chunk_size_x

            for localy in range(CHUNK_SIZE):
                scaled_y = (localy/CHUNK_SIZE + chunky)/world_chunk_size_y

                noise_val = noise1([scaled_x, scaled_y])
                noise_val += 0.5 * noise2([scaled_x, scaled_y])
                noise_val += 0.25 * noise3([scaled_x, scaled_y])
                noise_val += 0.125 * noise4([scaled_x, scaled_y])
                noise_val *= 200

                data[localx][localy] = min(255, max(1, noise_val))
                water_data[localx][localy] = 0

        output_queue.put((chunkx, chunky, data, water_data))


class Tile(arcade.SpriteSolidColor):
    def __init__(self, input_screenx, input_screeny, input_data, input_water_data):
        super().__init__(TILE_SIZE, TILE_SIZE, (int(input_data), int(input_data), int(input_data)))
        self.data = int(input_data)
        self.water_data = input_water_data
        self.center_x = input_screenx+(int(TILE_SIZE/2))
        self.center_y = input_screeny+(int(TILE_SIZE/2))


class Chunk():
    def __init__(self, input_chunkx, input_chunky, input_data, input_water_data, spritelist):
        self.chunkx = input_chunkx
        self.chunky = input_chunky
        self.tiles = []

        for localx in range(CHUNK_SIZE):
            screenx = (localx+CHUNK_SIZE*input_chunkx)*TILE_SIZE
            for localy in range(CHUNK_SIZE):
                screeny = (localy+CHUNK_SIZE*input_chunky)*TILE_SIZE
                tile = Tile(screenx, screeny, input_data[localx][localy], input_water_data[localx][localy])
                self.tiles.append(tile)
                spritelist.append(tile)

    def update_water(self):
        for x in range(self.tiles):
            for y in range(self.tiles):
                center_height = self.tiles.data
                center_water = self.tiles.water_data
                adjacent_cells = []
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        if i == 0 and j == 0:  # Skip the center cell
                            continue
                        if x + i < 0 or x + i >= self.size[0]: # Skip cells outside the board
                            continue
                        if y + j < 0 or y + j >= self.size[1]: # Skip cells outside the baord
                            continue
                        if self.tiles[x + i][y + j] < center_height:
                            adjacent_cells.append((x + i, y + j, self.tiles[x + i][y + j]))
    
    def __str__(self):
        return(f"[chunkx={self.chunkx}|chunky={self.chunky}]")


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
        print("seed"+str(self.seed))
        self.noise1 = PerlinNoise(octaves=2, seed=self.seed)
        self.noise2 = PerlinNoise(octaves=8, seed=self.seed)
        self.noise3 = PerlinNoise(octaves=32, seed=self.seed)
        self.noise4 = PerlinNoise(octaves=128, seed=self.seed)

        # Start the processes
        for i in range(self.NUMBER_OF_PROCESSES):
            mp.Process(target=perlin_worker, args=(self.task_queue, self.done_queue, self.noise1, self.noise2, self.noise3, self.noise4)).start()

    def request_chunks(self, chunk_coord_list):
        for coords in chunk_coord_list:
            print(f"Requested chunk: {coords}")
            self.task_queue.put(coords)

    def get_chunks(self):
        try:
            for i in range(8):  # This determines the max number of chunks to try and load per frame
                chunkx, chunky, data, water_data = self.done_queue.get(block=False)
                print(f"Got back chunk: ({chunkx},{chunky})")
                self.chunks.append(Chunk(chunkx, chunky, data, water_data, self.grid_sprite_list))
        except queue.Empty:
            return

    def cleanup(self):
        # Cleanup the worker processes.
        # Otherwise, they will be left orphaned (and that wouldn't be very nice.)
        for i in range(self.NUMBER_OF_PROCESSES):
            self.task_queue.put('STOP')


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
                    stuff_to_gen.add((chunkx, chunky))
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
        stuff_to_gen = []
    
        for chunkx in range(world_chunk_size_x):
            for chunky in range(world_chunk_size_x):
                if (chunkx,chunky) not in self.world.chunk_generated_coordinate_list:
                    stuff_to_gen.append((chunkx, chunky))
                    self.world.chunk_generated_coordinate_list.add((chunkx,chunky))

        self.world.request_chunks(stuff_to_gen)
        if stuff_to_gen:
            print(f"Requesting chunks: {stuff_to_gen}")

    def cleanup(self):
        self.world.cleanup()


def main():
    game = Game(WIDTH, HEIGHT, "arcadev")
    arcade.run()
    game.cleanup()


if __name__ == "__main__":
    main()