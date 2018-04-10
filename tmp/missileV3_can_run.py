# -*- coding: cp936 -*-
import pygame
import os, sys
import math

BACKGROUND_COLOR = (50, 100, 255)
WHITE = (255, 255, 255)
FPS = 60


class Missile(pygame.sprite.Sprite):
    def __init__(self, position, velocity, max_acceleration_parallel=0.028284, fuel=150):
        pygame.sprite.Sprite.__init__(self)

        self.image_original = pygame.image.load('homingmissile.png').convert()
        self.image_original.set_colorkey(WHITE)
        self.image = self.image_original.copy()

        self.position = position  # [x, y]
        self.rect = self.image.get_rect(center=position)

        self.velocity = velocity  # [x, y]
        self.fuel = fuel  # 150
        self.max_acceleration_parallel = max_acceleration_parallel  # 0.28284
        self.acceleration = [0, 0]

    def update(self):
        self.acceleration = self.calc_acc()
        for i in [0, 1]:
            self.velocity[i] += self.acceleration[i]
            self.position[i] += self.velocity[i]
        self.rect.center = self.position

        self.rotate()

        self.fuel -= 1
        if self.fuel < 0:
            self.remove()

    def remove(self):
        self.kill()

    def rotate(self):
        x, y = self.velocity
        angle = math.atan2(x, y) * 360 / 2 / math.pi - 180
        self.image = pygame.transform.rotate(self.image_original, angle)

    def calc_acc(self):
        x, y = self.velocity
        a = self.max_acceleration_parallel
        v = math.sqrt(x * x + y * y)
        return [x / v * a, y / v * a]


class HomingMissile(Missile):
    def __init__(self, position, velocity, max_acceleration_vertical=0.05414, max_acceleration_parallel=0.01414,
                 fuel=250):
        Missile.__init__(self, position=position, velocity=velocity, max_acceleration_parallel=max_acceleration_parallel,
                         fuel=fuel)

        # self.target_position = target_position  # [x,y]
        self.max_acceleration_vertical = max_acceleration_vertical  # 0.05414
        self.max_acceleration_parallel = max_acceleration_parallel  # 0.01414

    def update(self, target_position=None):
        if target_position:  # [x,y]
            #  make velocity with parallel acceleration 
            self.acceleration = self.calc_acc()
            for i in [0, 1]:
                self.velocity[i] += self.acceleration[i]  #

            # calculate the angle between Vector(velocity) and Vector(target to missile position)
            x, y = self.velocity
            angle_velocity = math.atan2(y, x)
            x1, y1 = self.position
            x2, y2 = target_position
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

            self.fuel -= 1
            if self.fuel < 0:
                self.remove()
        else:
            Missile.update(self)


class Plane(pygame.sprite.Sprite):
    def __init__(self, position, velocity):
        self.positon = position
        self.velocity = velocity


class Control():
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.screen_rect = self.screen.get_rect()
        self.done = False
        self.fps = FPS
        self.clock = pygame.time.Clock()
        self.groups = pygame.sprite.Group()
        # self.groups.add(HomingMissile([10,400],(1,0)))
        self.groups.add(Missile([10, 600], [1, -1]))
        self.groups.add(Missile([10, 400], [1, -2]))
        # self.groups.add(Missile([10, 400], [2, -2]))

        self.groups_homing = pygame.sprite.Group()
        self.groups_homing.add(HomingMissile([20,40],[1,0]))
        self.groups_homing.add(HomingMissile([20,40],[1,-1]))
        # self.groups_homing.add(HomingMissile([20,40],[1,1]))
        # self.groups_homing.add(HomingMissile([20,40],[0,1]))
        # self.groups_homing.add(HomingMissile([20,40],[2,3]))
        # self.groups_homing.add(HomingMissile([20,40],[1,1.5]))

    def event_loop(self):
        for event in pygame.event.get():
            self.keys = pygame.key.get_pressed()
            if event.type == pygame.QUIT or self.keys[pygame.K_ESCAPE]:
                self.done = True

    def update(self):
        self.groups.update()
        self.groups_homing.update([500, 100])

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        pygame.draw.circle(self.screen, (0, 0, 0), [500, 100], 3)
        self.groups.draw(self.screen)
        self.groups_homing.draw(self.screen)

    def main_loop(self):
        while not self.done:
            self.event_loop()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(self.fps)


if __name__ == "__main__":
    SCREEN_SIZE = (600, 600)

    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()

    pygame.display.set_mode(SCREEN_SIZE)

    run_it = Control()
    run_it.main_loop()
    pygame.quit()
    sys.exit()
