  # -*- coding: cp936 -*-
"""
当前主机探测直接采用udp群发消息，没有采用多线程tcp探测主机端口和arp缩小主机范围
目前已经打开 8987 TCP 主机探测端口； 8988 UDP 游戏初始化端口
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
        """根据label，更新自身children列表，删除other这个node"""
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
        thread1.setDaemon(True)  # True:不关注这个子线程，主线程跑完就结束整个python process
        thread1.start()

        # TCP listening
        thread_tcp = threading.Thread(target=self.tcp_server)
        thread_tcp.setDaemon(True)  # True:不关注这个子线程，主线程跑完就结束整个python process
        thread_tcp.start()


    def close(self):
        self.sock.close()
        self.sock_tcp.close()

    def tcp_server(self):
        """任何程序都开启这个TCP监听"""
        self.sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_tcp.bind((self.localip(), self.port_tcp))
        self.sock_tcp.listen(20)
        while not self.done:
            client_onnect, client_address = self.sock_tcp.accept()
            # data, address = self.sock_tcp.recv(1024)
            client_onnect.close()

    def msg_send(self):
        """
        self.q_send是普通数据对象，传输的时候会加json.dumps
        注： 消息队列不包含port，port都集成在这里
        """
        while not self.done:
            if not self.q_send.empty():
                msg, ip = self.q_send.get()
                self.sock.sendto(json.dumps(msg), (ip, self.port))
                logging.info('SEND [%s]:%s' % (ip + ':' + str(self.port), json.dumps(msg)))

    def msg_recv(self):
        """
        注： 消息队列不包含port，port在这里直接剔除了
        这里有个error: [Errno 10054]，有可能是winsock自身的bug：
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
                self.q.put((json.loads(data), address[0]))  # 获取数据，将数据转换为正常数据，并且只提取ip，不提取port
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
                s.settimeout(0.1)  # 100ms,需要采用多线程来编写，要不然主机探测时间将达到接近25s， to be coninue..
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
                hostip_list.append(ip)  # 记录ip地址，port就不记录了
            else:
                other_msg.append(((info, msg), ip))
        for i in other_msg:  # 将剩余非建主机的消息放回队列
            self.q.put(i)
        return hostip_list

    def broadcast(self, messages, ip_list):
        for i in ip_list:
            self.q_send.put((messages, i))

    def host_broadcast(self):
        """群发这么多人也不是个办法，to be continue.."""
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
                            filemode='w')  # 每次真正import logging之后，filemode为w就会清空内容

        SCREEN_SIZE = (800, 600)
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        pygame.mixer.init()  # 声音初始化
        pygame.display.set_mode(SCREEN_SIZE)
        pygame.mouse.set_visible(False)

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
                                'Gun':200, 'Rocket':10, 'Cobra':3}，
                        }
        """
        if not (self.frame % self.frame_chosen_gap ==0 or self.create_bool==False):  # 每*1帧发一次
            return
        # 局域网同网段群发
        self.sock.host_broadcast()

        if not self.create_bool:
            node.add(Node(u'主机(host):' + self.localip))
            self.sock.q_send.put((('player join', self.msg_player), self.localip))  # 先给自己发个消息，自己就是主机
            self.create_bool = True

            start_node = Node(u'开始游戏(Start)')
            node.add(start_node)
            start_node.target = self.start_func
            # to be con...
        while not self.sock.q.empty():
            (info, msg), ip = self.sock.q.get()  # 接受处理单个玩家的加入消息msg_player
            if info == 'player join' and ip not in node.get_children_label():
                node.add(Node(ip)) # 添加
                self.dict_player[ip] = msg
                for i in self.dict_player.keys():  # 给所有ip都发送所有玩家信息self.dict_player
                    if i != self.localip:  # 自己是主机，就不用发自己了
                        self.sock.q_send.put((('dict_player', self.dict_player), i))
            elif info == 'player exit':  # 处理收到玩家退出消息，删除玩家
                if self.dict_player.has_key(ip):
                    self.dict_player.pop(ip)
                    node.pop(label=ip)  # 删除
                    for i in self.dict_player.keys():  # 给所有ip都发送所有玩家信息self.dict_player
                        if i != self.localip:  # 自己是主机，就不用发自己了
                            self.sock.q_send.put((('dict_player', self.dict_player), i))

    def create_func_back(self, node):
        self.create_bool = False
        for i in node.children:
            del i
        node.children = []
        for i in self.dict_player.keys():  # 给所有ip都发送所有玩家信息self.dict_player
            if i != self.localip:  # 自己是主机，就不用发自己了
                self.sock.q_send.put((('host exit', ''), i))

    # JOIN FUNCTION
    def scan_hostip(self):
        return self.sock.scan_hostip()

    def join_func(self, node):
        if not(self.frame % (self.frame_chosen_gap*2) == 0 or self.join_func_bool==False):  # 每*2帧探测一次
            return
        self.join_func_bool = True
        hostip_list = self.scan_hostip()
        # children_list = []  # 把不在主机列表的node节点都清除
        # for node_ in node.children:
        #     if node_.label not in hostip_list:
        #         del (node_)
        #     else:
        #         children_list.append(node_)
        # node.children = children_list
        node.children = [node_ for node_ in node.children if node_.label in hostip_list]  # 把不在主机列表的node节点都清除
        for ip in hostip_list:  # 添加新的主机node节点
            if ip in node.get_children_label():
                continue  # 一直在就不重新添加
            ip_node = Node(ip)
            node.add(ip_node)
            ip_node.target = self.join_enter
            ip_node.args = (ip_node, ip)
            ip_node.back_target = self.join_enter_back
            ip_node.back_args = (ip)
        node.add(Node(u'自动刷新已经建立的主机（auto-updating host）..'))
    
    def join_func_back(self):
        self.join_func_bool = False
        
    # JOIN_ENTER FUNCTION
    def join_enter(self, (node, host_ip)):
        if not self.join_enter_bool:
            self.sock.q_send.put((('player join', self.msg_player), host_ip))  # 先给主机发个加入
            self.join_enter_bool = True

        # 获取&更新 self.dict_player
        while not self.sock.q.empty():
            (info, dict_player), ip = self.sock.q.get()
            if info == 'dict_player':
                self.dict_player = dict_player  # 直接等于主机所发送的dict_player
            elif info == 'host exit':
                self.has_backspace = True  # 自动回退
                self.has_selected = True
            elif info == 'start game':
                self.start_game()
        # 清空&刷新
        for i in node.children:
            del (i)
        node.children = []
        if 'Host:' + host_ip not in node.get_children_label():
            node.add(Node(u'主机地址(host):' + host_ip))
        for i in self.dict_player.keys():
            node.add(Node(i))
        node.add(Node(u'等待主机开始游戏(waiting host to "Start")..'))

    def join_enter_back(self, host_ip):
        self.join_enter_bool = False
        self.sock.q_send.put((('player exit', ''), host_ip))  # 发送消息给主机
        self.dict_player = {self.localip: self.msg_player}  # dict_player就只有自己了

    # EXIT FUNCTION
    def exit_func(self):
        self.done = True

    # START FUNCTION
    def start_func(self):
        for i in self.dict_player.keys():  # 给所有ip都发送所有玩家信息self.dict_player
            if i != self.localip:  # 自己是主机，就不用发自己了
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
        start_node.parent = start_node  # 原始节点的父亲节点就是自己
        # localip = self.get_localip()
        localip_node = Node(u'本机IP(localip):' + self.localip)
        create_node = Node(u'创建游戏(Create)')
        join_node = Node(u'加入游戏(Join)')
        exit_node = Node(u'退出(Exit)')
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
        # 生成目录树
        self.root_node = self.nodetree_produce()
        # 最开始的选择菜单        
        self.beginning_select_index = 0
        self.has_selected = False
        self.has_backspace = False

        self.menu_title = self.root_node.label
        self.list_node = self.root_node.children
        self.node_point = self.root_node

        # 游戏选择界面
        self.done = False
        while not self.done:
            self.frame += 1
            # 每一帧运行当前节点的子项刷新，当前 帧运行一次
            logging.info(str(self.frame))
            if self.frame % self.frame_chosen_gap == 0:
                self.node_point.be_chosen()
                self.list_node = self.node_point.children
            # 正常显示
            self.display_list = [i.label for i in self.list_node]
            self.draw(self.display_list)
            self.event_control()
            pygame.display.flip()
            self.clock.tick(self.fps)
            if self.has_selected:
                # 如果所选的这个有子集，进入这个子集
                if not self.has_backspace:  # and
                    self.node_point = self.list_node[self.beginning_select_index]
                    self.node_point.be_chosen()
                    if self.node_point.children:  # 有子集就替换root指向
                        self.list_node = self.node_point.children
                        self.beginning_select_index = 0
                    else:
                        self.node_point = self.node_point.parent
                #  返回上一层：向左回退或者为取消
                elif self.has_backspace or self.list_node[self.beginning_select_index].label == 'Cancel':
                    self.node_point.be_backed()
                    if self.node_point.parent:
                        self.node_point = self.node_point.parent
                    self.list_node = self.node_point.children
                    self.has_backspace = False
                    self.beginning_select_index = 0
                # 打印其他没有响应的值
                else:
                    logging.info(self.list_node[self.beginning_select_index].label)
                    # break  # Start from here!!!!!!!!!!!!!!!!!!
                self.has_selected = False

        self.sock.close()
        pygame.quit()
        return self.start_bool

    def draw(self, display_list):
        self.screen.fill(self.BACKGROUND_COLOR)
        # 设置标题 Homing Missile
        width, height = self.screen_rect[2:4]
        self.information.show_text(screen=self.screen, pos=(width *0.27, height *0.22 * 1), text=u"Homing Missile",
                                   size=40,
                                   bold=True)  # 显示实时状态文字
        # 设置选项
        for num, i in enumerate(display_list):
            size = 22
            if num == self.beginning_select_index:
                color = (255, 0, 0)
            else:
                color = (0, 0, 0)
            self.information.show_text(screen=self.screen,
                                       pos=(width / 4 + size * 2, height *0.4 + size * num*1.2 ), text=i,
                                       color=color, size=size)  # 显示选择菜单位置

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
