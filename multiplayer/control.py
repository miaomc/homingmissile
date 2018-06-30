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
        self.senario_index = 1  # ��Player1��ʼ

        # ȫ�ֱ���,����ѡ��ɻ�,���Ʒɻ����з���,������������
        self.selected_list = []  # ��ѡ��ķɻ�
        self.mouse_select_pos = None  # �������
        self.mouse_target_pos = None
        self.fire_operation = None  # ������������ϵͳ

        self.homing_missile_lock = False  # homing missile ���Ʊ���
        self.homing_missile_plane = None

        self.groups_plane = pygame.sprite.Group()
##        self.player1 = [unit.Plane([100, 300], [1, 0], plane_image='./image/plane_blue.png')]
##        self.player2 = [unit.Plane([1200, 300], [-1, 0], plane_image='./image/plane_blue.png')]
        self.player1 = [unit.Plane([100, 300], [1, 0],plane_image='./image/plane_blue.png'),
                         unit.Plane([100, 400], [1, 0],plane_image='./image/plane_blue.png'),
                         unit.Plane([100, 200], [1, 0], plane_image='./image/plane_blue.png')]  # ��ҵķɻ�
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

        self.groups_homing = pygame.sprite.Group()  # ��ʱû��
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

        if self.mouse_select_pos:  # ���������������Ϳ��Խ���ѡ����
            if self.senario_dir[self.senario_index] == 'Player1':  # ��ʱ�������Ľ�
                current_player = self.player1
            elif self.senario_dir[self.senario_index] == 'Player2':
                current_player = self.player2

            for plane in current_player:
                # print self.distance(plane.position,self.mouse_select_pos) , radiu
                pygame.draw.circle(self.screen, (0, 0, 0), self.mouse_select_pos, radiu, 1)
                if self.distance(plane.position, self.mouse_select_pos) <= radiu:
                    self.selected_list.append(plane)
        self.mouse_select_pos = None  # ѡ����ͽ���������,�´ε����������

        for plane in self.selected_list:  # ����ѡ��ķɻ�,����Ŀ�������,����������
            pygame.draw.circle(self.screen, (0, 0, 255), [int(i) for i in plane.position], radiu, 2)  # ��ɫ����Ѿ�ѡ��ķɻ�
            
            if self.mouse_target_pos: # ��ֵ,�Ҽ����ɵ�Ŀ�ĵ�����
                if self.homing_missile_lock: # ��homing missile����Ŀ��ѡ��
                    for target_plane in self.player1+self.player2:
                        # print target_plane.position, self.mouse_target_pos, self.distance(plane.position, self.mouse_target_pos), radiu
                        if self.distance(target_plane.position, self.mouse_target_pos) <= radiu:
                            pygame.draw.circle(self.screen, (255, 0, 0), [int(i) for i in target_plane.position], radiu, 2)  # ��ɫ����Ѿ�ѡ��ķɻ�
                            self.groups_missile.add(unit.Homing_Missile(self.homing_missile_plane.position[:], self.homing_missile_plane.velocity[:], target_object=target_plane))
                            self.homing_missile_lock = False
                            # print 'locked.'
                            break
                else: # ����Ŀ�������
                    plane.target_position = self.mouse_target_pos
            if plane.target_position:
                pygame.draw.circle(self.screen, (255, 255, 0), plane.target_position, 3, 1)  # ����Ѿ����ú�Ŀ�ĵص�λ��������ʾ���Ͻǵ�״̬��

            # ������������
            self.infomation.add(u"Weapons: %s " % plane.weapons)
            if self.fire_operation in plane.weapons.keys():  # ['missile','homing_missile']
                if plane.weapons[self.fire_operation] > 0:
                    plane.weapons[self.fire_operation] -= 1
                    if self.fire_operation == 'missile':
                        #  ���䴫�δ���,�б�����,���ʵ����,����һ���޸����ݵ� ^ ^
                        #  self.groups_missile.add(unit.Missile(plane.position, plane.velocity))
                        self.groups_missile.add(unit.Missile(plane.position[:], plane.velocity[:]))
                    elif self.fire_operation == 'homing_missile':
                        # �����Ǹ���˭(����,����Ӧ����position�������),�������Ҽ���ֵʱ���д���
                        self.homing_missile_lock = True
                        self.homing_missile_plane = plane

        self.mouse_target_pos = None  # ��ֵ�꣬�Ͷ��Ҽ����ɵ���������
        self.fire_operation = None  # ��ֵ�꣬�Ͷ�������������

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        # pygame.draw.circle(self.screen, (0, 0, 0), [500, 100], 3)

        # self.groups.draw(self.screen)
        self.groups_plane.draw(self.screen)
        self.groups_missile.draw(self.screen)
        self.groups_homing.draw(self.screen)

        self.infomation.add(u"Senario: %s " % self.senario_dir[self.senario_index])  # ��ʾʵʱ״̬����
        self.infomation.add(u"Mouse Left&Right: %s , %s " % (self.mouse_select_pos, self.mouse_target_pos))  # ��ʾ��һ�ε����λ��
        self.infomation.add(u"Player Status: %s " % (self.players))  # ��ʾ��һ�ε����λ��
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
                # ȫ�ָ���
                self.update()

                # �����ײ
                for weapon in self.groups_missile.sprites():  # ����ÿһ������
                    weapon_used = False
                    if weapon.activated():  # �����������״̬,��Ա�ÿһ�ܷɻ�,����û�п�������֮�����ײ To be continue...
                        lst = pygame.sprite.spritecollide(weapon, self.groups_plane, False)  # ������ײ�ķɻ�,���Ƴ�Ⱥ��,���ǲ���kill�ɻ�
                        for plane in lst:  # �����ɵ��ķɻ�
                            plane.delete()
                        if lst:
                            weapon_used = True
                    if weapon_used:  # ����������Ѿ���Ч,���Ƴ�
                        weapon.kill()

                # ״̬�滻
                if not previous_time:
                    previous_time = pygame.time.get_ticks()
                if pygame.time.get_ticks() - previous_time > 2000:  # �����run������״̬�³���3��,���л�Ϊ���ģʽ
                    previous_time = None
                    self.senario_index = (self.senario_index + 1) % len(self.senario_dir.keys())
                # print 'run'
                # print pygame.time.get_ticks(), previous_time
            else:
                # print 'player'
                self.update_player()

            pygame.display.flip()

            # ˢ����ҵķɻ�
            for player in self.players:
                for plane in player[:]:
                    if not plane.alive:
                        player.remove(plane)
            # ����ֱ�Ӹ�ֵ,����û�иı�ԭ�ж���
            # self.players = [[plane for plane in player if plane.alive] for player in self.players]

            self.clock.tick(self.fps)

    def distance(self, pos1, pos2):
        dis = 0
        for i in [0, 1]:
            dis += (pos1[i] - pos2[i]) * (pos1[i] - pos2[i])
        return math.sqrt(dis)
