# -*- coding: utf-8 -*-
import pygame
# import time
import random
import logging
import json
from queue import Queue

import config
import my_sprite
import my_sock
import my_player
import my_map
import information
import matrix


class Game:
    def __init__(self):
        self.screen_init()
        self.game_init()

    def screen_init(self):
        self.screen = pygame.display.get_surface()  # 游戏窗口对象
        self.screen_rect = self.screen.get_rect()  # 游戏窗口对象的rect
        logging.info('DISPLAY:%s' % self.screen_rect)

        self.test_font = pygame.font.SysFont("arial", 15)
        self.clock = pygame.time.Clock()

        # self.origin_screen = self.screen.copy()
        # self.screen.fill(config.BACKGROUND_COLOR)  # 暂时不提前----测试
        # self.clock = pygame.time.Clock()

    def game_init(self):
        self.player_dict = {}  # {'ip1':player_obj1, 'ip2':player_obj2}
        self.last_player_dict = {'frame': None}  # 用来SYN同步时，存储上一个整秒时刻的状态
        self.syn_fps = config.FPS

        self.plane_group = pygame.sprite.Group()
        self.health_group = pygame.sprite.Group()
        self.box_group = pygame.sprite.Group()
        self.weapon_group = pygame.sprite.Group()
        self.thrustbar_group = pygame.sprite.Group()
        self.slot_group = pygame.sprite.Group()
        self.game_groups = [self.box_group, self.plane_group, self.weapon_group, self.health_group,
                            self.thrustbar_group, self.slot_group]  # 有顺序讲究, 同时也是渲染叠加顺序

        self.map = None
        self.minimap = None
        self.origin_map_surface = None

        self.sock = my_sock.Sock(tcp_bool=False, thread_udp_bool=False)

        self.local_player = None  # 需要区分本地的其他ai玩家
        self.local_ip = None
        self.host_ip = None

        self.syn_frame = 0

        self.done = None

        self.host_operation_queue = Queue()
        self.guest_operation_queue = Queue()
        self.operation_dict = {}  # use for host msg

        self.screen_focus_obj = None  # 默认为空，首次指向本地plane, 空格指向本地plane, 为空但是本地plane还存在就指向plane
        self.move_pixels = 30
        self.done = False

        self.show_result = False  # 用来显示Win or Lose, 和游戏是否结束
        self.restart_game = False
        # ------------------------------------------------------------------------------------

        # self.lock_frame = 0
        # self.delay_frame = 0
        # self.start_time = 0

        self.info = information.Information()

        self.hide_result = False
        self.last_tab_frame = 0

    def main(self):
        if self.game_start():
            res = self.game_loop()
            self.sock.close()
            return res

    def game_start(self):
        # Read&Format player_dict.dat
        with open('game_dict.dat', 'r') as f1:
            game_dict_origin = json.load(f1)

        player_dict = game_dict_origin['player']
        _d = {}
        for ip in player_dict.keys():
            _d[ip] = player_dict[ip]
            # d[ip]['ip'] = ip
            _d[ip]['location'] = [config.MAP_SIZE[n] * i for n, i in enumerate(player_dict[ip]['location'])]
        self.host_ip = game_dict_origin['host']  # get host ip from "game_dict.dat"
        logging.info('formatting "player_dict.dat" to game.dict success: %s' % str(_d))

        # Loading Players INFO
        for ip in _d.keys():
            msg_player = _d[ip]
            player = my_player.Player(weapon_group=self.weapon_group, ip=ip)
            plane = my_sprite.Plane(catalog=msg_player['Plane'], location=msg_player['location'],
                                    color=msg_player['Color'])
            plane.load_weapon(catalog='Cobra', number=msg_player['Cobra'])
            plane.load_weapon(catalog='Bullet', number=msg_player['Bullet'])
            plane.load_weapon(catalog='Rocket', number=msg_player['Rocket'])
            plane.load_weapon(catalog='Cluster', number=msg_player['Cluster'])
            player.add_plane(plane)
            self.player_dict[ip] = player
        logging.info("loading player's INFO success-self.player_dict:%s" % str(self.player_dict))

        # add sprite_group
        for ip in self.player_dict:
            self.plane_group.add(self.player_dict[ip].plane)
            self.health_group.add(self.player_dict[ip].healthbar)

        # GAME TEST ADD
        # self.test_add_plane()

        # 获取本地玩家对象 self.local_player
        self.local_ip = self.sock.localip()
        if self.local_ip in self.player_dict:
            self.local_player = self.player_dict[self.local_ip]
            logging.info('get local_player success: ip - %s' % self.local_ip)
        else:
            logging.error('get local_player failed: localip-%s not in player_dict_ip-%s' % (
            self.local_ip, str(self.player_dict.keys())))

        # Weapon Slot
        self.slotbar_str_list = config.WEAPON_LIST
        self.slotbar_obj_dict = {}  # {<'Bullet'>:'Bullet', <'Rocket'>:'Rocket', ...}
        for i, catalog in enumerate(self.slotbar_str_list):
            _s = my_sprite.SlotBar(rect_topleft=(20, 16 * i +5))
            _s.update(health=self.local_player.plane.weapon[catalog])
            _logo = my_sprite.Box(location=(10, 16 * i +10), catalog=catalog)
            self.slot_group.add(_logo)
            self.slotbar_obj_dict[_s] = catalog
            # self.slot_obj_list.append(_s)
            self.slot_group.add(_s)

        # MAP
        self.map = my_map.Map()
        self.map.add_cloud(cloud_num=20)
        self.minimap = my_map.MiniMap(self.screen, self.map.surface.get_rect(), self.screen_rect, self.plane_group)
        self.origin_map_surface = self.map.surface.copy()

        # self.screen = pygame.display.get_surface()
        # self.screen.blit(source=self.map.surface, dest=(0, 0), area=self.screen.get_rect())
        # self.minimap.draw()
        # pygame.display.flip()
        # pygame.time.wait(3000)

        self.screen_focus_obj = self.local_player.plane
        self.deal_screen_focus()  # 根据local_player位置移动一次self.screen_rect

        # # lockframe deal
        # if self.host_ip == self.local_ip:  # 主机才发送同步LockFrame
        #     self.thread_lock = threading.Thread(target=self.syn_lock_frame)
        #     self.thread_lock.setDaemon(True)  # True:不关注这个子线程，主线程跑完就结束整个python process

        return self.start_syn_mainloop()

    def start_syn_mainloop(self):
        # last syn before main loop 同步开始循环
        if self.host_ip == self.local_ip:  # HOST
            msg_get_ip_list = [self.local_ip]
            last_time = pygame.time.get_ticks()
            while True:
                for ip in self.player_dict:
                    if ip in msg_get_ip_list:
                        continue
                    self.sock.msg_direct_send(('start main loop', ip))  # host send start msg to all players
                pygame.time.wait(100)
                while not self.sock.q.empty():
                    msg, ip = self.sock.q.get()
                    if msg == '200 OK':
                        msg_get_ip_list.append(ip)  # 每个IP只能回复1个 200 OK，否则会出问题
                if len(msg_get_ip_list) == len(self.player_dict.keys()):
                    logging.info('Start Msg All Get:%s' % str(msg_get_ip_list))
                    return True
                if pygame.time.get_ticks() - last_time > 10000:
                    logging.error('Start Msg Lost!:%s' % str(msg_get_ip_list))
                    break

        else:  # GUEST
            last_time = pygame.time.get_ticks()
            while pygame.time.get_ticks() - last_time < 10000:
                if not self.sock.q.empty():
                    msg, ip = self.sock.q.get()
                    if msg == 'start main loop':
                        self.sock.msg_direct_send(('200 OK', ip))
                        logging.info('Start Msg Get')
                        return True
                pygame.time.wait(1)
        logging.error('Get Start MSG FAILED! GAME EXIT.')
        return False

    def game_loop(self):
        # 主循环 Main Loop
        pygame.key.set_repeat(10)  # control how held keys are repeated
        logging.info('======MAIN LOOP Start.My IP&PORT: %s======' % (self.local_ip))
        self.lastframe_time = self.start_time = pygame.time.get_ticks()
        self.done = False
        while not self.done:
            # 从头开始就是按正常帧来----开始时间不重要，初步来看还不错
            # self.lastframe_time = pygame.time.get_ticks()
            logging.info("----------Frame No:%s----------" % self.syn_frame)
            # logging.info('T1.1:%d' % pygame.time.get_ticks())
            # OPERATION
            key_list = self.get_eventlist()
            # logging.info('T1.2:%d' % pygame.time.get_ticks())
            if self.local_player.alive:  # 玩家或者才上报数据
                self.sendtohost_eventlist(key_list)  # 上报这一帧的操作数据
            # logging.info('T1.3:%d' % pygame.time.get_ticks())
            self.getfromhost_operation()  # 接收主机上一帧的操作&执行，同步上一帧的数据

            # SCREEN
            # logging.info('T2.2:%d' % pygame.time.get_ticks())
            self.erase()  # 后clear可以保留一下残影？
            # logging.info('T2.3:%d' % pygame.time.get_ticks())
            self.blit_map()
            # logging.info('T2.4:%d' % pygame.time.get_ticks())
            self.focus_screen()
            self.blit_screen()
            # logging.info('T2.5:%d' % pygame.time.get_ticks())
            pygame.display.flip()
            # logging.info('T2.6:%d' % pygame.time.get_ticks())

            # HOST
            # logging.info('T2.1:%d' % pygame.time.get_ticks())
            if self.host_ip == self.local_ip:
                self.sendbyhost_operation()  # 主机接收 >= 当前帧的操作数据，并发送

            # MATH
            # logging.info('T3.1:%d' % pygame.time.get_ticks())
            self.update()
            self.game_collide()
            self.game_collide_with_box()

            # GET SYN_FRAME STATUS
            self.record_player_status()

            # GAME
            # logging.info('T4.1:%d' % pygame.time.get_tick  s())
            self.end_game()
            if self.restart_game:  # 重新开始游戏
                break
            self.wait_whole_frame()

            # FRAME PLUS ONE
            self.syn_frame = self.syn_frame + 1

        return self.restart_game

    def get_eventlist(self):
        """
        :return: 返回空列表，或者一个元素为keys的列表
        看这个样子，应该是每一self.syn_frame就读取一次键盘操作bool值列表
        """
        pygame.event.get()  # 一定要把操作get()出来
        key_list = ''
        if pygame.key.get_focused():
            keys = pygame.key.get_pressed()  # key is queue too， 一个列表，所有按键bool值列表
            # print '    KEY:', keys
            if keys[pygame.K_ESCAPE]:
                self.done = True
                return key_list  # EXIT GAME
            if keys[pygame.K_r] and self.show_result:
                self.done = True
                self.restart_game = True
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
                if self.syn_frame - self.last_tab_frame > config.FPS / 4:
                    self.last_tab_frame = self.syn_frame
                    self.hide_result = not self.hide_result  # 需要设置KEYUP和KEYDONW，to be continue...!!!!

            for keyascii in [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s,
                             pygame.K_i, pygame.K_o, pygame.K_p, pygame.K_u]:
                if keys[keyascii]:
                    key_list += chr(keyascii)

        return key_list

    def sendtohost_eventlist(self, key_list):
        self.sock.msg_direct_send(((('guest', self.syn_frame), {self.local_ip: key_list}), self.host_ip))

    def getfromhost_operation(self):
        """msg_player = {ip1: 'asi', ip2: 'wop'...}"""
        self.split_hostmsgqueue()
        if self.host_operation_queue.empty():
            logging.warning('do not receive operation from host at frame:%d' % self.syn_frame)
        else:
            while not self.host_operation_queue.empty():  # 非空就把队列都去出来
                tmp_frame, msg_dict = self.host_operation_queue.get()  # data = (('host',self.syn_frame), {'opr':operation_dict})
                #  进行操作消息的读取&操作
                msg_opr = msg_dict['opr']
                for ip in msg_opr:
                    weapon_obj = self.player_dict[ip].operation(msg_opr[ip], self.syn_frame)
                    if ip == self.local_ip and weapon_obj:  # 如果导弹对象不为空，就将屏幕聚焦对象指向它
                        self.screen_focus_obj = weapon_obj
                logging.info('running host operation at frame:%d' % tmp_frame[1])
                self.record_player_status()  # 记录last_player_dict操作
                # 进行同步消息的读取&操作
                if 'syn' in msg_dict:  # 在这一帧操作之前，进行上一帧的位置同步，后面会进行update()
                    if tmp_frame[1] == self.last_player_dict['frame']:  # 正常在本帧update()之前，同步上个本地标记帧的状态
                        msg_player = msg_dict['syn']
                        for ip in msg_player:
                            self.player_dict[ip].plane.location[:] += msg_player[ip]['location']-self.last_player_dict[ip]['location']
                            self.player_dict[ip].plane.velocity[:] += msg_player[ip]['velocity']-self.last_player_dict[ip]['velocity']
                            self.player_dict[ip].plane.health += msg_player[ip]['health']-self.last_player_dict[ip]['health']
                        logging.info('running player_synchronize at frame:%d.' % tmp_frame[1])
                    else:  # 当延迟，或者接收消息超过一个self.syn_fps也就是1s的时候，同步不发生
                        logging.warning('running player_synchronize failed at host frame:%d!' % tmp_frame[1])
                if 'box' in msg_dict:
                    box_dict = msg_dict['box']
                    for _catalog in box_dict:
                        self.box_group.add(my_sprite.Box(location=box_dict[_catalog], catalog=_catalog))

    def split_hostmsgqueue(self):
        """self.q ----> self.guest/host_operation_queue"""
        while not self.sock.q.empty():
            msg, ip = self.sock.q.get()
            try:
                if msg[0][0] == 'guest':  # msg =(('guest',self.syn_frame), {self.ip: key_list})
                    # logging.info('put in guest queque:%s' %msg)
                    self.guest_operation_queue.put(msg)
                elif msg[0][0] == 'host':  # msg = (('host',self.syn_frame), operation_dict)
                    self.host_operation_queue.put(msg)
                    # logging.info('put in host queque:%s' % msg)
            except Exception as err:
                logging.warning('Invalid MSG:"%s". Exception:%s' % (str(msg), err))

    def sendbyhost_operation(self):
        """get all guests msg, then merge & send host_operation"""
        alive_players = sum([player.alive for player in self.player_dict.values()])
        start_time = pygame.time.get_ticks()
        # 接收发来的guest消息进行处理，没有收集齐的就等待一帧
        while True:
            # 接受到的消息分类
            self.split_hostmsgqueue()
            # 对分类进入到 guest_operation_queue 队列中的消息做HOST消息整合
            while not self.guest_operation_queue.empty():
                (_tmp,
                 frame), key_dict = self.guest_operation_queue.get()  # (('guest',self.syn_frame), {self.ip: key_list})
                if frame >= self.syn_frame:  # 大于等于当前帧syn_frame的guest操作就留下执行
                    if frame not in self.operation_dict:
                        self.operation_dict[frame] = key_dict
                    else:
                        # logging.info('key_dict%s'%str(key_dict))
                        self.operation_dict[frame].update(key_dict)
                logging.info('operation_dict:%s' % str(self.operation_dict))
            # 当前帧收集齐了就退出
            if self.syn_frame in self.operation_dict and len(
                    self.operation_dict[self.syn_frame].keys()) == alive_players:
                break
            # 超出时间也退出， 玩家等于0也退出
            if pygame.time.get_ticks() - start_time > 1000 / config.FPS or alive_players == 0:
                break
            # 等一次
            pygame.time.wait(1)
            logging.info('wait one times, to ms:%d' % (pygame.time.get_ticks() - start_time))

        # over = False
        # while not over and pygame.time.get_ticks()-start_time <= 1000/config.FPS:
        #     # 接受到的消息分类
        #     self.split_hostmsgqueue()
        #     # 对分类进入到 guest_operation_queue 队列中的消息做HOST消息整合
        #     while not over and not self.guest_operation_queue.empty():
        #         (_tmp,frame), key_dict = self.guest_operation_queue.get() # (('guest',self.syn_frame), {self.ip: key_list})
        #         if frame >= self.syn_frame:  # 小于的syn_frame的guest操作就直接丢弃
        #             if frame not in self.operation_dict:
        #                 self.operation_dict[frame] = key_dict
        #             else:
        #                 # logging.info('key_dict%s'%str(key_dict))
        #                 self.operation_dict[frame].update(key_dict)
        #         logging.info('operation_dict:%s' % str(self.operation_dict))
        #
        #         if self.syn_frame in self.operation_dict and len(self.operation_dict[self.syn_frame].keys()) == alive_players:
        #             over = True
        #         logging.info('TRUEorFalse%d'%self.syn_frame in self.operation_dict and len(self.operation_dict[self.syn_frame].keys()) == alive_players or alive_players==0)
        #     if not over:
        #         pygame.time.wait(1)
        #         logging.info('wait one times, to ms:%d' % (pygame.time.get_ticks() - start_time))

        # 合并和发送HOST消息
        if self.syn_frame in self.operation_dict:
            """
            [["host", 300], {"opr": {"192.168.0.105": "wd"}, 
                             "syn": {"192.168.0.105": {"location": [2288.889, 1076.089],"velocity": [-2.351, -0.061], "health": 500}}
                                  }]
            """
            _head = ['host', self.syn_frame]
            # 添加玩家操作信息，每一帧
            _d = _operation = {'opr': self.operation_dict[self.syn_frame]}
            # 添加同步的玩家信息，每一秒
            if self.syn_frame % self.syn_fps == 0:
                _syn_dict = {}
                for ip in self.player_dict:
                    plane = self.player_dict[ip].plane
                    _syn_dict[ip] = {'location': [round(i, 3) for i in plane.location[:]],
                                     'velocity': [round(i, 3) for i in plane.velocity[:]],
                                     'health': plane.health}
                _d.update({'syn': _syn_dict})
            # 添加BOX，每2秒
            if self.syn_frame % (2 * config.FPS) == 0:
                _d.update({'box': self.box_produce()})  # 'box':{catalog:location,}
            # HOST MSG SEND
            _host_msg = _head, _d
            for ip in self.player_dict:  # 发送给每个玩家
                self.sock.msg_direct_send((_host_msg, ip))
            self.operation_dict.pop(self.syn_frame)

    def box_produce(self):
        location = [random.randint(0, config.MAP_SIZE[0]), random.randint(0, config.MAP_SIZE[1])]
        # Medic and so on. -->  10%, 30%, 20%, 30%, 10%
        rand_x = random.randint(0, 100)
        if rand_x <= 10:
            catalog = 'Medic'
        elif rand_x <= 40:
            catalog = 'Bullet'
        elif rand_x <= 60:
            catalog = 'Rocket'
        elif rand_x <= 90:
            catalog = 'Cluster'
        elif rand_x <= 100:
            catalog = 'Cobra'
        return {catalog: location}

    def erase(self):
        for _group in self.game_groups:
            _group.clear(self.map.surface, self.clear_callback)

    # def erase(self):
    #     self.weapon_group.clear(self.map.surface, self.clear_callback)
    #     self.plane_group.clear(self.map.surface, self.clear_callback)
    #     # self.tail_group.clear(self.map.surface, self.clear_callback)
    #     self.box_group.clear(self.map.surface, self.clear_callback)
    #     # self.slot.clear(self.clear_callback)
    #     self.health_group.clear(self.map.surface, self.clear_callback)

    def clear_callback(self, surf, rect):
        # surf.blit(source=self.map.surface, dest=(0, 0), area=self.current_rect)
        # self.screen.blit(source=self.map.surface, dest=(0, 0), area=self.current_rect)
        surf.blit(source=self.origin_map_surface, dest=rect,
                  area=rect)  # blit(source, dest, area=None, special_flags=0) -> Rect

    def blit_map(self):
        for _group in self.game_groups:
            if id(_group) == id(self.slot_group):  # 在screen的blit之后进行draw
                continue
            else:
                _group.draw(self.map.surface)

    def focus_screen(self):
        if self.screen_focus_obj:  # 跟随屏幕视角
            self.screen_rect.center = self.screen_focus_obj.rect.center
        # 调节屏幕不超出
        if self.screen_rect.left < 0:
            self.screen_rect.left = 0
        elif self.screen_rect.right > self.map.size[0]:
            self.screen_rect.right = self.map.size[0]
        if self.screen_rect.top < 0:
            self.screen_rect.top = 0
        elif self.screen_rect.bottom > self.map.size[1]:
            self.screen_rect.bottom = self.map.size[1]

        if self.screen_focus_obj and not self.map.surface.get_rect().contains(self.screen_focus_obj.rect):
            self.screen_focus_obj = None
        # print(self.screen_focus_obj,self.screen_rect)

    def blit_screen(self):
        self.screen.blit(source=self.map.surface, dest=(0, 0), area=self.screen_rect)  # Cost 5ms
        self.minimap.draw()
        self.slot_group.draw(self.screen)  # draw SlotWidget
        # self.show_info()

        self.screen.blit(self.test_font.render(str(self.clock.get_fps()), 1, config.BLACK, config.WHITE),
                         (config.SCREEN_SIZE[0] - 100, 10))
        self.clock.tick()
        if self.show_result and not self.hide_result:
            self.info.show_end(self.screen)

    # def show_info(self):
    #     # 显示游戏信息
    #     _time = pygame.time.get_ticks()
    #     self.info.add(str)
    #     self.info.show(self.screen)
    #     self.info.add(u'')
    #     self.info.add(u'')
    #     self.info.add(u'')
    #     self.info.add(u'')
    #     for ip in self.player_dict:
    #         self.info.add(u'Player IP:%s' % ip)
    #         if self.player_dict[ip].plane:
    #             self.info.add(u'Health:%d' % self.player_dict[ip].plane.health)
    #             self.info.add(u'Weapon:%s' % str(self.player_dict[ip].plane.weapon))
    #             self.info.add(u'Tail:%s' % self.tail_group)
    #             self.info.add(u'speed:%s,  location:%s,  rect:%s' % (
    #                 str(self.player_dict[ip].plane.velocity), str(self.player_dict[ip].plane.location), str(self.player_dict[ip].plane.rect)))
    #         self.info.add(u'Groups:%s' % str(self.plane_group))



    def update(self):
        for ip in self.player_dict:
            if self.player_dict[ip].alive:
                if self.player_dict[ip].update():  # player.update==True就是玩家飞机lost了
                    # self.plane_lost_msg_send(player.ip)  # 发送玩家lost的消息
                    # player.plane = None  # player.update()为True说明飞机已经delete了
                    # player.alive = False  # End Game
                    logging.info("player lost: %s" % ip)

        for _group in self.game_groups:  # WEAPON/PLANE update() 都放在这里
            if id(_group) == id(self.weapon_group):
                _group.update(self.plane_group)
            elif id(_group) == id(self.slot_group):
                # for index, obj in enumerate(self.slot_obj_list):
                #     obj.update(self.local_player.plane.weapon[index + 1]['number'])
                for slotbar in self.slotbar_obj_dict:
                    slotbar.update(self.local_player.plane.weapon[self.slotbar_obj_dict[slotbar]])
            else:
                _group.update()

        if self.syn_frame % 2 == 0:
            for _sprite in self.plane_group:
                t1 = my_sprite.ThrustBar(_sprite)
                self.thrustbar_group.add(t1)
            for _sprite in self.weapon_group:
                if _sprite.catalog in ['Rocket', 'Cobra']:
                    self.thrustbar_group.add(my_sprite.ThrustBar(_sprite))

        matrix.update()  # 基本上不花时间

        for _sprite in self.weapon_group:  # 读取1000个对象大约花5ms
            if not _sprite.hit:
                _sprite.rect.center = _sprite.write_out()
            # _sprite.rect.center = _sprite.write_out()
            # pygame.draw.rect(self.map.surface, (255, 0, 0), _sprite.rect, 1)
            # self.test_weapon_target(_sprite)
            # print('M:',_sprite.location)

            # print(matrix.pos_array[0:3])
        for _sprite in self.plane_group:  # 读取1000个对象大约花5ms
            _sprite.rect.center = _sprite.write_out()
            if _sprite.location.x < 10:
                _sprite.velocity.x = - _sprite.velocity.x
                _sprite.location.x = 10
            elif _sprite.location.x > config.MAP_SIZE[0] - 10:
                _sprite.velocity.x = - _sprite.velocity.x
                _sprite.location.x = config.MAP_SIZE[0] - 10
            if _sprite.location.y < 10:
                _sprite.velocity.y = - _sprite.velocity.y
                _sprite.location.y = 10
            elif _sprite.location.y > config.MAP_SIZE[1] - 10:
                _sprite.velocity.y = - _sprite.velocity.y
                _sprite.location.y = config.MAP_SIZE[1] - 10
            _sprite.write_in(_sprite.location)
            _sprite.rect.center = _sprite.write_out()
            # pygame.draw.rect(self.map.surface, (255, 0, 0), _sprite.rect, 1)

        self.minimap.update()

    def game_collide(self):
        """
        self.plane_group = pygame.sprite.Group()
        self.weapon_group = pygame.sprite.Group()
        [tobecontine]: 考虑替换spritecollide---groupcollide-------性能是一回事
        collide需要考虑是否还alive（因为爆炸的时候没有kill()），同时考虑自己碰撞自己是不算的
        """
        for plane in self.plane_group:  # 遍历每一个飞机
            if not plane.alive:
                continue
            weapon_list = pygame.sprite.spritecollide(plane, self.weapon_group, False)
            for weapon in weapon_list:
                if weapon.alive:
                    weapon.hitted(plane)
            # # 飞机之间的碰撞 spritecollide
            # plane_list = pygame.sprite.spritecollide(plane, self.plane_group, False, pygame.sprite.collide_rect_ratio(0.4))
            # for tmp_plane in plane_list:
            #     if id(tmp_plane) != id(plane) and tmp_plane.alive:
            #         plane.health = -401 #plane.health/2 # 碰撞血条折半==瞬间无数次碰撞
            #         tmp_plane.health = -401 #tmp_plane.health/2
        # # 飞机之间碰撞 groupcollide
        # plane_dict = pygame.sprite.groupcollide(self.plane_group, self.plane_group, False, False, pygame.sprite.collide_rect_ratio(0.4))
        # # planes = [_plane for _plane in plane_dict.keys()]  # key与value相撞，那么key一定包含了所有的value
        # for _plane in plane_dict.keys():  # key与value相撞，那么key一定包含了所有的value
        #     if len(plane_dict[_plane]) != 1:
        #         _plane.health = -401
        plane_list = self.plane_group.sprites()
        index_len = len(plane_list)
        for index_i in range(index_len-1):
            for index_j in range(index_i+1, index_len):
                if plane_list[index_i].location.distance_to(plane_list[index_j].location) < 20:
                    plane_list[index_i].health = -401
                    plane_list[index_j].health = -401

    def game_collide_with_box(self):
        for plane in self.plane_group:  # 进行飞机与Box之间碰撞探测
            box_collide_lst = pygame.sprite.spritecollide(plane, self.box_group, False,
                                                          pygame.sprite.collide_rect_ratio(config.COLLIDE_RATIO))
            for box in box_collide_lst:
                box.effect(plane)
                box.delete()

    def end_game(self):
        # 更新每个Player的状态
        for player in self.player_dict.values():
            player.update()

        # 更新本地玩家的状态
        alive_players = sum([player.alive for player in self.player_dict.values()])

        # 屏幕显示，本地飞机聚焦处理
        if self.local_player.alive:  # 本地玩家
            # FOCUS SCREEN
            if self.screen_focus_obj == None or self.screen_focus_obj.groups() == []:  # 本地飞机还活着，但是focus_obj不在任何group里面了，就指回本地飞机
                self.screen_focus_obj = self.local_player.plane
            if alive_players == 1:  # 只剩你一个人了
                self.show_result = True
                self.info.add_middle('YOU WIN!')
                self.info.add_middle_below('All players press "r" at the same time to restart the game.')
                # self.info.add_middle_below('press "ESC" to exit the game.')
                self.info.add_middle_below('press "Tab" to hide/show this message.')
        else:
            self.screen_focus_obj = None  # screen_rect聚焦为空，回复上下左右控制
            self.show_result = True
            self.info.add_middle('YOU LOST.')
            self.info.add_middle_below('All players press "r" at the same time to restart the game.')
            # self.info.add_middle_below('press "ESC" to exit the game.')
            self.info.add_middle_below('press "Tab" to hide/show this message.')

        return self.show_result

    def record_player_status(self):
        if self.syn_frame % self.syn_fps == 0:
            self.last_player_dict['frame'] = self.syn_frame
            for ip in self.player_dict:
                self.last_player_dict[ip] = {}
                self.last_player_dict[ip]['velocity'] = self.player_dict[ip].plane.velocity
                self.last_player_dict[ip]['location'] = self.player_dict[ip].plane.location
                self.last_player_dict[ip]['health'] = self.player_dict[ip].plane.health

    def wait_syn_frame(self):
        # 计算每帧时间，和时间等待
        # _time = time.time()*1000
        _time = pygame.time.get_ticks()
        logging.info('CostTime:%d' % int(_time - self.lastframe_time))
        # 每帧需要的时间 - 每帧实际运行时间，如果还有时间多，就等待一下
        stardard_diff_time = int(1000 / config.FPS - (_time - self.lastframe_time))
        if stardard_diff_time > 0:  # 等待多余的时间
            pygame.time.wait(stardard_diff_time)  # 这个等待时间写在这里不合适
            logging.info('WaitingTime:%d' % stardard_diff_time)

    def wait_whole_frame(self):
        now_time = pygame.time.get_ticks()
        logging.info('CostTime:%d' % int(now_time - self.lastframe_time))
        wait_time = int((1000 / config.FPS) * (self.syn_frame + 1) - (now_time - self.start_time))
        if wait_time > 0:
            pygame.time.wait(wait_time)
            logging.info('WaitingTime:%d' % wait_time)
        self.lastframe_time = pygame.time.get_ticks()

    def deal_screen_focus(self):
        if self.screen_focus_obj:
            self.screen_rect.center = self.screen_focus_obj.rect.center

    def test_add_plane(self):
        for i in range(100):
            xy = pygame.math.Vector2(random.randint(config.MAP_SIZE[0] // 10, config.MAP_SIZE[1]),
                                     random.randint(config.MAP_SIZE[1] // 10, config.MAP_SIZE[1]))
            p1 = my_sprite.Plane(location=xy, catalog='F35')
            self.plane_group.add(p1)
            h1 = my_sprite.HealthBar(stick_obj=p1)
            p1.add_healthbar(h1)
            self.health_group.add(h1)

    def test_weapon_target(self, _sprite):
        if _sprite.target:
            pygame.draw.aaline(self.map.surface, config.RED, _sprite.rect.center, _sprite.target.rect.center)


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
        logging.info("[%d][%d]%s%s" % (i, int(l1[i]) + int(l2[i]), '+' * int(l1[i]), '-' * int(l2[i])))
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,  # CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
                        format='%(asctime)s [line:%(lineno)d] [%(levelname)s] %(message)s',
                        filename='logger.log',
                        filemode='w')  # 每次真正import logging之后，filemode为w就会清空内容
    import widget

    w = widget.Widget()
    window = Game()
    window.main()
    test_calc_frame_cost()
