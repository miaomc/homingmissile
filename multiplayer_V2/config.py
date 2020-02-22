# -*- coding: utf-8 -*-
import glob

introduction = u"""Pure KEYBOARD operation:  
  (0) '↑', '↓', 'Enter' to create or join LAN game  
  (1)'w', 's' to speed plane up or down   
  (2)'a', 'd' to turn plane left or right  
  (3)'u', 'i', 'o', 'p' to fire different weapon  
  (4) 'Space' to focus back on plane  
"""

LIGHT_PINK = (255, 228, 225)
DARK_GREEN = (49, 79, 79)
GRAY = (168, 168, 168)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GREEN = (10, 200, 100)
DARK_RED = (120, 0, 0)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
PINK = (252, 199, 209)
GREEN = (0, 255, 0)
CYAN = (0, 200, 200)
BLUE = (0, 0, 255)
PURPLE = (139, 0, 255)
# RAINBOW_COLOR_LIST = (RED, ORANGE, YELLOW, GREEN, CYAN, BLUE, PURPLE)

BACKGROUND_COLOR = DARK_GREEN

FPS = 50

POLAR = (0, -1)

SCREEN_SIZE = (1280, 720)
MAP_SCREEN_RATIO = 3
MAP_SIZE = [SCREEN_SIZE[0] * MAP_SCREEN_RATIO, SCREEN_SIZE[1] * MAP_SCREEN_RATIO]

BACKGROUND_MUSIC_LIST = glob.glob('./bgm/*.mp3')

COLLIDE_RATIO = 1  # 小武器与大对象碰撞，该参数没有意义

PLANE_IMAGE = {'YELLOW': './image/plane_yellow.png',
               'ORANGE': './image/plane_orange.png',
               'RED': './image/plane_red.png',
               'GREEN': './image/plane_green.png',
               'BLUE': './image/plane_blue.png',
               'PURPLE': './image/plane_purple.png',
               'PINK': './image/plane_pink.png', }

WEAPON_LIST = ['Bullet', 'Rocket', 'Cobra', 'Cluster']
BULLET = 0
ROCKET = 0
COBRA = 0
CLUSTER = 50
WEAPON_DICT= {'i': 'Bullet',
               'o': 'Rocket',
               'p': 'Cobra',
               'u': 'Cluster', }
