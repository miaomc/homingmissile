# -*- coding: cp936 -*-
import os
import sys
import pygame
import control


if __name__ == "__main__":
    SCREEN_SIZE = (1300, 650)

    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()
    pygame.mixer.init()  # 声音初始化

    pygame.display.set_mode(SCREEN_SIZE)

    run_it = control.Control()
    run_it.main_loop()
    pygame.quit()
    sys.exit()
