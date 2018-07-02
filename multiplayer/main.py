# -*- coding: cp936 -*-
import os
import sys
import pygame
import single_player
import beginning
import multiplayer


if __name__ == "__main__":
    SCREEN_SIZE = (1300, 650)

    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()
    pygame.mixer.init()  # 声音初始化

    pygame.display.set_mode(SCREEN_SIZE)

    beginning_choice = beginning.Beginning()
    choice = beginning_choice.main()

    if choice== 'Single Player':
        run_it = single_player.Control()
        run_it.main_loop()
    elif choice == 'Multilayer':
        run = multiplayer.Multiplayer()
        run.main()
    elif choice == 'Exit':
        pass
    
    pygame.quit()
    sys.exit()
