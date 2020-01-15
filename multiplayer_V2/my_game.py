# -*- coding: utf-8 -*-
import pygame
import math
import os
from random import randint
import socket
import threading
from queue import Queue  # to be continue
import json
import logging
from information import Information


class Vector:
    def __init__(self, *args):
        if len(args) == 2:
            self.x = args[0]
            self.y = args[1]
        elif len(args[0]) == 2:
            self.x = args[0][0]
            self.y = args[0][1]
        else:
            logging.info('Invalid Vector:', args)

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, a):
        """乘以常量a"""
        return Vector(self.x * a, self.y * a)

    def __div__(self, a):
        return Vector(self.x / a, self.y / a)

    def __str__(self):
        return str(self.x) + ', ' + str(self.y)

    def __len__(self):
        return 2

    def __getitem__(self, item):
        if item == 0:
            return self.x
        if item == 1:
            return self.y

    # def __neg__(self):
    #     return Vector(-self.x, -self.y)

    def normalize_vector(self):
        """单位向量"""
        return Vector(self.x, self.y) * self.reverse_normalize()

    def reverse_normalize(self):
        """1/向量长度"""
        if self.x == 0 and self.y == 0:
            return 0
        else:
            return 1 / math.sqrt(self.x * self.x + self.y * self.y)

    def length(self):
        """向量长度"""
        return math.sqrt(self.x * self.x + self.y * self.y)

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    def angle(self):
        """
        本身的角度，带方向的。由于pygame的坐标特性，顺时针为正. 返回的为pi，不是度
        """
        return math.atan2(self.y, self.x)

    def vertical_left(self):
        """左转90°的法向量"""
        return Vector(self.y * self.reverse_normalize(), -self.x * self.reverse_normalize())

    def vertical_right(self):
        """左转90°的法向量"""
        return Vector(-self.y * self.reverse_normalize(), self.x * self.reverse_normalize())





class Game(object):

    def __init__(self):
        self.local_ip = None
        self.other_ip = None
        self.host_ip = None
        self.sock = None
        self.port = 8989

        self.re_local_ip = LOCALIP
        self.re_msg_player = None
        self.re_c_or_j = C_OR_J
        self.re_host_ip = HOSTIP

        self.local_player = None
        self.num_player = 0
        self.lock_frame = 0
        self.delay_frame = 0
        # self.start_time = 0

        self.show_result = False  # 用来显示Win or Lose
        self.hide_result = False
        self.last_tab_frame = 0

        self.screen_focus_obj = None  # 默认为空，首次指向本地plane, 空格指向本地plane, 为空但是本地plane还存在就指向plane

    def game_init(self, localip):
        logging.basicConfig(level=logging.DEBUG,  # CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
                            format='%(asctime)s [line:%(lineno)d] [%(levelname)s] %(message)s',

                            filename='logger.log',
                            filemode='a')

        self.done = False
        self.map = None
        self.minimap = None
        # self.current_rect = self.screen.get_rect()

        self.player_list = []
        self.d = {}

        # UDP server
        address = (localip, self.port)
        if self.sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(address)
            logging.info('Bind socket %s ok.' % str(address))
        else:
            pygame.time.wait(1200)
            while not self.q.empty():
                self.q.get()

        self.syn_frame = 0

        # MSG QUEUE
        self.q = queue.queue()  # GET
        self.q_send = queue.queue()

        # UDP sending
        self.thread_send = threading.Thread(target=self.msg_send)
        self.thread_send.setDaemon(True)
        self.thread_send.start()

        # UDP listening
        self.thread1 = threading.Thread(target=self.msg_recv)
        self.thread1.setDaemon(True)  # True:不关注这个子线程，主线程跑完就结束整个python process
        self.thread1.start()

        # sprite group
        self.plane_group = pygame.sprite.Group()
        self.weapon_group = pygame.sprite.Group()
        self.tail_group = pygame.sprite.Group()
        self.box_group = pygame.sprite.Group()
        self.health_group = pygame.sprite.Group()

        # backup map
        self.origin_map = None

        # Info show
        self.info = Information()

    def screen_init(self):
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        pygame.mixer.init()  # 声音初始化
        pygame.display.init()  # 初始化
        pygame.event.get()
        pygame.mouse.set_visible(False)
        display_info = pygame.display.Info()
        ret = pygame.display.set_mode(flags=pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        # ret = pygame.display.set_mode(size=(1366,768), flags=pygame.FULLSCREEN|pygame.HWSURFACE|pygame.DOUBLEBUF)
        logging.info('DISPLAY:%s' % str(ret))
        # pygame.display.set_mode(flags=pygame.FULLSCREEN, depth=0)
        # screen_size_fittable = (display_info.current_w * 19 / 20, display_info.current_h * 17 / 20)
        # if screen_size_fittable[0] * screen_size_fittable[1] > 0:
        #     pygame.display.set_mode(screen_size_fittable)
        # else:
        #     pygame.display.set_mode(SCREEN_SIZE)
        # Return the size of the window or screen
        # pygame.display.get_window_size()
        self.screen = pygame.display.get_surface()  # 游戏窗口对象
        self.screen_rect = self.screen.get_rect()  # 游戏窗口对象的rect
        logging.info('DISPLAY:%s' % self.screen_rect)

        # 更新游戏地图（MARS）与显示地图的比例
        global MARS_RATIO
        MARS_RATIO = (float(MARS_SCREEN_SIZE[0]) / self.screen_rect.w, float(MARS_SCREEN_SIZE[1]) / self.screen_rect.h)

        self.move_pixels = 30
        self.fps = FPS
        self.clock = pygame.time.Clock()

    #     self.mars_ratio = (float(MARS_SCREEN_SIZE[0])/self.screen_rect.w, float(MARS_SCREEN_SIZE[1])/self.screen_rect.h)
    #
    # def mars_translate(coordinate):
    #     """translate Mars Coordinate to current Display Coordinate"""
    #     return [int(coordinate[i] / self.mars_ratio[i]) for i in [0, 1]]
    #
    # def mars_unti_translate(coordinate):
    #     return [int(coordinate[i] * self.mars_ratio[i]) for i in [0, 1]]

    def msg_send(self):
        while not self.done:
            if not self.q_send.empty():
                msg_dumped, dest = self.q_send.get()
                self.sock.sendto(msg_dumped, dest)
                logging.info('SEND [%s]:%s' % (str(dest), msg_dumped))

    def msg_recv(self):
        while not self.done:
            data = self.sock.recvfrom(1487)
            self.q.put(data)
            logging.info('RECV %s' % str(data))
            # print("socket get msg.")

    def sock_send(self, msg, dest):
        """strs: unicode string or dict object"""
        self.q_send.put((json.dumps(msg), dest))
        # self.sock.sendto(json.dumps(msg), dest)

    def sock_waitfor(self, msg, dest, delay=100, waiting_times=30):
        count = 0
        while self.q.empty():
            pygame.time.wait(delay)
            count += 1
            if count > waiting_times:
                logging.error('Sock Waiting Timeout: %s' % msg)
                return False
        data, address = self.q.get()
        logging.info('GET:%s' % str(json.loads(data)))
        if address[0] == dest[0]:
            logging.info('Sock Msg Get:%s' % json.loads(data))
            return json.loads(data)
        else:
            logging.error('Sock Wrong Msg:%s %s' % (str(address), json.loads(data)))
            return False

    def add_player(self, player):
        self.player_list.append(player)
        self.plane_group.add(player.plane)
        self.health_group.add(player.plane.health_bar)
        self.num_player += 1

    def init_local_player(self, localip, plane_type):
        msg_player = {'ip': localip,
                      'location': (randint(MARS_MAP_SIZE[0] / 5, MARS_MAP_SIZE[0] * 4 / 5),
                                   randint(MARS_MAP_SIZE[1] / 5, MARS_MAP_SIZE[1] * 4 / 5)),
                      'Plane': plane_type,
                      'Gun': 200,
                      'Rocket': 10,
                      'Cobra': 3,
                      }
        return msg_player

    def msg2player(self, msg_player):
        player = Player(weapon_group=self.weapon_group, ip=msg_player['ip'])
        plane = Plane(catalog=msg_player['Plane'], location=msg_player['location'])
        plane.load_weapon(catalog='Cobra', number=msg_player['Cobra'])
        plane.load_weapon(catalog='Gun', number=msg_player['Gun'])
        plane.load_weapon(catalog='Rocket', number=msg_player['Rocket'])
        player.add_plane(plane)
        return player

    def create_or_join(self):
        if RESTART_MODE:
            if self.re_c_or_j == 'c':
                return True
            else:
                return False
        if raw_input('Input "c" to create game, else "j" to join a game:') == 'c':
            self.re_c_or_j = 'c'
            return True
        else:
            self.re_c_or_j = 'j'
            return False

    def create(self, localip, msg_player):
        print('Game is created. Host IP: %s:%d' % (localip, self.port))
        print('waiting players to entering.'),
        n = 0
        while self.q.empty():
            n += 1
            print('.'),
            if n % 45 == 0:
                print
            pygame.time.wait(500)

        data, address = self.q.get()  # 0.0 join get
        print('Create:GET_INFO:%s %s' % (str(data), str(address)))
        if json.loads(data) == 'join':
            self.sock_send('join_ack', address)  # 1.0 join_ack send
            tmp = self.sock_waitfor('msg_player', address)  # 2.1 msg_player get
            if tmp:
                self.d[address[0]] = tmp
                # self.add_player(self.msg2player(tmp))
                self.sock_send(msg_player, address)  # 3.0
                self.sock_send('msg_player_ack', address)  # 4.0
                if self.sock_waitfor('msg_player_ack', address) == 'msg_player_ack':  # 5.1
                    self.other_ip = address[0]
                    return True
        return False

    def join(self, msg_player, host_ip):
        address = (host_ip, self.port)
        self.sock_send('join', address)  # 0.1 join send
        if self.sock_waitfor('join_ack', address) == 'join_ack':  # 1.1 join_ack get
            self.sock_send(msg_player, address)  # 2.0 msg_player send
            tmp = self.sock_waitfor('msg_player', address)  # 3.1
            if tmp:
                self.d[address[0]] = tmp
                self.sock_send('msg_player_ack', address)  # 5.0
                if self.sock_waitfor('msg_player_ack', address) == 'msg_player_ack':  # 4.1
                    self.other_ip = address[0]
                    return True
        return False

    def render(self, screen_rect):
        self.current_rect = screen_rect
        # logging.info('T3.0:%d' % pygame.time.get_ticks())
        self.screen.blit(source=self.map.surface, dest=(0, 0), area=self.current_rect)  # Cost 5ms
        # self.screen = self.map.surface.subsurface(self.current_rect)  # 黑屏
        # logging.info('T3.1:%d' % pygame.time.get_ticks())
        self.minimap.draw()
        self.slot.draw()  # draw SlotWidget
        # logging.info('T3.2:%d' % pygame.time.get_ticks())
        # self.info.show(self.screen)  # 吃性能所在之处！！！！！！！！！！！！！！！
        # logging.info('T3.3:%d' % pygame.time.get_ticks())
        if self.show_result and not self.hide_result:
            self.info.show_end(self.screen)  # 吃性能所在之处！！！！！！！！！！！！！！！
        # logging.info('T3.4:%d' % pygame.time.get_ticks())

    def player_communicate(self, key_list):
        """
        在World类里面实现，TCP/IP的事件信息交互，Player类只做事件的update()
        发送本地玩家的操作
        """
        if not self.local_player.alive:
            return
        # str_key_list = json.dumps((self.syn_frame, key_list))  # # 如果没操作队列: event_list = key_list = []
        for player in self.player_list:  # 发送给每一个网卡，包括自己
            # print player.ip
            try:
                # logging.info('Send %d---> %s, %s' % (self.syn_frame, str((player.ip, self.port)), str_key_list))
                self.sock_send((self.syn_frame, key_list), (player.ip, self.port))
                # self.sock.sendto(str_key_list, (player.ip, self.port))
                # self.sock.sendto(str_event_list, (player.ip, self.port))  # 发双份
            except Exception as msg:
                logging.warn('Offline(Socket Error):' + str(msg))

    def deal_collide(self):
        """
        self.plane_group = pygame.sprite.Group()
        self.weapon_group = pygame.sprite.Group()
        """
        for weapon in self.weapon_group:  # 遍历每一个武器
            # 如果不是枪弹就进行相互碰撞测试
            if not weapon.alive:
                continue
            if weapon.catalog != 'Gun':
                # print weapon
                weapon_collide_lst = pygame.sprite.spritecollide(weapon, self.weapon_group, False,
                                                                 pygame.sprite.collide_rect_ratio(
                                                                     0.8))  # False代表不直接kill该对象
                weapon.hitted(weapon_collide_lst)  # 发生碰撞相互减血
                # for hitted_weapon in weapon_collide_lst:
                #     hitted_weapon.hitted([weapon])  # 本身受到攻击的对象
            # 检测武器与飞机之间的碰撞        
            plane_collide_lst = pygame.sprite.spritecollide(weapon, self.plane_group, False,
                                                            pygame.sprite.collide_rect_ratio(0.8))
            weapon.hitted(plane_collide_lst)  # 发生碰撞相互减血

    def deal_collide_with_box(self):
        for plane in self.plane_group:  # 进行飞机与Box之间碰撞探测
            box_collide_lst = pygame.sprite.spritecollide(plane, self.box_group, False,
                                                          pygame.sprite.collide_rect_ratio(0.8))
            for box in box_collide_lst:
                box.effect(plane)
                box.delete()

    def syn_status(self):
        if self.syn_frame % (int(2 * FPS)) == 0:  # 每2秒同步一次自己状态给对方
            # print self.player_list, self.local_ip, self.other_ip
            for player in self.player_list:
                # logging.info('PLAYERS INFO:%s, loca[%s],velo[%s]'%(player.ip,str(player.plane.location), str(player.plane.velocity)))
                if player.ip == self.local_ip and player.alive:
                    status_msg = ('syn_player_status', {'location': (player.plane.location.x, player.plane.location.y),
                                                        'velocity': (player.plane.velocity.x, player.plane.velocity.y),
                                                        'health': player.plane.health})
                    for player in self.player_list:
                        # self.sock_send(status_msg, (player.ip, self.port))  # test 谁都发
                        if player.ip != self.local_ip:
                            self.sock_send(status_msg, (player.ip, self.port))
                    break

    def add_weapon_tail(self, weapon_group):
        for weapon in weapon_group:
            if weapon.catalog == 'Rocket' or weapon.catalog == 'Cobra':
                self.tail_group.add(Tail((weapon.location.x, weapon.location.y)))

    def add_unit_tail(self, unit_group):
        for unit in unit_group:
            self.tail_group.add(Tail((unit.location.x, unit.location.y), catalog='Plane_tail'))

    def erase(self):
        self.weapon_group.clear(self.map.surface, self.clear_callback)
        self.plane_group.clear(self.map.surface, self.clear_callback)
        self.tail_group.clear(self.map.surface, self.clear_callback)
        self.box_group.clear(self.map.surface, self.clear_callback)
        self.slot.clear(self.clear_callback)
        self.health_group.clear(self.map.surface, self.clear_callback)

    def clear_callback(self, surf, rect):
        # surf.blit(source=self.map.surface, dest=(0, 0), area=self.current_rect)
        # self.screen.blit(source=self.map.surface, dest=(0, 0), area=self.current_rect)
        surf.blit(source=self.origin_map_surface, dest=rect,
                  area=rect)  # blit(source, dest, area=None, special_flags=0) -> Rect

    def event_control(self):
        """
        :return: 返回空列表，或者一个元素为keys的列表
        看这个样子，应该是每一self.syn_frame就读取一次键盘操作bool值列表
        """
        pygame.event.get()  # 一定要把操作get()出来
        key_list = ''
        # n_break = 0
        if pygame.key.get_focused():
            keys = pygame.key.get_pressed()  # key is queue too， 一个列表，所有按键bool值列表
            # print '    KEY:', keys
            if keys[pygame.K_ESCAPE]:
                self.done = True
                return  # EXIT GAME
            if keys[pygame.K_LEFT]:  # 直接使用 pygame.key.get_pressed() 可以多键同时独立识别
                self.screen_rect.x -= self.move_pixels
            if keys[pygame.K_RIGHT]:
                self.screen_rect.x += self.move_pixels
            if keys[pygame.K_UP]:
                self.screen_rect.y -= self.move_pixels
            if keys[pygame.K_DOWN]:
                self.screen_rect.y += self.move_pixels
            if keys[pygame.K_SPACE]:
                if self.local_player.plane:
                    self.screen_focus_obj = self.local_player.plane
                    # self.screen_focus = Map.mars_translate(self.d[self.local_ip]['location'])
                    # self.screen_rect.center = Map.mars_translate(self.local_player.plane.location)
            if keys[pygame.K_TAB]:
                if self.syn_frame - self.last_tab_frame > self.fps / 4:
                    self.last_tab_frame = self.syn_frame
                    self.hide_result = not self.hide_result  # 需要设置KEYUP和KEYDONW，to be continue...!!!!

            for keyascii in [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_i, pygame.K_o, pygame.K_p]:
                if keys[keyascii]:
                    key_list += chr(keyascii)

            # n_break += 1
            # if n_break > 3:
            #     break

        return key_list

    # def get_local_ip(self):
    #     l = socket.getaddrinfo(socket.gethostname(), None)
    #     for index, i in enumerate(l):
    #         print index, i[-1][0]
    #     if RESTART_MODE:
    #         localip = self.re_local_ip
    #     else:
    #         localip = l[input("select your own ip index:")][-1][0]
    #         self.re_local_ip = localip  # for repeat
    #     self.local_ip = localip
    #     return localip

    def get_local_ip(self):
        return socket.gethostbyname(socket.gethostname())

    def box_msg_send(self):
        if self.syn_frame % (10 * FPS) == 0:  # 每n=10秒同步一次自己状态给对方
            location = [randint(0, MARS_MAP_SIZE[0]), randint(0, MARS_MAP_SIZE[1])]
            # Medic and so on. -->  10%, 30%, 30%, #0%
            rand_x = randint(0, 100)
            if rand_x <= 10:
                rand_catalog = 'Medic'
            elif rand_x <= 40:
                rand_catalog = 'Gunfire_num'
            elif rand_x <= 70:
                rand_catalog = 'Rocket_num'
            elif rand_x <= 100:
                rand_catalog = 'Cobra_num'
            status_msg = ('box_status', {'location': location, 'catalog': rand_catalog})
            for player in self.player_list:
                self.sock_send(status_msg, (player.ip, self.port))

    def plane_lost_msg_send(self, player_ip):
        status_msg = ('plane_lost', {'ip': player_ip})
        for player in self.player_list:
            self.sock_send(status_msg, (player.ip, self.port))

    # def syn_lock_frame(self):
    #     lock_frame = 0
    #     while not self.done:
    #         pygame.time.wait(1000/FPS)
    #         status_msg = ('syn_lock_frame', lock_frame)
    #         for player in self.player_list:
    #             self.sock_send(status_msg, (player.ip, self.port))
    #         lock_frame += 1

    def process(self, event_list):
        """
        每个玩家接收自己的消息队列，刷新自己的界面；
        不管延迟和丢包的问题，接受操作消息等待为resend_time=30ms；
        每过2帧进行一次状态同步：只将本地玩家飞机状态发送给其他玩家；
        """
        # 产生随机奖励Box，并发送
        self.box_msg_send()

        # 状态同步, 先状态同步，再发送操作消息
        self.syn_status()

        # # 发送锁定帧
        # self.syn_lock_frame()

        # 发送普通键盘操作消息
        self.player_communicate(event_list)

        # 进行游戏对象参数计算&渲染
        self.minimap.update()
        self.weapon_group.update(self.plane_group)
        self.tail_group.update()  # update尾焰
        if self.local_player.plane:
            for weapon in ['Gun', 'Rocket', 'Cobra']:  # update SlotWidget
                if weapon == 'Gun':
                    index_ = 1
                elif weapon == 'Rocket':
                    index_ = 2
                else:  # weapon == 'Cobra':
                    index_ = 3
                self.slot.update_line(weapon_name=weapon, weapon_num=self.local_player.plane.weapon[index_]['number'])
        # self.map.surface = self.origin_map_surface.copy()  # [WARNING]很吃性能！！！！！极有可能pygame.display()渲染不吃时间，这个copy（）很吃时间
        # self.map.surface.blit(self.origin_map_surface, (0,0))  # ！！

        # 添加尾焰轨迹
        if self.syn_frame % 5 == 0:
            self.add_weapon_tail(self.weapon_group)
        # if self.syn_frame % 3 == 0:  # 添加飞机尾焰
        #     self.add_unit_tail(self.plane_group)

        # DRAW
        self.box_group.draw(self.map.surface)  # draw随机Box
        self.tail_group.draw(self.map.surface)  # draw尾焰
        self.plane_group.draw(self.map.surface)  # draw飞机
        self.health_group.draw(self.map.surface)  # draw飞机血条
        self.weapon_group.draw(self.map.surface)  # draw武器
        for i in self.weapon_group:  # 画被跟踪框框
            if i.target:
                # print i.target
                pygame.draw.rect(self.map.surface, (255, 0, 0), i.target.rect, 1)
        # print self.slot.slot_group.sprites()[0].rect
        # print self.slot.line_list[1]['sprite_group'].sprites()[0].rect

        # 碰撞处理
        self.deal_collide()
        self.deal_collide_with_box()

        # 判断游戏是否结束
        for player in self.player_list:
            if player.alive:
                # player.plane.draw_health(self.map.surface)  # 显示飞机血条
                # 更新玩家状态,player.update()-->plane.update()-->plane.delete(),delete没了的的飞机
                if player.update():  # player.update==True就是玩家飞机lost了
                    self.plane_lost_msg_send(player.ip)  # 发送玩家lost的消息
                    player.plane = None  # player.update()为True说明飞机已经delete了
                    player.alive = False  # End Game
                    self.num_player -= 1
                    logging.info("Player lost: %s" % player.ip)
                    # return True

        # 显示游戏信息
        # self.info.add(u'')
        # self.info.add(u'')
        # self.info.add(u'')
        # self.info.add(u'')
        # self.info.add(u'')
        # for py in self.player_list:
        #     self.info.add(u'Player IP:%s' % py.ip)
        #     if py.plane:
        #         self.info.add(u'Health:%d' % py.plane.health)
        #         self.info.add(u'Weapon:%s' % str(py.plane.weapon))
        #         self.info.add(u'Tail:%s' % self.tail_group)
        #         self.info.add(u'speed:%s,  location:%s,  rect:%s' % (
        #             str(py.plane.velocity), str(py.plane.location), str(py.plane.rect)))
        #     self.info.add(u'Groups:%s' % str(self.plane_group))

        # 屏幕显示，本地飞机聚焦处理
        if not self.local_player.alive:  # 本地玩家
            self.screen_focus_obj = None  # screen_rect聚焦为空，回复上下左右控制
            self.show_result = True
            self.info.add_middle('YOU LOST.')
            self.info.add_middle_below('press "ESC" to exit the game.')
            self.info.add_middle_below('press "Tab" to hide/show this message.')
        else:  # 本地飞机还或者的情况
            # print self.screen_focus_obj
            if not self.screen_focus_obj.groups():  # 本地飞机还活着，但是focus_obj不在任何group里面了，就指回本地飞机
                self.screen_focus_obj = self.local_player.plane
            if self.num_player == 1:  # 只剩你一个人了
                self.show_result = True
                self.info.add_middle('YOU WIN!')
                self.info.add_middle_below('press "ESC" to exit the game.')
                self.info.add_middle_below('press "Tab" to hide/show this message.')

        # 收到消息进行操作（最后处理动作，留给消息接收）
        # self.get_deal_msg()

        # # LockFrame关键帧同步, 根据情况每帧多拖累一针
        # while self.delay_frame > 0:
        #     pygame.time.wait(1000/FPS)
        #     self.delay_frame -= 1

    def get_deal_msg(self):
        while not self.done:  # 游戏结束判定
            # 空就不进行读取处理
            if self.q.empty():
                continue
                pygame.time.wait(1)

            # 处理消息
            data, address = self.q.get()
            data_tmp = json.loads(data)  # [frame_number, key_list], ['syn_player_status', dict]，['box_status', dict]

            # Msg Type1:操作类型的消息
            if isinstance(data_tmp[0], int):
                for player in self.player_list:  # 遍历玩家，看这个收到的数据是谁的
                    if player.ip == address[0] and player.alive:
                        # # 接收到大于当前帧的消息就等待, 比如：我自己才发送到第15帧，别人发到15,16,17帧来了我要等待
                        # while data_tmp[0] > self.syn_frame:
                        #     pygame.time.wait(1)
                        if data_tmp[1]:  # 消息-->操作
                            weapon_obj = player.operation(data_tmp[1],
                                                          self.syn_frame)  # data is list of pygame.key.get_pressed() of json.dumps
                            if player.ip == self.local_ip and weapon_obj:  # 如果导弹对象不为空，就将屏幕聚焦对象指向它
                                self.screen_focus_obj = weapon_obj
                        logging.info("Get %d----> %s, %s" % (data_tmp[0], str(address), str(data_tmp)))
                        break  # 一个数据只有可能对应一个玩家的操作，有一个玩家取完消息就可以了

            # Msg Type2:状态同步-->对象，同步类型消息
            elif data_tmp[0] == 'syn_player_status':
                # print 'in status.....', address
                for player in self.player_list:  # 因为没用{IP:玩家}，所以遍历玩家，看这个收到的数据是谁的
                    if player.ip == address[0] and player.alive:
                        player.plane.location = Vector(data_tmp[1]['location'])
                        # + Vector(data_tmp[1]['velocity'])* SPEED_RATIO / FPS  # 1帧的时间, 反而有跳跃感
                        player.plane.velocity = Vector(data_tmp[1]['velocity'])
                        player.plane.health = data_tmp[1]['health']  # !!!!!!!!会出现掉血了，然后回退回去的情况
                        logging.info("Get player status, local_frame:%d----> %s, %s" % (
                            self.syn_frame, str(address), str(data_tmp)))
                        break

            # Msg Type3:接受并处理Box类型消息
            elif data_tmp[0] == 'box_status':
                self.box_group.add(Box(location=data_tmp[1]['location'], catalog=data_tmp[1]['catalog']))

            # Msg Type4:接受并处理玩家飞机lost类型消息
            elif data_tmp[0] == 'plane_lost':  # status_msg = ('plane_lost', {'ip':player_ip})
                for player in self.player_list:
                    if player.alive and player.ip == data_tmp[1]['ip']:
                        player.plane.health = 0
                        break

            ## Msg Type:接受并处理LockFrame
            # elif data_tmp[0] == 'syn_lock_frame':
            #     # if self.syn_frame>data_tmp[1] and address[0] != self.local_ip:  # 如果LockFrame小于本系统的同步帧
            #     if self.syn_frame > data_tmp[1]:
            #         self.delay_frame = self.syn_frame - data_tmp[1]
            #     logging.info("DelayFrames:%d--->%s"%(self.delay_frame, str(data_tmp)))


    def deal_player_dict(self, player_dict):
        """From: dict_player = {'ip':{'location': (randint(20, 80) / 100.0, randint(20, 80) / 100.0),
                                      'Plane': 'F35','Gun': 200, 'Rocket': 10, 'Cobra': 3}，
                               }
            To:  d = {'ip':msg_player，
                     }
            P.S. msg_player = {'ip': localip,
                        'location': (randint(MARS_MAP_SIZE[0] / 5, MARS_MAP_SIZE[0] * 4 / 5),
                                   randint(MARS_MAP_SIZE[1] / 5, MARS_MAP_SIZE[1] * 4 / 5)),
                        'Plane': plane_type, 'Gun': 200, 'Rocket': 10, 'Cobra': 3,}
        }"""
        d = {}
        for ip in player_dict.keys():
            d[ip] = player_dict[ip]
            d[ip]['ip'] = ip
            d[ip]['location'] = [MARS_MAP_SIZE[n] * i for n, i in enumerate(player_dict[ip]['location'])]
        return d

    def deal_screen_focus(self, screen_rect):
        if self.screen_focus_obj:
            screen_rect.center = self.screen_focus_obj.rect.center
            # screen_rect.center = Map.mars_translate(self.screen_focus_obj.location)

    def main(self):
        self.local_ip = localip = self.get_local_ip()
        if SINGLE_TEST:
            plane_type = PLANE_TYPE
            msg_player = self.init_local_player(localip, plane_type)
            self.game_init(localip)
            self.d[localip] = msg_player
            self.other_ip = localip

        self.game_init(self.local_ip)
        with open('player_dict.dat', 'r') as f1:
            player_dict_origin = json.load(f1)
            self.d = self.deal_player_dict(player_dict_origin)
            logging.info('load "player_dict.dat":success')

        # Pygame screen init
        self.screen_init()
        for ip in self.d.keys():
            self.add_player(self.msg2player(self.d[ip]))

        # MAP
        self.map = Map()  # 8000*4500--->screen, (8000*5)*(4500*5)---->map
        self.map.add_cloud()
        self.minimap = MiniMap(self.screen, self.map.surface.get_rect(), self.screen_rect, self.plane_group)
        self.origin_map_surface = self.map.surface.copy()

        # Weapon SlotWidget
        self.slot = SlotWidget(screen=self.screen)

        # 获取本地玩家对象
        for player in self.player_list:
            if player.ip == self.local_ip:
                self.local_player = player

        # 根据local player位置移动一次self.screen_rect git
        # self.screen_rect.center = Map.mars_translate(self.d[self.local_ip]['location'])
        self.screen_focus_obj = self.local_player.plane
        self.deal_screen_focus(self.screen_rect)

        # PYGAME LOOP
        pygame.key.set_repeat(10)  # control how held keys are repeated
        logging.info('Game Start.My IP&PORT: %s - %d' % (self.local_ip, self.port))

        # MAIN LOOP
        self.main_loop()

    def main_loop(self):
        # GET MSG DEAL INIT
        self.thread_msg = threading.Thread(target=self.get_deal_msg)
        self.thread_msg.setDaemon(True)  # True:不关注这个子线程，主线程跑完就结束整个python process

        # # lockframe deal
        # if self.host_ip == self.local_ip:  # 主机才发送同步LockFrame
        #     self.thread_lock = threading.Thread(target=self.syn_lock_frame)
        #     self.thread_lock.setDaemon(True)  # True:不关注这个子线程，主线程跑完就结束整个python process

        # 同步开始循环
        for ip in self.d.keys():
            self.sock_send('200 OK', (ip, self.port))

        now_count = start_count = pygame.time.get_ticks()
        waiting_times = 20000  # 这里其实需要改写为TCP确认， 等待对方收到消息 to be continue...
        msg_get_ip_list = {}
        while True:  # 等收到所有玩家的'200 ok'
            while not self.q.empty():
                data, address = self.q.get()
                if json.loads(data) == '200 OK':
                    self.sock_send('200 OK', address)  # 收到补发一个200 OK，因为对方都是先打开监听，然后开始发送
                    logging.info('Start Msg Get:%s:%s' % (address, data))
                    msg_get_ip_list[address[0]] = True
                    if len(msg_get_ip_list.keys()) >= len(self.player_list):
                        break

            if len(msg_get_ip_list.keys()) >= len(self.player_list):
                logging.info('game:begin')
                break

            if pygame.time.get_ticks() - now_count > 1000:  # 每一秒朝没有收到消息的主机发送一个200 OK
                now_count = pygame.time.get_ticks()
                for ip in self.d.keys():
                    if ip not in msg_get_ip_list.keys():
                        self.sock_send('200 OK', (ip, self.port))

            if pygame.time.get_ticks() - start_count > waiting_times:
                logging.error('Sock Waiting Timeout: %s' % '"200 OK"')
                self.done = True  # 通过self.done关闭线程，防止Errno 9：bad file descriptor(错误的文件名描述符)
                return False

        # MSG deal
        logging.info('deal_msg:begin')
        self.thread_msg.start()  # 开启玩家处理接受消息的线程

        # 主循环 Main Loop
        # if self.host_ip == self.local_ip:  # 主机才发送同步LockFrame
        #     self.thread_lock.start()  # 开启玩家处理接受消息的线程
        # last_time = pygame.time.get_ticks()
        while not self.done:
            last_time = pygame.time.get_ticks()
            logging.info("Frame No:%s" % self.syn_frame)
            # logging.info('T1:%d'%pygame.time.get_ticks())
            event_list = self.event_control()

            # logging.info('T1.1:%d' % pygame.time.get_ticks())
            self.deal_screen_focus(self.screen_rect)  # 在飞机update()之前就不会抖动

            # logging.info('T1.2:%d' % pygame.time.get_ticks())
            if self.process(event_list):  # 在FULLSCREEN下，这个函数最占性能20~40ms
                self.done = True
                break

            # logging.info('T2:%d'%pygame.time.get_ticks()) # T1与T2之间平均花费12ms
            Map.adjust_rect(self.screen_rect, self.map.surface.get_rect())

            # logging.info('T3:%d'%pygame.time.get_ticks())
            self.render(self.screen_rect)  # 该函数平均花费10ms(26ms), 在FULLSCREEN下是2ms

            # logging.info('T4:%d'%pygame.time.get_ticks())
            pygame.display.flip()  # 2ms

            # logging.info('T5:%d'%pygame.time.get_ticks())
            # self.clock.tick(self.fps)
            self.erase()  # 8ms,如果采用blit方式，就不用clear()的方法了

            # 这个是按整理计算延迟的，如果前面卡了，后面就会加速：没必要因为会定时同步状态
            # stardard_diff_time = -(pygame.time.get_ticks() - self.start_time) + self.syn_frame * 1000 / FPS
            # 计算每帧时间，和时间等待
            _time = pygame.time.get_ticks()
            logging.info('CostTime:%s' % str(_time - last_time))
            # 每帧需要的时间 - 每帧实际运行时间，如果还有时间多，就等待一下
            stardard_diff_time = 1000 / FPS - (_time - last_time)
            if stardard_diff_time > 0:  # 等待多余的时间
                pygame.time.wait(stardard_diff_time)  # 这个等待时间写在这里不合适
                logging.info('WaitingTime:%s' % str(stardard_diff_time))

            self.syn_frame += 1  # 发送同步帧(上来就发送)
            # logging.info('T6:%d'%pygame.time.get_ticks())

        # self.thread1.close
        # self.sock.close()
        # pygame.time.wait(1000)
        pygame.quit()


def test_calc_frame_cost():
    """2019-Sep-01 01:03:39-Sun [line:1305] [INFO] Time:34"""
    with open('logger.log', 'r') as f1:
        s = f1.readlines()

    l = []
    l_w = []
    cost_bool = wait_bool = False
    for i in s:
        if 'Frame No:' in i:
            if wait_bool:
                l_w.append('WaitingTime:0')
            cost_bool = True
            wait_bool = True
            continue
        if cost_bool and 'CostTime:' in i:
            l.append(i)
            cost_bool = False
        if wait_bool and 'WaitingTime:' in i:
            l_w.append(i)
            wait_bool = False

    l1 = [i.split(':')[-1] for i in l]  # list of CostTime
    l2 = [i.split(':')[-1] for i in l_w]  # list of WaitingTime

    # show diagram. vertiacal
    for i in range(min(len(l1), len(l2))):
        logging.info("[%d]%s%s" % (int(l1[i]) + int(l2[i]), '+' * int(l1[i]), '-' * int(l2[i])))
        # print("[%d]%s%s" % (int(l1[i]) + int(l2[i]), '+' * int(l1[i]), '-' * int(l2[i])))

    # average cost
    logging.info('average frame lantency = CostTime + WaitingTime')
    sum = 0
    for i in l1:
        sum += int(i)
    if len(l1) > 0:
        logging.info('average CostTime:%s ms' % str(sum / len(l1)))
        # print('average Cost-Time:%s ms'%str(sum / len(l1)))

    # average waiting
    sum = 0
    for i in l2:
        sum += int(i)
    if len(l2) > 0:
        logging.info('average WaitingTime:%s ms' % str(sum / len(l2)))
        # print('average Waiting-Time:%s ms' % str(sum / len(l2)))

    return [int(i) for i in l1]  # z只返回CostTime


def test_send_get_analyze():
    """
    2019-09-01 23:30:25,572 [line:1043] [INFO] Frame:15
2019-09-01 23:30:25,572 [line:913] [INFO] Send 15---> ('192.168.0.107', 8989), [15, "a"]
2019-09-01 23:30:25,573 [line:1156] [INFO] Get 15----> ('192.168.0.107', 8989), [15, u'a']
2019-09-01 23:30:25,621 [line:1336] [INFO] CostTime:49
    :return:
    """
    with open('logger.log', 'r') as f1:
        s = f1.readlines()

    n = 0
    counts = 0
    # while True:
    #     if 'Send %d'%n in line:
    #         counts += 1


def main():
    game = Game()
    game.main()
    # while raw_input('press "r" to restart game:') == 'r':
    #     RESTART_MODE = True
    #     game.main()
    game.sock.close()
    test_calc_frame_cost()
    test_send_get_analyze()


if __name__ == '__main__':
    test_calc_frame_cost()
    test_send_get_analyze()
