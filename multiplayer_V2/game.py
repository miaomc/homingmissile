# -*- coding: utf-8 -*-
import pygame
import random
import config
import my_sprite
import matrix
import os
os.environ['SDL_VIDEO_CENTERED'] = '1'

class Widget:
    def __init__(self):
        self.screen_init()
        self.game_init()

    def screen_init(self):
        pygame.init()
        pygame.mixer.init()  # 声音初始化
        pygame.display.set_mode(config.SCREEN_SIZE)
        # pygame.mouse.set_visible(False)

        self.screen = pygame.display.get_surface()
        self.screen.fill(config.BACKGROUND_COLOR)
        self.origin_screen = self.screen.copy()
        # self.screen.fill(config.BACKGROUND_COLOR)  # 暂时不提前----测试
        self.clock = pygame.time.Clock()

        self.done = False

    def game_init(self):

        self.box_group = pygame.sprite.Group()
        self.weapon_group = pygame.sprite.Group()
        self.plane_group = pygame.sprite.Group()

        xy = pygame.math.Vector2(random.randint(config.MAP_SIZE[0] // 8, config.MAP_SIZE[0] * 2 // 8),
                                 random.randint(config.MAP_SIZE[1] // 3, config.MAP_SIZE[1] * 2 // 3))
        # print(my_sprite.Box.BOX_CATALOG)
        # print(xy,random.choice(.keys()))
        self.box_group.add(my_sprite.Box(xy, random.choice(list(my_sprite.Box.BOX_CATALOG.keys()))))
        for i in range(20):
            xy = pygame.math.Vector2(random.randint(config.MAP_SIZE[0] // 10, config.MAP_SIZE[1]),
                                     random.randint(config.MAP_SIZE[1] // 10, config.MAP_SIZE[1]))
            p1 = my_sprite.Plane(location=xy, catalog='F35')
            self.plane_group.add(p1)
        # print((config.MAP_SIZE[0]/3, config.MAP_SIZE[1]*2/3))
        # print(dir(p1))
        # print(type(p1.velocity))
        self.test_xy = xy = p1.location
        self.test_v = p1.velocity
        self.test_p = p1
        w1 = my_sprite.Weapon(location=xy, catalog='Bullet', velocity=p1.velocity)
        self.weapon_group.add(w1)
        w1 = my_sprite.Weapon(location=xy, catalog='Rocket', velocity=p1.velocity)
        self.weapon_group.add(w1)
        for i in range(1):
            w1 = my_sprite.Weapon(location=xy, catalog='Cobra', velocity=self.test_v.rotate(random.randint(0, 360)))
            self.weapon_group.add(w1)

    def draw(self, surface):
        self.box_group.draw(surface)
        self.weapon_group.draw(surface)
        self.plane_group.draw(surface)

    def update(self):
        # self.t1 = time.time()
        # w1 = my_sprite.Weapon(location=self.test_xy, catalog='Bullet', velocity=self.test_v.rotate(random.randint(0,360)))
        # self.weapon_group.add(w1)

        # self.t2 = time.time()
        # self.box_group.update()
        self.weapon_group.update(self.plane_group)
        self.plane_group.update()

        # self.t3 = time.time()
        matrix.update()  # 基本上不花时间

        # self.t4 = time.time()
        for _sprite in self.weapon_group:  # 读取1000个对象大约花5ms
            _sprite.rect.center = _sprite.write_out()
            # print(matrix.pos_array[0:3])
        for _sprite in self.plane_group:  # 读取1000个对象大约花5ms
            _sprite.rect.center = _sprite.write_out()
        # self.t5 = time.time()

    def erase(self):
        self.box_group.clear(self.screen, self.clear_callback)
        self.weapon_group.clear(self.screen, self.clear_callback)
        self.plane_group.clear(self.screen, self.clear_callback)
        # self.weapon_group.clear(self.map.surface, self.clear_callback)
        # self.plane_group.clear(self.map.surface, self.clear_callback)

    def clear_callback(self, surf, rect):
        surf.blit(source=self.origin_screen, dest=rect, area=rect)

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
            if keys[pygame.K_ESCAPE]:
                self.exit_func()
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
        return key_list

    def exit_func(self):
        self.done = True

    def operation(self, key_list, syn_frame):
        # print key_list
        for key in key_list:
            if key == 'a':
                self.plane.turn_left()
            elif key == 'd':
                self.plane.turn_right()
            elif key == 'w':
                self.plane.speedup()
            elif key == 's':
                self.plane.speeddown()

            elif key == 'i':
                self.weapon_fire(1)
            elif key == 'o' and syn_frame - self.fire_status[2] > config.FPS:
                self.fire_status[2] = syn_frame
                return self.weapon_fire(2)
            elif key == 'p' and syn_frame - self.fire_status[3] > config.FPS:
                self.fire_status[3] = syn_frame
                return self.weapon_fire(3)

    def main(self):
        # 绘制文字
        cur_font = pygame.font.SysFont("arial", 15)
        i = 0
        while not self.done:
            i += 1
            self.draw(self.screen)
            key_list = self.event_control()
            for _key in key_list:
                if _key == 'a':
                    self.test_p.turn_left()
                elif _key == 'd':
                    self.test_p.turn_right()
                elif _key == 'w':
                    self.test_p.speedup()
                elif _key == 's':
                    self.test_p.speeddown()
            self.clock.tick(config.FPS)
            self.screen.blit(cur_font.render(str(i) + '-' + str(self.clock.get_fps()), 1, config.BLACK, config.WHITE),
                             (10, 10))
            self.update()
            # self.screen.blit(cur_font.render(str(i) + '-' + str(self.t5 - self.t4),1, config.BLACK, config.WHITE), (40, 40))
            pygame.display.flip()
            self.erase()

        pygame.quit()


if __name__ == "__main__":
    window = Widget()
    window.main()
