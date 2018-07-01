# -*- coding: cp936 -*-
import pygame


class Infomation(object):
    """
    用来显示左上角的状态栏
    """

    def __init__(self):
        self.message_list = []

    def add(self, message):
        self.message_list.append(message)

    def show(self, screen):
        for i, text in enumerate(self.message_list):
            self.show_text(screen, (10, i * 12), text, (0, 0, 0), size=16)
        self.message_list = []

    def show_text(self, screen, pos, text, color=(0,0,0), size=16, bold=False):
        """文字处理函数        """
        # 获取系统字体，并设置文字大小
        cur_font = pygame.font.SysFont(u"Courier", size)
        cur_font.set_bold(bold)
        # 设置文字内容
        text_fmt = cur_font.render(text, 1, color)

        # 绘制文字
        screen.blit(text_fmt, pos)
