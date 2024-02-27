import pygame
import sys
import random
from perlin_noise import PerlinNoise
import threading
from multiprocessing import *
from numba import jit
import numpy as np

pygame.init()


# display settings
WIDTH, HEIGHT = 896, 896
SCREEN_SIZE = (WIDTH, HEIGHT)


# world/chunk/tile settings
world_chunk_size_x = 128
world_chunk_size_y = 128
CHUNK_SIZE = 8
TILE_SIZE = 4


# perlin generator settings
global_seed = random.randint(0, 1000000)
print("seed"+str(global_seed))

noise1 = PerlinNoise(octaves=12, seed=global_seed)
noise2 = PerlinNoise(octaves=24, seed=global_seed)
noise3 = PerlinNoise(octaves=48, seed=global_seed)
noise4 = PerlinNoise(octaves=96, seed=global_seed)


# color settings
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


# tile class
class Tile:
    def __init__(self, x, y, data):
        self.x = x
        self.y = y
        self.data = data*100
        self.color = (100*data,100*data,100*data)

        self.__str__()

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    def __str__(self):
        print("[self.x=" + str(self.x) + "|self.y=" + str(self.y) + "|self.data=" + str(self.data) + "] <-- TILE")


# chunk class
class Chunk:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tiles = []
        self.generate_tiles()

        #self.__str__()

    def generate_tiles(self):
        for x in range(self.x * CHUNK_SIZE, (self.x + 1) * CHUNK_SIZE):
            for y in range(self.y * CHUNK_SIZE, (self.y + 1) * CHUNK_SIZE):
                noise_val = noise1([x/(world_chunk_size_x*CHUNK_SIZE), y/(world_chunk_size_y*CHUNK_SIZE)])
                noise_val += 0.5 * noise2([x/(world_chunk_size_x*CHUNK_SIZE), y/(world_chunk_size_y*CHUNK_SIZE)])
                noise_val += 0.25 * noise3([x/(world_chunk_size_x*CHUNK_SIZE), y/(world_chunk_size_y*CHUNK_SIZE)])
                noise_val += 0.125 * noise4([x/(world_chunk_size_x*CHUNK_SIZE), y/(world_chunk_size_y*CHUNK_SIZE)])

                if noise_val <= 0:
                    noise_val = 0

                if noise_val >= 255:
                    noise_val = 255

                self.tiles.append(Tile(x, y, noise_val))

    def draw(self, screen):
        for tile in self.tiles:
            tile.draw(screen)
        pygame.draw.rect(screen, (10,10,10 ), [self.x*TILE_SIZE*CHUNK_SIZE, self.y*TILE_SIZE*CHUNK_SIZE, CHUNK_SIZE*TILE_SIZE, CHUNK_SIZE*TILE_SIZE], 1)

    def __str__(self):
        print("[self.x=" + str(self.x) + "|self.y=" + str(self.y) + "] <-- CHUNK")


# world class
class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.chunks = []

        #self.__str__()

    def generate_chunks(self, x, y):
        # calc chunk position 
        chunk_x = x // (CHUNK_SIZE * TILE_SIZE)
        chunk_y = y // (CHUNK_SIZE * TILE_SIZE)

        # if chunk exists at place
        for chunk in self.chunks:
            if chunk.x == chunk_x and chunk.y == chunk_y:
                return

        if chunk_x > self.width or chunk_y > self.height:
            return

        # chunk doesnt exist, generate it
        self.chunks.append(Chunk(chunk_x, chunk_y))

    def generate_chunks_range(self, self_chunk_x, self_chunk_y, _range):
        for i in range(self_chunk_x - _range, self_chunk_x + _range):
            for j in range(self_chunk_y - _range, self_chunk_y + _range):
                for chunk in self.chunks:
                    if chunk.x == i and chunk.y == j:
                        print("gen: breaking["+str(i)+"|"+str(j)+"]")
                        break
                else:
                    print("gen: generating["+str(i)+"|"+str(j)+"]")
                    self.chunks.append(Chunk(i, j))

    def draw(self, screen):
        for chunk in self.chunks:
            chunk.draw(screen)

    def __str__(self):
        print("[self.width=" + str(self.width) + "|self.height=" + str(self.height) + "] <-- WORLD")


# pygame settings
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("Chunk_ProofOfConcept")
clock = pygame.time.Clock()
world = World(world_chunk_size_x,world_chunk_size_y)

# main sim loop
def main():
    clock = pygame.time.Clock()
    running = True
    while running:
        # event handling
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # update game state
        world.generate_chunks_range(mouse_pos[0] // (CHUNK_SIZE * TILE_SIZE), mouse_pos[1] // (CHUNK_SIZE * TILE_SIZE),2)

        # draw everything
        screen.fill((0, 0, 0))
        world.draw(screen)

        font = pygame.font.Font('freesansbold.ttf', 16)
        text = font.render(('fps='+str(int(clock.get_fps()))), True, WHITE, BLACK)
        textRect = text.get_rect()
        textRect.center = (400 // 2, 400 // 2)

        # update the display
        screen.blit(text, textRect)
        pygame.display.flip()

        clock.tick(165)
    pygame.quit()
    sys.exit()

    
if __name__ == "__main__":
    main()
