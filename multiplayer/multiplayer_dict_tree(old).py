# -*- coding: cp936 -*-
import pygame
import infomation

class Tree():
    def __init__(self, root, children=None):
        self.root = root
        self.children = children
        self.visible = False
        self.be_chosen = False
    
class Player():
    def __init__(self, ip):
        self.ip = ip
    
class Multiplayer():
    def __init__(self):
        self.fps = 60  # FPS
        self.clock = pygame.time.Clock()
        self.BACKGROUND_COLOR = (168, 168, 168)

        self.screen = pygame.display.get_surface()
        self.screen_rect = self.screen.get_rect()

        self.infomation = infomation.Infomation()

##        self.list_players = []  #list_players
##        self.server_ip = '?.?.?.?'  # 不管是自己还是其他玩家，都朝自己这个主机发送消息

        dash_string = """Create Game
--Your computer IP: ?.1.1.1
--Waiting other players entering...
----Cancel
--Player(IP:?.1.1.1) has entered your game.
----Start
------3 vs 3 (with 20 missiles)
------3 vs 3 (with 2 homing_missiles & 10 missiles)
------1 vs 1 (with 2 homing_missiles & 10 missiles)
----Ban him
----Cancel
Enter a exiting game
--Input her computer IP:?.?.?.?
--Quick connect to: last IP
Cancel"""
        self.dash_list = dash_string.split('\n')
        self.dash_index = -1
        self.dash_tree = self.dash2tree(depth=0, root='Multiplayer')  # 返回的是一个字典d，d[key]是一个列表
        self.display_list = self.dash_tree['Multiplayer']
        
    def multiplayer_selcet_screen(self):
##        self.beginning_select_index = 0
        self.has_chosen = False
        # 游戏选择界面
        self.done = False
        while not self.done:
            self.update()
            self.draw()
            self.event()
            pygame.display.flip()
            self.clock.tick(self.fps)
            if self.has_chosen:
                break

    def update(self):
        pass

    def event(self):
        for event in pygame.event.get():
            self.keys = pygame.key.get_pressed()
            if event.type == pygame.QUIT or self.keys[pygame.K_ESCAPE]:
                self.done = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    pass
##                    self.beginning_select_index = (self.beginning_select_index+1)%len(self.list_player_mode)
                    #self.sound_selecting.play()
                if event.key == pygame.K_UP:
##                    self.beginning_select_index = (self.beginning_select_index-1)%len(self.list_player_mode)
                    pass
                    #self.sound_selecting.play()
                if event.key == pygame.K_RETURN:
                    self.has_chosen = True
                    #self.sound_return.play()
    
    def draw(self):
        # 显示选择菜单
        self.screen.fill(self.BACKGROUND_COLOR)
        width, height = self.screen_rect[2:4]        
        
        self.infomation.show_text(screen=self.screen, pos=(width/3, height/3*1), text=u"Homing Missile", size=48, bold=True)
        display_list = self.dash_tree['Multiplayer']
        for num,i in enumerate(self.display_list):
            size = 36
##            if num == self.beginning_select_index:
##                color = (255,0,0)
##            else:
##                color = (0,0,0)
            color = (0,0,0)
            tmp = i.keys()[0]
##            print repr(tmp)
            self.infomation.show_text(screen=self.screen, pos=(width/3+size*2, height/3*1+size*(num+2.5)), text=tmp, color=color, size=size)
        
    def dash2tree(self, depth, root):
        """{'Mult':[{k1:[ {k11:[]}, ... ]},{k2:[]},...]}"""
        tree = {root:[]}
        
        while True:
            self.dash_index += 1
            if self.dash_index >= len(self.dash_list):
                break           
            line = self.dash_list[self.dash_index]

            if line.startswith('--'*depth):
                tree[root].append(self.dash2tree(depth+1,line))
            else:
                self.dash_index -= 1
                break
        return tree
            
                
    def main(self):
        pass
            
##        # Set Planes & Positions
##        self.game_init()
##        
##        self.done = False
##        while not self.done:
##            self.draw(self.list_player_mode)
##            self.event_beginning()
##            pygame.display.flip()
##            self.clock.tick(self.fps)

if __name__ == '__main__':
    # Start 之后建立tcp监听
##    server = Server(ip)
##    server.start()
##
##    client = Client(ip)
##    client.start()
    import os
    import sys
    SCREEN_SIZE = (1300, 650)

    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()
    pygame.mixer.init()  # 声音初始化

    pygame.display.set_mode(SCREEN_SIZE)
    m = Multiplayer()
    s = m.multiplayer_selcet_screen()
