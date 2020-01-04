# -*- coding: utf-8 -*-
import pygame
import math
import os
from random import randint
import socket
import threading
from queue import Queue  # to be continue
import json
import logging
from information import Information





class Vector:
    def __init__(self, *args):
        if len(args) == 2:
            self.x = args[0]
            self.y = args[1]
        elif len(args[0]) == 2:
            self.x = args[0][0]
            self.y = args[0][1]
        else:
            logging.info('Invalid Vector:', args)

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
    MARS COORDINATE: location+=velocity(* SPEED_RATIO / FPS), acc+=velocity, velocity
    EARTH COORDINATE: rect,
    """

    def __init__(self, location, image):
        pygame.sprite.Sprite.__init__(self)
        # cloud.png has transparent color ,use "convert_alpha()"

        # image = Surface对象
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
        self.hit = None
        self.catalog = None

    def rotate(self):
        angle = math.atan2(self.velocity.x, self.velocity.y) * 360 / 2 / math.pi - 180  # 这个角度是以当前方向结合默认朝上的原图进行翻转的
        self.image = pygame.transform.rotate(self.origin_image, angle)

    def update(self):
        self.velocity += self.acc
        self.location.x += self.velocity.x * SPEED_RATIO / FPS
        self.location.y += self.velocity.y * SPEED_RATIO / FPS
        # if self.location.x < 0:
        #     self.location.x = 0
        # elif self.location.x > MARS_MAP_SIZE[0]:
        #     self.location.x = MARS_MAP_SIZE[0]
        # if self.location.y < 0:
        #     self.location.y = 0
        # elif self.location.y > MARS_MAP_SIZE[1]:
        #     self.location.y = MARS_MAP_SIZE[1]
        if self.location.x < 10*MAP_RATIO:
            self.velocity.x = - self.velocity.x
            self.location.x = 10*MAP_RATIO
        elif self.location.x > MARS_MAP_SIZE[0]-10*MAP_RATIO:
            self.velocity.x = - self.velocity.x
            self.location.x = MARS_MAP_SIZE[0]-10*MAP_RATIO
        if self.location.y < 10*MAP_RATIO:
            self.velocity.y = - self.velocity.y
            self.location.y = 10 * MAP_RATIO
        elif self.location.y > MARS_MAP_SIZE[1]-10*MAP_RATIO:
            self.velocity.y = - self.velocity.y
            self.location.y = MARS_MAP_SIZE[1]-10*MAP_RATIO
        self.rect.center = Map.mars_translate((self.location.x, self.location.y))
        # logging.info('acc: %s' % str(self.acc))
        self.acc = Vector(0, 0)
        self.rotate()
        # logging.info('location:%s, rect:%s' % (str(self.location), str(self.rect)))

    def delete(self, hit=False):
        if self.alive:  # 第一次进行的操作
            self.hit = hit
            # self.kill()  # remove the Sprite from all Groups
            self.alive = False
            if self.sound_kill:
                self.sound_kill.play()

        # 启动自爆动画
        # self.self_destruction += 0.25
        self.self_destruction += 0.5
        # if self.catalog == 'Gun':
        #     print self.self_destruction
        #     print self.hit,self.self_destruction,self.self_destruction // 1, self.destruct_image_index
        if self.hit and self.self_destruction < self.destruct_image_index:
            # print [self.self_destruction//2*40, 0, 39, 39],self.self_destruction,self.image.get_rect()
            self.origin_image = self.image = self.image_original.subsurface(
                [self.self_destruction //
                 1 * self.image_original.get_height(), 0, self.image_original.get_height()-1, self.image_original.get_height()-1])

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
                self.delete(hit=True)
            elif self.catalog in ['Rocket', 'Cobra'] and isinstance(base, Plane):
                self.sound_collide_plane.play()
                self.delete(hit=True)


class Box(Base):
    def __init__(self, location, catalog):
        image_path = BOX_CATALOG[catalog]['image']
        self.image = pygame.image.load(image_path).convert()
        self.image.set_colorkey(WHITE)
        super(Box, self).__init__(location=location, image=self.image)

        self.sound_kill = pygame.mixer.Sound("./sound/beep.wav")
        self.catalog = catalog
        if catalog == 'Medic':
            self.health = BOX_CATALOG[catalog]['health']
        elif catalog == 'Power':
            pass
        elif catalog in ['Gunfire_num', 'Rocket_num', 'Cobra_num']:
            self.num = BOX_CATALOG[catalog]['num']

    def effect(self, plane_object):
        if self.catalog == 'Medic':
            plane_object.change_health(self.health)
        # elif catalog == 'Power':  # 这个后面再做威力加强，武器是发射时，加载在飞机的weapon_group上
        #     pass
        elif self.catalog == 'Gunfire_num':
            plane_object.change_weapon('Gun', self.num)
        elif self.catalog == 'Rocket_num':
            plane_object.change_weapon('Rocket', self.num)
        elif self.catalog == 'Cobra_num':
            plane_object.change_weapon('Cobra', self.num)


class Tail(Base):
    def __init__(self, location, catalog='Point'):
        image_path = TAIL_CATALOG[catalog]['image']
        self.image = pygame.image.load(image_path).convert()
        self.image.set_colorkey(WHITE)
        super(Tail, self).__init__(location=location, image=self.image)
        self.life = TAIL_CATALOG[catalog]['life']

        self.live_time = TAIL_CATALOG[catalog]['init_time']
        self.rect_mark = self.rect
        self.rect = (0, 0)
        # print self.location

    def update(self):
        self.live_time += 1
        # print self.live_time,self.life
        if self.live_time == 0:  # 越过0点的时候，恢复位置
            self.rect = self.rect_mark
        if self.live_time > self.life:
            self.delete()

    # def draw(self):
    #     """SpriteGroup.draw() 是单独运行的"""
    #     if self.live_time <= 0:
    #         super(Tail,self).draw()

class HealthBar(Base):
    def __init__(self, location):
        self._max_length = 200
        self.health_surface = pygame.Surface((self._max_length, 5))  # 最多是默认血条的5*40被长度
        self.health_surface.fill(LIGHT_GREEN)
        self.health_surface.convert()
        _image = self.health_surface.subsurface((0,0,40,5))  # 默认是200的血量，对应40格血条长度
        super(HealthBar,self).__init__(location=location, image=_image)
        self.update(rect_topleft=Map.mars_translate(location), num=200)

    def update(self, rect_topleft ,num):
        if num <= 0:
            _num = 0
        elif num > self._max_length:
            _num = 200
        self.image = self.health_surface.subsurface((0,0,num/5,5))  # 默认是5的血量，对应1格血条长度
        self.rect.topleft = rect_topleft
        self.rect.move_ip(0, 50)  # 血条向下移50个像素点

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
        self.velocity = Vector(randint(-100, 100), randint(-100, 100)).normalize_vector() * self.speed  # Vector
        self.acc = Vector(0, 0)

        self.weapon = {1: {}, 2: {}, 3: {}}  # 默认没有武器

        self.sound_kill = pygame.mixer.Sound("./sound/explode3.wav")
        self.destruct_image_index = self.image_original.get_width() / self.image_original.get_height()
        # self.catalog = catalog

        self.health_bar = HealthBar(location=self.location)

        # self.last_health_rect = None
        # # print self.rect.width
        # self.health_surface = pygame.Surface((self.rect.width*5, 5))  # 最多是默认血条的5被长度
        # self.health_surface.fill(WHITE)
        # self.health_surface.convert()
        # self.image.set_colorkey(WHITE)

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
            self.health_bar.delete()  # 删除血条
            super(Plane, self).update()
            return self.delete(hit=True)

        super(Plane, self).update()
        self.health_bar.update(rect_topleft=self.rect.topleft, num=self.health)  # 更新血条
        # self.health -= 50
        if self.health <= 0:
            # if self.last_health_rect:  # 最后删除血条
            #     surface.blit(source=self.health_surface, dest=self.last_health_rect)
            #     self.last_health_rect=pygame.Rect(self.rect.left, self.rect.top+self.rect.height+10, self.rect.width*(self.health*1.0/200), 5)
            return self.delete(hit=True)

    def draw_health(self, surface):
        pass
        # # """sprite.Group()是单独blit的"""
        # # if self.last_health_rect:
        # #     surface.blit(source=self.health_surface, dest=self.last_health_rect)
        # health_rect = pygame.Rect(self.rect.left, self.rect.top+self.rect.height+10, self.rect.width*(self.health*1.0/200), 5)
        # # self.last_health_rect = health_rect
        # # self.health_surface.blit(source=surface, dest=(0, 0), area=health_rect)  # 从map_surface获取底图到health_surface
        # # # self.screen.blit(source=self.map.surface, dest=(0, 0), area=self.current_rect)
        # if self.health > 0:
        #     pygame.draw.rect(surface, (10,200,100), health_rect, 0)


class Weapon(Base):
    def __init__(self, catalog, location, velocity):
        if catalog == 'Gun':
            image_path = WEAPON_CATALOG['Gun']['image'][randint(0, len(WEAPON_CATALOG['Gun']['image']) - 1)]
            self.image_original = pygame.image.load(image_path).convert()
            self.image_original.set_colorkey(WHITE)
            self.image = self.image_original.subsurface((0, 0, self.image_original.get_height()-1, self.image_original.get_height()-1))
            super(Weapon, self).__init__(location=location, image=self.image)
            self.sound_fire = pygame.mixer.Sound("./sound/minigun_fire.wav")
            self.sound_fire.play(maxtime=200)
            self.sound_collide_plane = pygame.mixer.Sound(WEAPON_CATALOG['Gun']['sound_collide_plane'][randint(0, len(
                WEAPON_CATALOG['Gun']['sound_collide_plane']) - 1)])
            self.destruct_image_index = self.image_original.get_width() / self.image_original.get_height()
        else:
            image_path = WEAPON_CATALOG[catalog]['image']
            self.image_original = pygame.image.load(image_path).convert()
            self.image_original.set_colorkey(WHITE)
            self.image = self.image_original.subsurface((0, 0, self.image_original.get_height() - 1, self.image_original.get_height() - 1))
            # self.image = self.image_original.subsurface((0, 0, self.image_original.get_width() - 1, self.image_original.get_height() - 1))
            super(Weapon, self).__init__(location=location, image=self.image)
            self.sound_fire = pygame.mixer.Sound("./sound/TPhFi201.wav")
            self.sound_fire.play()
            self.sound_kill = pygame.mixer.Sound("./sound/ric5.wav")
            self.sound_collide_plane = pygame.mixer.Sound("./sound/shotgun_fire_1.wav")
            self.destruct_image_index = self.image_original.get_width() / self.image_original.get_height()
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

        self.rotate()

        self.catalog = catalog
        self.target = None

        self.destruct_image_index = self.image_original.get_width() / self.image_original.get_height()

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

        if self.fuel <= 0 or self.health <= 0:
            if self.catalog in ['Rocket','Cobra']:
                self.delete(hit=True)
            else:
                self.delete()
        else:
            super(Weapon, self).update()  # 正常更新
            self.fuel -= 1


class SlotWidget():
    """show local plane weapon slots' number"""
    def __init__(self, screen):
        """
        self.line_list = [{'key_obj':key_obj, 'value_obj':value_obj, 'num':num, 'sprite_group':sprite_group, 'sprite_list':[]}, {},..]
        self.slot_group = <slot1_obj, slot2_obj,.. .instance at pygame.sprite.Group>
        """
        self.screen_surface = screen
        self.weapon_name_list = ['Gun', 'Rocket', 'Cobra']
        self.slot_name_list = ['Gunfire_num', 'Rocket_num', 'Cobra_num']
        self.line_index = {k:v for v,k in enumerate(self.weapon_name_list)}  # {'Gun':1, ..}
        self.line_list = []
        self.slot_group = pygame.sprite.Group()
        self.make_body()

    def make_body(self):
        # zip 等价于 [('Gunfire_num', 'Gun'), ('Rocket_num', 'Rocket'), ('Cobra_num', 'Cobra')]
        slot_dict = {k:v for k,v in zip(self.slot_name_list, self.weapon_name_list)}

        for catalog in self.slot_name_list:
            image_path = BOX_CATALOG[catalog]['image']
            image = pygame.image.load(image_path).convert()
            image.set_colorkey(WHITE)
            # image = image.subsurface((0, 0, image.get_height() - 1, image.get_height() - 1))
            slot_obj = Base(location=(5,5), image=image)

            image_path = WEAPON_CATALOG[slot_dict[catalog]]['image_slot']
            # print WEAPON_CATALOG[slot_dict[catalog]]['image'], image_path, slot_dict[catalog]
            image = pygame.image.load(image_path).convert()
            image.set_colorkey(WHITE)
            weapon_obj = Base(location=(5,15), image=image)

            self.add_line(weapon_name=slot_dict[catalog], key_obj=slot_obj, value_obj=weapon_obj, num=0)

    def add_line(self, weapon_name, key_obj, value_obj, num):
        # deal key_obj: add into self.slot_group
        key_obj.rect.topleft = (7, 7+20*len(self.slot_group.sprites()))
        self.slot_group.add(key_obj)

        # deal value_obj
        sprite_group = pygame.sprite.Group()
        line_dict = {'key_obj':key_obj, 'value_obj':value_obj, 'num':0, 'sprite_group':sprite_group, 'sprite_list':[]}
        self.line_list.append(line_dict)

        self.update_line(weapon_name=weapon_name, weapon_num=num)

    def update_line(self, weapon_name, weapon_num, gap=1):
        """line_dict = {'key_obj':key_obj, 'value_obj':value_obj, 'num':0, 'sprite_group':sprite_group, 'sprite_list':[]}"""
        index = self.line_index[weapon_name]
        line_dict = self.line_list[index]
        if weapon_num > line_dict['num']:
            slot_obj = line_dict['key_obj']  # 指定slot_obj
            image_path = WEAPON_CATALOG[weapon_name]['image_slot']  # 创建weapon_obj
            image = pygame.image.load(image_path).convert()
            image.set_colorkey(WHITE)
            weapon_obj = Base(location=(5, 5), image=image)
            # weapon_obj = copy.copy(line_dict['value_obj'])  # 采用copy.copy, 不知道会不会有其他风险, 果然有问题，删除
            weapon_obj.rect.center = slot_obj.rect.center
            weapon_obj.rect.left = slot_obj.rect.left + slot_obj.rect.width + gap + line_dict['num']*weapon_obj.rect.width
            line_dict['num'] += 1
            line_dict['sprite_group'].add(weapon_obj)
            line_dict['sprite_list'].append(weapon_obj)
        elif weapon_num < line_dict['num']:
            weapon_obj_list = line_dict['sprite_group'].sprites()
            if len(weapon_obj_list) > 0:
                line_dict['sprite_group'].remove(line_dict['sprite_list'].pop())
                line_dict['num'] -= 1

    def draw(self):
        """draw slot and draw weapon"""
        self.slot_group.draw(self.screen_surface)
        for line in self.line_list:
            line['sprite_group'].draw(self.screen_surface)

    def clear(self, callback):
        self.slot_group.clear(self.screen_surface, callback)
        for line in self.line_list:
            line['sprite_group'].clear(self.screen_surface, callback)


class Game(object):

    def __init__(self):
        self.local_ip = None
        self.other_ip = None
        self.host_ip = None
        self.sock = None
        self.port = 8989

        self.re_local_ip = LOCALIP
        self.re_msg_player = None
        self.re_c_or_j = C_OR_J
        self.re_host_ip = HOSTIP

        self.local_player = None
        self.num_player = 0
        self.lock_frame = 0
        self.delay_frame = 0
        # self.start_time = 0

        self.show_result = False  # 用来显示Win or Lose
        self.hide_result = False
        self.last_tab_frame = 0

        self.screen_focus_obj = None  # 默认为空，首次指向本地plane, 空格指向本地plane, 为空但是本地plane还存在就指向plane

    def game_init(self, localip):
        logging.basicConfig(level=logging.DEBUG,  # CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
                            format='%(asctime)s [line:%(lineno)d] [%(levelname)s] %(message)s',

                            filename='logger.log',
                            filemode='a')

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
            logging.info('Bind socket %s ok.' % str(address))
        else:
            pygame.time.wait(1200)
            while not self.q.empty():
                self.q.get()

        self.syn_frame = 0

        # MSG QUEUE
        self.q = queue.queue()  # GET
        self.q_send = queue.queue()

        # UDP sending
        self.thread_send = threading.Thread(target=self.msg_send)
        self.thread_send.setDaemon(True)
        self.thread_send.start()

        # UDP listening
        self.thread1 = threading.Thread(target=self.msg_recv)
        self.thread1.setDaemon(True)  # True:不关注这个子线程，主线程跑完就结束整个python process
        self.thread1.start()

        # sprite group
        self.plane_group = pygame.sprite.Group()
        self.weapon_group = pygame.sprite.Group()
        self.tail_group = pygame.sprite.Group()
        self.box_group = pygame.sprite.Group()
        self.health_group = pygame.sprite.Group()

        # backup map
        self.origin_map = None

        # Info show
        self.info = Information()

    def screen_init(self):
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        pygame.mixer.init()  # 声音初始化
        pygame.display.init()  # 初始化
        pygame.event.get()
        pygame.mouse.set_visible(False)
        display_info = pygame.display.Info()
        ret = pygame.display.set_mode(flags=pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        # ret = pygame.display.set_mode(size=(1366,768), flags=pygame.FULLSCREEN|pygame.HWSURFACE|pygame.DOUBLEBUF)
        logging.info('DISPLAY:%s'%str(ret))
        # pygame.display.set_mode(flags=pygame.FULLSCREEN, depth=0)
        # screen_size_fittable = (display_info.current_w * 19 / 20, display_info.current_h * 17 / 20)
        # if screen_size_fittable[0] * screen_size_fittable[1] > 0:
        #     pygame.display.set_mode(screen_size_fittable)
        # else:
        #     pygame.display.set_mode(SCREEN_SIZE)
        # Return the size of the window or screen
        # pygame.display.get_window_size()
        self.screen = pygame.display.get_surface()  # 游戏窗口对象
        self.screen_rect = self.screen.get_rect()  # 游戏窗口对象的rect
        logging.info('DISPLAY:%s' % self.screen_rect)

        # 更新游戏地图（MARS）与显示地图的比例
        global MARS_RATIO
        MARS_RATIO = (float(MARS_SCREEN_SIZE[0]) / self.screen_rect.w, float(MARS_SCREEN_SIZE[1]) / self.screen_rect.h)

        self.move_pixels = 30
        self.fps = FPS
        self.clock = pygame.time.Clock()

    #     self.mars_ratio = (float(MARS_SCREEN_SIZE[0])/self.screen_rect.w, float(MARS_SCREEN_SIZE[1])/self.screen_rect.h)
    #
    # def mars_translate(coordinate):
    #     """translate Mars Coordinate to current Display Coordinate"""
    #     return [int(coordinate[i] / self.mars_ratio[i]) for i in [0, 1]]
    #
    # def mars_unti_translate(coordinate):
    #     return [int(coordinate[i] * self.mars_ratio[i]) for i in [0, 1]]

    def msg_send(self):
        while not self.done:
            if not self.q_send.empty():
                msg_dumped,dest = self.q_send.get()
                self.sock.sendto(msg_dumped, dest)
                logging.info('SEND [%s]:%s' % (str(dest), msg_dumped))

    def msg_recv(self):
        while not self.done:
            data = self.sock.recvfrom(1487)
            self.q.put(data)
            logging.info('RECV %s' % str(data))
            # print("socket get msg.")

    def sock_send(self, msg, dest):
        """strs: unicode string or dict object"""
        self.q_send.put((json.dumps(msg), dest))
        # self.sock.sendto(json.dumps(msg), dest)

    def sock_waitfor(self, msg, dest, delay=100, waiting_times=30):
        count = 0
        while self.q.empty():
            pygame.time.wait(delay)
            count += 1
            if count > waiting_times:
                logging.error('Sock Waiting Timeout: %s' % msg)
                return False
        data, address = self.q.get()
        logging.info('GET:%s' % str(json.loads(data)))
        if address[0] == dest[0]:
            logging.info('Sock Msg Get:%s' % json.loads(data))
            return json.loads(data)
        else:
            logging.error('Sock Wrong Msg:%s %s' % (str(address), json.loads(data)))
            return False

    def add_player(self, player):
        self.player_list.append(player)
        self.plane_group.add(player.plane)
        self.health_group.add(player.plane.health_bar)
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
        print('Create:GET_INFO:%s %s' % (str(data), str(address)))
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
        # logging.info('T3.0:%d' % pygame.time.get_ticks())
        self.screen.blit(source=self.map.surface, dest=(0, 0), area=self.current_rect)  # Cost 5ms
        # self.screen = self.map.surface.subsurface(self.current_rect)  # 黑屏
        # logging.info('T3.1:%d' % pygame.time.get_ticks())
        self.minimap.draw()
        self.slot.draw()  # draw SlotWidget
        # logging.info('T3.2:%d' % pygame.time.get_ticks())
        # self.info.show(self.screen)  # 吃性能所在之处！！！！！！！！！！！！！！！
        # logging.info('T3.3:%d' % pygame.time.get_ticks())
        if self.show_result and not self.hide_result:
            self.info.show_end(self.screen)  # 吃性能所在之处！！！！！！！！！！！！！！！
        # logging.info('T3.4:%d' % pygame.time.get_ticks())

    def player_communicate(self, key_list):
        """
        在World类里面实现，TCP/IP的事件信息交互，Player类只做事件的update()
        发送本地玩家的操作
        """
        if not self.local_player.alive:
            return
        # str_key_list = json.dumps((self.syn_frame, key_list))  # # 如果没操作队列: event_list = key_list = []
        for player in self.player_list:  # 发送给每一个网卡，包括自己
            # print player.ip
            try:
                # logging.info('Send %d---> %s, %s' % (self.syn_frame, str((player.ip, self.port)), str_key_list))
                self.sock_send((self.syn_frame, key_list), (player.ip, self.port))
                # self.sock.sendto(str_key_list, (player.ip, self.port))
                # self.sock.sendto(str_event_list, (player.ip, self.port))  # 发双份
            except Exception as msg:
                logging.warn('Offline(Socket Error):' + str(msg))

    def deal_collide(self):
        """
        self.plane_group = pygame.sprite.Group()
        self.weapon_group = pygame.sprite.Group()
        """
        for weapon in self.weapon_group:  # 遍历每一个武器
            # 如果不是枪弹就进行相互碰撞测试
            if not weapon.alive:
                continue
            if weapon.catalog != 'Gun':
                # print weapon
                weapon_collide_lst = pygame.sprite.spritecollide(weapon, self.weapon_group, False, pygame.sprite.collide_rect_ratio(0.8))  # False代表不直接kill该对象
                weapon.hitted(weapon_collide_lst)  # 发生碰撞相互减血
                # for hitted_weapon in weapon_collide_lst:
                #     hitted_weapon.hitted([weapon])  # 本身受到攻击的对象
            # 检测武器与飞机之间的碰撞        
            plane_collide_lst = pygame.sprite.spritecollide(weapon, self.plane_group, False, pygame.sprite.collide_rect_ratio(0.8))
            weapon.hitted(plane_collide_lst)  # 发生碰撞相互减血

    def deal_collide_with_box(self):
        for plane in self.plane_group:  # 进行飞机与Box之间碰撞探测
            box_collide_lst = pygame.sprite.spritecollide(plane, self.box_group, False, pygame.sprite.collide_rect_ratio(0.8))
            for box in box_collide_lst:
                box.effect(plane)
                box.delete()

    def syn_status(self):
        if self.syn_frame % (int(2 * FPS)) == 0:  # 每2秒同步一次自己状态给对方
            # print self.player_list, self.local_ip, self.other_ip
            for player in self.player_list:
                # logging.info('PLAYERS INFO:%s, loca[%s],velo[%s]'%(player.ip,str(player.plane.location), str(player.plane.velocity)))
                if player.ip == self.local_ip and player.alive:
                    status_msg = ('syn_player_status', {'location': (player.plane.location.x, player.plane.location.y),
                                                        'velocity': (player.plane.velocity.x, player.plane.velocity.y),
                                                        'health': player.plane.health})
                    for player in self.player_list:
                        # self.sock_send(status_msg, (player.ip, self.port))  # test 谁都发
                        if player.ip != self.local_ip:
                            self.sock_send(status_msg, (player.ip, self.port))
                    break

    def add_weapon_tail(self, weapon_group):
        for weapon in weapon_group:
            if weapon.catalog == 'Rocket' or weapon.catalog == 'Cobra':
                self.tail_group.add(Tail((weapon.location.x, weapon.location.y)))

    def add_unit_tail(self, unit_group):
        for unit in unit_group:
            self.tail_group.add(Tail((unit.location.x, unit.location.y), catalog='Plane_tail'))

    def erase(self):
        self.weapon_group.clear(self.map.surface, self.clear_callback)
        self.plane_group.clear(self.map.surface, self.clear_callback)
        self.tail_group.clear(self.map.surface, self.clear_callback)
        self.box_group.clear(self.map.surface, self.clear_callback)
        self.slot.clear(self.clear_callback)
        self.health_group.clear(self.map.surface, self.clear_callback)

    def clear_callback(self, surf, rect):
        # surf.blit(source=self.map.surface, dest=(0, 0), area=self.current_rect)
        # self.screen.blit(source=self.map.surface, dest=(0, 0), area=self.current_rect)
        surf.blit(source=self.origin_map_surface, dest=rect,
                  area=rect)  # blit(source, dest, area=None, special_flags=0) -> Rect

    def event_control(self):
        """
        :return: 返回空列表，或者一个元素为keys的列表
        看这个样子，应该是每一self.syn_frame就读取一次键盘操作bool值列表
        """
        pygame.event.get()  # 一定要把操作get()出来
        key_list = ''
        # n_break = 0
        if pygame.key.get_focused():
            keys = pygame.key.get_pressed()  # key is queue too， 一个列表，所有按键bool值列表
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
                    self.screen_focus_obj = self.local_player.plane
                    # self.screen_focus = Map.mars_translate(self.d[self.local_ip]['location'])
                    # self.screen_rect.center = Map.mars_translate(self.local_player.plane.location)
            if keys[pygame.K_TAB] :
                if self.syn_frame - self.last_tab_frame > self.fps/4:
                    self.last_tab_frame = self.syn_frame
                    self.hide_result = not self.hide_result  # 需要设置KEYUP和KEYDONW，to be continue...!!!!

            for keyascii in [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_i, pygame.K_o, pygame.K_p]:
                if keys[keyascii]:
                    key_list += chr(keyascii)

            # n_break += 1
            # if n_break > 3:
            #     break

        return key_list

    # def get_local_ip(self):
    #     l = socket.getaddrinfo(socket.gethostname(), None)
    #     for index, i in enumerate(l):
    #         print index, i[-1][0]
    #     if RESTART_MODE:
    #         localip = self.re_local_ip
    #     else:
    #         localip = l[input("select your own ip index:")][-1][0]
    #         self.re_local_ip = localip  # for repeat
    #     self.local_ip = localip
    #     return localip

    def get_local_ip(self):
        return socket.gethostbyname(socket.gethostname())

    def box_msg_send(self):
        if self.syn_frame % (10 * FPS) == 0:  # 每n=10秒同步一次自己状态给对方
            location = [randint(0, MARS_MAP_SIZE[0]), randint(0, MARS_MAP_SIZE[1])]
            # Medic and so on. -->  10%, 30%, 30%, #0%
            rand_x = randint(0,100)
            if rand_x <= 10:
                rand_catalog = 'Medic'
            elif rand_x <= 40:
                rand_catalog = 'Gunfire_num'
            elif rand_x <= 70:
                rand_catalog = 'Rocket_num'
            elif rand_x <= 100:
                rand_catalog = 'Cobra_num'
            status_msg = ('box_status', {'location': location, 'catalog': rand_catalog})
            for player in self.player_list:
                self.sock_send(status_msg, (player.ip, self.port))

    def plane_lost_msg_send(self, player_ip):
        status_msg = ('plane_lost', {'ip':player_ip})
        for player in self.player_list:
            self.sock_send(status_msg, (player.ip, self.port))

    # def syn_lock_frame(self):
    #     lock_frame = 0
    #     while not self.done:
    #         pygame.time.wait(1000/FPS)
    #         status_msg = ('syn_lock_frame', lock_frame)
    #         for player in self.player_list:
    #             self.sock_send(status_msg, (player.ip, self.port))
    #         lock_frame += 1

    def process(self, event_list):
        """
        每个玩家接收自己的消息队列，刷新自己的界面；
        不管延迟和丢包的问题，接受操作消息等待为resend_time=30ms；
        每过2帧进行一次状态同步：只将本地玩家飞机状态发送给其他玩家；
        """
        # 产生随机奖励Box，并发送
        self.box_msg_send()

        # 状态同步, 先状态同步，再发送操作消息
        self.syn_status()

        # # 发送锁定帧
        # self.syn_lock_frame()

        # 发送普通键盘操作消息
        self.player_communicate(event_list)

        # 进行游戏对象参数计算&渲染
        self.minimap.update()
        self.weapon_group.update(self.plane_group)
        self.tail_group.update()  # update尾焰
        if self.local_player.plane:
            for weapon in ['Gun', 'Rocket', 'Cobra']:  # update SlotWidget
                if weapon == 'Gun':
                    index_ = 1
                elif weapon == 'Rocket':
                    index_ = 2
                else:  # weapon == 'Cobra':
                    index_ = 3
                self.slot.update_line(weapon_name=weapon, weapon_num=self.local_player.plane.weapon[index_]['number'])
        # self.map.surface = self.origin_map_surface.copy()  # [WARNING]很吃性能！！！！！极有可能pygame.display()渲染不吃时间，这个copy（）很吃时间
        # self.map.surface.blit(self.origin_map_surface, (0,0))  # ！！

        # 添加尾焰轨迹
        if self.syn_frame % 5 == 0:
            self.add_weapon_tail(self.weapon_group)
        # if self.syn_frame % 3 == 0:  # 添加飞机尾焰
        #     self.add_unit_tail(self.plane_group)

        # DRAW
        self.box_group.draw(self.map.surface)  # draw随机Box
        self.tail_group.draw(self.map.surface)  # draw尾焰
        self.plane_group.draw(self.map.surface)  # draw飞机
        self.health_group.draw(self.map.surface)  # draw飞机血条
        self.weapon_group.draw(self.map.surface)  # draw武器
        for i in self.weapon_group:  # 画被跟踪框框
            if i.target:
                # print i.target
                pygame.draw.rect(self.map.surface, (255, 0, 0), i.target.rect, 1)
        # print self.slot.slot_group.sprites()[0].rect
        # print self.slot.line_list[1]['sprite_group'].sprites()[0].rect

        # 碰撞处理
        self.deal_collide()
        self.deal_collide_with_box()

        # 判断游戏是否结束
        for player in self.player_list:
            if player.alive:
                # player.plane.draw_health(self.map.surface)  # 显示飞机血条
                # 更新玩家状态,player.update()-->plane.update()-->plane.delete(),delete没了的的飞机
                if player.update():  # player.update==True就是玩家飞机lost了
                    self.plane_lost_msg_send(player.ip)  # 发送玩家lost的消息
                    player.plane = None  # player.update()为True说明飞机已经delete了
                    player.alive = False  # End Game
                    self.num_player -= 1
                    logging.info("Player lost: %s" % player.ip)
                    # return True

        # 显示游戏信息
        # self.info.add(u'')
        # self.info.add(u'')
        # self.info.add(u'')
        # self.info.add(u'')
        # self.info.add(u'')
        # for py in self.player_list:
        #     self.info.add(u'Player IP:%s' % py.ip)
        #     if py.plane:
        #         self.info.add(u'Health:%d' % py.plane.health)
        #         self.info.add(u'Weapon:%s' % str(py.plane.weapon))
        #         self.info.add(u'Tail:%s' % self.tail_group)
        #         self.info.add(u'speed:%s,  location:%s,  rect:%s' % (
        #             str(py.plane.velocity), str(py.plane.location), str(py.plane.rect)))
        #     self.info.add(u'Groups:%s' % str(self.plane_group))

        # 屏幕显示，本地飞机聚焦处理
        if not self.local_player.alive:  # 本地玩家
            self.screen_focus_obj = None  # screen_rect聚焦为空，回复上下左右控制
            self.show_result = True
            self.info.add_middle('YOU LOST.')
            self.info.add_middle_below('press "ESC" to exit the game.')
            self.info.add_middle_below('press "Tab" to hide/show this message.')
        else:  # 本地飞机还或者的情况
            # print self.screen_focus_obj
            if not self.screen_focus_obj.groups():  # 本地飞机还活着，但是focus_obj不在任何group里面了，就指回本地飞机
                self.screen_focus_obj = self.local_player.plane
            if self.num_player == 1:  # 只剩你一个人了
                self.show_result = True
                self.info.add_middle('YOU WIN!')
                self.info.add_middle_below('press "ESC" to exit the game.')
                self.info.add_middle_below('press "Tab" to hide/show this message.')

        # 收到消息进行操作（最后处理动作，留给消息接收）
        # self.get_deal_msg()

        # # LockFrame关键帧同步, 根据情况每帧多拖累一针
        # while self.delay_frame > 0:
        #     pygame.time.wait(1000/FPS)
        #     self.delay_frame -= 1


    def get_deal_msg(self):
        while not self.done:  # 游戏结束判定
            # 空就不进行读取处理
            if self.q.empty():
                continue
                pygame.time.wait(1)

            # 处理消息
            data, address = self.q.get()
            data_tmp = json.loads(data)  # [frame_number, key_list], ['syn_player_status', dict]，['box_status', dict]

            # Msg Type1:操作类型的消息
            if isinstance(data_tmp[0], int):
                for player in self.player_list:  # 遍历玩家，看这个收到的数据是谁的
                    if player.ip == address[0] and player.alive:
                        # # 接收到大于当前帧的消息就等待, 比如：我自己才发送到第15帧，别人发到15,16,17帧来了我要等待
                        # while data_tmp[0] > self.syn_frame:
                        #     pygame.time.wait(1)
                        if data_tmp[1]:  # 消息-->操作
                            weapon_obj = player.operation(data_tmp[1],
                                             self.syn_frame)  # data is list of pygame.key.get_pressed() of json.dumps
                            if player.ip==self.local_ip and weapon_obj:  # 如果导弹对象不为空，就将屏幕聚焦对象指向它
                                self.screen_focus_obj = weapon_obj
                        logging.info("Get %d----> %s, %s" % (data_tmp[0], str(address), str(data_tmp)))
                        break  # 一个数据只有可能对应一个玩家的操作，有一个玩家取完消息就可以了

            # Msg Type2:状态同步-->对象，同步类型消息
            elif data_tmp[0] == 'syn_player_status':
                # print 'in status.....', address
                for player in self.player_list:  # 因为没用{IP:玩家}，所以遍历玩家，看这个收到的数据是谁的
                    if player.ip == address[0] and player.alive:
                        player.plane.location = Vector(data_tmp[1]['location'])
                        #+ Vector(data_tmp[1]['velocity'])* SPEED_RATIO / FPS  # 1帧的时间, 反而有跳跃感
                        player.plane.velocity = Vector(data_tmp[1]['velocity'])
                        player.plane.health = data_tmp[1]['health']  # !!!!!!!!会出现掉血了，然后回退回去的情况
                        logging.info("Get player status, local_frame:%d----> %s, %s" % (
                            self.syn_frame, str(address), str(data_tmp)))
                        break

            # Msg Type3:接受并处理Box类型消息
            elif data_tmp[0] == 'box_status':
                self.box_group.add(Box(location=data_tmp[1]['location'], catalog=data_tmp[1]['catalog']))

            # Msg Type4:接受并处理玩家飞机lost类型消息
            elif data_tmp[0] == 'plane_lost':  # status_msg = ('plane_lost', {'ip':player_ip})
                for player in self.player_list:
                    if player.alive and player.ip == data_tmp[1]['ip']:
                        player.plane.health = 0
                        break

            ## Msg Type:接受并处理LockFrame
            # elif data_tmp[0] == 'syn_lock_frame':
            #     # if self.syn_frame>data_tmp[1] and address[0] != self.local_ip:  # 如果LockFrame小于本系统的同步帧
            #     if self.syn_frame > data_tmp[1]:
            #         self.delay_frame = self.syn_frame - data_tmp[1]
            #     logging.info("DelayFrames:%d--->%s"%(self.delay_frame, str(data_tmp)))

    def get_deal_msg_(self):
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
                        logging.info('[ERROR]MSG LOST: %d' % self.syn_frame)
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
                    if player.ip == address[0] and player.alive:
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
                    if player.ip == address[0] and player.alive:
                        player.plane.location = Vector(data_tmp[1]['location'])
                        player.plane.velocity = Vector(data_tmp[1]['velocity'])
                        player.plane.health = data_tmp[1]['health']  # !!!!!!!!会出现掉血了，然后回退回去的情况
                        logging.info("Get player status, local_frame:%d----> %s, %s" % (
                            self.syn_frame, str(address), str(data_tmp)))
                        break
            elif data_tmp[0] == 'box_status':  # 接受并处理Box
                self.box_group.add(Box(location=data_tmp[1]['location'], catalog=data_tmp[1]['catalog']))

    def deal_player_dict(self, player_dict):
        """From: dict_player = {'ip':{'location': (randint(20, 80) / 100.0, randint(20, 80) / 100.0),
                                      'Plane': 'F35','Gun': 200, 'Rocket': 10, 'Cobra': 3}，
                               }
            To:  d = {'ip':msg_player，
                     }
            P.S. msg_player = {'ip': localip,
                        'location': (randint(MARS_MAP_SIZE[0] / 5, MARS_MAP_SIZE[0] * 4 / 5),
                                   randint(MARS_MAP_SIZE[1] / 5, MARS_MAP_SIZE[1] * 4 / 5)),
                        'Plane': plane_type, 'Gun': 200, 'Rocket': 10, 'Cobra': 3,}
        }"""
        d = {}
        for ip in player_dict.keys():
            d[ip] = player_dict[ip]
            d[ip]['ip'] = ip
            d[ip]['location'] = [MARS_MAP_SIZE[n]*i for n,i in enumerate(player_dict[ip]['location'])]
        return d

    def deal_screen_focus(self, screen_rect):
        if self.screen_focus_obj:
            screen_rect.center = self.screen_focus_obj.rect.center
            # screen_rect.center = Map.mars_translate(self.screen_focus_obj.location)

    def main(self):
        self.local_ip = localip = self.get_local_ip()
        if SINGLE_TEST:
            plane_type = PLANE_TYPE
            msg_player = self.init_local_player(localip, plane_type)
            self.game_init(localip)
            self.d[localip] = msg_player
            self.other_ip = localip

        self.game_init(self.local_ip)
        with open('player_dict.dat','r') as f1:
            player_dict_origin = json.load(f1)
            self.d = self.deal_player_dict(player_dict_origin)
            logging.info('load "player_dict.dat":success')

        # Pygame screen init
        self.screen_init()
        for ip in self.d.keys():
            self.add_player(self.msg2player(self.d[ip]))

        # MAP
        self.map = Map()  # 8000*4500--->screen, (8000*5)*(4500*5)---->map
        self.map.add_cloud()
        self.minimap = MiniMap(self.screen, self.map.surface.get_rect(), self.screen_rect, self.plane_group)
        self.origin_map_surface = self.map.surface.copy()

        # Weapon SlotWidget
        self.slot = SlotWidget(screen=self.screen)

        # 获取本地玩家对象
        for player in self.player_list:
            if player.ip == self.local_ip:
                self.local_player = player

        # 根据local player位置移动一次self.screen_rect git
        # self.screen_rect.center = Map.mars_translate(self.d[self.local_ip]['location'])
        self.screen_focus_obj = self.local_player.plane
        self.deal_screen_focus(self.screen_rect)

        # PYGAME LOOP
        pygame.key.set_repeat(10)  # control how held keys are repeated
        logging.info('Game Start.My IP&PORT: %s - %d' % (self.local_ip, self.port))

        # MAIN LOOP
        self.main_loop()

    def main_loop(self):
        # GET MSG DEAL INIT
        self.thread_msg = threading.Thread(target=self.get_deal_msg)
        self.thread_msg.setDaemon(True)  # True:不关注这个子线程，主线程跑完就结束整个python process

        # # lockframe deal
        # if self.host_ip == self.local_ip:  # 主机才发送同步LockFrame
        #     self.thread_lock = threading.Thread(target=self.syn_lock_frame)
        #     self.thread_lock.setDaemon(True)  # True:不关注这个子线程，主线程跑完就结束整个python process

        # 同步开始循环
        for ip in self.d.keys():
            self.sock_send('200 OK', (ip, self.port))

        now_count = start_count = pygame.time.get_ticks()
        waiting_times = 20000  # 这里其实需要改写为TCP确认， 等待对方收到消息 to be continue...
        msg_get_ip_list = {}
        while True:  # 等收到所有玩家的'200 ok'
            while not self.q.empty():
                data, address = self.q.get()
                if json.loads(data)=='200 OK':
                    self.sock_send('200 OK', address)  # 收到补发一个200 OK，因为对方都是先打开监听，然后开始发送
                    logging.info('Start Msg Get:%s:%s' % (address,data))
                    msg_get_ip_list[address[0]] = True
                    if len(msg_get_ip_list.keys()) >= len(self.player_list):
                        break

            if len(msg_get_ip_list.keys())>=len(self.player_list):
                logging.info('game:begin')
                break

            if pygame.time.get_ticks() - now_count > 1000: # 每一秒朝没有收到消息的主机发送一个200 OK
                now_count = pygame.time.get_ticks()
                for ip in self.d.keys():
                    if ip not in msg_get_ip_list.keys():
                        self.sock_send('200 OK', (ip, self.port))

            if pygame.time.get_ticks()-start_count > waiting_times:
                logging.error('Sock Waiting Timeout: %s' % '"200 OK"')
                self.done = True  # 通过self.done关闭线程，防止Errno 9：bad file descriptor(错误的文件名描述符)
                return False

        # MSG deal
        logging.info('deal_msg:begin')
        self.thread_msg.start()  # 开启玩家处理接受消息的线程

        # 主循环 Main Loop
        # if self.host_ip == self.local_ip:  # 主机才发送同步LockFrame
        #     self.thread_lock.start()  # 开启玩家处理接受消息的线程
        # last_time = pygame.time.get_ticks()
        while not self.done:
            last_time = pygame.time.get_ticks()
            logging.info("Frame No:%s" % self.syn_frame)
            # logging.info('T1:%d'%pygame.time.get_ticks())
            event_list = self.event_control()

            # logging.info('T1.1:%d' % pygame.time.get_ticks())
            self.deal_screen_focus(self.screen_rect)  # 在飞机update()之前就不会抖动

            # logging.info('T1.2:%d' % pygame.time.get_ticks())
            if self.process(event_list):  # 在FULLSCREEN下，这个函数最占性能20~40ms
                self.done = True
                break

            # logging.info('T2:%d'%pygame.time.get_ticks()) # T1与T2之间平均花费12ms
            Map.adjust_rect(self.screen_rect, self.map.surface.get_rect())

            # logging.info('T3:%d'%pygame.time.get_ticks())
            self.render(self.screen_rect)  # 该函数平均花费10ms(26ms), 在FULLSCREEN下是2ms

            # logging.info('T4:%d'%pygame.time.get_ticks())
            pygame.display.flip()  # 2ms

            # logging.info('T5:%d'%pygame.time.get_ticks())
            # self.clock.tick(self.fps)
            self.erase()  # 8ms,如果采用blit方式，就不用clear()的方法了

            # 这个是按整理计算延迟的，如果前面卡了，后面就会加速：没必要因为会定时同步状态
            # stardard_diff_time = -(pygame.time.get_ticks() - self.start_time) + self.syn_frame * 1000 / FPS
            # 计算每帧时间，和时间等待
            _time = pygame.time.get_ticks()
            logging.info('CostTime:%s' % str(_time - last_time))
            # 每帧需要的时间 - 每帧实际运行时间，如果还有时间多，就等待一下
            stardard_diff_time = 1000 / FPS - (_time - last_time)
            if stardard_diff_time > 0:  # 等待多余的时间
                pygame.time.wait(stardard_diff_time)  # 这个等待时间写在这里不合适
                logging.info('WaitingTime:%s' % str(stardard_diff_time))

            self.syn_frame += 1  # 发送同步帧(上来就发送)
            # logging.info('T6:%d'%pygame.time.get_ticks())

        # self.thread1.close
        # self.sock.close()
        # pygame.time.wait(1000)
        pygame.quit()


def test_calc_frame_cost():
    """2019-Sep-01 01:03:39-Sun [line:1305] [INFO] Time:34"""
    with open('logger.log', 'r') as f1:
        s = f1.readlines()

    l = []
    l_w = []
    cost_bool = wait_bool = False
    for i in s:
        if 'Frame No:' in i:
            if wait_bool:
                l_w.append('WaitingTime:0')
            cost_bool = True
            wait_bool = True
            continue
        if  cost_bool and 'CostTime:' in i:
            l.append(i)
            cost_bool = False
        if wait_bool and 'WaitingTime:' in i:
            l_w.append(i)
            wait_bool = False

    l1 = [i.split(':')[-1] for i in l]  # list of CostTime
    l2 = [i.split(':')[-1] for i in l_w] # list of WaitingTime

    # show diagram. vertiacal
    for i in range(min(len(l1), len(l2))):
        logging.info("[%d]%s%s" % (int(l1[i]) + int(l2[i]), '+' * int(l1[i]), '-' * int(l2[i])))
        # print("[%d]%s%s" % (int(l1[i]) + int(l2[i]), '+' * int(l1[i]), '-' * int(l2[i])))

    # average cost
    logging.info('average frame lantency = CostTime + WaitingTime')
    sum = 0
    for i in l1:
        sum += int(i)
    if len(l1)>0:
        logging.info('average CostTime:%s ms'%str(sum / len(l1)))
        # print('average Cost-Time:%s ms'%str(sum / len(l1)))

    # average waiting
    sum = 0
    for i in l2:
        sum += int(i)
    if len(l2) > 0:
        logging.info('average WaitingTime:%s ms' % str(sum / len(l2)))
        # print('average Waiting-Time:%s ms' % str(sum / len(l2)))

    return [int(i) for i in l1]  # z只返回CostTime


def test_send_get_analyze():
    """
    2019-09-01 23:30:25,572 [line:1043] [INFO] Frame:15
2019-09-01 23:30:25,572 [line:913] [INFO] Send 15---> ('192.168.0.107', 8989), [15, "a"]
2019-09-01 23:30:25,573 [line:1156] [INFO] Get 15----> ('192.168.0.107', 8989), [15, u'a']
2019-09-01 23:30:25,621 [line:1336] [INFO] CostTime:49
    :return:
    """
    with open('logger.log', 'r') as f1:
        s = f1.readlines()

    n = 0
    counts = 0
    # while True:
    #     if 'Send %d'%n in line:
    #         counts += 1


def main():
    game = Game()
    game.main()
    # while raw_input('press "r" to restart game:') == 'r':
    #     RESTART_MODE = True
    #     game.main()
    game.sock.close()
    test_calc_frame_cost()
    test_send_get_analyze()


if __name__ == '__main__':
    test_calc_frame_cost()
    test_send_get_analyze()
