# -*- coding: utf-8 -*-

import pygame
import random
import math

import config
import matrix

import time


class Base(pygame.sprite.Sprite):
    """
    pygame.sprite.Sprite __build-in__ may be used: alive(), kill()
    location: pygame.math.Vector2
    matrix
    """

    def __init__(self, location, image_surface):
        super(Base, self).__init__()
        self.image = image_surface.convert()
        self.rect = self.image.get_rect()

        self.location = pygame.math.Vector2(location)
        self.index = self.write_new(location)
        self.rect.center = self.write_out()

    def write_new(self, location):
        return matrix.add(location)

    def write_in(self, location):
        return matrix.set(self.index, location)

    def write_add(self, velocity):
        matrix.change_add(self.index, velocity)

    def write_out(self):
        self.location[:] = matrix.pos_array[self.index]
        # return self.location.astype(matrix.INT32)
        return [int(i) for i in self.location]

    def delete(self):
        matrix.delete(self.index)
        self.kill()

    def rotate(self):
        angle = self.velocity.angle_to(config.POLAR)
        self.image = pygame.transform.rotate(self.unrotate_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)


class Cloud(pygame.sprite.Sprite):
    CLOUD_IMAGE_LIST = ['./image/cloud1.png', './image/cloud2.png', './image/cloud3.png', './image/cloud4.png']

    def __init__(self, location):
        super(Cloud, self).__init__()
        image_path = random.choice(Cloud.CLOUD_IMAGE_LIST)
        self.image = pygame.image.load(image_path).convert_alpha()  # convert_alpha与convert冲突
        self.rect = self.image.get_rect()
        self.rect.center = [int(i) for i in location]


class Box(Base):
    BOX_CATALOG = {
        'Medic': {
            'image': './image/box_medic.png',
            'num': 80,
        },
        'Bullet': {
            'image': './image/box_bullet.png',
            'num': 100,
        },
        'Rocket': {
            'image': './image/box_rocket.png',
            'num': 5,
        },
        'Cobra': {
            'image': './image/box_cobra.png',
            'num': 3,
        },
        'Cluster': {
            'image': './image/box_cluster.png',
            'num': 20,
        },
    }

    # 'Power':{
    #     'image': './image/box_power.png',
    # },

    def __init__(self, location, catalog):
        image_path = Box.BOX_CATALOG[catalog]['image']
        image = pygame.image.load(image_path).convert()
        image.set_colorkey(config.WHITE)
        super(Box, self).__init__(location=location, image_surface=image)

        self.sound_kill = pygame.mixer.Sound("./sound/beep.wav")
        self.catalog = catalog
        if catalog in ['Bullet', 'Rocket', 'Cobra', 'Medic', 'Cluster']:
            self.num = Box.BOX_CATALOG[catalog]['num']
        elif catalog == 'Power':
            pass

    def effect(self, plane_object):
        if self.catalog == 'Medic':
            plane_object.change_health(self.num)
        # elif catalog == 'Power':  # 这个后面再做威力加强
        #     pass
        elif self.catalog in ['Bullet', 'Rocket', 'Cobra', 'Cluster']:
            plane_object.change_weapon(self.catalog, self.num)


class Weapon(Base):
    """ matrix.update(),最后进行speed等参数调节，这些数据直接作用在 MAP/location上 """
    WEAPON_CATALOG = {
        'Bullet': {
            'health': 10,
            'init_speed': 4,
            'max_speed': 8,
            'thrust_acc': 0,
            'turn_acc': 0,
            'damage': 2,
            'image': ['./image/bullet.png'],
            'image_slot': './image/bullet.png',
            'image_explosion': './image/gunfire_explosion.png',
            'fuel': 250,  # 8
            'sound_collide_plane': ['./sound/bulletLtoR08.wav', './sound/bulletLtoR09.wav', './sound/bulletLtoR10.wav',
                                    './sound/bulletLtoR11.wav', './sound/bulletLtoR13.wav', './sound/bulletLtoR14.wav']
        },
        'Rocket': {
            'health': 10,
            'init_speed': 0,
            'max_speed': 7,
            'thrust_acc': 0.06,
            'damage': 35,
            'image': ['./image/rocket.png'],
            'image_slot': './image/homingmissile2.png',
            'fuel': 1000,
        },
        'Cobra': {
            'health': 10,
            'init_speed': 0,
            'max_speed': 6,  # 1360
            'thrust_acc': 0.04,
            'turn_acc': 0.01,
            'damage': 55,
            'image': ['./image/homingmissile.png'],
            'image_slot': './image/homingmissile1.png',
            'fuel': 1000,
            'detect_range': 1000,
            'detect_degree': 60
        },
        # 'Pili': {
        #     # ...,
        # }
    }

    def __init__(self, location, catalog, velocity):
        image_path = random.choice(Weapon.WEAPON_CATALOG[catalog]['image'])
        self.origin_image = pygame.image.load(image_path).convert()
        self.origin_image.set_colorkey(config.WHITE)
        image = self.origin_image.subsurface(
            (0, 0, self.origin_image.get_height() - 1, self.origin_image.get_height() - 1))
        self.unrotate_image = image.copy()
        super(Weapon, self).__init__(location=location, image_surface=image)

        self.alive = True
        self.self_destruction = 0
        self.destruct_image_index = self.origin_image.get_width() / self.origin_image.get_height()
        self.sound_kill = None
        self.hit = None
        self.hitted_obj = None
        self.offset_vecter = None

        self.catalog = catalog
        if catalog == 'Bullet':
            # self.sound_fire = pygame.mixer.Sound("./sound/minigun_fire.wav")
            # self.sound_fire.play(maxtime=200)
            self.sound_collide_plane = pygame.mixer.Sound(
                random.choice(Weapon.WEAPON_CATALOG['Bullet']['sound_collide_plane']))
        else:  # ['Rocket','Cobra']
            self.sound_fire = pygame.mixer.Sound("./sound/TPhFi201.wav")
            self.sound_fire.play()
            self.sound_kill = pygame.mixer.Sound("./sound/ric5.wav")
            self.sound_collide_plane = pygame.mixer.Sound("./sound/shotgun_fire_1.wav")

        if catalog == 'Cobra':
            self.turn_acc = Weapon.WEAPON_CATALOG[catalog]['turn_acc']
            self.detect_range = Weapon.WEAPON_CATALOG[catalog]['detect_range']
            self.detect_degree = Weapon.WEAPON_CATALOG[catalog]['detect_degree']

        self.target = None  # 跟踪对象

        self.health = Weapon.WEAPON_CATALOG[catalog]['health']
        self.damage = Weapon.WEAPON_CATALOG[catalog]['damage']
        self.init_speed = Weapon.WEAPON_CATALOG[catalog]['init_speed']
        self.max_speed = Weapon.WEAPON_CATALOG[catalog]['max_speed']
        self.thrust_acc = Weapon.WEAPON_CATALOG[catalog]['thrust_acc']
        self.fuel = Weapon.WEAPON_CATALOG[catalog]['fuel']

        self.velocity = velocity + velocity.normalize() * self.init_speed  # 初始速度为飞机速度+发射速度
        self.write_add(self.velocity)

        # self.acc = self.velocity.normalize()*self.thrust_acc  # 加速度调整为速度方向
        self.acc = pygame.math.Vector2((0, 0))
        self.rotate()

    # def rotate(self):
    #     angle = self.velocity.angle_to(config.POLAR)
    #     # angle = math.atan2(self.velocity.x, self.velocity.y) * 360 / 2 / math.pi - 180  # 这个角度是以当前方向结合默认朝上的原图进行翻转的
    #     self.image = pygame.transform.rotate(self.unrotate_image, angle)

    def detect_target(self, target):
        """degree:向前方扫描的半个张角 120/2 = 60"""
        _degree = abs(self.velocity.angle_to(target.location - self.location))
        _range = (self.location - target.location).length()
        return _degree < self.detect_degree and _range < self.detect_range

    def update(self, target_group=None):
        # 专门处理推进加速度
        if self.catalog != 'Bullet' and self.velocity.length() < self.max_speed:
            self.acc = self.velocity.normalize() * self.thrust_acc  # 加上垂直速度
            # print(self.acc)
        # 专门处理转向加速度
        if self.catalog == 'Cobra':
            """
            飞机、枪弹是一回事，加速度在不去动的情况下，为0；
            """
            if self.target and self.detect_target(self.target):
                # Vector2.angle_to 是顺时针,[0,180]and[-360,-180]就顺时针旋转90度
                _degree = self.velocity.angle_to(self.target.location - self.location)
                if 0 < _degree < 180 or -360 < _degree < -180:
                    self.acc += self.velocity.rotate(90).normalize() * self.turn_acc  # 由于是全力加速，有可能加过头而打不中
                else:
                    self.acc += self.velocity.rotate(-90).normalize() * self.turn_acc
            else:  # 探索新target
                self.target = None
                # self.acc = pygame.math.Vector2(0, 0)  # 如果
                for plane in target_group:
                    if self.detect_target(target=plane):
                        self.target = plane
                        # if self.target:
                        #     print(id(self.target))
                        break
        # print self.min_speed, self.velocity.length(), self.max_speed
        if self.acc != pygame.math.Vector2((0, 0)):
            self.velocity += self.acc  # 在1000个object的时候需要2ms
            self.write_add(self.velocity)  # [COST]在1000个object的时候需要30ms
        # print(self.location, self.velocity, self.acc, self.velocity * self.acc)
        # print(matrix.pos_array[self.index],matrix.add_array[self.index])

        if self.fuel <= 0 or self.health <= 0:
            if self.catalog in ['Rocket', 'Cobra']:
                self.delete(hit=True)
            else:
                self.delete()
        else:
            # super(Weapon, self).update()  # 正常更新
            self.rotate()
            self.fuel -= 1

    def hitted(self, base):
        self.health -= base.damage
        base.health -= self.damage
        if self.catalog == 'Bullet' and isinstance(base, Plane):
            self.sound_collide_plane.play()
            self.delete(hit=True, hitted_obj=base)
        elif self.catalog in ['Rocket', 'Cobra'] and isinstance(base, Plane):
            self.sound_collide_plane.play()
            self.delete(hit=True, hitted_obj=base)

    # def hitted(self, base_lst):
    #     for base in base_lst:
    #         if id(self) == id(base):  # spritecollide如果是自己和自己就不需要碰撞了
    #             continue
    #         # print base.rect, self.rect
    #         self.health -= base.damage
    #         base.health -= self.damage
    #         if self.catalog == 'Bullet' and isinstance(base, Plane):
    #             self.sound_collide_plane.play()
    #             self.delete(hit=True, hitted_obj=base)
    #         elif self.catalog in ['Rocket', 'Cobra'] and isinstance(base, Plane):
    #             self.sound_collide_plane.play()
    #             self.delete(hit=True, hitted_obj=base)

    def delete(self, hit=False, hitted_obj=None):
        """hit用来判断是否是击中，用来触发爆炸特效"""
        if self.alive:  # 第一次进行的操作
            self.alive = False
            self.hit = hit
            self.hitted_obj = hitted_obj
            # if self.sound_kill:
            #     self.sound_kill.play()
            if hitted_obj:
                self.offset_vecter = (self.rect.x - hitted_obj.rect.x) // 3, (self.rect.y - hitted_obj.rect.y) // 3

        # 启动自爆动画
        self.self_destruction += 0.5
        if self.hit and self.self_destruction < self.destruct_image_index:
            self.unrotate_image = self.origin_image.subsurface(
                [self.self_destruction //
                 1 * self.origin_image.get_height(), 0, self.origin_image.get_height() - 1,
                 self.origin_image.get_height() - 1])
            self.rotate()
            if self.hitted_obj:  # 被撞击的对象，跟着被撞击的对象移动-Plane
                self.rect.center = self.hitted_obj.rect.center
                self.rect.move_ip(self.offset_vecter[0], self.offset_vecter[1])
            return False
        else:
            super(Weapon, self).delete()
            return True


class ClusterWeapon(pygame.sprite.Sprite):
    FUEL = config.FPS*4
    VELOCITY = 2
    BULLETS = 100
    BULLETS_VELOCITY = 6

    def __init__(self, location, velocity):
        super(ClusterWeapon, self).__init__()
        self.location = location
        self.image = pygame.image.load('./image/clustermissile.png').convert()
        self.image.set_colorkey(config.WHITE)

        self.unrotate_image = self.image.copy()
        self.rect = self.image.get_rect()
        self.location = location
        self.rect.center = [int(i) for i in location[:]]


        self.fuel = ClusterWeapon.FUEL
        self.velocity = velocity + velocity.normalize() * ClusterWeapon.VELOCITY
        self.sound_split = pygame.mixer.Sound("./sound/shotgun_fire_1.wav")

        self.catalog = 'Cluster'
        self.hit = True
        self.health = 10
        self.damage = 1
        self.rotate()

    def update(self, target_group=None):
        self.fuel -= 1
        if self.fuel <= 0:
            self.delete()
        self.location += self.velocity
        self.rect.center = [int(i) for i in self.location[:]]
        self.rotate()

    def hitted(self, base):
        self.health -= base.damage
        base.health -= self.damage
        self.delete()

    def delete(self):
        base_velocity_list = [pygame.math.Vector2(1, 0).normalize()*i for i in range(1,ClusterWeapon.BULLETS_VELOCITY+1)]
        weapon_group = self.groups()[0]
        for i in range(ClusterWeapon.BULLETS):
            weapon_group.add(
                Weapon(location=self.location, catalog='Bullet',
                       velocity=random.choice(base_velocity_list).rotate(random.randint(0, 360))))
        self.sound_split.play()
        self.kill()

    def rotate(self):
        angle = self.velocity.angle_to(config.POLAR)
        self.image = pygame.transform.rotate(self.unrotate_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)


class Plane(Base):
    """to be continue : 飞机应该可以继承 Weapon"""
    PLANE_CATALOG = {
        'J20': {
            'health': 200,
            'max_speed': 10,
            'min_speed': 0.5,
            'thrust_acc': 0.6,
            'turn_acc': 0.35,  # 20
            'image': ['./image/plane_red.png'],
            'damage': 100,
        },
        'F35': {
            'health': 400,
            'max_speed': 5,  # 2400
            'min_speed': 2,
            'thrust_acc': 0.03,
            'turn_acc': 0.03,
            'image': config.PLANE_IMAGE,  # dict = {'COLOR':'path',..}
            'damage': 100,
        },
    }

    def __init__(self, location, catalog='J20', color=None):
        if color:
            image_path = Plane.PLANE_CATALOG[catalog]['image'][color]
        else:
            # print(Plane.PLANE_CATALOG[catalog]['image'])
            image_path = random.choice(list(Plane.PLANE_CATALOG[catalog]['image'].values()))
        self.origin_image = pygame.image.load(image_path).convert()
        self.origin_image.set_colorkey(config.WHITE)
        image = self.origin_image.subsurface(
            (0, 0, self.origin_image.get_height() - 1, self.origin_image.get_height() - 1))
        # self.image = pygame.image.load(image_path).convert_alpha()  # 透明色的搞法
        self.unrotate_image = image.copy()
        super(Plane, self).__init__(location=location, image_surface=image)

        self.alive = True
        self.self_destruction = 0
        self.destruct_image_index = self.origin_image.get_width() / self.origin_image.get_height()
        self.sound_kill = pygame.mixer.Sound("./sound/explode3.wav")

        self.catalog = catalog
        self.max_speed = Plane.PLANE_CATALOG[catalog]['max_speed']
        self.min_speed = Plane.PLANE_CATALOG[catalog]['min_speed']
        self.turn_acc = Plane.PLANE_CATALOG[catalog]['turn_acc']
        self.thrust_acc = Plane.PLANE_CATALOG[catalog]['thrust_acc']
        self.damage = Plane.PLANE_CATALOG[catalog]['damage']
        self.health = Plane.PLANE_CATALOG[catalog]['health']

        self.speed = (self.min_speed + self.max_speed) / 2  # 初速度为一半
        # self.velocity = pygame.math.Vector2(random.random(), random.random()).normalize() * self.speed  # Vector
        self.velocity = pygame.math.Vector2(1, 0).normalize() * self.speed  # Vector
        self.acc = pygame.math.Vector2(0, 0)

        # self.weapon = {1: {'catalog': 'Bullet', 'number': 0},
        #                2: {'catalog': 'Rocket', 'number': 0},
        #                3: {'catalog': 'Cobra', 'number': 0},
        #                4: {'catalog': 'Cluster', 'number': 0}}  # 默认武器为0
        self.weapon = {'Bullet': 0, 'Rocket':0,'Cobra': 0,'Cluster': 0}

        self.sound_kill = pygame.mixer.Sound("./sound/explode3.wav")
        # self.healthbar = HealthBar(location=self.location)

    def add_healthbar(self, healthbar):
        self.healthbar = healthbar  # 把self.healthbar加进来的目的就是为了可以kill()

    def turn_left(self):
        self.acc += self.velocity.rotate(-90).normalize() * self.turn_acc

    def turn_right(self):
        self.acc += self.velocity.rotate(90).normalize() * self.turn_acc

    def speedup(self):
        acc_tmp = self.acc + self.velocity.normalize() * self.thrust_acc
        if (self.velocity + acc_tmp).length() < self.max_speed:
            self.acc = acc_tmp

    def speeddown(self):
        acc_tmp = self.acc - self.velocity.normalize() * self.thrust_acc
        if (self.velocity - acc_tmp).length() > self.min_speed:
            self.acc = acc_tmp

    def change_health(self, num):
        self.health += num

    def load_weapon(self, catalog='Cobra', number=6):
        """self.weapon = {1: {'catalog': 'Bullet', 'number': 200},
        2: {'catalog': 'Rocket', 'number': 20},
        3: {'catalog': 'Cobra', 'number': 10}} """
        # index = 3  # 默认为非Gun子弹和Rocket火箭弹的其他类
        # if catalog == 'Bullet':
        #     index = 1
        # elif catalog == 'Rocket':
        #     index = 2
        # elif catalog == 'Cobra':
        #     index = 3
        # elif catalog == 'Cluster':
        #     index = 4
        # self.weapon[index]['catalog'] = catalog
        # self.weapon[index]['number'] = number
        # # print(self.weapon, catalog, number)
        self.weapon[catalog] = number

    def change_weapon(self, catalog, number):
        # print(self.weapon,catalog,number)
        # if catalog == 'Bullet':
        #     self.weapon[1]['number'] += number
        # elif catalog == 'Rocket':
        #     self.weapon[2]['number'] += number
        # elif catalog == 'Cobra':
        #     self.weapon[3]['number'] += number
        self.weapon[catalog] += number

    def weapon_fire(self, slot):
        pass
        # print 'Plane:', self.plane.velocity
        # if self.plane.weapon[slot]:
        #     if self.plane.weapon[slot]['number'] > 0:
        #         self.plane.weapon[slot]['number'] -= 1
        #         # print dir(self.plane)
        #         tmp_rect = Map.mars_unti_translate((
        #             self.plane.velocity.normalize_vector().x * self.plane.rect.height,
        #             self.plane.velocity.normalize_vector().y * self.plane.rect.height))
        #         location_x = self.plane.location.x + tmp_rect[0]
        #         location_y = self.plane.location.y + tmp_rect[1]
        #         # print location_x,location_y, '<------------', self.plane.location, self.plane.rect
        #         weapon = Weapon(catalog=self.plane.weapon[slot]['catalog'],
        #                         location=(location_x, location_y),
        #                         velocity=self.plane.velocity)
        #         self.weapon_group.add(weapon)
        #         return weapon

    def update(self):
        # print(self.velocity.length(), self.velocity, self.acc, self.velocity*self.acc,self.velocity+self.acc)
        self.velocity += self.acc

        self.acc = pygame.math.Vector2((0, 0))
        self.write_in(self.location)
        self.write_add(self.velocity)
        self.rotate()
        # self.healthbar.update(rect_topleft=self.rect.topleft, health=self.health)
        # if not self.alive:  # 如果挂了,就启动自爆动画
        #     self.healthbar.delete()  # 删除血条
        #     super(Plane, self).update()
        #     return self.delete(hit=True)
        #
        # # super(Plane, self).update()
        # self.healthbar.update(rect_topleft=self.rect.topleft, num=self.health)  # 更新血条
        # # self.health -= 50
        if self.health <= 0:
            self.healthbar.kill()  # 把self.healthbar加进来的目的就是为了可以kill()
            self.delete()
        #     # if self.last_health_rect:  # 最后删除血条
        #     #     surface.blit(source=self.health_surface, dest=self.last_health_rect)
        #     #     self.last_health_rect=pygame.Rect(self.rect.left, self.rect.top+self.rect.height+10, self.rect.width*(self.health*1.0/200), 5)
        #     return self.delete(hit=True)

    def delete(self):
        if self.alive:  # 第一次进行的操作
            # self.kill()  # remove the Sprite from all Groups
            self.alive = False
            if self.sound_kill:
                self.sound_kill.play()

        # 启动自爆动画
        self.self_destruction += 0.25
        if self.self_destruction < self.destruct_image_index:
            self.unrotate_image = self.origin_image.subsurface(
                [self.self_destruction //
                 1 * self.origin_image.get_height(), 0, self.origin_image.get_height() - 1,
                 self.origin_image.get_height() - 1])
            self.rotate()
            return False
        else:
            super(Plane, self).delete()
            return True

    def draw_health(self, surface):
        pass
        # # """sprite.Group()是单独blit的"""


# class Bar(Base):
#     def __init__(self, location, length=5, width=2, color=config.BLACK):
#         self.color = color
#         self.width = width
#         self.length = length
#         image = pygame.Surface((self.length, self.width))
#         image.fill(self.color)
#         image.convert()
#         super(Bar, self).__init__(location=location, image=image)

class SlotBar(pygame.sprite.Sprite):
    COLOR_LIST = ((50, 200, 50), (50, 150, 150), (100, 100, 50), (200, 0, 50), (255, 0, 0), (0, 255, 0))
    # LEN_COLOR_LIST = len(COLOR_LIST)
    FULL_HEALTH = 100
    FULL_LENGTH = 100
    MAX_LENGTH = FULL_LENGTH * 5
    FULL_WIDTH = 10

    def __init__(self, rect_topleft):  # , health=100):
        self.origin_image = pygame.Surface((SlotBar.MAX_LENGTH, SlotBar.FULL_WIDTH)).convert()
        super(SlotBar, self).__init__()
        self.health = -1
        self.rect_topleft = rect_topleft
        # self.rect = self.origin_image.get_rect()

        # self.rect = pygame.Rect((0,0,0,0))
        # self.rect.topleft = rect_topleft
        # self.update()

    def update(self, health):
        if health != self.health:
            self.health = health
            # Set subsuface of self
            _length = int(self.health / self.FULL_HEALTH * self.FULL_LENGTH)
            if _length > self.MAX_LENGTH:
                _length = self.MAX_LENGTH
            elif _length < 0:
                _length = 0
            self.image = self.origin_image.subsurface((0, 0, _length, self.FULL_WIDTH))
            self.rect = self.image.get_rect()
            # Set color of self
            _color_index = int(self.health / self.FULL_HEALTH * len(self.COLOR_LIST) - 1)
            if _color_index > len(self.COLOR_LIST) - 1:
                _color_index = len(self.COLOR_LIST) - 1
            elif _color_index < 0:
                _color_index = 0
            self.image.fill(self.COLOR_LIST[_color_index])
            self.rect.topleft = self.rect_topleft


class HealthBar(SlotBar):
    COLOR_LIST = (config.DARK_RED,config.RED, config.ORANGE,config.LIGHT_GREEN, config.GREEN)

    #(255, 0, 0),(50, 150, 150),(100, 100, 50),(200, 0, 50),(0, 255, 0),(50, 200, 50))
    FULL_HEALTH = 400
    FULL_WIDTH = 5
    FULL_LENGTH = 40
    MAX_LENGTH = FULL_LENGTH * 2

    def __init__(self, stick_obj):
        self.stick_obj = stick_obj
        rect_topleft = self.stick_obj.rect.topleft
        # health = self.stick_obj.health
        super(HealthBar, self).__init__(rect_topleft=rect_topleft)
        self.update()  # !!!

    def update(self):
        rect_topleft = self.stick_obj.rect.topleft
        health = self.stick_obj.health
        # health = stick_obj
        # super(HealthBar,self).update(health)
        super(HealthBar, self).update(health=health)
        self.rect.topleft = rect_topleft


class ThrustBar(pygame.sprite.Sprite):
    RECT_LIST = ((5, 2), (4, 2), (3, 2), (2, 2), (1, 2), (1, 1))
    COLOR_LIST = (
    (255, 244, 237), (200, 213, 255), (181, 199, 255), (172, 192, 255), (167, 188, 255), (164, 186, 255), (255, 51, 0))
    MAX_HEALTH = 30
    LEN_RECT_LIST = len(RECT_LIST)
    LEN_COLOR_LIST = len(COLOR_LIST)

    def __init__(self, sprite_obj):
        """sprite_obj has member: .origin_image.get_height(), .location, .velocity"""
        self.health = 0
        self.angle = sprite_obj.velocity.angle_to(config.POLAR)
        _diff = rotate_around(sprite_obj.origin_image.get_height() / 2, self.angle)
        self.location = [int(sprite_obj.location[0] + _diff[0]), int(sprite_obj.location[1] + _diff[1])]
        # self.location = [int(i) for i in location]
        super(ThrustBar, self).__init__()
        self.update()
        # self.rect.center = [int(i) for i in self.location]

    def update(self):
        if self.health >= ThrustBar.MAX_HEALTH:
            self.delete()
        else:
            rect_index = int(self.health / ThrustBar.MAX_HEALTH * ThrustBar.LEN_RECT_LIST)
            color_index = int(self.health / ThrustBar.MAX_HEALTH * ThrustBar.LEN_COLOR_LIST)
            self.image = pygame.Surface(ThrustBar.RECT_LIST[rect_index]).convert()
            self.image.fill(ThrustBar.COLOR_LIST[color_index])
            self.rect = self.image.get_rect()
            self.rect.center = self.location
            # self.rect.size = (40,40)
            # print(self.rect)
            self.rotate()
            self.health += 1

    def rotate(self):
        self.image = pygame.transform.rotate(self.image, self.angle)

    def delete(self):
        self.kill()


def rotate_around(r, angle):
    # print(angle-180)
    x = + r * math.sin(math.radians(angle))
    y = + r * math.cos(math.radians(angle))
    # x = math.cos(math.radians(angle))*point[0] - math.sin(math.radians(angle))*point[1]
    # y = math.sin(math.radians(angle))*point[0] + math.cos(math.radians(angle))*point[1]
    return (x, y)


class Widget:
    def __init__(self):
        self.screen_init()
        self.game_init()

    def screen_init(self):

        import os
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        pygame.mixer.init()  # 声音初始化
        pygame.display.set_mode(config.SCREEN_SIZE)
        # pygame.mouse.set_visible(False)

        self.screen = pygame.display.get_surface()
        self.screen.fill(config.BACKGROUND_COLOR)
        self.origin_screen = self.screen.copy()
        # self.screen.fill(config.BACKGROUND_COLOR)  # 暂时不提前----测试
        self.clock = pygame.time.Clock()

        self.done = False
        self.frame = 0

    def game_init(self):

        self.box_group = pygame.sprite.Group()
        self.weapon_group = pygame.sprite.Group()
        self.plane_group = pygame.sprite.Group()
        self.healthbar_group = pygame.sprite.Group()
        self.thrustbar_group = pygame.sprite.Group()
        self.game_groups = [self.box_group, self.weapon_group, self.plane_group, self.healthbar_group,
                            self.thrustbar_group]

        xy = pygame.math.Vector2(random.randint(config.MAP_SIZE[0] // 8, config.MAP_SIZE[0] * 2 // 8),
                                 random.randint(config.MAP_SIZE[1] // 3, config.MAP_SIZE[1] * 2 // 3))
        # print(Box.BOX_CATALOG)
        # print(xy,random.choice(.keys()))
        self.box_group.add(Box(xy, random.choice(list(Box.BOX_CATALOG.keys()))))
        for i in range(1):
            xy = pygame.math.Vector2(random.randint(config.MAP_SIZE[0] // 10, config.MAP_SIZE[1]),
                                     random.randint(config.MAP_SIZE[1] // 10, config.MAP_SIZE[1]))
            p1 = Plane(location=xy, catalog='F35')
            self.plane_group.add(p1)
            h1 = HealthBar(rect_topleft=p1.rect.topleft, health=100)
            p1.add_healthbar(h1)
            self.healthbar_group.add(h1)
        # print((config.MAP_SIZE[0]/3, config.MAP_SIZE[1]*2/3))
        # print(dir(p1))
        # print(type(p1.velocity))
        self.test_xy = xy = p1.location
        self.test_v = p1.velocity
        self.test_p = p1
        w1 = Weapon(location=xy, catalog='Bullet', velocity=p1.velocity)
        self.weapon_group.add(w1)
        w1 = Weapon(location=xy, catalog='Rocket', velocity=p1.velocity)
        self.weapon_group.add(w1)
        for i in range(1):
            w1 = Weapon(location=xy, catalog='Cobra', velocity=self.test_v.rotate(random.randint(0, 360)))
            self.weapon_group.add(w1)

    def add_thrustbar(self, sprite_group):
        for _sprite in sprite_group:
            t1 = ThrustBar(_sprite)
            self.thrustbar_group.add(t1)

    def draw(self, surface):
        for _group in self.game_groups:
            _group.draw(surface)

    def update(self):
        self.frame += 1
        # self.t1 = time.time()
        # w1 = Weapon(location=self.test_xy, catalog='Bullet', velocity=self.test_v.rotate(random.randint(0,360)))
        # self.weapon_group.add(w1)

        # self.t2 = time.time()
        # self.box_group.update()
        # print(self.game_groups)
        for _group in self.game_groups:
            if id(_group) == id(self.weapon_group):
                _group.update(self.plane_group)
            elif id(_group) == id(self.healthbar_group):
                continue
            else:
                # print(type(_group))
                # for i in _group:
                #     print(type(i))
                _group.update()

        if self.frame % 2 == 0:
            self.add_thrustbar(self.plane_group)
            for _sprite in self.weapon_group:
                if _sprite.catalog in ['Rocket', 'Cobra']:
                    self.thrustbar_group.add(ThrustBar(_sprite))
                    # print(_sprite.location)

            # self.add_thrustbar(self.weapon_group)

        # self.t3 = time.time()
        matrix.update()  # 基本上不花时间

        # self.t4 = time.time()
        for _sprite in self.weapon_group:  # 读取1000个对象大约花5ms
            _sprite.rect.center = _sprite.write_out()
            # print('M:',_sprite.location)

            # print(matrix.pos_array[0:3])
        for _sprite in self.plane_group:  # 读取1000个对象大约花5ms
            _sprite.rect.center = _sprite.write_out()
            # print('P:',_sprite.location)
        # self.t5 = time.time()
        # print()
        pygame.draw.rect(self.screen, (255, 0, 0), self.test_p.rect, 1)

    def erase(self):
        for _group in self.game_groups:
            _group.clear(self.screen, self.clear_callback)

    def clear_callback(self, surf, rect):
        surf.blit(source=self.origin_screen, dest=rect, area=rect)

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
            if keys[pygame.K_ESCAPE]:
                self.exit_func()
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
            if keys[pygame.K_TAB]:
                if self.syn_frame - self.last_tab_frame > self.fps / 4:
                    self.last_tab_frame = self.syn_frame
                    self.hide_result = not self.hide_result  # 需要设置KEYUP和KEYDONW，to be continue...!!!!

            for keyascii in [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_i, pygame.K_o, pygame.K_p]:
                if keys[keyascii]:
                    key_list += chr(keyascii)
        return key_list

    def exit_func(self):
        self.done = True

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

            elif key == 'i':
                self.weapon_fire(1)
            elif key == 'o' and syn_frame - self.fire_status[2] > config.FPS:
                self.fire_status[2] = syn_frame
                return self.weapon_fire(2)
            elif key == 'p' and syn_frame - self.fire_status[3] > config.FPS:
                self.fire_status[3] = syn_frame
                return self.weapon_fire(3)

    def main(self):
        # 绘制文字
        cur_font = pygame.font.SysFont("arial", 15)
        i = 0
        while not self.done:
            i += 1
            self.erase()
            self.draw(self.screen)
            key_list = self.event_control()
            for _key in key_list:
                if _key == 'a':
                    self.test_p.turn_left()
                elif _key == 'd':
                    self.test_p.turn_right()
                elif _key == 'w':
                    self.test_p.speedup()
                elif _key == 's':
                    self.test_p.speeddown()
            self.clock.tick(config.FPS)
            self.screen.blit(cur_font.render(str(i) + '-' + str(self.clock.get_fps()), 1, config.BLACK, config.WHITE),
                             (10, 10))
            self.update()
            # self.screen.blit(cur_font.render(str(i) + '-' + str(self.t5 - self.t4),1, config.BLACK, config.WHITE), (40, 40))
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    window = Widget()
    window.main()
