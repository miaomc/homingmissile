# -*- coding: utf-8 -*-

import pygame
import random
import math

import config
import matrix


class Base(pygame.sprite.Sprite):
    """
    pygame.sprite.Sprite __build-in__ may be used: alive(), kill()
    location: pygame.Vector2
    matrix
    """

    def __init__(self, location, image_surface):
        super(Base, self).__init__()
        self.location = location
        self.image = image_surface
        self.rect = self.image.get_rect()
        self.rect.center = (round(location.x / config.MAP_SCREEN_RATIO), round(location.y / config.MAP_SCREEN_RATIO))

        self.index = matrix.add(self.location)

    def delete(self):
        matrix.delete(self.index)
        self.kill()


class Cloud(Base):
    CLOUD_IMAGE_LIST = ['./image/cloud1.png', './image/cloud2.png', './image/cloud3.png', './image/cloud4.png']

    def __init__(self, location):
        image_path = random.choice(Cloud.CLOUD_IMAGE_LIST)
        image = pygame.image.load(image_path).convert_alpha().convert()
        super(Cloud, self).__init__(location=location, image_surface=image)




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
        if catalog in ['Bullet', 'Rocket', 'Cobra', 'Medic']:
            self.num = Box.BOX_CATALOG[catalog]['num']
        elif catalog == 'Power':
            pass

    def effect(self, plane_object):
        if self.catalog == 'Medic':
            plane_object.change_health(self.num)
        # elif catalog == 'Power':  # 这个后面再做威力加强
        #     pass
        elif self.catalog == 'Bullet':
            plane_object.change_weapon('Bullet', self.num)
        elif self.catalog == 'Rocket':
            plane_object.change_weapon('Rocket', self.num)
        elif self.catalog == 'Cobra':
            plane_object.change_weapon('Cobra', self.num)


class Weapon(Base):
    """to be continue:
        matrix.update()
        最后进行speed等参数调节，这些数据直接作用在 MAP/location上
    """
    WEAPON_CATALOG = {
        'Bullet': {
            'health': 10,
            'init_speed': 5000,
            'max_speed': 2500,
            'thrust_acc': 0,
            'turn_acc': 0,
            'damage': 2,
            'image': ['./image/bullet.png'],
            'image_slot': './image/bullet.png',
            'image_explosion': './image/gunfire_explosion.png',
            'fuel': 80,  # 8
            'sound_collide_plane': ['./sound/bulletLtoR08.wav', './sound/bulletLtoR09.wav', './sound/bulletLtoR10.wav',
                                    './sound/bulletLtoR11.wav', './sound/bulletLtoR13.wav', './sound/bulletLtoR14.wav']
        },
        'Rocket': {
            'health': 10,
            'init_speed': 0,
            'max_speed': 8000,
            'thrust_acc': 65,
            'damage': 35,
            'turn_acc': 0,
            'image': ['./image/rocket.png'],
            'image_slot': './image/homingmissile2.png',
            'fuel': 200,
        },
        'Cobra': {
            'health': 10,
            'init_speed': 0,
            'max_speed': 4500,  # 1360
            'thrust_acc': 25,
            'turn_acc': 35,
            'damage': 25,
            'image': ['./image/homingmissile.png'],
            'image_slot': './image/homingmissile1.png',
            'fuel': 160,
            'detect_range': 10000 * 30
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

        self.destruct_image_index = self.origin_image.get_width() / self.origin_image.get_height()
        self.catalog = catalog

        if catalog == 'Bullet':
            self.sound_fire = pygame.mixer.Sound("./sound/minigun_fire.wav")
            self.sound_fire.play(maxtime=200)
            self.sound_collide_plane = pygame.mixer.Sound(
                random.choice(Weapon.WEAPON_CATALOG['Bullet']['sound_collide_plane']))
        else:  # ['Rocket','Cobra']
            self.sound_fire = pygame.mixer.Sound("./sound/TPhFi201.wav")
            self.sound_fire.play()
            self.sound_kill = pygame.mixer.Sound("./sound/ric5.wav")
            self.sound_collide_plane = pygame.mixer.Sound("./sound/shotgun_fire_1.wav")
        if catalog == 'Cobra':
            self.detect_range = Weapon.WEAPON_CATALOG[catalog]['detect_range']
            self.target = None

        self.health = Weapon.WEAPON_CATALOG[catalog]['health']
        self.damage = Weapon.WEAPON_CATALOG[catalog]['damage']
        self.init_speed = Weapon.WEAPON_CATALOG[catalog]['init_speed']
        self.max_speed = Weapon.WEAPON_CATALOG[catalog]['max_speed']
        self.turn_acc = Weapon.WEAPON_CATALOG[catalog]['turn_acc']
        self.thrust_acc = Weapon.WEAPON_CATALOG[catalog]['thrust_acc']
        self.fuel = Weapon.WEAPON_CATALOG[catalog]['fuel']

        self.velocity = velocity + velocity.normalize()*self.init_speed  # 初始速度为飞机速度+发射速度
        self.acc = self.velocity.normalize()*self.thrust_acc  # 加速度调整为速度方向

        self.rotate()

    def rotate(self):
        angle = self.velocity.angle_to(config.POLAR)
        # angle = math.atan2(self.velocity.x, self.velocity.y) * 360 / 2 / math.pi - 180  # 这个角度是以当前方向结合默认朝上的原图进行翻转的
        self.image = pygame.transform.rotate(self.unrotate_image, angle)


    def update(self, plane_group):
        if self.catalog == 'Cobra':
            """
            飞机、枪弹是一回事，加速度在不去动的情况下，为0；
            """
            if self.target and abs(self.velocity.angle_to(self.target.location - self.location)) < 60 \
                    and (self.location - self.target.location).length() < self.detect_range:
                angle_between = self.velocity.angle_to(self.target.location - self.location)/180*math.pi
                # print 'on target~',
                # 预计垂直速度的长度, 带正s负的一个float数值
                expect_acc = (self.target.location - self.location).length() * math.sin(angle_between)
                if abs(expect_acc) < self.turn_acc:  # 如果期望转向速度够了，就不用全力
                    acc = abs(expect_acc) * (1 and 0 < angle_between < math.pi or -1)
                else:  # 期望转向速度不够，使用全力转向
                    acc = self.turn_acc * (1 and 0 < angle_between < math.pi or -1)
                self.acc.x += acc * math.sin(self.velocity.angle_to(config.POLAR)/180*math.pi)
                self.acc.y += - acc * math.cos(self.velocity.angle_to(config.POLAR)/180*math.pi)
                # print 'target on:',self.target
            else:
                self.target = None
                for plane in plane_group:
                    if abs(self.velocity.angle_to(plane.location - self.location)) < 60 and \
                            (self.location - plane.location).length() < self.detect_range:
                        self.target = plane
                        break
        # print self.min_speed, self.velocity.length(), self.max_speed
        if self.min_speed < self.velocity.length() < self.max_speed:
            self.acc += self.velocity.normalize()*self.thrust_acc  # 加上垂直速度

        if self.fuel <= 0 or self.health <= 0:
            if self.catalog in ['Rocket', 'Cobra']:
                self.delete(hit=True)
            else:
                self.delete()
        else:
            # super(Weapon, self).update()  # 正常更新
            self.velocity += self.acc
            matrix.change_add(self.index, self.velocity)
            self.fuel -= 1


class Plane(Base):
    """to be continue : 飞机应该可以继承 Weapon"""
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
            'max_speed': 2400,  # 2400
            'min_speed': 540,
            'acc_speed': 50,
            'turn_acc': 25,
            'image': './image/plane_blue.png',
            'damage': 100,
        },
    }
    def __init__(self, location, catalog='J20'):
        image_path = Plane.PLANE_CATALOG[catalog]['image']
        self.origin_image = pygame.image.load(image_path).convert()
        self.origin_image.set_colorkey(config.WHITE)
        image = self.origin_image.subsurface((0, 0, 39, 39))
        # self.image = pygame.image.load(image_path).convert_alpha()  # 透明色的搞法
        self.unrotate_image = image.copy()
        super(Plane, self).__init__(location=location, image_surface=image)

        self.sound_kill = pygame.mixer.Sound("./sound/explode3.wav")

        self.max_speed = Plane.PLANE_CATALOG[catalog]['max_speed']
        self.min_speed = Plane.PLANE_CATALOG[catalog]['min_speed']
        self.turn_acc = Plane.PLANE_CATALOG[catalog]['turn_acc']
        self.acc_speed = Plane.PLANE_CATALOG[catalog]['acc_speed']
        self.damage = Plane.PLANE_CATALOG[catalog]['damage']
        self.health = Plane.PLANE_CATALOG[catalog]['health']

        self.speed = (self.max_speed + self.min_speed) / 2  # 初速度为一半
        self.velocity = pygame.Vector2(random.random(), random.random()).normalize()*self.speed  # Vector
        self.acc = pygame.Vector2(0, 0)

        self.weapon = {1: {}, 2: {}, 3: {}}  # 默认没有武器

        self.sound_kill = pygame.mixer.Sound("./sound/explode3.wav")
        self.destruct_image_index = self.origin_image.get_width() / self.origin_image.get_height()
        # self.catalog = catalog

        # self.health_bar = HealthBar(location=self.location)

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

class Bar(Base):
    def __init__(self, location, length=5, width=2, color=config.BLACK):
        self.color = color
        self.width = width
        self.length = length
        image = pygame.Surface((self.length, self.width))
        image.fill(self.color)
        image.convert()
        super(Bar, self).__init__(location=location, image=image)

    # def update(self, rect_topleft, num):
    #     self.image = self.health_surface.subsurface((0, 0, num / 5, 5))  # 默认是5的血量，对应1格血条长度
    #     self.rect.topleft = rect_topleft
    #     self.rect.move_ip(0, 50)  # 血条向下移50个像素点



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
        self.origin_screen = self.screen.copy()
        self.screen.fill(config.BACKGROUND_COLOR)
        self.clock = pygame.time.Clock()

        self.done = False

    def game_init(self):
        self.box_group = pygame.sprite.Group()
        self.weapon_group = pygame.sprite.Group()
        self.plane_group = pygame.sprite.Group()

        xy = pygame.Vector2(random.randint(0, config.MAP_SIZE[0]), random.randint(0, config.MAP_SIZE[1]))
        p1 = Plane(location=xy, catalog='F35')
        self.plane_group.add(p1)

        xy = pygame.Vector2(random.randint(0, config.MAP_SIZE[0]), random.randint(0, config.MAP_SIZE[1]))
        # print(Box.BOX_CATALOG)
        # print(xy,random.choice(.keys()))
        self.box_group.add(Box(xy, random.choice(list(Box.BOX_CATALOG.keys()))))
        # print(dir(p1))
        # print(type(p1.velocity))
        xy = p1.location+p1.velocity
        w1 = Weapon(location=xy, catalog='Bullet', velocity=p1.velocity)
        self.weapon_group.add(w1)

    def draw(self, surface):
        self.box_group.draw(surface)
        self.weapon_group.draw(surface)
        self.plane_group.draw(surface)

    def update(self):

        # self.box_group.update()
        self.weapon_group.update()
        # self.plane_group.update()
        matrix.update()

    def erase(self):
        self.box_group.clear(self.screen, self.clear_callback)
        self.weapon_group.clear(self.map.surface, self.clear_callback)
        self.plane_group.clear(self.map.surface, self.clear_callback)

    def clear_callback(self, surf, rect):
        surf.blit(source=self.origin_screen, dest=rect, area=rect)

    def event_control(self):
        for event in pygame.event.get():
            self.keys = pygame.key.get_pressed()
            if event.type == pygame.QUIT or self.keys[pygame.K_ESCAPE]:
                self.exit_func()

    def exit_func(self):
        self.done = True

    def main(self):

        while not self.done:
            pygame.display.flip()
            self.clock.tick(config.FPS)
            self.update()

            self.draw(self.screen)
            self.event_control()
        pygame.quit()


if __name__ == "__main__":
    window = Widget()
    window.main()
