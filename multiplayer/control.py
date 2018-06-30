# -*- coding: cp936 -*-
import math
import os
import sys
import pygame
import unit
import infomation

BACKGROUND_COLOR = (168, 168, 168)
FPS = 60

class Control():
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.screen_rect = self.screen.get_rect()
        self.done = False
        self.fps = FPS
        self.clock = pygame.time.Clock()
        # self.groups = pygame.sprite.Group()

        self.infomation = infomation.Infomation()

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
##        self.player1 = [unit.Plane([100, 300], [1, 0], plane_image='./image/plane_blue.png')]
##        self.player2 = [unit.Plane([1200, 300], [-1, 0], plane_image='./image/plane_blue.png')]
        self.player1 = [unit.Plane([100, 300], [1, 0],plane_image='./image/plane_blue.png'),
                         unit.Plane([100, 400], [1, 0],plane_image='./image/plane_blue.png'),
                         unit.Plane([100, 200], [1, 0], plane_image='./image/plane_blue.png')]  # 玩家的飞机
        self.player2 = [unit.Plane([1200, 300], [-1, 0],plane_image='./image/plane_red.png', weapons = {'missile': 20, 'homing_missile': 10}),]
##                      unit.Plane([1200, 400], [-1, 0],plane_image='./image/plane_blue.png'),
##                         unit.Plane([1200, 200], [-1, 0], plane_image='./image/plane_blue.png')]
        self.players = [self.player1, self.player2]

        for i in self.player1 + self.player2:
            self.groups_plane.add(i)

        # self.groups.add(unit.Homing_Missile([10,400],(1,0)))

        self.groups_missile = pygame.sprite.Group()
        # self.groups.add( unit.Missile([10,600], [1,-1]) )
        # self.groups.add( unit.Missile([10,400], [1,-2]) )
        # self.groups.add( unit.Missile([10,400], [2,-2]) )

        self.groups_homing = pygame.sprite.Group()  # 暂时没用
        # self.groups_homing.add(unit.Homing_Missile([20,40],[1,0]))
        # self.groups_homing.add(unit.Homing_Missile([20,40],[1,-1]))
        # self.groups_homing.add(unit.Homing_Missile([20,40],[1,1]))
        # self.groups_homing.add(unit.Homing_Missile([20,40],[0,1]))
        # self.groups_homing.add(unit.Homing_Missile([20,40],[2,3]))
        # self.groups_homing.add(unit.Homing_Missile([20,40],[1,1.5]))

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
                # print self.distance(plane.position,self.mouse_select_pos) , radiu
                pygame.draw.circle(self.screen, (0, 0, 0), self.mouse_select_pos, radiu, 1)
                if self.distance(plane.position, self.mouse_select_pos) <= radiu:
                    self.selected_list.append(plane)
        self.mouse_select_pos = None  # 选择完就将坐标清理,下次点击会再生成

        for plane in self.selected_list:  # 对已选择的飞机,进行目标地设置,和武器控制
            pygame.draw.circle(self.screen, (0, 0, 255), [int(i) for i in plane.position], radiu, 2)  # 蓝色标记已经选择的飞机
            
            if self.mouse_target_pos: # 传值,右键生成的目的地坐标
                if self.homing_missile_lock: # 对homing missile进行目标选定
                    for target_plane in self.player1+self.player2:
                        # print target_plane.position, self.mouse_target_pos, self.distance(plane.position, self.mouse_target_pos), radiu
                        if self.distance(target_plane.position, self.mouse_target_pos) <= radiu:
                            pygame.draw.circle(self.screen, (255, 0, 0), [int(i) for i in target_plane.position], radiu, 2)  # 蓝色标记已经选择的飞机
                            self.groups_missile.add(unit.Homing_Missile(self.homing_missile_plane.position[:], self.homing_missile_plane.velocity[:], target_object=target_plane))
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
                        #  self.groups_missile.add(unit.Missile(plane.position, plane.velocity))
                        self.groups_missile.add(unit.Missile(plane.position[:], plane.velocity[:]))
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

    def distance(self, pos1, pos2):
        dis = 0
        for i in [0, 1]:
            dis += (pos1[i] - pos2[i]) * (pos1[i] - pos2[i])
        return math.sqrt(dis)
