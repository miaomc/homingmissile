# -*- coding: utf-8 -*-
import os
import pygame
import config
import random
import logging


class Widget:
    def __init__(self):
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        pygame.mixer.init()  # 声音初始化
        pygame.display.set_mode(config.SCREEN_SIZE)
        pygame.mouse.set_visible(False)

        self.frame = 0
        self.clock = pygame.time.Clock()
        self.BACKGROUND_COLOR = (168, 168, 168)
        self.screen = pygame.display.get_surface()
        self.screen_rect = self.screen.get_rect()

        # self.sound_return = pygame.mixer.Sound()
        # self.sound_selecting = pygame.mixer.Sound()
        # print(config.BACKGROUND_MUSIC_LIST)
        try:
            pygame.mixer.music.load(random.choice(config.BACKGROUND_MUSIC_LIST))
            # pygame.mixer.music.queue(random.choice(config.BACKGROUND_MUSIC_LIST))
            pygame.mixer.music.play()
            pygame.mixer.music.set_endevent(pygame.USEREVENT)
        except Exception as msg:
            logging.error('play background music failed! ErrorMSG:%s' % msg)

    def test_bgm(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.USEREVENT:
                    # print('one')
                    pygame.mixer.music.load(random.choice(config.BACKGROUND_MUSIC_LIST))
                    pygame.mixer.music.play()

    def __del__(self):
        pygame.quit()
