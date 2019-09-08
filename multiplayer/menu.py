# -*- coding: cp936 -*-
import pygame
import infomation
import os
import sys

CONTENT = {
    'Homing Missle':{
        'local_ip': None,
        'name': None,
        'Multiplay(LAN)':{
            'Create Game':{
                'host_ip':None,
                'Start':None,
                'Cancel':None,
            },
            'Join': None,
            'Cancel':None,
        },
        'SingleTest':{
            'Cancel':None,
        },
        'Exit':None,
    },
}


class Beginning():
    def __init__(self):
        self.fps = 20  # FPS

        self.clock = pygame.time.Clock()
        self.BACKGROUND_COLOR = (168, 168, 168)

        self.screen = pygame.display.get_surface()
        self.screen_rect = self.screen.get_rect()

        self.infomation = infomation.Infomation()
        # self.sound_return = pygame.mixer.Sound()
        # self.sound_selecting = pygame.mixer.Sound()

    def main(self):
        # 最开始的选择菜单        
        self.beginning_select_index = 0
        self.has_chosen = False
        self.has_backspace = False
        
        
        self.root_node = CONTENT.root_node.keys()[0]
        self.menu_title = self.root_node
        self.list_node = self.root_node.keys()

        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!111 to be continues
        # 游戏选择界面
        self.done = False
        while not self.done:
            self.display_list = [i.label for i in self.list_node]
            self.draw_beginning(self.display_list)
            self.event_beginning()
            pygame.display.flip()
            self.clock.tick(self.fps)
            if self.has_chosen:
                if not self.has_backspace and self.list_node[self.beginning_select_index].children:  # 如果所选的这个有子集
                    self.root_node = self.list_node[self.beginning_select_index]
                    self.list_node = self.root_node.children
                    self.beginning_select_index = 0
                elif self.has_backspace or self.list_node[self.beginning_select_index].label == 'Cancel':
                    if self.root_node.root:
                        self.root_node = self.root_node.root
                    self.list_node = self.root_node.children
                    self.has_backspace = False
                    self.beginning_select_index = 0
                else:
                    print self.list_node[self.beginning_select_index].label
                    # break  # Start from here!!!!!!!!!!!!!!!!!!
                self.has_chosen = False

    def draw_beginning(self, display_list):
        self.screen.fill(self.BACKGROUND_COLOR)
        # 设置标题 Homing Missile
        width, height = self.screen_rect[2:4]
        self.infomation.show_text(screen=self.screen, pos=(width / 3, height / 3 * 1), text=u"Homing Missile",
                                  size=48,
                                  bold=True)  # 显示实时状态文字
        # 设置选项

        for num, i in enumerate(display_list):
            size = 36
            if num == self.beginning_select_index:
                color = (255, 0, 0)
            else:
                color = (0, 0, 0)
            self.infomation.show_text(screen=self.screen,
                                      pos=(width / 3 + size * 2, height / 3 * 1 + size * (num + 2.5)), text=i,
                                      color=color, size=size)  # 显示上一次的鼠标位置

    def event_beginning(self):
        for event in pygame.event.get():
            self.keys = pygame.key.get_pressed()
            if event.type == pygame.QUIT or self.keys[pygame.K_ESCAPE]:
                self.done = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    self.beginning_select_index = (self.beginning_select_index + 1) % len(self.list_node)
                    # self.sound_selecting.play()
                if event.key == pygame.K_UP:
                    self.beginning_select_index = (self.beginning_select_index - 1) % len(self.list_node)
                    # self.sound_selecting.play()
                if event.key == pygame.K_LEFT:
                    self.has_backspace = True
                    self.has_chosen = True
                if event.key in [pygame.K_RETURN, pygame.K_RIGHT]:
                    self.has_chosen = True
                    # self.sound_return.play()

def entry_main():
    SCREEN_SIZE = (1300, 650)
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()
    pygame.mixer.init()  # 声音初始化
    pygame.display.set_mode(SCREEN_SIZE)

    beginning_choice = Beginning()
    choice = beginning_choice.main()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    # entry_main()
    pass