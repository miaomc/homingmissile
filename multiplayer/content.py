# -*- coding: cp936 -*-
import os
import sys
import time
import socket
import pygame
import information

PORT = 80

class Node():
    def __init__(self, label):
        self.parent = None
        self.children = []
        self.label = label
        self.target = None
        self.args = None

    def add(self, other):
        self.children.append(other)
        other.parent = self

    def be_chosen(self):
        if self.target:
            if self.args:
                return self.target(self.args)
            else:
                return self.target()
        else:
            return None


class Sock():
    def __init__(self):
        self.port = PORT

    def localip(self):
        return socket.gethostbyname(socket.gethostname())

    def scan_hostip(self):
        delay = 0.001
        time_start = time.time()
        ip_up =[]
        ip_head = '.'.join(self.localip().split('.')[0:3])
        ip_list = [ip_head+'.'+str(i) for i in range(256)]
        port_list = [self.port]
        for ip in ip_list:
            # print('Scan %s' % ip)
            up = False
            for port in port_list:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(delay)
                result = s.connect_ex((ip, port))
                if result == 0:
                    print('Port %d: open' % (port))
                    up = True
                s.close()
            if up:
                ip_up.append(ip)
        time_end = time.time()
        print('IP Scan:%s'%ip_list)
        print('IP Scan:%s'%port_list)
        print('PortScan done! %d IP addresses (%d hosts up) scanned in %f seconds.' % (
            len(ip_list), len(ip_up), time_end - time_start))
        print('Up hosts:')
        for i in ip_up:
            print i
        return ip_up

class Widget():
    def __init__(self):
        SCREEN_SIZE = (800, 600)
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        pygame.mixer.init()  # 声音初始化
        pygame.display.set_mode(SCREEN_SIZE)

        self.fps = 20  # FPS
        self.clock = pygame.time.Clock()
        self.BACKGROUND_COLOR = (168, 168, 168)
        self.screen = pygame.display.get_surface()
        self.screen_rect = self.screen.get_rect()
        self.information = information.Information()
        # self.sound_return = pygame.mixer.Sound()
        # self.sound_selecting = pygame.mixer.Sound()

        self.sock = Sock()

    def get_localip(self):
        return self.sock.localip()

    def scan_hostip(self):
        return self.sock.scan_hostip()

    def join_func(self, node):
        for i in node.children:
            del(i)
        node.children = []
        for ip in self.scan_hostip():
            ip_node = Node(ip)
            # ip_node.target =
            node.add(ip_node)

    def nodetree_produce(self):
        """
        'Homing Missle':
            'Local IP'
            'Create Game':
                'host_ip'
                'other player1'
                'other player2'
                'Start',
                'Cancel'
            'Join Game'
                'host_ip1'
                'host_ip2'
            'Exit'
        """
        # START_NODE
        start_node = Node('Homing Missile')
        start_node.parent = start_node  # 原始节点的父亲节点就是自己
        localip = self.get_localip()
        localip_node = Node('Local IP:' + localip)
        create_node = Node('Create Game')
        join_node = Node('Join Game')
        exit_node = Node('Exit')
        start_node.add(localip_node)
        start_node.add(create_node)
        start_node.add(join_node)
        start_node.add(exit_node)

        # CREATE_NODE
        hostip_node = Node('Host IP:' + localip)


        # JOIN_NODE
        join_node.target = self.join_func
        join_node.args = (join_node)
        # join_node.be_chosen()

        # EXIT_NODE
        # window.exit =
        return start_node


    def main_loop(self):
        # 生成目录树
        self.node_point = self.nodetree_produce()
        # 最开始的选择菜单        
        self.beginning_select_index = 0
        self.has_chosen = False
        self.has_backspace = False

        self.root_node = self.node_point
        self.menu_title = self.root_node.label
        self.list_node = self.root_node.children

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!111 to be continues
        # 游戏选择界面
        self.done = False
        while not self.done:
            self.display_list = [i.label for i in self.list_node]
            self.draw(self.display_list)
            self.event_control()
            pygame.display.flip()
            self.clock.tick(self.fps)
            if self.has_chosen:
                # 如果所选的这个有子集，进入这个子集
                if not self.has_backspace: #and
                    self.root_node = self.list_node[self.beginning_select_index]
                    self.root_node.be_chosen()
                    if self.root_node.children:  # 有子集就替换root指向
                        self.list_node = self.root_node.children
                        self.beginning_select_index = 0
                    else:
                        self.root_node = self.root_node.parent
                #  返回上一层：向左回退或者为取消
                elif self.has_backspace or self.list_node[self.beginning_select_index].label == 'Cancel':
                    if self.root_node.parent:
                        self.root_node = self.root_node.parent
                    self.list_node = self.root_node.children
                    self.has_backspace = False
                    self.beginning_select_index = 0
                # 打印其他没有响应的值
                else:
                    print self.list_node[self.beginning_select_index].label
                    # break  # Start from here!!!!!!!!!!!!!!!!!!
                self.has_chosen = False

    def draw(self, display_list):
        self.screen.fill(self.BACKGROUND_COLOR)
        # 设置标题 Homing Missile
        width, height = self.screen_rect[2:4]
        self.information.show_text(screen=self.screen, pos=(width / 3, height / 3 * 1), text=u"Homing Missile",
                                   size=48,
                                   bold=True)  # 显示实时状态文字
        # 设置选项
        for num, i in enumerate(display_list):
            size = 36
            if num == self.beginning_select_index:
                color = (255, 0, 0)
            else:
                color = (0, 0, 0)
            self.information.show_text(screen=self.screen,
                                       pos=(width / 4 + size * 2, height / 3 * 1 + size * (num + 2.5)), text=i,
                                       color=color, size=size)  # 显示上一次的鼠标位置

    def event_control(self):
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




#
#
# class Control():
#     """
#     'Homing Missle':
#         'Local IP'
#         'Create Game':
#             'host_ip'
#             'other player1'
#             'other player2'
#             'Start',
#             'Cancel'
#         'Join Game'
#         'Exit'
#     """
#     def get_localip(self):
#         pass
#
#     def nodelist_make(self):
#         pass
#
#     def main(self):
#
#
#         # start_node
#         start_node = Node('HomingMissile')
#         start_node.parent = start_node  # 原始节点的父亲节点就是自己
#         localip = get_localip()
#         localip_node = Node('Local IP:' + localip)
#         create_node = Node('Create Game')
#         join_node = Node('Join Game')
#         exit_node = Node('Exit')
#         start_node.add(localip_node)
#         start_node.add(create_node)
#         start_node.add(join_node)
#         start_node.add(exit_node)
#
#         # create_node
#         hostip_node = Node('Host IP:' + localip)
#         start
#         start_node.children=[Node('Multiplayer'),Node('SingleTest'),Node('Exit')]
#
#         # join_node
#
#         # exit_node
#         # window.exit =
#
#         # show screen
#         window = Widget()
#         window.main_loop()
#

if __name__ == "__main__":
    widget = Widget()
    widget.main_loop()