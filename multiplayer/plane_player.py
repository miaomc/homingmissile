# -*- coding: cp936 -*-
import pygame
import numpy
import os
from random import randint


"""
plane:
    initial_speed:
    speed:
    max_speed:
    accelerate_parallel
    # accelerate_vertical
    control_key: left, right, fire_gun, fire_missile, fire_homing_missile

missile:
    initial_speed:
    speed:
    max_speed:
    accelerate_parallel
    accelerate_vertical
"""

# 性能参数放在最前面,方便最后核对调整
PLANE_CATALOG = {
    'J20': {
        'health': 100,
        'speed': 850,
        'gun_speed': 1000,
        'gun_damage': 5,
        'max_missile': 6
    },
    'F35': {
        # ...
    },
    'F22': {
        # ...
    }
}

MISSILE_CATALOG = {
    'Cobra': {
        'health': 9999,
        'max_speed': 1360,
        'accelerate_speed': 100,
        'accelerate_turn': 25
    },
    'Pili': {
        # ...,
    }
}

WHITE = (255, 255, 255)
MAP_SIZE = (8000 * 5, 4500 * 5)  # topleft starts: width, height
CLOUD_IMAGE = './cloud.png'

class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return [self.x + other[0], self.y + other[1]]

    def __mul__(self, other):
        return [self.x + other[0], self.y + other[1]]

    # def ...


class Base(pygame.sprite.Sprite):
"""
location:
image:
"""
    def __init__(self, location, image):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.image.load(image).convert()  # image of Sprite
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect(center=location)  # rect of Sprite



        self.location = Vector(0, 0)  # ...

        self.min_speed = 0
        self.max_speed = 3000  # m/s
        self.speed = Vector
        self.accelerate_turn = 0
        self.accelerate_accelerate = 0

        # ...
        self.location = location  # [x, y]
        self.rect = self.image.get_rect(center=location)

class Missile(Base):
    pass


class Plane(Base):
    pass


class Map(object):

    def __init__(self):
        self.surface = pygame.Surface(MAP_SIZE)

    def add_cloud(self):
        sprite_group = pygame.sprite.Group()
        for i in range(10):  # make 10 clouds randomly
            location = [randint(0,MAP_SIZE[0]), randint(0,MAP_SIZE[1])]
            cloud = Base(location=location, image=CLOUD_IMAGE)
            sprite_group.add(cloud)
        sprite_group.draw(self.surface)


class World(object):
    pass


class Game(object):

    def __init__(self):
        SCREEN_SIZE = (1366, 768)
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        pygame.mixer.init()  # 声音初始化
        pygame.display.set_mode(SCREEN_SIZE)

        self.screen = pygame.display.get_surface()
        self.screen_rect = self.screen.get_rect()

    def main(self):
        # INIT
        world = World()

        player = Player()
        plane = Plane(catalog='F35')
        plane.load_weapon(catalog='Cobra', number=6)
        player.add_plane(plane)
        world.add_player(player)

        map = Map(8000 * 5, 4500 * 5)  # 8000*4500--->screen, (8000*5)*(4500*5)---->map
        map.add_cloud()
        world.add_map(map)

        #####............to be continue

        # PYGAME LOOP
        self.done = False
        while not self.done:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.done = True

            world.process()
            world.render()


if __name__ == '__main__':
    game = Game()
    game.main()
