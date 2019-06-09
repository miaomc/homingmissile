# -*- coding: cp936 -*-
import pygame
# import numpy
import os
from random import randint
import socket
import threading
import Queue
import json

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
FPS = 50
SCREEN_SIZE = (1300, 650)
MARS_SCREEN_SIZE = (8000, 4500)
MARS_MAP_SIZE = (8000 * 5, 4500 * 5)  # topleft starts: width, height
CLOUD_IMAGE_LIST = ['./image/cloud1.png', './image/cloud2.png', './image/cloud3.png', './image/cloud4.png']


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

    def __init__(self, ip='127.0.0.1'):
        self.ip = ip

    def add_plane(self, plane):
        pass

    def update(self, event_list):
        # Get all data from NetCard
        # 如果操作更新了，就把操作发送到各个电脑终端上，进行演绎
        # ..........to be continue
        pass

    def operation(self, event_list):
        # !!!!!!!!!! 从这里开始  to be continue...
        pass


class Map(object):

    def __init__(self, size=MARS_MAP_SIZE):
        self.size = self.mars_translate(size)  # print size, self.size
        self.surface = pygame.Surface(self.size)
        self.surface.fill(BACKGROUND_COLOR)

    def mars_translate(self, coordinate):
        """translate Mars Coordinate to current Display Coordinate"""
        return [int(coordinate[i] / (float(MARS_SCREEN_SIZE[i]) / SCREEN_SIZE[i])) for i in [0, 1]]

    def add_cloud(self, cloud_num=100):
        sprite_group = pygame.sprite.Group()
        for i in range(cloud_num):  # make 10 clouds randomly
            location = [randint(0, self.size[0]), randint(0, self.size[1])]
            cloud_image = CLOUD_IMAGE_LIST[randint(0, len(CLOUD_IMAGE_LIST)) - 1]  # print location , cloud_image
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
        self.rect = pygame.Rect(left, top, width, height)

        self.current_location = current_location
        self.map_rect = map_rect
        self.mini_width = int(self.rect.width / (float(MARS_MAP_SIZE[0]) / MARS_SCREEN_SIZE[0]))
        self.mini_height = int(self.rect.height / (float(MARS_MAP_SIZE[1]) / MARS_SCREEN_SIZE[1]))
        self.mini_left = self.rect.left + int(
            self.rect.width * self.current_location.left / float(self.map_rect.left + 1))
        self.mini_top = self.rect.top + int(self.rect.height * self.current_location.top / float(self.map_rect.top + 1))
        self.mini_rect = pygame.Rect(self.mini_left, self.mini_top, self.mini_width, self.mini_height)

    def update(self):
        self.mini_left = self.rect.left + int(
            self.current_location.left / float(self.map_rect.width) * self.rect.width)  # 当前比例*小图宽度
        self.mini_top = self.rect.top + int(
            self.current_location.top / float(self.map_rect.height) * self.rect.height)  # 当前比例*小图高度
        self.mini_rect = pygame.Rect(self.mini_left, self.mini_top, self.mini_width, self.mini_height)

    def draw(self):
        pygame.draw.rect(self.screen, (0, 0, 0), self.rect, 1)  # Big Rect in MiniMap
        pygame.draw.rect(self.screen, (0, 225, 10), self.mini_rect, 1)  # Small(current display) Rect in MiniMap


class World(object):

    def __init__(self, screen):
        super(World, self).__init__()
        self.map = None
        self.minimap = None
        self.screen = screen
        # self.current_location = self.screen.get_rect()

        self.player_list = []

        # MSG QUEUE
        self.q = Queue.Queue()

        # UDP server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        address = ("127.0.0.1", 8989)
        self.sock.bind(address)

        # UDP listening
        thread1 = threading.Thread(target=self.msg_recv)
        thread1.setDaemon(True)  # True:不关注这个子线程，主线程跑完就结束整个python process
        thread1.start()

    def msg_recv(self):
        while True:
            self.q.put(self.sock.recvfrom(2048))
            print("get msg.")

    def add_player(self, player):
        self.player_list.append(player)
        pass

    def add_map(self, big_map):
        self.map = big_map

    def add_minimap(self, mini_map):
        self.minimap = mini_map

    def render(self, screen_rect):

        self.current_location = screen_rect
        self.screen.blit(source=self.map.surface, dest=(0, 0), area=self.current_location)

        self.minimap.draw()

        # self.screen.blit()

    def player_communicate(self, event_list):
        """
        在World类里面实现，TCP/IP的事件信息交互，Player类只做事件的update()
        """
        if not event_list:  # 如果没操作队列，就不发消息
            return

        str_event_list = json.dumps(event_list)
        for player in self.player_list:  # 发送给每一个网卡，包括自己
            self.sock.sendto(str_event_list, (player.ip, 8989))

    def process(self, event_list):
        """[WARNING]每个玩家（world）接收自己的消息队列，刷新自己的界面，没有消息同步机制，也没有同步下发机制，
        会导致不同玩家画面不一致情况（尤其在网络延迟大的情况下）"""
        self.minimap.update()

        self.player_communicate(event_list)

        while not self.q.empty():  # [WARNING]这么写有可能被阻塞，当一直有消息发过来的时候
            data, address = self.q.get()
            for player in self.player_list:  # 遍历玩家，看这个收到的数据是谁的
                if player.ip == address[0]:
                    player.operation(json.loads(data))  # data is pygame.EventList of json.dumps

        for player in self.player_list:
            player.update(event_list)
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
        event_list = pygame.event.get()
        print 'EVENT:',event_list
        key_list = []
        for event in event_list:
            keys = pygame.key.get_pressed()  # key is queue too
            print '    KEY:', keys
            if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
                self.done = True
                return  # EXIT GAME
            if keys[pygame.K_LEFT]:  # 直接使用 pygame.key.get_pressed() 可以多键同时独立识别
                self.screen_rect.x -= self.move_pixels
            if keys[pygame.K_RIGHT]:
                self.screen_rect.x += self.move_pixels
            if keys[pygame.K_UP]:
                self.screen_rect.y -= self.move_pixels
            if keys[pygame.K_DOWN]:
                self.screen_rect.y += self.move_pixels
        return ''
        # 1player_operation2keyorevent3sprite_location
        # event_list  # pygame's Eventlist

        # if event.type == pygame.KEYDOWN:
        #     if event.key == pygame.K_LEFT:
        #         self.screen_rect.x -= self.move_pixels
        #     if event.key == pygame.K_RIGHT:
        #         self.screen_rect.x += self.move_pixels
        #     if event.key == pygame.K_UP:
        #         self.screen_rect.y -= self.move_pixels
        #     if event.key == pygame.K_DOWN:
        #         self.screen_rect.y += self.move_pixels

    def main(self):
        # INIT
        world = World(self.screen)

        # local player
        player = Player()
        plane = Plane(catalog='F35')
        plane.load_weapon(catalog='Cobra', number=6)
        player.add_plane(plane)
        world.add_player(player)

        # LAN player
        player = Player()  # Player(ip)
        world.add_player(player)

        game_map = Map()  # 8000*4500--->screen, (8000*5)*(4500*5)---->map
        game_map.add_cloud()
        world.add_map(game_map)

        minimap = MiniMap(self.screen, world.map.surface.get_rect(), self.screen_rect)
        world.add_minimap(minimap)

        # ####............to be continue

        # PYGAME LOOP
        pygame.key.set_repeat(10, 10)  # control how held keys are repeated
        while not self.done:
            event_list = self.event_control()
            world.process(event_list)
            world.render(self.screen_rect)

            pygame.display.flip()
            self.clock.tick(self.fps)


if __name__ == '__main__':
    game = Game()
    game.main()
