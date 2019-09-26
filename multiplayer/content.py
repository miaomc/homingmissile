# -*- coding: cp936 -*-
import os
import sys
import time
import socket
import pygame
import threading
import Queue
import json
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

        # UDP connect
        address = (self.localip(), self.port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(address)
        print('Bind socket %s ok.' % str(address))
        self.done = False

        # MSG QUEUE
        self.q = Queue.Queue()  # GET
        self.q_send = Queue.Queue()

        # UDP sending
        thread_send = threading.Thread(target=self.msg_send)
        thread_send.setDaemon(True)
        thread_send.start()

        # UDP listening
        thread1 = threading.Thread(target=self.msg_recv)
        thread1.setDaemon(True)  # True:����ע������̣߳����߳�����ͽ�������python process
        thread1.start()

    def msg_send(self):
        """self.q_send����ͨ���ݶ��󣬴����ʱ����json.dumps"""
        while not self.done:
            if not self.q_send.empty():
                msg,dest = self.q_send.get()
                self.sock.sendto(json.dumps(msg), dest)
                print('SEND [%s]:%s' % (str(dest), json.dumps(msg)))

    def msg_recv(self):
        while not self.done:
            data, address = self.sock.recvfrom(1024)  # data=JSON, address=(ip, port)
            self.q.put((json.loads(data),address[0]))  # ��ȡ���ݣ�������ת��Ϊ�������ݣ�����ֻ��ȡip������ȡport

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
        pygame.mixer.init()  # ������ʼ��
        pygame.display.set_mode(SCREEN_SIZE)

        self.fps = 20  # FPS
        self.frame = 0
        self.clock = pygame.time.Clock()
        self.BACKGROUND_COLOR = (168, 168, 168)
        self.screen = pygame.display.get_surface()
        self.screen_rect = self.screen.get_rect()
        self.information = information.Information()
        # self.sound_return = pygame.mixer.Sound()
        # self.sound_selecting = pygame.mixer.Sound()

        self.sock = Sock()

        self.dict_player = {}

    def get_localip(self):
        return self.sock.localip()

    # CREATE FUNCTION
    def create_func(self, node):
        """msg_player = {'ip': localip,
                      'location': (randint(MARS_MAP_SIZE[0] / 5, MARS_MAP_SIZE[0] * 4 / 5),
                                   randint(MARS_MAP_SIZE[1] / 5, MARS_MAP_SIZE[1] * 4 / 5)),
                      'Plane': plane_type,
                      'Gun': 200,
                      'Rocket': 10,
                      'Cobra': 3,}
        """
        print('create..')
        self.sock.q_send.put(('Oh, test.',('192.168.0.102',self.sock.port)))
        while not self.sock.q.empty():
            msg,ip = self.sock.q.get()
            node.add(Node(ip))
            self.dict_player[ip] = msg

    # JOIN FUNCTION
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
        node.add(Node('updating host list..'))

    # EXIT FUNCTION
    def exit_func(self):
        self.done = True

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
        start_node.parent = start_node  # ԭʼ�ڵ�ĸ��׽ڵ�����Լ�
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
        create_node.add(hostip_node)
        create_node.target = self.create_func
        create_node.args = (create_node)

        # JOIN_NODE
        join_node.target = self.join_func
        join_node.args = (join_node)

        # EXIT_NODE
        exit_node.target = self.exit_func

        return start_node


    def main_loop(self):
        # ����Ŀ¼��
        self.root_node = self.nodetree_produce()
        # �ʼ��ѡ��˵�        
        self.beginning_select_index = 0
        self.has_chosen = False
        self.has_backspace = False

        self.menu_title = self.root_node.label
        self.list_node = self.root_node.children
        self.node_point = self.root_node

        # ��Ϸѡ�����
        self.done = False
        while not self.done:
            self.frame += 1
            # ÿ��1s�ͽ���һ�ε�ǰ�ڵ������ˢ��
            if self.frame%self.fps == 0:
                self.node_point.be_chosen()
                self.list_node = self.node_point.children
            # ������ʾ
            self.display_list = [i.label for i in self.list_node]
            self.draw(self.display_list)
            self.event_control()
            pygame.display.flip()
            self.clock.tick(self.fps)
            if self.has_chosen:
                # �����ѡ��������Ӽ�����������Ӽ�
                if not self.has_backspace: #and
                    self.node_point = self.list_node[self.beginning_select_index]
                    self.node_point.be_chosen()
                    if self.node_point.children:  # ���Ӽ����滻rootָ��
                        self.list_node = self.node_point.children
                        self.beginning_select_index = 0
                    else:
                        self.node_point = self.node_point.parent
                #  ������һ�㣺������˻���Ϊȡ��
                elif self.has_backspace or self.list_node[self.beginning_select_index].label == 'Cancel':
                    if self.node_point.parent:
                        self.node_point = self.node_point.parent
                    self.list_node = self.node_point.children
                    self.has_backspace = False
                    self.beginning_select_index = 0
                # ��ӡ����û����Ӧ��ֵ
                else:
                    print self.list_node[self.beginning_select_index].label
                    # break  # Start from here!!!!!!!!!!!!!!!!!!
                self.has_chosen = False

    def draw(self, display_list):
        self.screen.fill(self.BACKGROUND_COLOR)
        # ���ñ��� Homing Missile
        width, height = self.screen_rect[2:4]
        self.information.show_text(screen=self.screen, pos=(width / 3, height / 3 * 1), text=u"Homing Missile",
                                   size=48,
                                   bold=True)  # ��ʾʵʱ״̬����
        # ����ѡ��
        for num, i in enumerate(display_list):
            size = 36
            if num == self.beginning_select_index:
                color = (255, 0, 0)
            else:
                color = (0, 0, 0)
            self.information.show_text(screen=self.screen,
                                       pos=(width / 4 + size * 2, height / 3 * 1 + size * (num + 2.5)), text=i,
                                       color=color, size=size)  # ��ʾ��һ�ε����λ��

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
#         start_node.parent = start_node  # ԭʼ�ڵ�ĸ��׽ڵ�����Լ�
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