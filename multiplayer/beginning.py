# -*- coding: cp936 -*-
import pygame
import infomation

class Beginning():
    def __init__(self):
        self.list_player_mode = ['Single Player','Multiplayer','Exit']
        self.fps = 60  # FPS

        self.clock = pygame.time.Clock()
        self.BACKGROUND_COLOR = (168, 168, 168)

        self.screen = pygame.display.get_surface()
        self.screen_rect = self.screen.get_rect()

        self.infomation = infomation.Infomation()
        #self.sound_return = pygame.mixer.Sound()
        #self.sound_selecting = pygame.mixer.Sound()
        
    def main(self):
        # 最开始的选择菜单        
        self.beginning_select_index = 0
        self.has_chosen = False
        # 游戏选择界面
        self.done = False
        while not self.done:
            self.draw_beginning(self.list_player_mode)
            self.event_beginning()
            pygame.display.flip()
            self.clock.tick(self.fps)
            if self.has_chosen:
                break
        # 根据选择的情况，进行单机还是联网游戏    
        if self.done or self.list_player_mode[self.beginning_select_index] == 'Exit':
            return 'Exit'
        elif self.list_player_mode[self.beginning_select_index] == 'Single Player':
            return 'Single Player'
        elif self.list_player_mode[self.beginning_select_index] == 'Multiplayer':
            return 'Multiplayer'

    def draw_beginning(self,display_list):
        self.screen.fill(self.BACKGROUND_COLOR)
        # 设置标题 Homing Missile
        width, height = self.screen_rect[2:4]
        self.infomation.show_text(screen=self.screen, pos=(width/3, height/3*1), text=u"Homing Missile", size=48, bold=True)  # 显示实时状态文字
        # 设置选项
        for num,i in enumerate(display_list):
            size = 36
            if num == self.beginning_select_index:
                color = (255,0,0)
            else:
                color = (0,0,0)
            self.infomation.show_text(screen=self.screen, pos=(width/3+size*2, height/3*1+size*(num+2.5)), text=i, color=color, size=size)  # 显示上一次的鼠标位置
        
    def event_beginning(self):
        for event in pygame.event.get():
            self.keys = pygame.key.get_pressed()
            if event.type == pygame.QUIT or self.keys[pygame.K_ESCAPE]:
                self.done = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    self.beginning_select_index = (self.beginning_select_index+1)%len(self.list_player_mode)
                    #self.sound_selecting.play()
                if event.key == pygame.K_UP:
                    self.beginning_select_index = (self.beginning_select_index-1)%len(self.list_player_mode)
                    #self.sound_selecting.play()
                if event.key == pygame.K_RETURN:
                    self.has_chosen = True
                    #self.sound_return.play()
