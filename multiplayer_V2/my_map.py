# -*- coding: utf-8 -*-
import config
import pygame
import random
import my_sprite


class Map(object):

    def __init__(self, size=config.MAP_SIZE):
        self.size = size
        self.surface = pygame.Surface(self.size)
        self.surface.fill(config.BACKGROUND_COLOR)

    def add_cloud(self, cloud_num=80):
        sprite_group = pygame.sprite.Group()
        for i in range(cloud_num):  # make 100 clouds randomly
            location = [random.randint(0, self.size[0]), random.randint(0, self.size[1])]
            cloud = my_sprite.Cloud(location=location)
            sprite_group.add(cloud)
            # print('add cloud%s'%str(location))
        sprite_group.draw(self.surface)
        # pygame.draw.line(self.surface,(255,0,0),(10,10),(500,500))
        # print('draw cloud')

    @staticmethod
    def adjust_rect(rect, big_rect):
        """调节rect，不出big_rect的大框框"""
        if rect.left < big_rect.left:
            rect.left = big_rect.left
        if rect.top < big_rect.top:
            rect.top = big_rect.top


class MiniMap(object):
    def __init__(self, screen, map_rect, current_rect, plane_group):
        self.screen = screen
        self.screen_rect = self.screen.get_rect()
        left = 10
        width = self.screen_rect.width / 5
        height = self.screen_rect.height / 4
        # logging.info('screen size:%s,  minimap_pos(w,h):%s'%(str(self.screen_rect), str(width, height))
        top = self.screen_rect.height - 10 - height
        self.rect = pygame.Rect(left, top, width, height)

        self.current_rect = current_rect
        self.map_rect = map_rect
        self.mini_width = int(self.rect.width / config.MAP_SCREEN_RATIO)
        self.mini_height = int(self.rect.height / config.MAP_SCREEN_RATIO)
        self.mini_left = self.rect.left + int(
            self.rect.width * self.current_rect.left / float(self.map_rect.left + 1))
        self.mini_top = self.rect.top + int(self.rect.height * self.current_rect.top / float(self.map_rect.top + 1))
        self.mini_rect = pygame.Rect(self.mini_left, self.mini_top, self.mini_width, self.mini_height)

        # self.unit_rect_list = []
        self.minimap_group = plane_group
        # for plane in plane_group:
        #     self.unit_rect_list.append(plane.rect)

    def update(self):
        self.mini_left = self.rect.left + int(
            self.current_rect.left / float(self.map_rect.width) * self.rect.width)  # 当前比例*小图宽度
        self.mini_top = self.rect.top + int(
            self.current_rect.top / float(self.map_rect.height) * self.rect.height)  # 当前比例*小图高度
        self.mini_rect = pygame.Rect(self.mini_left, self.mini_top, self.mini_width, self.mini_height)

    def draw(self):
        pygame.draw.rect(self.screen, (0, 0, 0), self.rect, 1)  # Big Rect in MiniMap
        pygame.draw.rect(self.screen, (0, 225, 10), self.mini_rect, 1)  # Small(current display) Rect in MiniMap

        for _sprite in self.minimap_group:
            rect = _sprite.rect
            left = self.rect.left + int(rect.left / float(self.map_rect.width) * self.rect.width)
            top = self.rect.top + int(rect.top / float(self.map_rect.height) * self.rect.height)
            if _sprite.alive:
                color = (0,255,255)
            else:
                color = (255,0,0)  # 消失的话就不在group里面了，所以没有红色的了
            pygame.draw.rect(self.screen, color, pygame.Rect(left, top, 2, 2), 4)
