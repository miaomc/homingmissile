# -*- coding: cp936 -*-
import pygame
import math
import os
from random import randint
import socket
import threading
import Queue
import json
import logging
from infomation import Infomation

DEBUG_MODE = False
LOCALIP = '192.168.1.113'
OTHERIP = '192.168.0.103'
PLANE_TYPE = 'F35'

PLANE_CATALOG = {
    'J20': {
        'health': 100,
        'max_speed': 1400,
        'min_speed': 200,  # 540,
        'acc_speed': 50,
        'turn_acc': 10,
        'image': './image/plane_red.png',
        'damage': 100,
    },
    'F35': {
        'health': 100,
        'max_speed': 1400,
        'min_speed': 200,  # 540,
        'acc_speed': 50,
        'turn_acc': 10,
        'image': './image/plane_blue.png',
        'damage': 100,
    },
    'F22': {
        # ...
    }
}

WEAPON_CATALOG = {
    'Gun': {
        'health': 10,
        'init_speed': 1500,
        'max_speed': 2500,
        'acc_speed': 0,
        'turn_acc': 0,
        'damage': 2,
        'image': ['./image/gunfire1.png', './image/gunfire2.png'],
        'fuel': 6,
        'sound_collide_plane': ['./sound/bulletLtoR08.wav', './sound/bulletLtoR09.wav', './sound/bulletLtoR10.wav',
                                './sound/bulletLtoR11.wav', './sound/bulletLtoR13.wav', './sound/bulletLtoR14.wav']
    },
    'Rocket': {
        'health': 10,
        'init_speed': 0,
        'max_speed': 1500,
        'acc_speed': 120,
        'damage': 35,
        'turn_acc': 0,
        'image': './image/homingmissile.png',
        'fuel': 9,
    },
    'Cobra': {
        'health': 10,
        'init_speed': 0,
        'max_speed': 1360,
        'acc_speed': 40,
        'turn_acc': 35,
        'damage': 25,
        'image': './image/homingmissile.png',
        'fuel': 9,
        'dectect_range': 10000 * 30
    },
    'Pili': {
        # ...,
    }
}

SPEED_RATIO = 0.25

BACKGROUND_COLOR = (168, 168, 168)
WHITE = (255, 255, 255)
FPS = 50
SCREEN_SIZE = (1280, 720)
MARS_SCREEN_SIZE = (8000, 4500)
MARS_MAP_SIZE = (8000 * 4, 4500 * 4)  # topleft starts: width, height
CLOUD_IMAGE_LIST = ['./image/cloud1.png', './image/cloud2.png', './image/cloud3.png', './image/cloud4.png']


class Vector:
    def __init__(self, *args):
        if len(args) == 2:
            self.x = args[0]
            self.y = args[1]
        elif len(args[0]) == 2:
            self.x = args[0][0]
            self.y = args[0][1]
        else:
            print('Invalid Vector:', args)

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, a):
        """乘以常量a"""
        return Vector(self.x * a, self.y * a)

    def __div__(self, a):
        return Vector(self.x / a, self.y / a)

    def __str__(self):
        return str(self.x) + ', ' + str(self.y)

    # def __neg__(self):
    #     return Vector(-self.x, -self.y)

    def normalize_vector(self):
        """单位向量"""
        return Vector(self.x, self.y) * self.reverse_normalize()

    def reverse_normalize(self):
        """1/向量长度"""
        if self.x == 0 and self.y == 0:
            return 0
        else:
            return 1 / math.sqrt(self.x * self.x + self.y * self.y)

    def length(self):
        """向量长度"""
        return math.sqrt(self.x * self.x + self.y * self.y)

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    def angle(self):
        """
        本身的角度，带方向的。由于pygame的坐标特性，顺时针为正. 返回的为pi，不是度
        """
        return math.atan2(self.y, self.x)

    def vertical_left(self):
        """左转90°的法向量"""
        return Vector(self.y * self.reverse_normalize(), -self.x * self.reverse_normalize())

    def vertical_right(self):
        """左转90°的法向量"""
        return Vector(-self.y * self.reverse_normalize(), self.x * self.reverse_normalize())


class Base(pygame.sprite.Sprite):
    """
location:
image:
"""

    def __init__(self, location, image):
        pygame.sprite.Sprite.__init__(self)
        # cloud.png has transparent color ,use "convert_alpha()"

        # ![WARNING] 这个应该要修改为 image = Surface对象
        self.image = image  # pygame.image.load(image).convert_alpha()  # image of Sprite

        # self.image.set_colorkey(WHITE)

        self.location = Vector(location)  # 采用 self.location记录位置，因为self.rect里面的值都是个整数
        # print self.location
        self.rect = self.image.get_rect(center=location)  # rect of Sprite

        # 图像翻转
        self.origin_image = self.image.copy()
        self.velocity = Vector(0, 1)  # 默认朝上

        # self.location = Vector(0, 0)  # ...

        self.min_speed = 0
        self.max_speed = 3000  # m/s
        self.speed = None  # Vector
        self.turn_acc = 0
        self.acc_speed = 0

        self.health = 0
        self.damage = 0
        self.alive = True

        self.acc = Vector(0, 0)

        self.sound_kill = None

    def rotate(self):
        angle = math.atan2(self.velocity.x, self.velocity.y) * 360 / 2 / math.pi - 180  # 这个角度是以当前方向结合默认朝上的原图进行翻转的
        self.image = pygame.transform.rotate(self.origin_image, angle)

    def update(self):
        self.velocity += self.acc
        self.location.x += self.velocity.x * SPEED_RATIO / FPS
        self.location.y += self.velocity.y * SPEED_RATIO / FPS
        if self.location.x < 0:
            self.location.x = 0
        elif self.location.x > MARS_MAP_SIZE[0]:
            self.location.x = MARS_MAP_SIZE[0]
        if self.location.y < 0:
            self.location.y = 0
        elif self.location.y > MARS_MAP_SIZE[1]:
            self.location.y = MARS_MAP_SIZE[1]
        self.rect.center = Map.mars_translate((self.location.x, self.location.y))
        # logging.info('acc: %s' % str(self.acc))
        self.acc = Vector(0, 0)
        self.rotate()
        # logging.info('location:%s, rect:%s' % (str(self.location), str(self.rect)))

    def delete(self):
        self.kill()  # remove the Sprite from all Groups
        self.alive = False
        if self.sound_kill:
            self.sound_kill.play()

    def hitted(self, base_lst):
        for base in base_lst:
            if id(self) == id(base):  # spritecollide如果是自己和自己就不需要碰撞了
                continue
            # print base.rect, self.rect
            self.health -= base.damage
            base.health -= self.damage
            if self.catalog == 'Gun' and isinstance(base, Plane):
                self.sound_collide_plane.play()


class Plane(Base):

    def __init__(self, location, catalog='J20'):
        image_path = PLANE_CATALOG[catalog]['image']
        self.image_original = pygame.image.load(image_path).convert()
        self.image = self.image_original.subsurface((0, 0, 39, 39))
        self.image.set_colorkey(WHITE)
        super(Plane, self).__init__(location=location, image=self.image)

        self.max_speed = PLANE_CATALOG[catalog]['max_speed']
        self.min_speed = PLANE_CATALOG[catalog]['min_speed']
        self.turn_acc = PLANE_CATALOG[catalog]['turn_acc']
        self.acc_speed = PLANE_CATALOG[catalog]['acc_speed']
        self.damage = PLANE_CATALOG[catalog]['damage']
        self.health = PLANE_CATALOG[catalog]['health']

        self.speed = (self.max_speed + self.min_speed) / 2  # 初速度为一半
        self.velocity = Vector(1, 1).normalize_vector() * self.speed  # Vector
        self.acc = Vector(0, 0)

        self.weapon = {1: {}, 2: {}, 3: {}}  # 默认没有武器

        self.sound_kill = pygame.mixer.Sound("./sound/explode3.wav")

    def turn_left(self):
        self.acc += self.velocity.vertical_left() * self.turn_acc

    def turn_right(self):
        self.acc += self.velocity.vertical_right() * self.turn_acc

    def speedup(self):
        self.acc += self.velocity.normalize_vector() * self.acc_speed
        if (self.velocity + self.acc).length() > self.max_speed:
            self.acc = Vector(0, 0)

    def speeddown(self):
        self.acc -= self.velocity.normalize_vector() * self.acc_speed
        if (self.velocity - self.acc).length() < self.min_speed:
            self.acc = Vector(0, 0)

    def load_weapon(self, catalog='Cobra', number=6):
        """self.weapon = { 1: {catalog:<Gun>, number=500},
            2:{catalog:<Cobra>, number=6},
            3: None
        }"""
        index = 3  # 默认为非Gun子弹和Rocket火箭弹的其他类
        if catalog == 'Gun':
            index = 1
        elif catalog == 'Rocket':
            index = 2
        self.weapon[index]['catalog'] = catalog
        self.weapon[index]['number'] = number

    def update(self):
        super(Plane, self).update()
        if self.health <= 0:
            self.delete()


class Missile(Base):
    def __init__(self, catalog, location, velocity):
        if catalog == 'Gun':
            image_path = WEAPON_CATALOG['Gun']['image'][randint(0, len(WEAPON_CATALOG['Gun']['image']) - 1)]
            self.sound_fire = pygame.mixer.Sound("./sound/minigun_fire.wav")
            self.sound_fire.play(maxtime=100)
            self.sound_collide_plane = pygame.mixer.Sound(WEAPON_CATALOG['Gun']['sound_collide_plane'][randint(0, len(
                WEAPON_CATALOG['Gun']['sound_collide_plane']) - 1)])
        else:
            image_path = WEAPON_CATALOG[catalog]['image']
            self.sound_fire = pygame.mixer.Sound("./sound/TPhFi201.wav")
            self.sound_fire.play()
            self.sound_kill = pygame.mixer.Sound("./sound/ric5.wav")
        if catalog == 'Cobra':
            self.detect_range = WEAPON_CATALOG[catalog]['dectect_range']
        self.image_original = pygame.image.load(image_path).convert()
        self.image_original.set_colorkey(WHITE)
        super(Missile, self).__init__(location=location, image=self.image_original)

        self.health = WEAPON_CATALOG[catalog]['health']
        self.damage = WEAPON_CATALOG[catalog]['damage']
        self.init_speed = WEAPON_CATALOG[catalog]['init_speed']
        self.turn_acc = WEAPON_CATALOG[catalog]['turn_acc']
        self.acc_speed = WEAPON_CATALOG[catalog]['acc_speed']
        self.acc = self.velocity.normalize_vector() * self.acc_speed
        self.fuel = WEAPON_CATALOG[catalog]['fuel'] * FPS  # 单位为秒

        self.velocity = velocity + velocity.normalize_vector() * self.init_speed  # 初始速度为飞机速度+发射速度

        self.catalog = catalog
        self.target = None

    def update(self, plane_group):
        if self.catalog == 'Cobra':
            """
            飞机、枪弹是一回事，加速度在不去动的情况下，为0；
            """
            if self.target and abs(self.velocity.angle() - (self.target.location - self.location).angle()) < math.pi / 3\
                    and (self.location - self.target.location).length() < self.detect_range:
                angle_between = self.velocity.angle() - (self.target.location - self.location).angle()
                # print 'on target~',
                # 预计垂直速度的长度, 带正s负的一个float数值
                expect_acc = (self.target.location - self.location).length() * math.sin(angle_between)
                if abs(expect_acc) < self.turn_acc:  # 如果期望转向速度够了，就不用全力
                    acc = abs(expect_acc) * (1 and 0 < angle_between < math.pi or -1)
                else:  # 期望转向速度不够，使用全力转向
                    acc = self.turn_acc * (1 and 0 < angle_between < math.pi or -1)
                self.acc.x += acc * math.sin(self.velocity.angle())
                self.acc.y += - acc * math.cos(self.velocity.angle())
                # print 'target on:',self.target
            else:
                self.target = None
                for plane in plane_group:
                    if abs(self.velocity.angle() - (plane.location - self.location).angle()) < math.pi / 3 and \
                            (self.location - plane.location).length() < self.detect_range:
                        self.target = plane
                        break

        if self.min_speed < self.velocity.length() < self.max_speed:
            self.acc += self.velocity.normalize_vector() * self.acc_speed  # 加上垂直速度

        super(Missile, self).update()  # 正常更新
        self.fuel -= 1
        if self.fuel <= 0 or self.health <= 0:
            self.delete()


class Player(object):

    def __init__(self, ip, weapon_group=None):
        """self.weapon_group = pygame.sprite.Group() in Class Game()"""
        self.ip = ip
        self.plane = None
        self.weapon_group = weapon_group
        self.fire_status = {1: True, 2: True, 3: True}
        self.win = True

    def add_plane(self, plane):
        self.plane = plane

    def update(self):
        self.plane.update()

    def weapon_fire(self, slot):
        # print 'Plane:', self.plane.velocity
        if self.plane.weapon[slot]:
            if self.plane.weapon[slot]['number'] > 0:
                self.plane.weapon[slot]['number'] -= 1
                # print dir(self.plane)
                tmp_rect = Map.mars_unti_translate((
                    self.plane.velocity.normalize_vector().x * self.plane.rect.height,
                    self.plane.velocity.normalize_vector().y * self.plane.rect.height))
                location_x = self.plane.location.x + tmp_rect[0]
                location_y = self.plane.location.y + tmp_rect[1]
                # print location_x,location_y, '<------------', self.plane.location, self.plane.rect
                weapon = Missile(catalog=self.plane.weapon[slot]['catalog'],
                                 location=(location_x, location_y),
                                 velocity=self.plane.velocity)
                self.weapon_group.add(weapon)

    def operation(self, key_list):
        for keys in key_list:
            if keys[pygame.K_a]:  # 直接使用 pygame.key.get_pressed() 可以多键同时独立识别
                self.plane.turn_left()
            if keys[pygame.K_d]:
                self.plane.turn_right()
            if keys[pygame.K_w]:
                self.plane.speedup()
            if keys[pygame.K_s]:
                self.plane.speeddown()

            if keys[pygame.K_1]:
                self.weapon_fire(1)
            if keys[pygame.K_2] and self.fire_status[2]:
                self.fire_status[2] = False
                self.weapon_fire(2)
            if keys[pygame.K_3] and self.fire_status[3]:
                self.fire_status[3] = False
                self.weapon_fire(3)

            if not keys[pygame.K_2]:
                self.fire_status[2] = True
            if not keys[pygame.K_3]:
                self.fire_status[3] = True


class Map(object):

    def __init__(self, size=MARS_MAP_SIZE):
        self.size = self.mars_translate(size)  # print size, self.size
        self.surface = pygame.Surface(self.size)
        self.surface.fill(BACKGROUND_COLOR)

    @staticmethod
    def mars_translate(coordinate):
        """translate Mars Coordinate to current Display Coordinate"""
        return [int(coordinate[i] / (float(MARS_SCREEN_SIZE[i]) / SCREEN_SIZE[i])) for i in [0, 1]]

    @staticmethod
    def mars_unti_translate(coordinate):
        return [int(coordinate[i] * (float(MARS_SCREEN_SIZE[i]) / SCREEN_SIZE[i])) for i in [0, 1]]

    def add_cloud(self, cloud_num=100):
        sprite_group = pygame.sprite.Group()
        for i in range(cloud_num):  # make 100 clouds randomly
            location = [randint(0, self.size[0]), randint(0, self.size[1])]
            cloud_image_path = CLOUD_IMAGE_LIST[randint(0, len(CLOUD_IMAGE_LIST)) - 1]  # print location , cloud_image
            cloud_image = pygame.image.load(cloud_image_path).convert_alpha()
            cloud = Base(location=location, image=cloud_image)
            sprite_group.add(cloud)
        sprite_group.draw(self.surface)

    @staticmethod
    def adjust_rect(rect, big_rect):
        """调节rect，不出big_rect的大框框"""
        if rect.left < big_rect.left:
            rect.left = big_rect.left
        if rect.top < big_rect.top:
            rect.top = big_rect.top
        if rect.right > big_rect.right:
            rect.right = big_rect.right
        if rect.bottom > big_rect.bottom:
            rect.bottom = big_rect.bottom


class MiniMap(object):

    def __init__(self, screen, map_rect, current_rect, plane_group):
        self.screen = screen
        self.screen_rect = self.screen.get_rect()
        left = 10
        width = self.screen_rect.width / 5
        height = self.screen_rect.height / 4
        top = self.screen_rect.height - 10 - height
        self.rect = pygame.Rect(left, top, width, height)

        self.current_rect = current_rect
        self.map_rect = map_rect
        self.mini_width = int(self.rect.width / (float(MARS_MAP_SIZE[0]) / MARS_SCREEN_SIZE[0]))
        self.mini_height = int(self.rect.height / (float(MARS_MAP_SIZE[1]) / MARS_SCREEN_SIZE[1]))
        self.mini_left = self.rect.left + int(
            self.rect.width * self.current_rect.left / float(self.map_rect.left + 1))
        self.mini_top = self.rect.top + int(self.rect.height * self.current_rect.top / float(self.map_rect.top + 1))
        self.mini_rect = pygame.Rect(self.mini_left, self.mini_top, self.mini_width, self.mini_height)

        self.unit_rect_list = []
        self.mini_plane_group = plane_group
        for plane in plane_group:
            self.unit_rect_list.append(plane.rect)

    def update(self):
        self.mini_left = self.rect.left + int(
            self.current_rect.left / float(self.map_rect.width) * self.rect.width)  # 当前比例*小图宽度
        self.mini_top = self.rect.top + int(
            self.current_rect.top / float(self.map_rect.height) * self.rect.height)  # 当前比例*小图高度
        self.mini_rect = pygame.Rect(self.mini_left, self.mini_top, self.mini_width, self.mini_height)

    def draw(self):
        pygame.draw.rect(self.screen, (0, 0, 0), self.rect, 1)  # Big Rect in MiniMap
        pygame.draw.rect(self.screen, (0, 225, 10), self.mini_rect, 1)  # Small(current display) Rect in MiniMap

        for rect in self.unit_rect_list:
            left = self.rect.left + int(rect.left / float(self.map_rect.width) * self.rect.width)
            top = self.rect.top + int(rect.top / float(self.map_rect.height) * self.rect.height)
            pygame.draw.rect(self.screen, (255, 0, 255), pygame.Rect(left, top, 2, 2), 4)


class Game(object):

    # def game_init(self, screen, ip):
    def game_init(self, localip, port):
        super(Game, self).__init__()
        logging.basicConfig(level=logging.DEBUG,  # CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
                            format='%(asctime)s %(filename)s[line:%(lineno)d] [%(levelname)s] %(message)s',
                            datefmt='%Y-%b-%d %H:%M:%S-%a',
                            filename='logger.log',
                            filemode='w')

        self.map = None
        self.minimap = None
        # self.current_rect = self.screen.get_rect()

        self.player_list = []
        self.other_ip = None
        self.d = {}

        # UDP server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        address = (localip, port)
        self.sock.bind(address)
        self.syn_frame = 0
        # MSG QUEUE
        self.q = Queue.Queue()
        # UDP listening
        thread1 = threading.Thread(target=self.msg_recv)
        thread1.setDaemon(True)  # True:不关注这个子线程，主线程跑完就结束整个python process
        thread1.start()

        # sprite group
        self.plane_group = pygame.sprite.Group()
        self.weapon_group = pygame.sprite.Group()

        # backup map
        self.origin_map = None

        # Info show
        self.info = Infomation()

    def screen_init(self):
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        pygame.mixer.init()  # 声音初始化
        pygame.display.set_mode(SCREEN_SIZE)  # pygame.display.set_mode(pygame.FULLSCREEN)
        # Return the size of the window or screen
        # pygame.display.get_window_size()
        self.screen = pygame.display.get_surface()  # 游戏窗口对象
        self.screen_rect = self.screen.get_rect()  # 游戏窗口对象的rect
        self.move_pixels = 20
        self.fps = FPS
        self.clock = pygame.time.Clock()
        self.done = False

    def msg_recv(self):
        while True:
            self.q.put(self.sock.recvfrom(4096))
            # print("socket get msg.")

    def add_player(self, player):
        self.player_list.append(player)
        self.plane_group.add(player.plane)

    def init_local_player(self, localip):
        if DEBUG_MODE:
            plane_type = PLANE_TYPE
        else:
            plane_type = raw_input("choose your plane catalog, 'J20' or 'F35':")
            while plane_type not in ['J20', 'F35']:
                plane_type = raw_input("spell fault, choose your plane catalog, 'J20' or 'F35':")

        msg_player = {'ip': localip,
                      'location': (randint(MARS_MAP_SIZE[0] / 5, MARS_MAP_SIZE[0] * 4 / 5),
                                   randint(MARS_MAP_SIZE[1] / 5, MARS_MAP_SIZE[1] * 4 / 5)),
                      'Plane': plane_type,
                      'Gun': 500,
                      'Rocket': 15,
                      'Cobra': 5,
                      }
        return msg_player

    def msg2player(self, msg_player):
        player = Player(weapon_group=self.weapon_group, ip=msg_player['ip'])
        plane = Plane(catalog=msg_player['Plane'], location=msg_player['location'])
        plane.load_weapon(catalog='Cobra', number=msg_player['Cobra'])
        plane.load_weapon(catalog='Gun', number=msg_player['Gun'])
        plane.load_weapon(catalog='Rocket', number=msg_player['Rocket'])
        player.add_plane(plane)
        return player

    def create_or_join(self):
        if raw_input('Input "c" to create game, else "j" to join a game:') == 'c':
            return True
        else:
            return False

    def create(self, localip, msg_player):
        print('Game is created. Host IP: %s' % localip)
        print('waiting players to entering.'),
        n = 0
        while self.q.empty():
            n += 1
            print('.'),
            if n % 45 == 0:
                print
            pygame.time.wait(500)

        data, address = self.q.get()  # 0.0 join get
        if json.loads(data) == 'join':
            self.sock_send('join_ack', address)  # 1.0 join_ack send
            tmp = self.sock_waitfor('msg_player', address)  # 2.1 msg_player get
            if tmp:
                self.d[address[0]] = tmp
                # self.add_player(self.msg2player(tmp))
                self.sock_send(msg_player, address)  # 3.0
                self.sock_send('msg_player_ack', address)  # 4.0
                if self.sock_waitfor('msg_player_ack', address) == 'msg_player_ack':  # 5.1
                    self.other_ip = address[0]
                    return True
        return False

    def join(self, port, msg_player):
        host_ip = raw_input('Input a host ip to join a game:')
        address = (host_ip, port)
        self.sock_send('join', address)  # 0.1 join send
        if self.sock_waitfor('join_ack', address) == 'join_ack':  # 1.1 join_ack get
            self.sock_send(msg_player, address)  # 2.0 msg_player send
            tmp = self.sock_waitfor('msg_player', address)  # 3.1
            if tmp:
                self.d[address[0]] = tmp
                self.sock_send('msg_player_ack', address)  # 5.0
                if self.sock_waitfor('msg_player_ack', address) == 'msg_player_ack':  # 4.1
                    self.other_ip = address[0]
                    return True
        return False

    def render(self, screen_rect):
        self.current_rect = screen_rect
        self.screen.blit(source=self.map.surface, dest=(0, 0), area=self.current_rect)
        self.minimap.draw()
        self.info.show(self.screen)

    def player_communicate(self, event_list):
        """
        在World类里面实现，TCP/IP的事件信息交互，Player类只做事件的update()
        """
        str_event_list = json.dumps((event_list, self.syn_frame))  # # 如果没操作队列: event_list = key_list = []
        self.syn_frame += 1
        for player in self.player_list:  # 发送给每一个网卡，包括自己
            # print player.ip
            try:
                logging.info('Send---> %s, %s' % (str((player.ip, 8989)),str_event_list))
                self.sock.sendto(str_event_list, (player.ip, 8989))
                # self.sock.sendto(str_event_list, (player.ip, 8989))  # 发双份
            except Exception, msg:
                logging.warn('Offline(Socket Error):' + str(msg))

    def deal_collide(self):
        """
        self.plane_group = pygame.sprite.Group()
        self.weapon_group = pygame.sprite.Group()
        """
        for weapon in self.weapon_group:  # 遍历每一个武器
            # 如果不是枪弹就进行相互碰撞测试
            if weapon.catalog != 'Gun':
                # print weapon
                weapon_collide_lst = pygame.sprite.spritecollide(weapon, self.weapon_group, False)  # False代表不直接kill该对象
                weapon.hitted(weapon_collide_lst)  # 发生碰撞相互减血
                # for hitted_weapon in weapon_collide_lst:
                #     hitted_weapon.hitted([weapon])  # 本身受到攻击的对象
            # 检测武器与飞机之间的碰撞        
            plane_collide_lst = pygame.sprite.spritecollide(weapon, self.plane_group, False)
            weapon.hitted(plane_collide_lst)  # 发生碰撞相互减血

    def process(self, event_list):
        """[WARNING]每个玩家（world）接收自己的消息队列，刷新自己的界面，没有消息同步机制，也没有同步下发机制，
        会导致不同玩家画面不一致情况（尤其在网络延迟大的情况下）"""
        # 发送同步帧(上来就发送)
        self.player_communicate(event_list)

        self.minimap.update()
        self.weapon_group.update(self.plane_group)
        # self.plane_group.clear(self.map.surface, )
        # self.map.surface = self.origin_map_surface.copy()  # [WARNING]很吃性能！！！！！极有可能pygame.display()渲染不吃时间，这个copy（）很吃时间
        self.plane_group.draw(self.map.surface)
        self.weapon_group.draw(self.map.surface)
        for i in self.weapon_group:
            if i.target:
                # print i.target
                pygame.draw.rect(self.map.surface, (255, 0, 0), i.target.rect, 1)

        # 碰撞处理
        self.deal_collide()

        for player in self.player_list:
            if player.win:
                player.update()
                if not player.plane.alive:  # delete没了的的飞机
                    player.plane = None
                    player.win = False  # End Game
                    # return True

        for py in self.player_list:
            self.info.add(u'Player IP:%s' % py.ip)
            if py.plane:
                self.info.add(u'Health:%d' % py.plane.health)
                self.info.add(u'Weapon:%s' % str(py.plane.weapon))
                self.info.add(u'speed:%s,  location:%s,  rect:%s' % (
                    str(py.plane.velocity), str(py.plane.location), str(py.plane.rect)))
            self.info.add(u'Groups:%s' % str(self.plane_group))

        # 收到消息进行操作（最后处理动作，留给消息接收）

        msg_num = 0
        # get_msg_dir = {ip:False for ip in self.player_list.ip}
        while True:
            resend_time = 0
            while self.q.empty():
                resend_time += 1
                pygame.time.wait(1)  # 等待1ms
                if resend_time > 200:
                    msg_num += 1
                    print('[ERROR]MSG LOST: %d'%self.syn_frame)
                    break
                    # for ip in get_msg_dir.keys()
                    #     if not get_msg_dir[ip]:
                    #         self.sock_send('package lost',(get_msg_dir[ip], 8989))
            data, address = self.q.get()
            data_tmp = json.loads(data)[0]  # [key_lists, frame_number]
            for player in self.player_list:  # 遍历玩家，看这个收到的数据是谁的
                if player.ip == address[0] and player.win:
                    # get_msg_dir[player.ip] = Ture
                    msg_num += 1
                    if not data_tmp:
                        logging.info("Get ----> %s, %s" % (str(address), str(data_tmp)))
                    else:
                        player.operation(data_tmp)  # data is list of pygame.key.get_pressed() of json.dumps
                        logging.info("Get ----> %s, %s" % (str(address), str(data_tmp)))
                    break  # 一个数据只有可能对应一个玩家的操作，有一个玩家取完消息就可以了

            if msg_num >= len(self.player_list):  # 一共有两个玩家发送的消息要接受，否则卡死等待
                break

    def erase(self):
        # self.weapon_group.clear(self.map.surface, self.clear_callback)
        # self.plane_group.clear(self.map.surface, self.clear_callback)
        pass

    def clear_callback(self, surf, rect):
        # surf.blit(source=self.map.surface, dest=(0, 0), area=self.current_rect)
        # self.screen.blit(source=self.map.surface, dest=(0, 0), area=self.current_rect)
        surf.blit(source=self.origin_map_surface, dest=rect, area=rect)  # blit(source, dest, area=None, special_flags=0) -> Rect

    def event_control(self):
        """
        :return: 返回空列表，或者一个元素为keys的列表
        """
        event_list = pygame.event.get()
        key_list = []
        for event in event_list:
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()  # key is queue too
                # print '    KEY:', keys
                # if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
                if keys[pygame.K_ESCAPE]:
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
                key_list.append(keys)
        return key_list

    def get_local_ip(self):
        l = socket.getaddrinfo(socket.gethostname(), None)
        for index, i in enumerate(l):
            print index, i[-1][0]
        if DEBUG_MODE:
            localip = LOCALIP
        else:
            localip = l[input("select your own ip index:")][-1][0]
        return localip

    def sock_send(self, strs, dest):
        """strs: unicode string or dict object"""
        self.sock.sendto(json.dumps(strs), dest)
        print('SEND:%s'%json.dumps(strs))

    def sock_waitfor(self, msg, dest, delay=100, waiting_times=30):
        count = 0
        while self.q.empty():
            pygame.time.wait(delay)
            count += 1
            if count > waiting_times:
                print('[ERROR]Sock Waiting Timeout: %s' % msg)
                return False
        data, address = self.q.get()
        print('GET:%s'%str(json.loads(data)))
        if address[0] == dest[0]:
            print('[INFO]Sock Msg Get:%s' % json.loads(data))
            return json.loads(data)
        else:
            print('[ERROR]Sock Wrong Msg:%s %s' % (str(address), json.loads(data)))
            return False

    def main(self):
        localip = self.get_local_ip()
        msg_player = self.init_local_player(localip)  # !!需要修改这个msg_player,json好发送

        # self.sock & self.q is ready.
        sock_port = 8989
        self.game_init(localip, sock_port)
        self.d[localip] = msg_player

        if self.create_or_join():
            if not self.create(localip, msg_player):
                print('waiting join failed!')
                return False
        else:
            if not self.join(sock_port, msg_player):
                print('join failed!')
                return False

        # Pygame screen init
        self.screen_init()
        for ip in self.d.keys():
            self.add_player(self.msg2player(self.d[ip]))

        # MAP
        self.map = Map()  # 8000*4500--->screen, (8000*5)*(4500*5)---->map
        self.map.add_cloud()
        self.minimap = MiniMap(self.screen, self.map.surface.get_rect(), self.screen_rect, self.plane_group)
        self.origin_map_surface = self.map.surface.copy()

        # 根据local player位置移动一次self.screen_rect git
        self.screen_rect.center = Map.mars_translate(msg_player['location'])

        # 同步开始循环
        self.sock_send('200 OK', (self.other_ip, sock_port))
        self.sock_waitfor('200 OK', (self.other_ip, sock_port))

        # PYGAME LOOP
        pygame.key.set_repeat(10, 10)  # control how held keys are repeated
        while not self.done:
            event_list = self.event_control()
            self.process(event_list)
            Map.adjust_rect(self.screen_rect, self.map.surface.get_rect())
            # Map.adjust_rect()
            self.render(self.screen_rect)

            pygame.display.flip()
            self.clock.tick(self.fps)
            self.erase()

        self.sock.close()
        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.main()
