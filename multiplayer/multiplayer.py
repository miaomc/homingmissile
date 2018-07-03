# -*- coding: cp936 -*-
import pygame


class Player():
    def __init__(self, ip):
        self.ip = ip
    
class Multiplayer():
    def __init__(self, list_players):
        self.fps = 60  # FPS
        self.BACKGROUND_COLOR = (168, 168, 168)

##        self.screen = pygame.display.get_surface()
##        self.screen_rect = self.screen.get_rect()

##        self.infomation = infomation.Infomation()

        self.list_players = list_players
        self.server_ip = '?.?.?.?'  # 不管是自己还是其他玩家，都朝自己这个主机发送消息

    def multiplayer_selcet_screen(self):
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
        dash_tree = self.dash2tree(depth=0, root='Multiplayer')
        return dash_tree
        
    def dash2tree(self, depth, root):
        """{'Mult':[{k1:[ {k11:[]}, ... ]},{k2:[]},...]}"""
        tree = {root:[]}
        
        while True:            
            self.dash_index += 1
            if self.dash_index >= len(self.dash_list):
                break           
            line = self.dash_list[self.dash_index]

            if line.startswith('--'*depth):
                print 1
                tree[root].append(self.dash2tree(depth+1,line))
                print 2
            else:
                self.dash_index -= 1
                break
        return tree
            
                
    def main(self):
        # Set Planes & Positions
        self.game_init()
        
        self.done = False
        while not self.done:
            self.draw(self.list_player_mode)
            self.event_beginning()
            pygame.display.flip()
            self.clock.tick(self.fps)

if __name__ == '__main__':
    # Start 之后建立tcp监听
##    server = Server(ip)
##    server.start()
##
##    client = Client(ip)
##    client.start()
    m = Multiplayer('dd')
    s = m.multiplayer_selcet_screen()
