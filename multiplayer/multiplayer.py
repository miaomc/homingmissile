# -*- coding: cp936 -*-

"""
Create Game
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

Cancel
"""

class Player():
    def __init__(self, ip):
        self.ip = ip
        
class Multiplayer():
    def __init__(self, list_players):
        self.fps = 60  # FPS
        self.BACKGROUND_COLOR = (168, 168, 168)

        self.screen = pygame.display.get_surface()
        self.screen_rect = self.screen.get_rect()

##        self.infomation = infomation.Infomation()

        self.list_players = list_players
        self.server_ip = '?.?.?.?'  # 不管是自己还是其他玩家，都朝自己这个主机发送消息
        
    def main(self):
        # Set Planes & Positions
        self.game_init()
        
        self.done = False
         while not self.done:
            self.draw(self.list_player_mode)
            self.event_beginning()
            pygame.display.flip()
            self.clock.tick(self.fps)
        
