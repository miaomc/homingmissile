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
        angle = math.atan2(x, y) * 360 / 2 / math.pi
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
        self.max_acceleration_vertical = max_acceleration_vertical  # 0.01414
        self.max_acceleration_parallel = max_acceleration_parallel  # 0.01414

    def update(self, target_position=None):
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
                self.remove()
        else:
            Missile.update(self)


class Plane(pygame.sprite.Sprite):
    """
    之前的trace思路没有写了,参考plane_ABSTRACT2.py中的Plane
    """

    def __init__(self, position, velocity,max_acceleration_vertical=0.01414,max_acceleration_parallel=0):
        pygame.sprite.Sprite.__init__(self)

        self.image_original = pygame.image.load('plane.png').convert()  # 设置飞机图案
        self.image_original.set_colorkey(WHITE)
        self.image = self.image_original.copy()

        self.position = position  # [x, y]
        self.rect = self.image.get_rect(center=position)  # 根据这个位置进行刷新

        self.velocity = velocity  # 恒定的
        self.acceleration = [0, 0]  # 没有加速度指导列表的时候，加速度默认为0

        self.max_acceleration_vertical = max_acceleration_vertical  # 0.00000
        self.max_acceleration_parallel = max_acceleration_parallel  # 0.01414
        self.target_position = None  # [x,y]  目的地坐标

    def calc_acc(self):
        x,y = self.velocity
        a = self.max_acceleration_parallel
        v = math.sqrt(x*x + y*y)
        return [x/v*a, y/v*a]

    def update(self):
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

    def remove(self):
        self.kill()

    def rotate(self):
        x, y = self.velocity
        angle = math.atan2(x, y) * 360 / 2 / math.pi - 180
        self.image = pygame.transform.rotate(self.image_original, angle)


class Control():
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.screen_rect = self.screen.get_rect()
        self.done = False
        self.fps = FPS
        self.clock = pygame.time.Clock()
        self.groups = pygame.sprite.Group()

        self.senario_dir = {0: 'Run', 1: 'Player1', 2: 'Player2'}  #
        self.senario_index = 0

        self.selected_list = []  # 被选择的飞机
        self.mouse_select_pos = None  # 鼠标坐标
        self.mouse_target_pos = None

        self.groups_plane = pygame.sprite.Group()
        self.player1 = [Plane([100, 400], [1, 0]), Plane([200, 400], [1, 0])]  # 玩家的飞机
        self.player2 = [Plane([400, 100], [1, 0])]
        for i in self.player1 + self.player2:
            self.groups_plane.add(i)
        # self.groups.add(HomingMissile([10,400],(1,0)))
        # self.groups.add( Missile([10,600], [1,-1]) )
        # self.groups.add( Missile([10,400], [1,-2]) )
        # self.groups.add( Missile([10,400], [2,-2]) )

        self.groups_homing = pygame.sprite.Group()  # 暂时没用
        # self.groups_homing.add(HomingMissile([20,40],[1,0]))
        # self.groups_homing.add(HomingMissile([20,40],[1,-1]))
        # self.groups_homing.add(HomingMissile([20,40],[1,1]))
        # self.groups_homing.add(HomingMissile([20,40],[0,1]))
        # self.groups_homing.add(HomingMissile([20,40],[2,3]))
        # self.groups_homing.add(HomingMissile([20,40],[1,1.5]))

    def event_loop(self):
        for event in pygame.event.get():
            self.keys = pygame.key.get_pressed()
            if event.type == pygame.QUIT or self.keys[pygame.K_ESCAPE]:
                self.done = True
            if self.keys[pygame.K_SPACE]:
                self.senario_index = (self.senario_index + 1) % len(self.senario_dir.keys())
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.selected_list = []
                self.mouse_select_pos = list(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self.mouse_target_pos = list(event.pos)

    def update(self):
        self.groups.update()
        self.groups_plane.update()
        # self.groups_homing.update([500,100])

    def update_player(self):
        """pygame.draw.circle(screen, drawcolor, [top, left], radiu, width)"""

        radiu = 25

        if self.mouse_select_pos:  # 如果点击了鼠标左键就可以进行选择了
            for plane in self.player1:
                # print distance(plane.position,self.mouse_select_pos) , radiu
                pygame.draw.circle(self.screen, (0, 0, 0), self.mouse_select_pos, radiu, 1)
                if distance(plane.position,self.mouse_select_pos) <= radiu:
                    self.selected_list.append(plane)
        self.mouse_select_pos = None  # 选择完就将坐标清理,下次点击会再生成


        for plane in self.selected_list:  # 对已选择的飞机,进行目标地设置
            pygame.draw.circle(self.screen, (255, 0, 0), [int(i) for i in plane.position], radiu, 2)  # 蓝色标记已经选择的飞机
            if self.mouse_target_pos:
                plane.target_position = self.mouse_target_pos

            if plane.target_position:
                pygame.draw.circle(self.screen, (255, 255, 0), plane.target_position, 3, 1)  # 标记已经设置好目的地的位置
        self.mouse_target_pos = None  # 传值完，就对右键生成的坐标清理

        # pygame.sprite.spritecollide()


    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        # pygame.draw.circle(self.screen, (0, 0, 0), [500, 100], 3)

        self.groups.draw(self.screen)
        self.groups_plane.draw(self.screen)
        self.groups_homing.draw(self.screen)

        text_pos = u"Senario: %s " % self.senario_dir[self.senario_index]  # 显示实时状态文字
        show_text(self.screen, (10, 10), text_pos, (0, 0, 0))
        # print repr(self.mouse_select_pos)
        text_pos = u"Mouse pos: %s " % self.mouse_select_pos  # 显示上一次的鼠标位置
        show_text(self.screen, (10, 20), text_pos, (0, 0, 0))

        text_pos = u"Mouse pos: %s  -  %s   " % (self.player1[0].target_position, self.player1[1].target_position)  # 显示上一次的鼠标位置
        show_text(self.screen, (10, 30), text_pos, (0, 0, 0))



    def main_loop(self):
        # i = 0
        while not self.done:
            self.event_loop()
            # i += 1
            # print i
            self.draw()
            if self.senario_dir[self.senario_index] == 'Run':
                self.update()
                # print 'run'
            else:
                # print 'player'
                self.update_player()

            pygame.display.flip()
            self.clock.tick(self.fps)


def show_text(surface_handle, pos, text, color, font_size=14):
    """
    Function:文字处理函数
    """
    # 获取系统字体，并设置文字大小
    cur_font = pygame.font.SysFont(u"", font_size)

    # 设置文字内容
    text_fmt = cur_font.render(text, 1, color)

    # 绘制文字
    surface_handle.blit(text_fmt, pos)

def distance(pos1,pos2):
    dis = 0
    for i in [0,1]:
        dis += (pos1[i]-pos2[i]) * (pos1[i]-pos2[i])
    return math.sqrt(dis)

if __name__ == "__main__":
    SCREEN_SIZE = (600, 600)

    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()

    pygame.display.set_mode(SCREEN_SIZE)

    run_it = Control()
    run_it.main_loop()
    pygame.quit()
    sys.exit()
