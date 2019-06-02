# -*- coding: cp936 -*-
import pygame
#import numpy
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

BACKGROUND_COLOR = (168, 168, 168)
WHITE = (255, 255, 255)
FPS = 60
SCREEN_SIZE = (1300, 650)
MARS_SCREEN_SIZE = (8000, 4500)
MARS_MAP_SIZE = (8000 * 5, 4500 * 5)  # topleft starts: width, height
CLOUD_IMAGE_LIST = ['./image/cloud1.png','./image/cloud2.png','./image/cloud3.png','./image/cloud4.png']

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
        # cloud.png has transparent color ,use "convert_alpha()"
        self.image = pygame.image.load(image).convert_alpha()  # image of Sprite
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect(center=location)  # rect of Sprite

        # self.location = Vector(0, 0)  # ...

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

    def __init__(self, catalog):
        pass

    def load_weapon(self, catalog='Cobra', number=6):
        pass

class Player(object):

    def __init__(self):
        pass

    def add_plane(self, plane):
        pass

class Map(object):

    def __init__(self, size=MARS_MAP_SIZE):
        self.size = self.mars_translate(size)  # print size, self.size
        self.surface = pygame.Surface(self.size)
        self.surface.fill(BACKGROUND_COLOR)

    def mars_translate(self, coordinate):
        """translate Mars Coordinate to current Display Coordinate"""
        return [int(coordinate[i]/(float(MARS_SCREEN_SIZE[i])/SCREEN_SIZE[i])) for i in [0,1]]

    def add_cloud(self, cloud_num=100):
        sprite_group = pygame.sprite.Group()
        for i in range(cloud_num):  # make 10 clouds randomly
            location = [randint(0, self.size[0]), randint(0, self.size[1])]
            cloud_image = CLOUD_IMAGE_LIST[randint(0,len(CLOUD_IMAGE_LIST))-1]  # print location , cloud_image
            cloud = Base(location=location, image=cloud_image)
            sprite_group.add(cloud)
        sprite_group.draw(self.surface)

class MiniMap(object):

    def __init__(self, screen, map_rect, current_location):
        self.screen = screen
        self.screen_rect = self.screen.get_rect()
        left = 10
        width = self.screen_rect.width / 5
        height = self.screen_rect.height / 4
        top = self.screen_rect.height - 10 - height
        self.rect = pygame.Rect(left,top,width,height)

        self.current_location = current_location
        self.map_rect = map_rect
        self.mini_width = int(self.rect.width / (float(MARS_MAP_SIZE[0]) / MARS_SCREEN_SIZE[0]))
        self.mini_height = int(self.rect.height / (float(MARS_MAP_SIZE[1]) / MARS_SCREEN_SIZE[1]))
        self.mini_left = self.rect.left + int(self.rect.width * self.current_location.left/ float(self.map_rect.left+1))
        self.mini_top = self.rect.top + int(self.rect.height* self.current_location.top/ float(self.map_rect.top+1) )
        self.mini_rect = pygame.Rect(self.mini_left, self.mini_top, self.mini_width, self.mini_height)

    def update(self):
        self.mini_left = self.rect.left + int(self.current_location.left / float(self.map_rect.width) * self.rect.width)  # 当前比例*小图宽度
        self.mini_top = self.rect.top + int(self.current_location.top / float(self.map_rect.height) * self.rect.height)  # 当前比例*小图高度
        self.mini_rect = pygame.Rect(self.mini_left, self.mini_top, self.mini_width, self.mini_height)

    def draw(self):
        pygame.draw.rect(self.screen, (0, 0, 0), self.rect, 1)  # Big Rect in MiniMap
        pygame.draw.rect(self.screen, (0,225,10), self.mini_rect ,1)  # Small(current display) Rect in MiniMap

class World(object):

    def __init__(self, screen):
        super(World,self).__init__()
        self.map = None
        self.screen = screen
        # self.current_location = self.screen.get_rect()

    def add_player(self, player):
        pass

    def add_map(self, map):
        self.map = map

    def add_minimap(self, minimap):
        self.minimap = minimap

    def render(self, screen_rect):

        self.current_location = screen_rect
        self.screen.blit(source=self.map.surface, dest=(0,0), area=self.current_location)

        self.minimap.draw()


        # self.screen.blit()

    def process(self):
        self.minimap.update()
        pass



class Game(object):

    def __init__(self):

        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        pygame.mixer.init()  # 声音初始化
        pygame.display.set_mode(SCREEN_SIZE)  # pygame.display.set_mode(pygame.FULLSCREEN)

        self.screen = pygame.display.get_surface()
        self.screen_rect = self.screen.get_rect()
        self.move_pixels = 10

        self.fps = FPS
        self.clock = pygame.time.Clock()

        self.done = False

    def event_control(self):
        for event in pygame.event.get():
            self.keys = pygame.key.get_pressed()
            if event.type == pygame.QUIT or self.keys[pygame.K_ESCAPE]:
                self.done = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.screen_rect.x -= self.move_pixels
                if event.key == pygame.K_RIGHT:
                    self.screen_rect.x += self.move_pixels
                if event.key == pygame.K_UP:
                    self.screen_rect.y -= self.move_pixels
                if event.key == pygame.K_DOWN:
                    self.screen_rect.y += self.move_pixels


    def main(self):
        # INIT
        world = World(self.screen)

        player = Player()
        plane = Plane(catalog='F35')
        plane.load_weapon(catalog='Cobra', number=6)
        player.add_plane(plane)
        world.add_player(player)

        map = Map()  # 8000*4500--->screen, (8000*5)*(4500*5)---->map
        map.add_cloud()
        world.add_map(map)

        minimap = MiniMap(self.screen, world.map.surface.get_rect(), self.screen_rect)
        world.add_minimap(minimap)

        pygame.key.set_repeat(10,10)  # control how held keys are repeated
        #####............to be continue

        # PYGAME LOOP
        while not self.done:
            self.event_control()
            world.render(self.screen_rect)
            world.process()

            pygame.display.flip()
            self.clock.tick(self.fps)

if __name__ == '__main__':
    game = Game()
    game.main()
