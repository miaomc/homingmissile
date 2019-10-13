  # -*- coding: cp936 -*-
"""
��ǰ����̽��ֱ�Ӳ���udpȺ����Ϣ��û�в��ö��߳�tcp̽�������˿ں�arp��С������Χ
Ŀǰ�Ѿ��� 8987 TCP ����̽��˿ڣ� 8988 UDP ��Ϸ��ʼ���˿�
"""
import os
import sys
import time
import socket
import pygame
import threading
import Queue
import json
from random import randint
import logging
import information
import plane_player

PORT = 8988
TCP_PORT = 8987

class Node():
    def __init__(self, label):
        self.parent = None
        self.children = []
        self.label = label
        self.target = None
        self.args = None
        self.back_target = None
        self.back_args = None

    def add(self, other):
        self.children.append(other)
        other.parent = self

    def pop(self, label):
        """����label����������children�б�ɾ��other���node"""
        other = None
        other_index = None
        for n,i in enumerate(self.children):
            if i.label == label:
                other = i
                other_index = n
                break
        if other_index:
            del self.children[n]
            del other

    def be_chosen(self):
        if self.target:
            if self.args:
                return self.target(self.args)
            else:
                return self.target()
        else:
            return None

    def be_backed(self):
        if self.back_target:
            if self.back_args:
                return self.back_target(self.back_args)
            else:
                return self.back_target()
        else:
            return None

    def get_children_label(self):
        return [i.label for i in self.children]


class Sock():
    def __init__(self):
        self.port = PORT
        self.port_tcp = TCP_PORT

        # UDP connect
        address = (self.localip(), self.port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(address)
        logging.info('Bind socket %s ok.' % str(address))
        self.done = False

        # MSG QUEUE
        self.q = Queue.Queue()  # GET  [((info,msg), ip), (), ...]
        self.q_send = Queue.Queue()  # SEND [((info,msg), ip), (), ...]

        # UDP sending
        thread_send = threading.Thread(target=self.msg_send)
        thread_send.setDaemon(True)
        thread_send.start()

        # UDP listening
        thread1 = threading.Thread(target=self.msg_recv)
        thread1.setDaemon(True)  # True:����ע������̣߳����߳�����ͽ�������python process
        thread1.start()

        # TCP listening
        thread_tcp = threading.Thread(target=self.tcp_server)
        thread_tcp.setDaemon(True)  # True:����ע������̣߳����߳�����ͽ�������python process
        thread_tcp.start()


    def close(self):
        self.sock.close()

    def tcp_server(self):
        """�κγ��򶼿������TCP����"""
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.bind((self.localip(), self.port_tcp))
        sock_tcp.listen(20)
        while not self.done:
            client_onnect, client_address = sock_tcp.accept()
            # data, address = sock_tcp.recv(1024)
            client_onnect.close()

    def msg_send(self):
        """
        self.q_send����ͨ���ݶ��󣬴����ʱ����json.dumps
        ע�� ��Ϣ���в�����port��port������������
        """
        while not self.done:
            if not self.q_send.empty():
                msg, ip = self.q_send.get()
                self.sock.sendto(json.dumps(msg), (ip, self.port))
                logging.info('SEND [%s]:%s' % (ip + ':' + str(self.port), json.dumps(msg)))

    def msg_recv(self):
        """
        ע�� ��Ϣ���в�����port��port������ֱ���޳���
        �����и�error: [Errno 10054]���п�����winsock�����bug��
        If sending a datagram using the sendto function results in an "ICMP port unreachable" response and the select
        function is set for readfds, the program returns 1 and the subsequent call to the recvfrom function does not
        work with a WSAECONNRESET (10054) error response. In Microsoft Windows NT 4.0, this situation causes the select
         function to block or time out.
        """
        while not self.done:
            try:
                data, address = self.sock.recvfrom(1024)  # data=JSON, address=(ip, port)
                logging.info('RECV [%s]:%s' % (address[0] + ':' + str(self.port), data))
                self.q.put((json.loads(data), address[0]))
            except Exception,msg:
                logging.warning('SOCK RECV ERROR-->%s'%msg)
                logging.info('RECV [%s]:%s' % (address[0] + ':' + str(self.port), data))
                self.q.put((json.loads(data), address[0]))  # ��ȡ���ݣ�������ת��Ϊ�������ݣ�����ֻ��ȡip������ȡport
            # data, address = self.sock.recvfrom(1024)  # data=JSON, address=(ip, port)
            # logging.info('RECV [%s]:%s' % (address[0] + ':' + str(self.port), data))
            # self.q.put((json.loads(data) , address[0]))

    def localip(self):
        return socket.gethostbyname(socket.gethostname())

    def scan_ip_tcp(self):
        time_start = time.time()
        ip_up = []
        ip_head = '.'.join(self.localip().split('.')[0:3])
        ip_list = [ip_head + '.' + str(i) for i in range(256)]
        port_list = [self.port_tcp]
        for ip in ip_list:
            # logging.info('Scan %s' % ip)
            up = False
            for port in port_list:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.1)  # 100ms,��Ҫ���ö��߳�����д��Ҫ��Ȼ����̽��ʱ�佫�ﵽ�ӽ�25s�� to be coninue..
                # print 'scan..'
                result = s.connect_ex((ip, port))
                # print (ip,port),
                if result == 0:
                    print ip
                    logging.info('Port %d: open' % (port))
                    up = True
                s.close()
            if up:
                ip_up.append(ip)
        time_end = time.time()
        # logging.info('IP Scan:%s'%ip_list)
        # logging.info('IP Scan:%s'%port_list)
        logging.info('PortScan done! %d IP addresses (%d hosts up) scanned in %f seconds.' % (
            len(ip_list), len(ip_up), time_end - time_start))
        logging.info('Up hosts:')
        for i in ip_up:
            logging.info(i)
        # return [self.localip()]
        return ip_up

    def scan_ip_arp(self):
        pass

    def scan_hostip(self):
        hostip_list = []
        other_msg = []
        while not self.q.empty():
            (info, msg), ip = self.q.get()
            if info == 'host created':
                hostip_list.append(ip)  # ��¼ip��ַ��port�Ͳ���¼��
            else:
                other_msg.append(((info, msg), ip))
        for i in other_msg:  # ��ʣ��ǽ���������Ϣ�Żض���
            self.q.put(i)
        return hostip_list

    def broadcast(self, messages, ip_list):
        for i in ip_list:
            self.q_send.put((messages, i))

    def host_broadcast(self):
        """Ⱥ����ô����Ҳ���Ǹ��취��to be continue.."""
        ip_head = '.'.join(self.localip().split('.')[0:3])
        # ip_list = [ip_head + '.' + str(i) for i in range(100, 111, 1)]  # test, to be con...
        ip_list = [ip_head + '.' + str(i) for i in range(256)]
        # ip_list = self.scan_ip_tcp()
        logging.info('broadcast host ip list:%s' % str(ip_list))
        self.broadcast(messages=('host created', ''), ip_list=ip_list)


class Widget():
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG,  # CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
                            format='%(asctime)s [line:%(lineno)d] [%(levelname)s] %(message)s',
                            filename='logger.log',
                            filemode='w')  # ÿ������import logging֮��filemodeΪw�ͻ��������

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
        self.localip = self.get_localip()

        self.msg_player = {'location': (randint(20, 80) / 100.0, randint(20, 80) / 100.0),
                           'Plane': 'F35',
                           'Gun': 200, 'Rocket': 10, 'Cobra': 3, }
        self.dict_player = {self.localip: self.msg_player}

        self.create_bool = False
        self.join_func_bool = False
        self.join_enter_bool = False
        self.start_bool = False

        self.frame_chosen_gap = self.fps*2

    def get_localip(self):
        return self.sock.localip()

    # CREATE FUNCTION
    def create_func(self, node):
        """dict_player = {'ip':
                                {'location':(randint(20,80)/100.0,randint(20,80)/100.0),
                                'Plane':'F35',
                                'Gun':200, 'Rocket':10, 'Cobra':3}��
                        }
        """
        if not (self.frame % self.frame_chosen_gap ==0 or self.create_bool==False):  # ÿ*1֡��һ��
            return
        # ������ͬ����Ⱥ��
        self.sock.host_broadcast()

        if not self.create_bool:
            node.add(Node(u'����(host):' + self.localip))
            self.sock.q_send.put((('player join', self.msg_player), self.localip))  # �ȸ��Լ�������Ϣ���Լ���������
            self.create_bool = True

            start_node = Node(u'��ʼ��Ϸ(Start)')
            node.add(start_node)
            start_node.target = self.start_func
            # to be con...
        while not self.sock.q.empty():
            (info, msg), ip = self.sock.q.get()  # ���ܴ�������ҵļ�����Ϣmsg_player
            if info == 'player join' and ip not in node.get_children_label():
                node.add(Node(ip)) # ���
                self.dict_player[ip] = msg
                for i in self.dict_player.keys():  # ������ip���������������Ϣself.dict_player
                    if i != self.localip:  # �Լ����������Ͳ��÷��Լ���
                        self.sock.q_send.put((('dict_player', self.dict_player), i))
            elif info == 'player exit':  # �����յ�����˳���Ϣ��ɾ�����
                if self.dict_player.has_key(ip):
                    self.dict_player.pop(ip)
                    node.pop(label=ip)  # ɾ��
                    for i in self.dict_player.keys():  # ������ip���������������Ϣself.dict_player
                        if i != self.localip:  # �Լ����������Ͳ��÷��Լ���
                            self.sock.q_send.put((('dict_player', self.dict_player), i))

    def create_func_back(self, node):
        self.create_bool = False
        for i in node.children:
            del i
        node.children = []
        for i in self.dict_player.keys():  # ������ip���������������Ϣself.dict_player
            if i != self.localip:  # �Լ����������Ͳ��÷��Լ���
                self.sock.q_send.put((('host exit', ''), i))

    # JOIN FUNCTION
    def scan_hostip(self):
        return self.sock.scan_hostip()

    def join_func(self, node):
        if not(self.frame % (self.frame_chosen_gap*2) == 0 or self.join_func_bool==False):  # ÿ*2֡̽��һ��
            return
        self.join_func_bool = True
        hostip_list = self.scan_hostip()
        # children_list = []  # �Ѳ��������б��node�ڵ㶼���
        # for node_ in node.children:
        #     if node_.label not in hostip_list:
        #         del (node_)
        #     else:
        #         children_list.append(node_)
        # node.children = children_list
        node.children = [node_ for node_ in node.children if node_.label in hostip_list]  # �Ѳ��������б��node�ڵ㶼���
        for ip in hostip_list:  # ����µ�����node�ڵ�
            if ip in node.get_children_label():
                continue  # һֱ�ھͲ��������
            ip_node = Node(ip)
            node.add(ip_node)
            ip_node.target = self.join_enter
            ip_node.args = (ip_node, ip)
            ip_node.back_target = self.join_enter_back
            ip_node.back_args = (ip)
        node.add(Node(u'�Զ�ˢ���Ѿ�������������auto-updating host��..'))
    
    def join_func_back(self):
        self.join_func_bool = False
        
    # JOIN_ENTER FUNCTION
    def join_enter(self, (node, host_ip)):
        if not self.join_enter_bool:
            self.sock.q_send.put((('player join', self.msg_player), host_ip))  # �ȸ�������������
            self.join_enter_bool = True

        # ��ȡ&���� self.dict_player
        while not self.sock.q.empty():
            (info, dict_player), ip = self.sock.q.get()
            if info == 'dict_player':
                self.dict_player = dict_player  # ֱ�ӵ������������͵�dict_player
            elif info == 'host exit':
                self.has_backspace = True  # �Զ�����
                self.has_selected = True
            elif info == 'start game':
                self.start_game()
        # ���&ˢ��
        for i in node.children:
            del (i)
        node.children = []
        if 'Host:' + host_ip not in node.get_children_label():
            node.add(Node(u'������ַ(host):' + host_ip))
        for i in self.dict_player.keys():
            node.add(Node(i))
        node.add(Node(u'�ȴ�������ʼ��Ϸ(waiting host to "Start")..'))

    def join_enter_back(self, host_ip):
        self.join_enter_bool = False
        self.sock.q_send.put((('player exit', ''), host_ip))  # ������Ϣ������
        self.dict_player = {self.localip: self.msg_player}  # dict_player��ֻ���Լ���

    # EXIT FUNCTION
    def exit_func(self):
        self.done = True

    # START FUNCTION
    def start_func(self):
        for i in self.dict_player.keys():  # ������ip���������������Ϣself.dict_player
            if i != self.localip:  # �Լ����������Ͳ��÷��Լ���
                self.sock.q_send.put((('start game', ''), i))
        self.start_game()

    def start_game(self):
        with open('player_dict.dat','w') as f:
            json.dump(self.dict_player,f)
            logging.info("start:write in players' data..ok")
        self.exit_func()
        self.start_bool = True
        logging.info('start:content is done')

    def nodetree_produce(self):
        """
        'Homing Missile':
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
        # localip = self.get_localip()
        localip_node = Node(u'����IP(localip):' + self.localip)
        create_node = Node(u'������Ϸ(Create)')
        join_node = Node(u'������Ϸ(Join)')
        exit_node = Node(u'�˳�(Exit)')
        start_node.add(localip_node)
        start_node.add(create_node)
        start_node.add(join_node)
        start_node.add(exit_node)

        # CREATE_NODE
        create_node.target = self.create_func
        create_node.args = (create_node)
        create_node.back_target = self.create_func_back
        create_node.back_args = (create_node)

        # JOIN_NODE
        join_node.target = self.join_func
        join_node.args = (join_node)
        join_node.back_target = self.join_func_back

        # EXIT_NODE
        exit_node.target = self.exit_func

        return start_node

    def main_loop(self):
        # ����Ŀ¼��
        self.root_node = self.nodetree_produce()
        # �ʼ��ѡ��˵�        
        self.beginning_select_index = 0
        self.has_selected = False
        self.has_backspace = False

        self.menu_title = self.root_node.label
        self.list_node = self.root_node.children
        self.node_point = self.root_node

        # ��Ϸѡ�����
        self.done = False
        while not self.done:
            self.frame += 1
            # ÿһ֡���е�ǰ�ڵ������ˢ�£���ǰ ֡����һ��
            logging.info(str(self.frame))
            if self.frame % self.frame_chosen_gap == 0:
                self.node_point.be_chosen()
                self.list_node = self.node_point.children
            # ������ʾ
            self.display_list = [i.label for i in self.list_node]
            self.draw(self.display_list)
            self.event_control()
            pygame.display.flip()
            self.clock.tick(self.fps)
            if self.has_selected:
                # �����ѡ��������Ӽ�����������Ӽ�
                if not self.has_backspace:  # and
                    self.node_point = self.list_node[self.beginning_select_index]
                    self.node_point.be_chosen()
                    if self.node_point.children:  # ���Ӽ����滻rootָ��
                        self.list_node = self.node_point.children
                        self.beginning_select_index = 0
                    else:
                        self.node_point = self.node_point.parent
                #  ������һ�㣺������˻���Ϊȡ��
                elif self.has_backspace or self.list_node[self.beginning_select_index].label == 'Cancel':
                    self.node_point.be_backed()
                    if self.node_point.parent:
                        self.node_point = self.node_point.parent
                    self.list_node = self.node_point.children
                    self.has_backspace = False
                    self.beginning_select_index = 0
                # ��ӡ����û����Ӧ��ֵ
                else:
                    logging.info(self.list_node[self.beginning_select_index].label)
                    # break  # Start from here!!!!!!!!!!!!!!!!!!
                self.has_selected = False

        self.sock.close()
        pygame.quit()
        return self.start_bool

    def draw(self, display_list):
        self.screen.fill(self.BACKGROUND_COLOR)
        # ���ñ��� Homing Missile
        width, height = self.screen_rect[2:4]
        self.information.show_text(screen=self.screen, pos=(width *0.27, height *0.22 * 1), text=u"Homing Missile",
                                   size=40,
                                   bold=True)  # ��ʾʵʱ״̬����
        # ����ѡ��
        for num, i in enumerate(display_list):
            size = 22
            if num == self.beginning_select_index:
                color = (255, 0, 0)
            else:
                color = (0, 0, 0)
            self.information.show_text(screen=self.screen,
                                       pos=(width / 4 + size * 2, height *0.4 + size * num*1.2 ), text=i,
                                       color=color, size=size)  # ��ʾѡ��˵�λ��

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
                    self.has_selected = True
                if event.key in [pygame.K_RETURN, pygame.K_RIGHT]:
                    self.has_selected = True
                    # self.sound_return.play()


if __name__ == "__main__":
    widget = Widget()
    if widget.main_loop():
        logging.info('-------------------plane_player.main() start-------------------')
        plane_player.main()
