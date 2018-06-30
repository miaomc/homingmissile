# -*- coding: cp936 -*-
import math
import pygame

WHITE = (255, 255, 255)


class Missile(pygame.sprite.Sprite):
    def __init__(self, position, velocity, max_acceleration_parallel=0.028284, fuel=1500):
        pygame.sprite.Sprite.__init__(self)

        self.image_original = pygame.image.load('./image/homingmissile.png').convert()
        self.image_original.set_colorkey(WHITE)
        self.image = self.image_original.copy()

        self.sound_fire = pygame.mixer.Sound("./sound/TPhFi201.wav")
        self.sound_fire.play()

        self.position = position  # [x, y]
        self.rect = self.image.get_rect(center=position)

        self.velocity = velocity  # [x, y]
        self.fuel = fuel  # 150
        self.max_acceleration_parallel = max_acceleration_parallel  # 0.28284
        self.acceleration = [0, 0]

        self.activated_value = 0

        self.rotate()

    def activated(self):
        """是否激活武器,如果激活则在碰撞检测. 要发射完一阵子之后才能生效，要不然一发射就炸到自己."""
        if self.activated_value > 50:
            return True
        else:
            return False

    def update(self):
        self.acceleration = self.calc_acc()
        for i in [0, 1]:
            self.velocity[i] += self.acceleration[i]
            self.position[i] += self.velocity[i]
        self.rect.center = self.position

        self.rotate()

        self.fuel -= 1
        if self.fuel < 0:
            self.kill()

        self.activated_value += 1  # 用来计算发射多久了

    def rotate(self):
        x, y = self.velocity
        angle = math.atan2(x, y) * 360 / 2 / math.pi - 180
        self.image = pygame.transform.rotate(self.image_original, angle)

    def calc_acc(self):
        x, y = self.velocity
        a = self.max_acceleration_parallel
        v = math.sqrt(x * x + y * y)
        return [x / v * a, y / v * a]


class Homing_Missile(Missile):
    def __init__(self, position, velocity, max_acceleration_vertical=0.05414, max_acceleration_parallel=0.01414,
                 fuel=250, target_object=None):
        Missile.__init__(self, position=position, velocity=velocity,
                         max_acceleration_parallel=max_acceleration_parallel, fuel=fuel)

        # self.target_position = target_position  # [x,y]
        self.target_object = target_object
        self.max_acceleration_vertical = max_acceleration_vertical  # 0.01414
        self.max_acceleration_parallel = max_acceleration_parallel  # 0.01414

    def update(self, target_position=None):
        if self.target_object:
            if hasattr(self.target_object,'position'):
                target_position = self.target_object.position
        
        if target_position:  # [x,y]
            #  make velocity with parallel acceleration 
            self.acceleration = self.calc_acc()
            for i in [0, 1]:
                self.velocity[i] += self.acceleration[i]

            # calculate the angle between Vector(velocity) and Vector(target to missile position)
            x, y = self.velocity
            angle_velocity = math.atan2(y, x)
            x1, y1 = self.position
            x2, y2 = target_position
            angle_2target = math.atan2(y2 - y1, x2 - x1)
            angle_between = -angle_2target + angle_velocity

            # calculate the vertical acceleration whether reach the target
            expect_acc = math.tan(angle_between) * math.sqrt(x * x + y * y)
            if abs(expect_acc) < self.max_acceleration_vertical:
                acc = abs(expect_acc) * (1 and 0 < angle_between < math.pi or -1)
            else:
                acc = self.max_acceleration_vertical * (1 and 0 < angle_between < math.pi or -1)

            # modify the velocity
            x += math.sin(angle_velocity) * acc
            y += -math.cos(angle_velocity) * acc
            self.velocity = [x, y]

            # modify the position
            self.position[0] += self.velocity[0]
            self.position[1] += self.velocity[1]
            self.rect.center = self.position

            self.rotate()

            self.fuel -= 1
            if self.fuel < 0:
                self.kill()
            self.activated_value += 1  # 用来计算发射多久了
        else:
            Missile.update(self)

    def activated(self):
        """是否激活武器,如果激活则在碰撞检测. 要发射完一阵子之后才能生效，要不然一发射就炸到自己."""
        if self.activated_value > 80:
            return True
        else:
            return False


class Plane(pygame.sprite.Sprite):
    """
    之前的trace思路没有写了,参考plane_ABSTRACT2.py中的Plane
    """
    MAX_PLANE_IMAGE_INDEX = 8

    def __init__(self, position, velocity, max_acceleration_vertical=0.01414,
                 max_acceleration_parallel=0, plane_image='./image/plane_blue.png', weapons = {'missile': 20, 'homing_missile': 2}):
        pygame.sprite.Sprite.__init__(self)

        self.image_original = pygame.image.load(plane_image).convert()  # 设置飞机图案 320*40 = 40*40 * MAX_PLANE_IMAGE_INDEX
        self.image_original.set_colorkey(WHITE)
        # self.image = self.image_original.copy()[]
        self.image = self.image_original.subsurface((0,0,39,39))
        self.image_normal = self.image_original.subsurface((0,0,39,39))  # 正常情况下的原图

        self.position = position  # [x, y]
        self.rect = self.image.get_rect(center=position)  # 根据这个位置进行刷新
        # print self.rect

        self.velocity = velocity  # 恒定的
        self.acceleration = [0, 0]  # 没有加速度指导列表的时候，加速度默认为0

        self.max_acceleration_vertical = max_acceleration_vertical  # 0.00000
        self.max_acceleration_parallel = max_acceleration_parallel  # 0.01414
        self.target_position = None  # [x,y]  目的地坐标

        self.weapons = weapons

        self.alive = True  # 是否还活着
        self.self_destruction = 0

        self.sound_hit = pygame.mixer.Sound("./sound/TTaHit00.wav")

        self.rotate()

    def calc_acc(self):
        x, y = self.velocity
        a = self.max_acceleration_parallel
        v = math.sqrt(x * x + y * y)
        return [x / v * a, y / v * a]

    def update(self):
        if not self.alive:  # 如果挂了,就启动自爆动画
            self.delete()
            return

        if self.target_position:  # [x,y]
            #  make velocity with parallel acceleration
            self.acceleration = self.calc_acc()
            for i in [0, 1]:
                self.velocity[i] += self.acceleration[i]  #

            # calculate the angle between Vector(velocity) and Vector(target to missile position)
            x, y = self.velocity
            angle_velocity = math.atan2(y, x)
            x1, y1 = self.position
            x2, y2 = self.target_position
            angle_2target = math.atan2(y2 - y1, x2 - x1)
            angle_between = -angle_2target + angle_velocity  # 算出二者的角度:飞机速度矢量, 目标矢量

            # calculate the vertical acceleration whether reach the target
            expect_acc = math.tan(angle_between) * math.sqrt(x * x + y * y)  # 期望的一步到位加速度
            if abs(expect_acc) < self.max_acceleration_vertical:
                acc = abs(expect_acc) * (1 and 0 < angle_between < math.pi or -1)  # 够了就少一点垂直加速度
            else:
                acc = self.max_acceleration_vertical * (1 and 0 < angle_between < math.pi or -1)  # 不够就全力

            # modify the velocity
            x += math.sin(angle_velocity) * acc
            y += -math.cos(angle_velocity) * acc
            self.velocity = [x, y]

        # modify the position
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        self.rect.center = self.position

        self.rotate()

    def rotate(self):
        x, y = self.velocity
        angle = math.atan2(x, y) * 360 / 2 / math.pi - 180  # 这个角度是以当前方向结合默认朝上的原图进行翻转的
        #print angle,x,y
        self.image = pygame.transform.rotate(self.image_normal, angle)

    def delete(self):
        if self.alive:  # 第一次进行的操作
            self.alive = False
            self.sound_hit.play()

        # 启动自爆动画    
        self.self_destruction += 0.5
        #print self.self_destruction
        if self.self_destruction < self.MAX_PLANE_IMAGE_INDEX:
            #print [self.self_destruction//2*40, 0, 39, 39],self.self_destruction,self.image.get_rect()
            self.image = self.image_original.subsurface([self.self_destruction//2*40, 0, 39, 39])
            return False
        else:
            self.kill()
            return True
