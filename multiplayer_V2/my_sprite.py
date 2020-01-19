# -*- coding: utf-8 -*-

import pygame
import random

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
        self.rect.center = (round(location.x/config.GAME_RECT_RATIO),round(location.y/config.GAME_RECT_RATIO))

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
    WEAPON_CATALOG = {
        'Bullet': {
            'health': 10,
            'init_speed': 5000,
            'max_speed': 2500,
            'thrust_acc': 0,
            'turn_acc': 0,
            'damage': 2,
            'image': ['./image/gunfire.png'],
            'image_slot': './image/gunfire.png',
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
        'Pili': {
            # ...,
        }
    }

    def __init__(self, location, catalog, velocity):
        image_path = random.choice(Weapon.WEAPON_CATALOG[catalog]['image'])
        self.image_original = pygame.image.load(image_path).convert()
        self.image_original.set_colorkey(config.WHITE)
        image = self.image_original.subsurface(
            (0, 0, self.image_original.get_height() - 1, self.image_original.get_height() - 1))
        super(Weapon, self).__init__(location=location, image_surface=image)

        self.destruct_image_index = self.image_original.get_width() / self.image_original.get_height()
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
        self.acc = self.velocity.rescale_to_length(self.thrust_acc)
        self.fuel = Weapon.WEAPON_CATALOG[catalog]['fuel']

        self.velocity = velocity + velocity.rescale_to_length(self.init_speed)  # 初始速度为飞机速度+发射速度

        self.rotate()

    def rotate(self):
        pass

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
            self.acc += self.velocity.normalize_vector() * self.thrust_acc  # 加上垂直速度

        if self.fuel <= 0 or self.health <= 0:
            if self.catalog in ['Rocket', 'Cobra']:
                self.delete(hit=True)
            else:
                self.delete()
        else:
            super(Weapon, self).update()  # 正常更新
            self.fuel -= 1


class Widget:
    def __init__(self):
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

        self.box_group = pygame.sprite.Group()

    def draw(self, surface):
        self.box_group.draw(surface)

    def erase(self):
        self.box_group.clear(self.screen, self.clear_callback)

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

            xy = pygame.Vector2(random.randint(0, 3200), random.randint(0, 2400))
            # print(Box.BOX_CATALOG)
            # print(xy,random.choice(.keys()))
            self.box_group.add(Box(xy, random.choice(list(Box.BOX_CATALOG.keys()))))
            self.draw(self.screen)
            self.event_control()
        pygame.quit()


if __name__ == "__main__":
    window = Widget()
    window.main()
