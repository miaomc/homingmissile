# -*- coding: cp936 -*-
import pygame


class Infomation(object):
    """
    ������ʾ���Ͻǵ�״̬��
    """

    def __init__(self):
        self.message_list = []

    def add(self, message):
        self.message_list.append(message)

    def show(self, screen):
        for i, text in enumerate(self.message_list):
            self.show_text(screen, (10, i * 12), text, (0, 0, 0))
        self.message_list = []

    def show_text(self, surface_handle, pos, text, color, font_size=16):
        """���ִ�����        """
        # ��ȡϵͳ���壬���������ִ�С
        cur_font = pygame.font.SysFont(u"", font_size)

        # ������������
        text_fmt = cur_font.render(text, 1, color)

        # ��������
        surface_handle.blit(text_fmt, pos)
