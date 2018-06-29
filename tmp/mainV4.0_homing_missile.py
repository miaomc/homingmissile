# -*- coding: cp936 -*-
import math
import os
import sys

import pygame

BACKGROUND_COLOR = (168, 168, 168)
WHITE = (255, 255, 255)
FPS = 60


class Missile(pygame.sprite.Sprite):
    def __init__(self, position, velocity, max_acceleration_parallel=0.028284, fuel=1500):
        pygame.sprite.Sprite.__init__(self)

        self.image_original = pygame.image.load('homingmissile.png').convert()
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
                 max_acceleration_parallel=0, plane_image='plane_blue.png', weapons = {'missile': 20, 'homing_missile': 2}):
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


class Control():
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.screen_rect = self.screen.get_rect()
        self.done = False
        self.fps = FPS
        self.clock = pygame.time.Clock()
        # self.groups = pygame.sprite.Group()

        self.infomation = Infomation()

        self.senario_dir = {0: 'Run', 1: 'Player1', 2: 'Player2'}  #
        self.senario_index = 1  # 从Player1开始

        # 全局变量,用来选择飞机,控制飞机飞行方向,控制武器发射
        self.selected_list = []  # 被选择的飞机
        self.mouse_select_pos = None  # 鼠标坐标
        self.mouse_target_pos = None
        self.fire_operation = None  # 用来控制武器系统

        self.homing_missile_lock = False  # homing missile 控制变量
        self.homing_missile_plane = None

        self.groups_plane = pygame.sprite.Group()
##        self.player1 = [Plane([100, 300], [1, 0], plane_image='plane_blue.png')]
##        self.player2 = [Plane([1200, 300], [-1, 0], plane_image='plane_blue.png')]
        self.player1 = [Plane([100, 300], [1, 0],plane_image='plane_blue.png'),
                         Plane([100, 400], [1, 0],plane_image='plane_blue.png'),
                         Plane([100, 200], [1, 0], plane_image='plane_blue.png')]  # 玩家的飞机
        self.player2 = [Plane([1200, 300], [-1, 0],plane_image='plane_red.png', weapons = {'missile': 20, 'homing_missile': 10}),]
##                      Plane([1200, 400], [-1, 0],plane_image='plane_blue.png'),
##                         Plane([1200, 200], [-1, 0], plane_image='plane_blue.png')]
        self.players = [self.player1, self.player2]

        for i in self.player1 + self.player2:
            self.groups_plane.add(i)

        # self.groups.add(Homing_Missile([10,400],(1,0)))

        self.groups_missile = pygame.sprite.Group()
        # self.groups.add( Missile([10,600], [1,-1]) )
        # self.groups.add( Missile([10,400], [1,-2]) )
        # self.groups.add( Missile([10,400], [2,-2]) )

        self.groups_homing = pygame.sprite.Group()  # 暂时没用
        # self.groups_homing.add(Homing_Missile([20,40],[1,0]))
        # self.groups_homing.add(Homing_Missile([20,40],[1,-1]))
        # self.groups_homing.add(Homing_Missile([20,40],[1,1]))
        # self.groups_homing.add(Homing_Missile([20,40],[0,1]))
        # self.groups_homing.add(Homing_Missile([20,40],[2,3]))
        # self.groups_homing.add(Homing_Missile([20,40],[1,1.5]))

    def event_loop(self):
        for event in pygame.event.get():
            self.keys = pygame.key.get_pressed()
            if event.type == pygame.QUIT or self.keys[pygame.K_ESCAPE]:
                self.done = True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.selected_list = []
                self.mouse_select_pos = list(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self.mouse_target_pos = list(event.pos)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.senario_index = (self.senario_index + 1) % len(self.senario_dir.keys())
                if event.key == pygame.K_f:
                    self.fire_operation = 'missile'
                if event.key == pygame.K_h:
                    self.fire_operation = 'homing_missile'

    def update(self):
        # self.groups.update()
        self.groups_plane.update()
        self.groups_missile.update()
        # self.groups_homing.update([500,100])

    def update_player(self):
        """pygame.draw.circle(screen, drawcolor, [top, left], radiu, width)"""
        radiu = 25

        if self.mouse_select_pos:  # 如果点击了鼠标左键就可以进行选择了
            if self.senario_dir[self.senario_index] == 'Player1':  # 到时候再来改进
                current_player = self.player1
            elif self.senario_dir[self.senario_index] == 'Player2':
                current_player = self.player2

            for plane in current_player:
                # print distance(plane.position,self.mouse_select_pos) , radiu
                pygame.draw.circle(self.screen, (0, 0, 0), self.mouse_select_pos, radiu, 1)
                if distance(plane.position, self.mouse_select_pos) <= radiu:
                    self.selected_list.append(plane)
        self.mouse_select_pos = None  # 选择完就将坐标清理,下次点击会再生成

        for plane in self.selected_list:  # 对已选择的飞机,进行目标地设置,和武器控制
            pygame.draw.circle(self.screen, (0, 0, 255), [int(i) for i in plane.position], radiu, 2)  # 蓝色标记已经选择的飞机
            
            if self.mouse_target_pos: # 传值,右键生成的目的地坐标
                if self.homing_missile_lock: # 对homing missile进行目标选定
                    for target_plane in self.player1+self.player2:
                        # print target_plane.position, self.mouse_target_pos, distance(plane.position, self.mouse_target_pos), radiu
                        if distance(target_plane.position, self.mouse_target_pos) <= radiu:
                            pygame.draw.circle(self.screen, (255, 0, 0), [int(i) for i in target_plane.position], radiu, 2)  # 蓝色标记已经选择的飞机
                            self.groups_missile.add(Homing_Missile(self.homing_missile_plane.position[:], self.homing_missile_plane.velocity[:], target_object=target_plane))
                            self.homing_missile_lock = False
                            # print 'locked.'
                            break
                else: # 进行目标地设置
                    plane.target_position = self.mouse_target_pos
            if plane.target_position:
                pygame.draw.circle(self.screen, (255, 255, 0), plane.target_position, 3, 1)  # 标记已经设置好目的地的位置用来显示左上角的状态栏

            # 进行武器控制
            self.infomation.add(u"Weapons: %s " % plane.weapons)
            if self.fire_operation in plane.weapons.keys():  # ['missile','homing_missile']
                if plane.weapons[self.fire_operation] > 0:
                    plane.weapons[self.fire_operation] -= 1
                    if self.fire_operation == 'missile':
                        #  经典传参错误,列表传传参,变成实参了,还能一起修改数据的 ^ ^
                        #  self.groups_missile.add(Missile(plane.position, plane.velocity))
                        self.groups_missile.add(Missile(plane.position[:], plane.velocity[:]))
                    elif self.fire_operation == 'homing_missile':
                        # 或者是跟踪谁(对象,对象应该有position这个参数),在上面右键传值时进行处理
                        self.homing_missile_lock = True
                        self.homing_missile_plane = plane

        self.mouse_target_pos = None  # 传值完，就对右键生成的坐标清理
        self.fire_operation = None  # 传值完，就对武器操作归零

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        # pygame.draw.circle(self.screen, (0, 0, 0), [500, 100], 3)

        # self.groups.draw(self.screen)
        self.groups_plane.draw(self.screen)
        self.groups_missile.draw(self.screen)
        self.groups_homing.draw(self.screen)

        self.infomation.add(u"Senario: %s " % self.senario_dir[self.senario_index])  # 显示实时状态文字
        self.infomation.add(u"Mouse Left&Right: %s , %s " % (self.mouse_select_pos, self.mouse_target_pos))  # 显示上一次的鼠标位置
        self.infomation.add(u"Player Status: %s " % (self.players))  # 显示上一次的鼠标位置
        self.infomation.add(u"FPS: %s " % self.clock.get_fps())

        self.infomation.show(screen=self.screen)

    def main_loop(self):
        # i = 0
        previous_time = None
        while not self.done:
            self.event_loop()
            # i += 1
            # print i
            self.draw()
            if self.senario_dir[self.senario_index] == 'Run':
                # 全局更新
                self.update()

                # 检测碰撞
                for weapon in self.groups_missile.sprites():  # 遍历每一个武器
                    weapon_used = False
                    if weapon.activated():  # 如果武器激活状态,则对比每一架飞机,这里没有考虑武器之间的碰撞 To be continue...
                        lst = pygame.sprite.spritecollide(weapon, self.groups_plane, False)  # 返回碰撞的飞机,并移出群组,但是不会kill飞机
                        for plane in lst:  # 清理被干掉的飞机
                            plane.delete()
                        if lst:
                            weapon_used = True
                    if weapon_used:  # 如果该武器已经生效,则移除
                        weapon.kill()

                # 状态替换
                if not previous_time:
                    previous_time = pygame.time.get_ticks()
                if pygame.time.get_ticks() - previous_time > 2000:  # 如果在run的运行状态下超过3秒,则切换为玩家模式
                    previous_time = None
                    self.senario_index = (self.senario_index + 1) % len(self.senario_dir.keys())
                # print 'run'
                # print pygame.time.get_ticks(), previous_time
            else:
                # print 'player'
                self.update_player()

            pygame.display.flip()

            # 刷新玩家的飞机
            for player in self.players:
                for plane in player[:]:
                    if not plane.alive:
                        player.remove(plane)
            # 不能直接复值,这样没有改变原有对象
            # self.players = [[plane for plane in player if plane.alive] for player in self.players]

            self.clock.tick(self.fps)


class Infomation(object):
    """
    用来显示左上角的状态栏
    """

    def __init__(self):
        self.message_list = []

    def add(self, message):
        self.message_list.append(message)

    def show(self, screen):
        for i, text in enumerate(self.message_list):
            self.show_text(screen, (10, i * 12), text, (0, 0, 0))
        self.message_list = []

    def show_text(self, surface_handle, pos, text, color, font_size=16):
        """文字处理函数        """
        # 获取系统字体，并设置文字大小
        cur_font = pygame.font.SysFont(u"", font_size)

        # 设置文字内容
        text_fmt = cur_font.render(text, 1, color)

        # 绘制文字
        surface_handle.blit(text_fmt, pos)


def distance(pos1, pos2):
    dis = 0
    for i in [0, 1]:
        dis += (pos1[i] - pos2[i]) * (pos1[i] - pos2[i])
    return math.sqrt(dis)


if __name__ == "__main__":
    SCREEN_SIZE = (1300, 650)

    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()
    pygame.mixer.init()  # 声音初始化

    pygame.display.set_mode(SCREEN_SIZE)

    run_it = Control()
    run_it.main_loop()
    pygame.quit()
    sys.exit()
