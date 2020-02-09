# -*- coding: cp936 -*-
import pygame



import glob

def test_2():
    for png_file in glob.glob('*.png'):
        image = pygame.image.load(png_file).convert()
        image.set_colorkey((255,255,255))
        pygame.image.save(image, png_file)

def change_plane_color():
    image = pygame.image.load('plane_blue.png').convert()

    size = image.get_size()
    point = (20, 20)

    origin_color = image.get_at(point)

    RED = (255, 0, 0)
    ORANGE = (255, 165, 0)
    PINK = (252, 199, 209)
    GREEN = (0, 255, 0)
    CYAN = (0, 200, 200)
    BLUE = (0, 0, 255)
    PURPLE = (139, 0, 255)
    RAINBOW_COLOR_LIST = (RED, ORANGE, PINK, GREEN, CYAN, BLUE, PURPLE)
    str_list = 'RED,ORANGE,PINK,GREEN,CYAN,BLUE0,PURPLE'.lower().split(',')

    # print(len(RAINBOW_COLOR_LIST))
    new_image = image.copy()
    for index in range(len(RAINBOW_COLOR_LIST)):
        dest_color = RAINBOW_COLOR_LIST[index]
        name_str = str_list[index]
        # print(dest_color,name_str)

        for i in range(size[0]):
            for j in range(size[1]):
                if image.get_at((i,j)) == origin_color:
                    new_image.set_at((i,j), dest_color)

        pygame.image.save(new_image, 'plane_%s.png'%name_str)


def test_color():
    image = pygame.image.load('plane_blue.png').convert()
    size = image.get_size()
    point = (20, 20)

    origin_color = image.get_at(point)
    dest_color = (0,255,0,255)


    for i in range(size[0]):
        for j in range(size[1]):
            if image.get_at((i,j)) == origin_color:
                image.set_at((i,j), dest_color)

    pygame.image.save(image, 'plane_blue.png')


if __name__ == '__main__':
    pygame.init()
    pygame.mixer.init()  # 声音初始化
    pygame.display.init()  # 初始化
    pygame.display.set_mode((10,10))

    change_plane_color()


    pygame.quit()
