# -*- coding: cp936 -*-
import pygame
import math
import os
from random import randint,choice
import socket
import threading
import Queue
import json
import logging
from infomation import Infomation

"""
ok随机弹药包, 补血包,还需要同步才行，要不然每个玩家得到的Box不一样
飞机受伤烟雾，随机产生在飞机身上
开始菜单、游戏操作说明、restart game
13.209.137.170
被导弹跟踪了之后的滴滴滴声音
ok转弯+加速不能同时使用
ok飞机爆炸之后要可以继续游戏，显示win lose ， press esc to exit
ok空格键回到飞机位置
ok爆炸效果（目前只制作了F35和J20飞机的效果）
"""
SINGLE_TEST = True
MAP_RATIO = 5
RESTART_MODE = False
LOCALIP = '192.168.0.107'
HOSTIP = '192.168.0.103'
PLANE_TYPE = 'J20'
C_OR_J = ''


SPEED_RATIO = 0.25

PINK = (255,228,225)
DARK_GREEN = (49,79,79)
GRAY =  (168,168,168)
BACKGROUND_COLOR = DARK_GREEN
WHITE = (255, 255, 255)
FPS = 50
SCREEN_SIZE = (1300, 800)
MARS_SCREEN_SIZE = (8000, 4500)
MARS_MAP_SIZE = (8000 * MAP_RATIO, 4500 * MAP_RATIO)  # topleft starts: width, height
CLOUD_IMAGE_LIST = ['./image/cloud1.png', './image/cloud2.png', './image/cloud3.png', './image/cloud4.png']

BOX_CATALOG = {
    'Medic':{
        'image': './image/box_medic.png',
        'health': 80,
    },
    # 'Power':{
    #     'image': './image/box_power.png',
    # },
    'Gunfire_num':{
        'image': './image/box_gunfire_num.png',
        'num': 100,
    },
    'Rocket_num': {
        'image': './image/box_rocket_num.png',
        'num': 5,
    },
    'Cobra_num': {
        'image': './image/box_cobra_num.png',
        'num': 3,
    },
}

TAIL_CATALOG = {
    'Point': {
        'image': './image/point.png',
        'init_time': -5,
        'life': 250,
    },
}

PLANE_CATALOG = {
    'J20': {
        'health': 200,
        'max_speed': 3000,
        'min_speed': 540,
        'acc_speed': 60,
        'turn_acc': 35,  # 20
        'image': './image/plane_red.png',
        'damage': 100,
    },
    'F35': {
        'health': 200,
        'max_speed': 2400,
        'min_speed': 540,
        'acc_speed': 50,
        'turn_acc': 25,
        'image': './image/plane_blue.png',
        'damage': 100,
    },
    'PDH': {
        'health': 300,
        'max_speed': 2400,
        'min_speed': 540,
        'acc_speed': 50,
        'turn_acc': 25,
        'image': './image/airplane.png',
        'damage': 100,
    },
    'PPDH': {
        'health': 500,
        'max_speed': 2400,
        'min_speed': 540,
        'acc_speed': 50,
        'turn_acc': 25,
        'image': './image/airplane1.png',
        'damage': 100,
    },
}

WEAPON_CATALOG = {
    'Gun': {
        'health': 10,
        'init_speed': 5000,
        'max_speed': 2500,
        'acc_speed': 0,
        'turn_acc': 0,
        'damage': 2,
        'image': ['./image/gunfire1.png', './image/gunfire2.png', './image/gunfire3.png',
                  './image/gunfire4.png', './image/gunfire5.png', './image/gunfire6.png'],
        'fuel': 8,
        'sound_collide_plane': ['./sound/bulletLtoR08.wav', './sound/bulletLtoR09.wav', './sound/bulletLtoR10.wav',
                                './sound/bulletLtoR11.wav', './sound/bulletLtoR13.wav', './sound/bulletLtoR14.wav']
    },
    'Rocket': {
        'health': 10,
        'init_speed': 0,
        'max_speed': 8000,
        'acc_speed': 65,
        'damage': 35,
        'turn_acc': 0,
        'image': './image/homingmissile.png',
        'fuel': 20,
    },
    'Cobra': {
        'health': 10,
        'init_speed': 0,
        'max_speed': 4500, # 1360
        'acc_speed': 25,
        'turn_acc': 35,
        'damage': 25,
        'image': './image/homingmissile2.png',
        'fuel': 16,
        'dectect_range': 10000 * 30
    },
    'Pili': {
        # ...,
    }
}


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

    def __len__(self):
        return 2

    def __getitem__(self, item):
        if item == 0:
            return self.x
        if item == 1:
            return self.y

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
        self.rect.center = Map.mars_translate((self.location.x, self.location.y))  # !!!!!!!!!!这个坐标需要转换，这里需要重新设计

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
        self.destruct_image_index = 0  # 爆炸图片不在这个里面，未设计To be continue
        self.self_destruction = 0

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
        if self.alive:  # 第一次进行的操作
            # self.kill()  # remove the Sprite from all Groups
            self.alive = False
            if self.sound_kill:
                self.sound_kill.play()

        # 启动自爆动画
        self.self_destruction += 0.2
        # print self.self_destruction
        if self.self_destruction < self.destruct_image_index:
            # print [self.self_destruction//2*40, 0, 39, 39],self.self_destruction,self.image.get_rect()
            self.origin_image = self.image = self.image_original.subsurface([self.self_destruction // 2 * 40, 0, 39, 39])
            self.image.set_colorkey(WHITE)
            self.rotate()
            return False
        else:
            self.kill()
            return True

    def hitted(self, base_lst):
        for base in base_lst:
            if id(self) == id(base):  # spritecollide如果是自己和自己就不需要碰撞了
                continue
            # print base.rect, self.rect
            self.health -= base.damage
            base.health -= self.damage
            if self.catalog == 'Gun' and isinstance(base, Plane):
                self.sound_collide_plane.play()
            if self.catalog in ['Rocket', 'Cobra']:
                self.sound_collide_plane.play()

class Box(Base):
    def __init__(self, location, catalog):
        image_path = BOX_CATALOG[catalog]['image']
        self.image = pygame.image.load(image_path).convert()
        self.image.set_colorkey(WHITE)
        super(Box,self).__init__(location=location, image=self.image)

        self.sound_kill = pygame.mixer.Sound("./sound/beep.wav")
        self.catalog = catalog
        if catalog == 'Medic':
            self.health = BOX_CATALOG[catalog]['health']
        elif catalog == 'Power':
            pass
        elif catalog in ['Gunfire_num','Rocket_num','Cobra_num']:
            self.num = BOX_CATALOG[catalog]['num']

    def effect(self, plane_object):
        if self.catalog == 'Medic':
            plane_object.change_health(self.health)
        # elif catalog == 'Power':  # 这个后面再做威力加强，武器是发射时，加载在飞机的weapon_group上
        #     pass
        elif self.catalog =='Gunfire_num':
            plane_object.change_weapon('Gun', self.num)
        elif self.catalog =='Rocket_num':
            plane_object.change_weapon('Rocket', self.num)
        elif self.catalog == 'Cobra_num':
            plane_object.change_weapon('Cobra', self.num)

class Tail(Base):
    def __init__(self, location, catalog='Point'):
        image_path = TAIL_CATALOG[catalog]['image']
        self.image = pygame.image.load(image_path).convert()
        self.image.set_colorkey(WHITE)
        super(Tail, self).__init__(location=location, image=self.image)
        self.live_time = TAIL_CATALOG[catalog]['init_time']
        self.life = TAIL_CATALOG[catalog]['life']
        # print self.location

    def update(self):
        self.live_time += 1
        # print self.live_time,self.life
        if self.live_time > self.life:
            self.delete()

class Plane(Base):

    def __init__(self, location, catalog='J20'):
        image_path = PLANE_CATALOG[catalog]['image']
        self.sound_kill = pygame.mixer.Sound("./sound/explode3.wav")
        if catalog in ['J20', 'F35']:  # 非透明图
            self.image_original = pygame.image.load(image_path).convert()
            self.image = self.image_original.subsurface((0, 0, 39, 39))
            self.image.set_colorkey(WHITE)
        else:
            self.image = pygame.image.load(image_path).convert_alpha()  # 透明色的搞法
        super(Plane, self).__init__(location=location, image=self.image)

        self.max_speed = PLANE_CATALOG[catalog]['max_speed']
        self.min_speed = PLANE_CATALOG[catalog]['min_speed']
        self.turn_acc = PLANE_CATALOG[catalog]['turn_acc']
        self.acc_speed = PLANE_CATALOG[catalog]['acc_speed']
        self.damage = PLANE_CATALOG[catalog]['damage']
        self.health = PLANE_CATALOG[catalog]['health']

        self.speed = (self.max_speed + self.min_speed) / 2  # 初速度为一半
        self.velocity = Vector(randint(-100,100), randint(-100,100)).normalize_vector() * self.speed  # Vector
        self.acc = Vector(0, 0)

        self.weapon = {1: {}, 2: {}, 3: {}}  # 默认没有武器

        self.sound_kill = pygame.mixer.Sound("./sound/explode3.wav")
        self.destruct_image_index = self.image_original.get_width() / self.image_original.get_height()
        # self.catalog = catalog


    def turn_left(self):
        self.acc += self.velocity.vertical_left() * self.turn_acc

    def turn_right(self):
        self.acc += self.velocity.vertical_right() * self.turn_acc

    def speedup(self):
        acc_tmp = self.acc + self.velocity.normalize_vector() * self.acc_speed
        if (self.velocity + acc_tmp).length() < self.max_speed:
            self.acc = acc_tmp

    def speeddown(self):
        acc_tmp = self.acc - self.velocity.normalize_vector() * self.acc_speed
        if (self.velocity - acc_tmp).length() > self.min_speed:
            self.acc = acc_tmp

    def change_health(self, num):
        self.health += num

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

    def change_weapon(self, catalog, number):
        if catalog == 'Gun':
            self.weapon[1]['number'] += number
        elif catalog == 'Rocket':
            self.weapon[2]['number'] += number
        elif catalog == 'Cobra':
            self.weapon[3]['number'] += number

    def update(self):
        if not self.alive:  # 如果挂了,就启动自爆动画
            super(Plane, self).update()
            return self.delete()

        super(Plane, self).update()
        # self.health -= 50
        if self.health <= 0 :
            return  self.delete()


class Weapon(Base):
    def __init__(self, catalog, location, velocity):
        if catalog == 'Gun':
            image_path = WEAPON_CATALOG['Gun']['image'][randint(0, len(WEAPON_CATALOG['Gun']['image']) - 1)]
            self.image_original = pygame.image.load(image_path).convert()
            self.image_original.set_colorkey(WHITE)
            super(Weapon, self).__init__(location=location, image=self.image_original)
            self.sound_fire = pygame.mixer.Sound("./sound/minigun_fire.wav")
            self.sound_fire.play(maxtime=200)
            self.sound_collide_plane = pygame.mixer.Sound(WEAPON_CATALOG['Gun']['sound_collide_plane'][randint(0, len(
                WEAPON_CATALOG['Gun']['sound_collide_plane']) - 1)])
        else:
            image_path = WEAPON_CATALOG[catalog]['image']
            self.image_original = pygame.image.load(image_path).convert()
            self.image_original.set_colorkey(WHITE)
            super(Weapon, self).__init__(location=location, image=self.image_original)
            self.sound_fire = pygame.mixer.Sound("./sound/TPhFi201.wav")
            self.sound_fire.play()
            self.sound_kill = pygame.mixer.Sound("./sound/ric5.wav")
            self.sound_collide_plane = pygame.mixer.Sound("./sound/shotgun_fire_1.wav")
        if catalog == 'Cobra':
            self.detect_range = WEAPON_CATALOG[catalog]['dectect_range']

        self.health = WEAPON_CATALOG[catalog]['health']
        self.damage = WEAPON_CATALOG[catalog]['damage']
        self.init_speed = WEAPON_CATALOG[catalog]['init_speed']
        self.max_speed = WEAPON_CATALOG[catalog]['max_speed']
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
            if self.target and abs(self.velocity.angle() - (self.target.location - self.location).angle()) < math.pi / 3 \
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
        # print self.min_speed, self.velocity.length(), self.max_speed
        if self.min_speed < self.velocity.length() < self.max_speed:
            self.acc += self.velocity.normalize_vector() * self.acc_speed  # 加上垂直速度

        super(Weapon, self).update()  # 正常更新
        self.fuel -= 1
        if self.fuel <= 0 or self.health <= 0:
            self.delete()


class Player(object):

    def __init__(self, ip, weapon_group=None):
        """self.weapon_group = pygame.sprite.Group() in Class Game()"""
        self.ip = ip
        self.plane = None
        self.weapon_group = weapon_group
        self.fire_status = {1: 0, 2: 0, 3: 0}
        self.win = True

    def add_plane(self, plane):
        self.plane = plane

    def update(self):
        return self.plane.update()

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
                weapon = Weapon(catalog=self.plane.weapon[slot]['catalog'],
                                 location=(location_x, location_y),
                                 velocity=self.plane.velocity)
                self.weapon_group.add(weapon)

    def operation(self, key_list, syn_frame):
        # print key_list
        for key in key_list:
            if key == 'a':
                self.plane.turn_left()
            elif key == 'd':
                self.plane.turn_right()
            elif key == 'w':
                self.plane.speedup()
            elif key == 's':
                self.plane.speeddown()

            elif key == '1':
                self.weapon_fire(1)
            elif key == '2' and syn_frame-self.fire_status[2]>FPS:
                self.fire_status[2] = syn_frame
                self.weapon_fire(2)
            elif key == '3' and syn_frame-self.fire_status[3]>FPS:
                self.fire_status[3] = syn_frame
                self.weapon_fire(3)

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
            location = [randint(0, MARS_MAP_SIZE[0]), randint(0, MARS_MAP_SIZE[1])]
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

    def __init__(self):
        self.local_ip = None
        self.other_ip = None
        self.sock = None
        self.port = 8989

        self.re_local_ip = LOCALIP
        self.re_msg_player = None
        self.re_c_or_j = C_OR_J
        self.re_host_ip = HOSTIP

        self.local_player = None
        self.num_player = 0

    def game_init(self, localip):
        logging.basicConfig(level=logging.DEBUG,  # CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
                            format='%(asctime)s [line:%(lineno)d] [%(levelname)s] %(message)s',
                            datefmt='%Y-%b-%d %H:%M:%S-%a',
                            filename='logger.log',
                            filemode='w')

        self.done = False
        self.map = None
        self.minimap = None
        # self.current_rect = self.screen.get_rect()

        self.player_list = []
        self.d = {}

        # UDP server
        address = (localip, self.port)
        if self.sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(address)
        else:
            pygame.time.wait(1200)
            while not self.q.empty():
                self.q.get()

        self.syn_frame = -1
        # MSG QUEUE
        self.q = Queue.Queue()
        # UDP listening
        self.thread1 = threading.Thread(target=self.msg_recv)
        self.thread1.setDaemon(True)  # True:不关注这个子线程，主线程跑完就结束整个python process
        self.thread1.start()

        # sprite group
        self.plane_group = pygame.sprite.Group()
        self.weapon_group = pygame.sprite.Group()
        self.tail_group = pygame.sprite.Group()
        self.box_group = pygame.sprite.Group()

        # backup map
        self.origin_map = None

        # Info show
        self.info = Infomation()

    def screen_init(self):
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        pygame.mixer.init()  # 声音初始化
        pygame.display.init()  # 初始化
        display_info = pygame.display.Info()
        screen_size_fittable = (display_info.current_w*19/20, display_info.current_h*17/20)
        if screen_size_fittable[0]*screen_size_fittable[1]>0:
            pygame.display.set_mode(screen_size_fittable)
        else:
            pygame.display.set_mode(SCREEN_SIZE)  # pygame.display.set_mode(pygame.FULLSCREEN)
        # Return the size of the window or screen
        # pygame.display.get_window_size()
        self.screen = pygame.display.get_surface()  # 游戏窗口对象
        self.screen_rect = self.screen.get_rect()  # 游戏窗口对象的rect
        self.move_pixels = 20
        self.fps = FPS
        self.clock = pygame.time.Clock()

    def msg_recv(self):
        while not self.done:
            self.q.put(self.sock.recvfrom(1487))
            # print("socket get msg.")

    def add_player(self, player):
        self.player_list.append(player)
        self.plane_group.add(player.plane)
        self.num_player += 1

    def init_local_player(self, localip, plane_type):
        msg_player = {'ip': localip,
                      'location': (randint(MARS_MAP_SIZE[0] / 5, MARS_MAP_SIZE[0] * 4 / 5),
                                   randint(MARS_MAP_SIZE[1] / 5, MARS_MAP_SIZE[1] * 4 / 5)),
                      'Plane': plane_type,
                      'Gun': 200,
                      'Rocket': 10,
                      'Cobra': 3,
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
        if RESTART_MODE:
            if self.re_c_or_j == 'c':
                return True
            else:
                return False
        if raw_input('Input "c" to create game, else "j" to join a game:') == 'c':
            self.re_c_or_j = 'c'
            return True
        else:
            self.re_c_or_j = 'j'
            return False

    def create(self, localip, msg_player):
        print('Game is created. Host IP: %s:%d' % (localip, self.port))
        print('waiting players to entering.'),
        n = 0
        while self.q.empty():
            n += 1
            print('.'),
            if n % 45 == 0:
                print
            pygame.time.wait(500)

        data, address = self.q.get()  # 0.0 join get
        print 'Create:GET_INFO:%s %s'%(str(data),str(address))
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

    def join(self, msg_player, host_ip):
        address = (host_ip, self.port)
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
        self.info.show_end(self.screen)

    def player_communicate(self, key_list):
        """
        在World类里面实现，TCP/IP的事件信息交互，Player类只做事件的update()
        发送本地玩家的操作
        """
        if not self.local_player.win:
            return
        str_key_list = json.dumps((self.syn_frame, key_list))  # # 如果没操作队列: event_list = key_list = []
        for player in self.player_list:  # 发送给每一个网卡，包括自己
            # print player.ip
            try:
                logging.info('Send %d---> %s, %s' % (self.syn_frame, str((player.ip, self.port)), str_key_list))
                self.sock.sendto(str_key_list, (player.ip, self.port))
                # self.sock.sendto(str_event_list, (player.ip, self.port))  # 发双份
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

    def deal_collide_with_box(self):
        for plane in self.plane_group:  # 进行飞机与Box之间碰撞探测
            box_collide_lst = pygame.sprite.spritecollide(plane, self.box_group, False)
            for box in box_collide_lst:
                box.effect(plane)
                box.delete()

    def syn_status(self):
        if self.syn_frame % (2 * FPS) == 0:  # 每2秒同步一次自己状态给对方
            # print self.player_list, self.local_ip, self.other_ip
            for player in self.player_list:
                if player.ip == self.local_ip and player.win:
                    status_msg = ('syn_player_status', {'location': (player.plane.location.x, player.plane.location.y),
                                                        'velocity': (player.plane.velocity.x, player.plane.velocity.y),
                                                        'health': player.plane.health})
                    self.sock_send(status_msg, (self.other_ip, self.port))

    def add_tail(self, weapon_group):
        for weapon in weapon_group:
            if weapon.catalog == 'Rocket' or weapon.catalog == 'Cobra':
                self.tail_group.add(Tail((weapon.location.x,weapon.location.y)))

    def erase(self):
        self.weapon_group.clear(self.map.surface, self.clear_callback)
        self.plane_group.clear(self.map.surface, self.clear_callback)
        self.tail_group.clear(self.map.surface, self.clear_callback)
        self.box_group.clear(self.map.surface, self.clear_callback)

    def clear_callback(self, surf, rect):
        # surf.blit(source=self.map.surface, dest=(0, 0), area=self.current_rect)
        # self.screen.blit(source=self.map.surface, dest=(0, 0), area=self.current_rect)
        surf.blit(source=self.origin_map_surface, dest=rect,
                  area=rect)  # blit(source, dest, area=None, special_flags=0) -> Rect

    def event_control(self):
        """
        :return: 返回空列表，或者一个元素为keys的列表
        """
        event_list = pygame.event.get()  # 一定要把操作get()出来
        key_list = ''
        # n_break = 0
        if pygame.key.get_focused():
            keys = pygame.key.get_pressed()  # key is queue too
            # print '    KEY:', keys
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
            if keys[pygame.K_SPACE]:
                if self.local_player.plane:
                    self.screen_rect.center = Map.mars_translate(self.local_player.plane.location)

            for keyascii in [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_1, pygame.K_2, pygame.K_3]:
                if keys[keyascii]:
                    key_list += chr(keyascii)

            # n_break += 1
            # if n_break > 3:
            #     break

        return key_list

    def get_local_ip(self):
        l = socket.getaddrinfo(socket.gethostname(), None)
        for index, i in enumerate(l):
            print index, i[-1][0]
        if RESTART_MODE:
            localip = self.re_local_ip
        else:
            localip = l[input("select your own ip index:")][-1][0]
            self.re_local_ip = localip  # for repeat
        self.local_ip = localip
        return localip

    def sock_send(self, msg, dest):
        """strs: unicode string or dict object"""
        self.sock.sendto(json.dumps(msg), dest)
        # print('SEND [%s]:%s' % (str(dest), json.dumps(msg)))

    def sock_waitfor(self, msg, dest, delay=100, waiting_times=30):
        count = 0
        while self.q.empty():
            pygame.time.wait(delay)
            count += 1
            if count > waiting_times:
                print('[ERROR]Sock Waiting Timeout: %s' % msg)
                return False
        data, address = self.q.get()
        print('GET:%s' % str(json.loads(data)))
        if address[0] == dest[0]:
            print('[INFO]Sock Msg Get:%s' % json.loads(data))
            return json.loads(data)
        else:
            print('[ERROR]Sock Wrong Msg:%s %s' % (str(address), json.loads(data)))
            return False

    def box_msg_send(self):
        if self.syn_frame % (1 * FPS) == 0:  # 每n秒同步一次自己状态给对方
            location = [randint(0, MARS_MAP_SIZE[0]), randint(0, MARS_MAP_SIZE[1])]
            status_msg = ('box_status', {'location': location, 'catalog': choice(BOX_CATALOG.keys())})
            for player in self.player_list:
                self.sock_send(status_msg, (player.ip, self.port))

    def process(self, event_list):
        """
        每个玩家接收自己的消息队列，刷新自己的界面；
        不管延迟和丢包的问题，接受操作消息等待为resend_time=30ms；
        每过2帧进行一次状态同步：只将本地玩家飞机状态发送给其他玩家；
        """
        self.syn_frame += 1  # 发送同步帧(上来就发送)

        # 产生随机奖励Box，并发送
        self.box_msg_send()

        # 状态同步, 先状态同步，再发送操作消息
        self.syn_status()

        # 发送普通键盘操作消息
        self.player_communicate(event_list)

        # 进行游戏对象参数计算&渲染
        self.minimap.update()
        self.weapon_group.update(self.plane_group)
        self.tail_group.update()  # update尾焰
        # self.map.surface = self.origin_map_surface.copy()  # [WARNING]很吃性能！！！！！极有可能pygame.display()渲染不吃时间，这个copy（）很吃时间
        if self.syn_frame % 5 == 0:  # 添加尾焰轨迹
            self.add_tail(self.weapon_group)
        self.box_group.draw(self.map.surface)  # draw随机Box
        self.tail_group.draw(self.map.surface)  # draw尾焰
        self.plane_group.draw(self.map.surface)  # draw飞机
        self.weapon_group.draw(self.map.surface)  # draw武器
        for i in self.weapon_group:
            if i.target:
                # print i.target
                pygame.draw.rect(self.map.surface, (255, 0, 0), i.target.rect, 1)

        # 碰撞处理
        self.deal_collide()
        self.deal_collide_with_box()

        # 判断游戏是否结束
        for player in self.player_list:
            if player.win:
                if player.update():  # 更新玩家状态,player.update()-->plane.update()-->plane.delete(),delete没了的的飞机
                    player.plane = None  # player.update()为True说明飞机已经delete了
                    player.win = False  # End Game
                    self.num_player -= 1
                    logging.info("Player lost: %s" % player.ip)
                    print("Player lost: %s" % player.ip)
                    # return True

        # 显示游戏信息
        for py in self.player_list:
            self.info.add(u'Player IP:%s' % py.ip)
            if py.plane:
                self.info.add(u'Health:%d' % py.plane.health)
                self.info.add(u'Weapon:%s' % str(py.plane.weapon))
                self.info.add(u'Tail:%s'%self.tail_group)
                # self.info.add(u'speed:%s,  location:%s,  rect:%s' % (
                #     str(py.plane.velocity), str(py.plane.location), str(py.plane.rect)))
            # self.info.add(u'Groups:%s' % str(self.plane_group))

        if not self.local_player.win: # 本地玩家
            self.info.add_middle('YOU LOST.')
            self.info.add_middle_below('press "ESC" to exit the game.')
            self.info.add_middle_below('press "r" to restart.')
        elif self.num_player == 1: # 只剩你一个人了
            self.info.add_middle('YOU WIN!')
            self.info.add_middle_below('press "ESC" to exit the game.')
            self.info.add_middle_below('press "r" to restart.')

        # 收到消息进行操作（最后处理动作，留给消息接收）
        self.get_deal_msg()

    def get_deal_msg(self):
        msg_num = 0
        # get_msg_dir = {ip:False for ip in self.player_list.ip}
        while True:
            if msg_num >= self.num_player:  # 一共有两个玩家发送的消息要接受，否则卡死等待
                break
            resend_time = 0
            while self.q.empty():
                resend_time += 1
                pygame.time.wait(1)
                if resend_time >= 25:  # 等待ms
                    msg_num += 1  # 超时++++++++++1
                    if not self.done:
                        print('[ERROR]MSG LOST: %d' % self.syn_frame)
                    break
                    # for ip in get_msg_dir.keys()
                    #     if not get_msg_dir[ip]:
                    #         self.sock_send('package lost',(get_msg_dir[ip], self.port))

            if self.q.empty():  # 空就不进行读取处理
                continue
            data, address = self.q.get()
            data_tmp = json.loads(data)  # [frame_number, key_list], ['syn_player_status', dict]，['box_status', dict]
            # if len(str(data_tmp)) > 15:
            #     print type(data_tmp), '===', data_tmp, '---', data_tmp[0]
            if isinstance(data_tmp[0], int):
                for player in self.player_list:  # 遍历玩家，看这个收到的数据是谁的
                    if player.ip == address[0] and player.win:
                        # get_msg_dir[player.ip] = Ture
                        if data_tmp[0] >= self.syn_frame:
                            msg_num += 1  # 获取到有效消息++++++++++1
                        if data_tmp[1]:  # 消息-->操作
                            player.operation(data_tmp[1],
                                             self.syn_frame)  # data is list of pygame.key.get_pressed() of json.dumps
                        logging.info("Get, other_frame:%d----> %s, %s" % (data_tmp[0], str(address), str(data_tmp)))
                        break  # 一个数据只有可能对应一个玩家的操作，有一个玩家取完消息就可以了
            elif data_tmp[0] == 'syn_player_status':  # 状态同步-->对象
                # print 'in status.....', address
                for player in self.player_list:  # 因为没用{IP:玩家}，所以遍历玩家，看这个收到的数据是谁的
                    if player.ip == address[0] and player.win:
                        player.plane.location = Vector(data_tmp[1]['location'])
                        player.plane.velocity = Vector(data_tmp[1]['velocity'])
                        player.plane.health = data_tmp[1]['health']  # !!!!!!!!会出现掉血了，然后回退回去的情况
                        logging.info("Get player status, local_frame:%d----> %s, %s" % (
                        self.syn_frame, str(address), str(data_tmp)))
                        break
            elif data_tmp[0] == 'box_status':  # 接受并处理Box
                self.box_group.add(Box(location=data_tmp[1]['location'], catalog=data_tmp[1]['catalog']))

    def main(self):
        # print self.re_local_ip
        # print self.re_c_or_j
        # print self.re_plane_type
        # print self.re_host_ip
        # self.port += 1
        if SINGLE_TEST:
            localip = LOCALIP
            plane_type = PLANE_TYPE
            msg_player = self.init_local_player(localip, plane_type)
            self.game_init(localip)
            self.d[localip] = msg_player
            self.local_ip = self.other_ip = localip
        else:
            localip = self.get_local_ip()
            if RESTART_MODE:
                player_type = self.re_player_type
            else:
                plane_type = raw_input("choose your plane catalog in %s:" % str(PLANE_CATALOG.keys()))
                while plane_type not in PLANE_CATALOG.keys():
                    plane_type = raw_input("spell fault, choose your plane catalog, %s:" % str(PLANE_CATALOG.keys()))
                self.re_player_type = plane_type
            msg_player = self.init_local_player(localip, plane_type)  # !!需要修改这个msg_player,json好发送

            # self.sock & self.q is ready.
            self.game_init(localip)
            self.d[localip] = msg_player

            if self.create_or_join():
                if not self.create(localip, msg_player):
                    self.done = True
                    print('waiting join failed!')
                    return False
            else:
                if RESTART_MODE:
                    host_ip = self.re_host_ip
                else:
                    host_ip = raw_input('Input a host ip to join a game:')
                    self.re_host_ip = host_ip
                if not self.join(msg_player, host_ip):
                    self.done = True
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

        # 获取本地玩家对象
        for player in self.player_list:
            if player.ip == self.local_ip:
                self.local_player = player

        # 同步开始循环
        self.sock_send('200 OK', (self.other_ip, self.port))
        self.sock_waitfor('200 OK', (self.other_ip, self.port))
        print('Game Start.My IP&PORT: %s - %d' % (self.local_ip, self.port))

        # PYGAME LOOP
        pygame.key.set_repeat(10)  # control how held keys are repeated
        while not self.done:
            event_list = self.event_control()
            if self.process(event_list):
                self.done = True
                # for player in self.player_list:
                #     if player.ip == self.local_ip:
                # if self.local_player.win:
                #     print '[%s]YOU WIN.' % self.local_ip
                # else:
                #     print '[%s]GAME OVER' % self.local_ip
                break
            Map.adjust_rect(self.screen_rect, self.map.surface.get_rect())
            # Map.adjust_rect()
            self.render(self.screen_rect)

            pygame.display.flip()
            self.clock.tick(self.fps)
            self.erase()

        # self.thread1.close
        # self.sock.close()
        # pygame.time.wait(1000)
        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.main()
    # while raw_input('press "r" to restart game:') == 'r':
    #     RESTART_MODE = True
    #     game.main()
    game.sock.close()
