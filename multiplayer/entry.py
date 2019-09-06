# -*- coding: cp936 -*-
import pygame
import infomation
import os
import sys

DASH_STRING = """Single Player
Multiplayer
    Create Game
        Your computer IP: ?.1.1.1
        Waiting other players entering...
            Cancel
        Player(IP:?.1.1.1) has entered your game.
            Start
                3 vs 3 (with 20 missiles)
                3 vs 3 (with 2 homing_missiles & 10 missiles)
                1 vs 1 (with 2 homing_missiles & 10 missiles)
            Ban him
            Cancel
    Enter a exiting game
        Input her computer IP:?.?.?.?
        Quick connect to: last IP
    Cancel
Exit"""


class Tree(object):
    def __init__(self, label):
        self.root = None
        self.children = None
        self.label = label
        self.be_chosen = False


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

        self.dash_list = DASH_STRING.split('\n')

        self.dash_index = -1
        self.context_tree = Tree('Game')
        self.dash2tree(depth=0, root=self.context_tree)  # 会丰富self.context_tree这棵树

    def dash2tree(self, depth, root):
        """Class Tree"""
        while True:
            self.dash_index += 1
            if self.dash_index >= len(self.dash_list):
                break
            line = self.dash_list[self.dash_index]

            if line.startswith('    ' * depth):
                child = Tree(line[len('    ')*depth:])  # 一个节点就是一个对象
                child.root = root
                if not root.children:
                    root.children = [child]
                else:
                    root.children.append(child)
                self.dash2tree(depth + 1, child)  # 继续深入递归
            else:
                self.dash_index -= 1
                break

    def main(self):
        # 最开始的选择菜单        
        self.beginning_select_index = 0
        self.has_chosen = False
        self.has_backspace = False
        self.root_node = self.context_tree
        self.list_node = self.root_node.children
        # 游戏选择界面
        self.done = False
        while not self.done:
            self.display_list = [i.label for i in self.list_node]
            self.draw_beginning(self.display_list)
            self.event_beginning()
            pygame.display.flip()
            self.clock.tick(self.fps)
            if self.has_chosen:
                if not self.has_backspace and self.list_node[self.beginning_select_index].children :  # 如果所选的这个有子集
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
                    #break  # Start from here!!!!!!!!!!!!!!!!!!
                self.has_chosen = False

    def draw_beginning(self, display_list):
        self.screen.fill(self.BACKGROUND_COLOR)
        # 设置标题 Homing Missile
        width, height = self.screen_rect[2:4]
        self.infomation.show_text(screen=self.screen, pos=(width / 3, height / 3 * 1), text=u"Homing Missile", size=48,
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


if __name__ == "__main__":
    SCREEN_SIZE = (1300, 650)

    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()
    pygame.mixer.init()  # 声音初始化

    pygame.display.set_mode(SCREEN_SIZE)

    beginning_choice = Beginning()
    choice = beginning_choice.main()

    if choice == 'Single Player':
        pass
        # run_it = single_player.Control()
        # run_it.main_loop()
    elif choice == 'Multiplayer':
        pass
        # run = multiplayer.Multiplayer()
        # run.multiplayer_selcet_screen()
    elif choice == 'Exit':
        pass

    pygame.quit()
    sys.exit()