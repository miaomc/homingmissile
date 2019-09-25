# -*- coding: cp936 -*-
import pygame


class Information(object):
    """
    用来显示左上角的状态栏
    """

    def __init__(self):
        self.message_list = []
        self.text_middle = 'MIDDLE TEST'
        self.text_middle_below = []
        self.whether_show_end = False

    def add(self, message):
        self.message_list.append(message)

    def show(self, screen):
        for i, text in enumerate(self.message_list):
            self.show_text(screen, (10, i * 12), text, (0, 0, 0), size=16)
        self.message_list = []

    def show_text(self, screen, pos, text, color=(0, 0, 0), size=16, bold=False):
        """文字处理函数        """
        # 获取系统字体，并设置文字大小
        cur_font = pygame.font.SysFont(u"Courier", size)
        cur_font.set_bold(bold)
        # 设置文字内容
        text_fmt = cur_font.render(text, 1, color)

        # 绘制文字
        screen.blit(text_fmt, pos)

    def add_middle(self, text):
        self.text_middle = text
        self.whether_show_end = True

    def add_middle_below(self, text):
        self.text_middle_below.append(text)
        self.whether_show_end = True

    def show_end(self, screen):
        if self.whether_show_end:
            self.show_text(screen, (screen.get_rect().centerx - 160, screen.get_rect().centery - 40), self.text_middle,
                           (0, 0, 0), size=40, bold=True)
            for i, text in enumerate(self.text_middle_below):
                self.show_text(screen, (screen.get_rect().centerx - 230, screen.get_rect().centery + 24 * i),
                               text, (0, 0, 0), size=24)
                self.text_middle_below = []
