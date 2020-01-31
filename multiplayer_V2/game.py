# -*- coding: utf-8 -*-
import pygame
import random
import logging
import json

import config
import my_sprite
import my_sock

class Game:
    def __init__(self):
        self.screen_init()
        self.game_init()

    def screen_init(self):
        # ret = pygame.display.set_mode(size=(1366, 768), flags=pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        # logging.info('DISPLAY:%s' % str(ret))
        self.screen = pygame.display.get_surface()  # 游戏窗口对象
        self.screen_rect = self.screen.get_rect()  # 游戏窗口对象的rect
        logging.info('DISPLAY:%s' % self.screen_rect)

        self.origin_screen = self.screen.copy()
        # self.screen.fill(config.BACKGROUND_COLOR)  # 暂时不提前----测试
        self.clock = pygame.time.Clock()

    def game_init(self):


        self.player_dict = {}  # {'ip1':player_obj1, 'ip2':player_obj2}

        self.plane_group = pygame.sprite.Group()
        self.health_group = pygame.sprite.Group()

        self.map = None
        self.minimap = None
        self.origin_map_surface = None

        self.sock = my_sock.Sock()
        # ------------------------------------------------------------------------------------
        self.local_player = None # 需要区分本地的其他ai玩家
        self.host_player = None
        
        self.lock_frame = 0
        self.delay_frame = 0
        # self.start_time = 0

        self.show_result = False  # 用来显示Win or Lose
        self.hide_result = False
        self.last_tab_frame = 0

        self.screen_focus_obj = None  # 默认为空，首次指向本地plane, 空格指向本地plane, 为空但是本地plane还存在就指向plane
        
        self.done = False

        # self.current_rect = self.screen.get_rect()


        self.syn_frame = 0
        
        self.done = False
        self.box_group = pygame.sprite.Group()
        self.weapon_group = pygame.sprite.Group()

    def main(self):
        # Read&Format player_dict.dat
        with open('player_dict.dat','r') as f1:
            player_dict_origin = json.load(f1)
        _d = self.format_playerdict(player_dict_origin)
        logging.info('formatting "player_dict.dat" to game.dict success: %s'%str(_d))

        # Loading Players INFO
        for ip in _d.keys():
            msg_player = _d[ip]
            player = Player(weapon_group=self.weapon_group, ip=ip)
            plane = Plane(catalog=msg_player['Plane'], location=msg_player['location'])
            plane.load_weapon(catalog='Cobra', number=msg_player['Cobra'])
            plane.load_weapon(catalog='Bullet', number=msg_player['Bullet'])
            plane.load_weapon(catalog='Rocket', number=msg_player['Rocket'])
            player.add_plane(plane)
            self.player_dict[ip] = player
        logging.info('loading player INFO success: %s'%str(self.player_dict))

        # add sprite_group
        for ip in self.player_dict:
            self.plane_group.add(self.player_dict[ip].plane)
            self.health_group.add(self.player_dict[ip].health_bar)

        # # Weapon SlotWidget
        # self.slot = SlotWidget(screen=self.screen)

        # 获取本地玩家对象 self.local_player
        self.local_ip = self.sock.localip()
        if self.local_ip in self.player_dict:
            self.local_player = self.player_dict[self.local_player]
            logging.info('get local_player success: ip - %s'%self.local_ip)
        else:
            logging.error('get local_player failed: localip-%s not in player_dict_ip-%s'%(self.local_ip), str(self.player_dict.keys()))

        # MAP
        self.map = Map()
        self.map.add_cloud()
        self.minimap = MiniMap(self.screen, self.map.surface.get_rect(), self.screen_rect, self.plane_group)
        self.origin_map_surface = self.map.surface.copy()

        self.screen_focus_obj = self.local_player.plane
        self.deal_screen_focus() # 根据local_player位置移动一次self.screen_rect

        # to be continue ....start from here  2020-01-31 需要处理matirx的变换，考虑player_dict[ip]['ip']是否还有保留价值,保留sock两种模式?
        # MAIN LOOP
        pygame.key.set_repeat(10)  # control how held keys are repeated
        logging.info('MAIN LOOP Start.My IP&PORT: %s - %d' % (self.local_ip, self.port))
        self.main_loop()

    def format_playerdict(self, player_dict):
        """From: dict_player = {'ip':{'location': (randint(20, 80) / 100.0, randint(20, 80) / 100.0),
                                      'Plane': 'F35','Bullet': 200, 'Rocket': 10, 'Cobra': 3}，
                               }
            To:  d = {'ip':msg_player，
                     }
        }"""
        d = {}
        for ip in player_dict.keys():
            d[ip] = player_dict[ip]
            # d[ip]['ip'] = ip
            d[ip]['location'] = [config.MAP_SIZE[n]*i for n,i in enumerate(player_dict[ip]['location'])]
        return d

    def sock_waitfor(self, msg, dest, delay=100, waiting_times=30):
        count = 0
        while self.sock.q.empty():
            pygame.time.wait(delay)
            count += 1
            if count > waiting_times:
                logging.error('Sock Waiting Timeout: %s' % msg)
                return False
        data, address = self.sock.q.get()
        logging.info('GET:%s' % str(json.loads(data)))
        if address[0] == dest[0]:
            logging.info('Sock Msg Get:%s' % json.loads(data))
            return json.loads(data)
        else:
            logging.error('Sock Wrong Msg:%s %s' % (str(address), json.loads(data)))
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
        self.info.show(self.screen)  # 吃性能所在之处！！！！！！！！！！！！！！！
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
        for ip in self.player_dict:  # 发送给每一个网卡，包括自己
            try:
                # logging.info('Send %d---> %s, %s' % (self.syn_frame, str((ip, self.port)), str_key_list))
                self.sock.q_send.put(((self.syn_frame, key_list), ip))
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
            if weapon.catalog != 'Bullet':
                # print weapon
                weapon_collide_lst = pygame.sprite.spritecollide(weapon, self.weapon_group, False, pygame.sprite.collide_rect_ratio(1))  # False代表不直接kill该对象
                weapon.hitted(weapon_collide_lst)  # 发生碰撞相互减血
                # for hitted_weapon in weapon_collide_lst:
                #     hitted_weapon.hitted([weapon])  # 本身受到攻击的对象
            # 检测武器与飞机之间的碰撞        
            plane_collide_lst = pygame.sprite.spritecollide(weapon, self.plane_group, False, pygame.sprite.collide_rect_ratio(1))
            weapon.hitted(plane_collide_lst)  # 发生碰撞相互减血

    def deal_collide_with_box(self):
        for plane in self.plane_group:  # 进行飞机与Box之间碰撞探测
            box_collide_lst = pygame.sprite.spritecollide(plane, self.box_group, False, pygame.sprite.collide_rect_ratio(1))
            for box in box_collide_lst:
                box.effect(plane)
                box.delete()

    def syn_status(self):
        if self.syn_frame % (int(2 * FPS)) == 0:  # 每2秒同步一次自己状态给对方
            if self.local_player.alive:
                status_msg = ('syn_player_status', {'location': (self.local_player.plane.location[:]),
                                                    'velocity': (self.local_player.plane.velocity[:]),
                                                    'health': player.plane.health})
                for ip in self.player_dict:  # 发送给除自己的所有玩家
                    if ip != self.local_ip:
                        self.sock.q_send.put((status_msg, ip))


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
            if keys[pygame.K_TAB] :
                if self.syn_frame - self.last_tab_frame > self.fps/4:
                    self.last_tab_frame = self.syn_frame
                    self.hide_result = not self.hide_result  # 需要设置KEYUP和KEYDONW，to be continue...!!!!

            for keyascii in [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_i, pygame.K_o, pygame.K_p]:
                if keys[keyascii]:
                    key_list += chr(keyascii)

            # n_break += 1
            # if n_break > 3:
            #     break

        return key_list

    def box_msg_send(self):
        if self.syn_frame % (10 * FPS) == 0:  # 每n=10秒同步一次自己状态给对方
            location = [randint(0, config.MAP_SIZE[0]), randint(0, config.MAP_SIZE[1])]
            # Medic and so on. -->  10%, 30%, 30%, #0%
            rand_x = randint(0,100)
            if rand_x <= 10:
                rand_catalog = 'Medic'
            elif rand_x <= 40:
                rand_catalog = 'Gunfire_num'
            elif rand_x <= 70:
                rand_catalog = 'Rocket_num'
            elif rand_x <= 100:
                rand_catalog = 'Cobra_num'
            status_msg = ('box_status', {'location': location, 'catalog': rand_catalog})
            for ip in self.player_dict:
                self.sock.q_send.put((status_msg, ip))

    def plane_lost_msg_send(self, player_ip):
        status_msg = ('plane_lost', {'ip':player_ip})
        for ip in self.player_dict:
            self.sock.q_send.put((status_msg, ip))

    # def syn_lock_frame(self):
    #     lock_frame = 0
    #     while not self.done:
    #         pygame.time.wait(1000/FPS)
    #         status_msg = ('syn_lock_frame', lock_frame)
    #         for ip in self.player_dict:
    #             self.sock.q_send.put((status_msg, ip))
    #         lock_frame += 1

    def process(self, event_list):
        """
        每个玩家接收自己的消息队列，刷新自己的界面；
        不管延迟和丢包的问题，接受操作消息等待为resend_time=30ms；
        每过2帧进行一次状态同步：只将本地玩家飞机状态发送给其他玩家；
        """
        logging.info('Tp.10:%d' % pygame.time.get_ticks())
        # 产生随机奖励Box，并发送
        self.box_msg_send()

        # 状态同步, 先状态同步，再发送操作消息
        self.syn_status()

        # # 发送锁定帧
        # self.syn_lock_frame()

        # 发送普通键盘操作消息
        self.player_communicate(event_list)

        # logging.info('Tp.20:%d' % pygame.time.get_ticks())  #2-3 30ms

        # 进行游戏对象参数计算&渲染
        self.minimap.update()
        logging.info('Tp.21:%d' % pygame.time.get_ticks())  # 50ms
        self.weapon_group.update(self.plane_group)
        logging.info('Tp.22:%d' % pygame.time.get_ticks())
        self.tail_group.update()  # update尾焰
        if self.local_player.plane:
            for weapon in ['Bullet', 'Rocket', 'Cobra']:  # update SlotWidget
                if weapon == 'Bullet':
                    index_ = 1
                elif weapon == 'Rocket':
                    index_ = 2
                else:  # weapon == 'Cobra':
                    index_ = 3
                self.slot.update_line(weapon_name=weapon, weapon_num=self.local_player.plane.weapon[index_]['number'])
        # logging.info('Tp.23:%d' % pygame.time.get_ticks())  # 2-3 30ms
        # self.map.surface = self.origin_map_surface.copy()  # [WARNING]很吃性能！！！！！极有可能pygame.display()渲染不吃时间，这个copy（）很吃时间
        # self.map.surface.blit(self.origin_map_surface, (0,0))  # ！！

        # 添加尾焰轨迹
        # logging.info('Tp.30:%d' % pygame.time.get_ticks())

        if self.syn_frame % 5 == 0:
            self.add_weapon_tail(self.weapon_group)
        # if self.syn_frame % 3 == 0:  # 添加飞机尾焰
        #     self.add_unit_tail(self.plane_group)

        # DRAW
        self.box_group.draw(self.map.surface)  # draw随机Box
        self.tail_group.draw(self.map.surface)  # draw尾焰
        self.plane_group.draw(self.map.surface)  # draw飞机
        self.health_group.draw(self.map.surface)  # draw飞机血条
        # logging.info('Tp.31:%d' % pygame.time.get_ticks())  # 2-3 30ms
        self.weapon_group.draw(self.map.surface)  # draw武器

        for i in self.weapon_group:  # 画被跟踪框框
            if i.target:
                # print i.target
                pygame.draw.rect(self.map.surface, (255, 0, 0), i.target.rect, 1)
        # print self.slot.slot_group.sprites()[0].rect
        # print self.slot.line_list[1]['sprite_group'].sprites()[0].rect

        logging.info('Tp.40:%d' % pygame.time.get_ticks())  # 4-5 10ms

        # 碰撞处理
        self.deal_collide()
        logging.info('Tp.41:%d' % pygame.time.get_ticks())  # 20ms
        self.deal_collide_with_box()
        # logging.info('Tp.42:%d' % pygame.time.get_ticks())  # 1ms
        # 判断游戏是否结束
        for ip in self.player_dict:
            player = self.player_dict[ip]
            if player.alive:
                # player.plane.draw_health(self.map.surface)  # 显示飞机血条
                # 更新玩家状态,player.update()-->plane.update()-->plane.delete(),delete没了的的飞机
                if player.update():  # player.update==True就是玩家飞机lost了
                    self.plane_lost_msg_send(ip)  # 发送玩家lost的消息
                    player.plane = None  # player.update()为True说明飞机已经delete了
                    player.alive = False  # End Game
                    self.player_dict.pop(ip)
                    logging.info("Player lost: %s" % ip)
                    # return True
        logging.info('Tp.50:%d' % pygame.time.get_ticks())

        # 显示游戏信息
        self.info.add(u'')
        self.info.add(u'')
        self.info.add(u'')
        self.info.add(u'')
        self.info.add(u'')
        for ip in self.player_dict:
            self.info.add(u'Player IP:%s' % ip)
            if self.player_dict[ip].plane:
                self.info.add(u'Health:%d' % self.player_dict[ip].plane.health)
                self.info.add(u'Weapon:%s' % str(self.player_dict[ip].plane.weapon))
                self.info.add(u'Tail:%s' % self.tail_group)
                self.info.add(u'speed:%s,  location:%s,  rect:%s' % (
                    str(self.player_dict[ip].plane.velocity), str(self.player_dict[ip].plane.location), str(self.player_dict[ip].plane.rect)))
            self.info.add(u'Groups:%s' % str(self.plane_group))

        # 屏幕显示，本地飞机聚焦处理
        if not self.local_player.alive:  # 本地玩家
            self.screen_focus_obj = None  # screen_rect聚焦为空，回复上下左右控制
            self.show_result = True
            self.info.add_middle('YOU LOST.')
            self.info.add_middle_below('press "ESC" to exit the game.')
            self.info.add_middle_below('press "Tab" to hide/show this message.')
        else:  # 本地飞机还或者的情况
            if not self.screen_focus_obj.groups():  # 本地飞机还活着，但是focus_obj不在任何group里面了，就指回本地飞机
                self.screen_focus_obj = self.local_player.plane
            if len(self.player_dict.keys()) == 1:  # 只剩你一个人了
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
        logging.info('Tp.60:%d' % pygame.time.get_ticks())

    def get_deal_msg(self):
        while not self.done:  # 游戏结束判定
            # 空就不进行读取处理
            if self.sock.q.empty():
                continue
                pygame.time.wait(1)

            # 处理消息
            data, address = self.sock.q.get()
            data_tmp = json.loads(data)  # [frame_number, key_list], ['syn_player_status', dict]，['box_status', dict]

            # Msg Type1:操作类型的消息
            if isinstance(data_tmp[0], int):
                player = self.player_dict[address[0]]
                if player.alive and data_tmp[1]:  # 消息-->操作
                    weapon_obj = player.operation(data_tmp[1],self.syn_frame)  # data is list of pygame.key.get_pressed() of json.dumps
                    if address[0] == self.local_ip and weapon_obj:  # 如果导弹对象不为空，就将屏幕聚焦对象指向它
                        self.screen_focus_obj = weapon_obj
                    logging.info("Get %d----> %s, %s" % (data_tmp[0], str(address), str(data_tmp)))

            # Msg Type2:状态同步-->对象，同步类型消息
            elif data_tmp[0] == 'syn_player_status':
                player = self.player_dict[address[0]]
                if player.alive and data_tmp[1]:  # 消息-->操作
                    player.plane.location[:] = data_tmp[1]['location']
                    #+ data_tmp[1]['velocity']/ R_F  # 1帧的时间, 反而有跳跃感
                    player.plane.velocity[:] = data_tmp[1]['velocity']
                    player.plane.health = data_tmp[1]['health']  # !!!!!!!!会出现掉血了，然后回退回去的情况
                    logging.info("Get player status, local_frame:%d----> %s, %s" % (
                        self.syn_frame, str(address), str(data_tmp)))

            # Msg Type3:接受并处理Box类型消息
            elif data_tmp[0] == 'box_status':
                self.box_group.add(Box(location=data_tmp[1]['location'], catalog=data_tmp[1]['catalog']))

            # Msg Type4:接受并处理玩家飞机lost类型消息
            elif data_tmp[0] == 'plane_lost':  # status_msg = ('plane_lost', {'ip':player_ip})
                self.player_dict[data_tmp[1]['ip']].plane.health = 0

            ## Msg Type:接受并处理LockFrame
            # elif data_tmp[0] == 'syn_lock_frame':
            #     # if self.syn_frame>data_tmp[1] and address[0] != self.local_ip:  # 如果LockFrame小于本系统的同步帧
            #     if self.syn_frame > data_tmp[1]:
            #         self.delay_frame = self.syn_frame - data_tmp[1]
            #     logging.info("DelayFrames:%d--->%s"%(self.delay_frame, str(data_tmp)))


    def deal_screen_focus(self):
        if self.screen_focus_obj:
            self.screen_rect.center = self.screen_focus_obj.rect.center

    def main_loop(self):
        # GET MSG DEAL INIT
        self.thread_msg = threading.Thread(target=self.get_deal_msg)
        self.thread_msg.setDaemon(True)  # True:不关注这个子线程，主线程跑完就结束整个python process

        # # lockframe deal
        # if self.host_ip == self.local_ip:  # 主机才发送同步LockFrame
        #     self.thread_lock = threading.Thread(target=self.syn_lock_frame)
        #     self.thread_lock.setDaemon(True)  # True:不关注这个子线程，主线程跑完就结束整个python process

        # 同步开始循环
        for ip in self.player_dict:
            self.sock.q_send.put(('200 OK', ip))

        now_count = start_count = pygame.time.get_ticks()
        waiting_times = 20000
        msg_get_ip_list = {}
        while True:  # 等收到所有玩家的'200 ok'
            while not self.sock.q.empty():
                data, address = self.sock.q.get()
                if json.loads(data)=='200 OK':
                    self.sock.q_send.put(('200 OK', address))  # 收到补发一个200 OK，因为对方都是先打开监听，然后开始发送
                    logging.info('Start Msg Get:%s:%s' % (address,data))
                    msg_get_ip_list[address[0]] = True
                    if len(msg_get_ip_list.keys()) >= len(self.player_dict.keys()):
                        break

            if len(msg_get_ip_list.keys())>=len(self.player_dict.keys()):
                logging.info('game:begin')
                break

            if pygame.time.get_ticks() - now_count > 1000: # 每一秒朝没有收到消息的主机发送一个200 OK
                now_count = pygame.time.get_ticks()
                for ip in self.player_dict:
                    if ip not in msg_get_ip_list.keys():
                        self.sock.q_send.put(('200 OK', self.port))

            if pygame.time.get_ticks()-start_count > waiting_times:
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
            logging.info('T1:%d'%pygame.time.get_ticks())
            event_list = self.event_control()

            logging.info('T1.1:%d' % pygame.time.get_ticks())
            self.deal_screen_focus()  # 在飞机update()之前就不会抖动

            logging.info('T1.2:%d' % pygame.time.get_ticks())
            if self.process(event_list):  # 在FULLSCREEN下，这个函数最占性能20~40ms
                self.done = True
                break

            logging.info('T2:%d'%pygame.time.get_ticks()) # T1与T2之间平均花费12ms
            Map.adjust_rect(self.screen_rect, self.map.surface.get_rect())

            logging.info('T3:%d'%pygame.time.get_ticks())
            self.render(self.screen_rect)  # 该函数平均花费10ms(26ms), 在FULLSCREEN下是2ms

            logging.info('T4:%d'%pygame.time.get_ticks())
            pygame.display.flip()  # 2ms

            logging.info('T5:%d'%pygame.time.get_ticks())
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
            logging.info('T6:%d'%pygame.time.get_ticks())

        # self.thread1.close
        # self.sock.close()
        # pygame.time.wait(1000)
        pygame.quit()

    # def draw(self, surface):
    #     self.box_group.draw(surface)
    #     self.weapon_group.draw(surface)
    #     self.plane_group.draw(surface)
    # 
    # def update(self):
    #     # self.t1 = time.time()
    #     # w1 = my_sprite.Weapon(location=self.test_xy, catalog='Bullet', velocity=self.test_v.rotate(random.randint(0,360)))
    #     # self.weapon_group.add(w1)
    # 
    #     # self.t2 = time.time()
    #     # self.box_group.update()
    #     self.weapon_group.update(self.plane_group)
    #     self.plane_group.update()
    # 
    #     # self.t3 = time.time()
    #     matrix.update()  # 基本上不花时间
    # 
    #     # self.t4 = time.time()
    #     for _sprite in self.weapon_group:  # 读取1000个对象大约花5ms
    #         _sprite.rect.center = _sprite.write_out()
    #         # print(matrix.pos_array[0:3])
    #     for _sprite in self.plane_group:  # 读取1000个对象大约花5ms
    #         _sprite.rect.center = _sprite.write_out()
    #     # self.t5 = time.time()
    # 
    # def erase(self):
    #     self.box_group.clear(self.screen, self.clear_callback)
    #     self.weapon_group.clear(self.screen, self.clear_callback)
    #     self.plane_group.clear(self.screen, self.clear_callback)
    #     # self.weapon_group.clear(self.map.surface, self.clear_callback)
    #     # self.plane_group.clear(self.map.surface, self.clear_callback)
    # 
    # def clear_callback(self, surf, rect):
    #     surf.blit(source=self.origin_screen, dest=rect, area=rect)
    # 
    # def event_control(self):
    #     """
    #     :return: 返回空列表，或者一个元素为keys的列表
    #     看这个样子，应该是每一self.syn_frame就读取一次键盘操作bool值列表
    #     """
    #     pygame.event.get()  # 一定要把操作get()出来
    #     key_list = ''
    #     # n_break = 0
    #     if pygame.key.get_focused():
    #         keys = pygame.key.get_pressed()  # key is queue too， 一个列表，所有按键bool值列表
    #         if keys[pygame.K_ESCAPE]:
    #             self.exit_func()
    #             return  # EXIT GAME
    #         if keys[pygame.K_LEFT]:  # 直接使用 pygame.key.get_pressed() 可以多键同时独立识别
    #             self.screen_rect.x -= self.move_pixels
    #         if keys[pygame.K_RIGHT]:
    #             self.screen_rect.x += self.move_pixels
    #         if keys[pygame.K_UP]:
    #             self.screen_rect.y -= self.move_pixels
    #         if keys[pygame.K_DOWN]:
    #             self.screen_rect.y += self.move_pixels
    #         if keys[pygame.K_SPACE]:
    #             if self.local_player.plane:
    #                 self.screen_focus_obj = self.local_player.plane
    #                 # self.screen_focus = Map.mars_translate(self.d[self.local_ip]['location'])
    #                 # self.screen_rect.center = Map.mars_translate(self.local_player.plane.location)
    #         if keys[pygame.K_TAB]:
    #             if self.syn_frame - self.last_tab_frame > self.fps / 4:
    #                 self.last_tab_frame = self.syn_frame
    #                 self.hide_result = not self.hide_result  # 需要设置KEYUP和KEYDONW，to be continue...!!!!
    # 
    #         for keyascii in [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_i, pygame.K_o, pygame.K_p]:
    #             if keys[keyascii]:
    #                 key_list += chr(keyascii)
    #     return key_list
    # 
    # def exit_func(self):
    #     self.done = True
    # 
    # def operation(self, key_list, syn_frame):
    #     # print key_list
    #     for key in key_list:
    #         if key == 'a':
    #             self.plane.turn_left()
    #         elif key == 'd':
    #             self.plane.turn_right()
    #         elif key == 'w':
    #             self.plane.speedup()
    #         elif key == 's':
    #             self.plane.speeddown()
    # 
    #         elif key == 'i':
    #             self.weapon_fire(1)
    #         elif key == 'o' and syn_frame - self.fire_status[2] > config.FPS:
    #             self.fire_status[2] = syn_frame
    #             return self.weapon_fire(2)
    #         elif key == 'p' and syn_frame - self.fire_status[3] > config.FPS:
    #             self.fire_status[3] = syn_frame
    #             return self.weapon_fire(3)
    # 
    # def main(self):
    #     # 绘制文字
    #     cur_font = pygame.font.SysFont("arial", 15)
    #     i = 0
    #     while not self.done:
    #         i += 1
    #         self.draw(self.screen)
    #         key_list = self.event_control()
    #         for _key in key_list:
    #             if _key == 'a':
    #                 self.test_p.turn_left()
    #             elif _key == 'd':
    #                 self.test_p.turn_right()
    #             elif _key == 'w':
    #                 self.test_p.speedup()
    #             elif _key == 's':
    #                 self.test_p.speeddown()
    #         self.clock.tick(config.FPS)
    #         self.screen.blit(cur_font.render(str(i) + '-' + str(self.clock.get_fps()), 1, config.BLACK, config.WHITE),
    #                          (10, 10))
    #         self.update()
    #         # self.screen.blit(cur_font.render(str(i) + '-' + str(self.t5 - self.t4),1, config.BLACK, config.WHITE), (40, 40))
    #         pygame.display.flip()
    #         self.erase()


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


if __name__ == "__main__":
    window = Widget()
    window.main()
