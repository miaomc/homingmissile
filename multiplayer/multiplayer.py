# -*- coding: cp936 -*-



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
        dash_tree = self.dash2tree(dash_string, depth=0)
        
    def dash2tree(self, dash_string, depth):
        """[{k1:[ {k11:[]}, ... ]},{k2:[]},...]"""
        dash_tree = []
        
        for line in str_list.split('\n'):
            if line.start_with('--'*(depth+2)): # 如果为当前深度+1，则就是值
                
            elif line.start_with('--'*(depth+1))
                dash_tree += line
            elif line.start_with('--'*depth)
                dash_tree += {line:[]}
            
                
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
    server = Server(ip)
    server.start()

    client = Client(ip)
    client.start()
