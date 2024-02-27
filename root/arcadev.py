import random
from perlin_noise import PerlinNoise
import arcade
import multiprocessing as mp
import numpy as np
import queue
import time

# display settings
WIDTH, HEIGHT = 896, 896
SCREEN_SIZE = (WIDTH, HEIGHT)


# world/chunk/tile settings
world_chunk_size_x = 64
world_chunk_size_y = 64
CHUNK_SIZE = 8
TILE_SIZE = 1
CHUNK_FULLSIZE = CHUNK_SIZE*TILE_SIZE
_range = 8


def perlin_worker(input_queue, output_queue, noise1, noise2, noise3, noise4):
    for chunkx, chunky in iter(input_queue.get, 'STOP'):
        data = np.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=np.int8)
        for localx in range(CHUNK_SIZE):
            scaled_x = (localx/CHUNK_SIZE + chunkx)/world_chunk_size_x

            for localy in range(CHUNK_SIZE):
                scaled_y = (localy/CHUNK_SIZE + chunky)/world_chunk_size_y

                noise_val = noise1([scaled_x, scaled_y])
                noise_val += 0.5 * noise2([scaled_x, scaled_y])
                noise_val += 0.25 * noise3([scaled_x, scaled_y])
                noise_val += 0.125 * noise4([scaled_x, scaled_y])
                noise_val *= 200

                data[localx][localy] = min(255, max(0, noise_val))

        output_queue.put((chunkx, chunky, data))


class Tile(arcade.SpriteSolidColor):
    def __init__(self, screenx, screeny, data):
        self.data = int(data)
        super().__init__(TILE_SIZE, TILE_SIZE, (self.data, self.data, self.data))
        self.center_x = screenx
        self.center_y = screeny
        #print("self.x="+str(screenx)+"|self.y="+str(screeny)+"|data="+str(self.data))


class Chunk():
    def __init__(self, chunkx, chunky, data, spritelist):
        self.chunkx = chunkx
        self.chunky = chunky
        self.tiles = []

        for localx in range(CHUNK_SIZE):
            screenx = (localx+CHUNK_SIZE*chunkx)*TILE_SIZE
            for localy in range(CHUNK_SIZE):
                screeny = (localy+CHUNK_SIZE*chunky)*TILE_SIZE
                tile = Tile(screenx, screeny, data[localx][localy])
                self.tiles.append(tile)
                spritelist.append(tile)
    
    def __str__(self):
        return(f"[chunkx={self.chunkx}|chunky={self.chunky}]")


class World:
    def __init__(self, width, height, grid_sprite_list):
        self.width = width
        self.height = height
        self.chunks = []
        self.chunk_list = set(())
        self.grid_sprite_list = grid_sprite_list

        self.task_queue = mp.Queue()
        self.done_queue = mp.Queue()

        self.NUMBER_OF_PROCESSES = 8

        # perlin generator settings
        self.seed = random.randint(0, 1000000)
        print("seed"+str(self.seed))
        self.noise1 = PerlinNoise(octaves=4, seed=self.seed)
        self.noise2 = PerlinNoise(octaves=12, seed=self.seed)
        self.noise3 = PerlinNoise(octaves=48, seed=self.seed)
        self.noise4 = PerlinNoise(octaves=128, seed=self.seed)

        # Start the processes
        for i in range(self.NUMBER_OF_PROCESSES):
            mp.Process(target=perlin_worker, args=(self.task_queue, self.done_queue, self.noise1, self.noise2, self.noise3, self.noise4)).start()

    def request_chunks(self, chunk_coord_list):
        # Request a list of chunks, given their x and y chunk coordinate.
        # Format should be similar to: chunk_list = [[1,2], [1,0], [-1, 4]]
        for coords in chunk_coord_list:
            print(f"Requested chunk: {coords}")
            self.task_queue.put(coords)

    def get_chunks(self):
        try:
            for i in range(8):  # This determines the max number of chunks to try and load per frame
                chunkx, chunky, data = self.done_queue.get(block=False)
                print(f"Got back chunk: ({chunkx},{chunky})")
                self.chunks.append(Chunk(chunkx, chunky, data, self.grid_sprite_list))
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

        stuff_to_gen = []
    
        for chunkx in range(self.mouse_chunk_x-_range, self.mouse_chunk_x+_range):
            for chunky in range(self.mouse_chunk_y-_range, self.mouse_chunk_y+_range):
                if (chunkx,chunky) not in self.world.chunk_list:
                    stuff_to_gen.append((chunkx, chunky))
                    self.world.chunk_list.add((chunkx,chunky))

        self.world.request_chunks(stuff_to_gen)
        print(f"Requesting chunks: {stuff_to_gen}")

    def on_draw(self):
        self.clear()

        self.grid_sprite_list.draw()

        # for chunk in self.world.chunks:
        #    arcade.draw_rectangle_outline((chunk.x*TILE_SIZE*CHUNK_SIZE)+((TILE_SIZE*CHUNK_SIZE)/2),(chunk.y*TILE_SIZE*CHUNK_SIZE)+((TILE_SIZE*CHUNK_SIZE)/2),CHUNK_SIZE*TILE_SIZE,CHUNK_SIZE*TILE_SIZE,(10,10,10),1,0)

        arcade.draw_circle_filled(self.mouse_x, self.mouse_y, 5, arcade.color.WHITE)
        arcade.draw_text(str(self.mouse_x), self.mouse_x+10, self.mouse_y, arcade.color.GREEN, 12, 100, "left", "calibri")
        arcade.draw_text(str(self.mouse_y), self.mouse_x+10, self.mouse_y-15, arcade.color.GREEN, 12, 100, "left", "calibri")
        arcade.draw_text("fps:"+str(int(arcade.get_fps(10))), self.mouse_x+10, self.mouse_y-30, arcade.color.GREEN, 12, 100, "left", "calibri")
        arcade.draw_text("chunkx:"+str(self.mouse_x // CHUNK_FULLSIZE), self.mouse_x+10, self.mouse_y-45, arcade.color.GREEN, 12, 100, "left", "calibri")
        arcade.draw_text("chunky:"+str(self.mouse_y // CHUNK_FULLSIZE), self.mouse_x+10, self.mouse_y-60, arcade.color.GREEN, 12, 100, "left", "calibri")

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

        self.mouse_chunk_x = x // CHUNK_FULLSIZE
        self.mouse_chunk_y = y // CHUNK_FULLSIZE

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def cleanup(self):
        self.world.cleanup()


def main():
    game = Game(WIDTH, HEIGHT, "arcadev")
    arcade.run()
    game.cleanup()


if __name__ == "__main__":
    main()