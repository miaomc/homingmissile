# -*- coding: cp936 -*-
import pygame

pygame.init()
pygame.mixer.init()  # 声音初始化
pygame.display.init()  # 初始化
pygame.display.set_mode((10,10))
#pygame.display.get_surface()

image = pygame.image.load('plane_blue.png').convert()
image.set_colorkey((255,255,255))
size = image.get_size()
point = (20, 20)

origin_color = image.get_at(point)
dest_color = (0,255,0,255)

for i in range(size[0]):
    for j in range(size[1]):
        if image.get_at((i,j)) == origin_color:
            image.set_at((i,j), dest_color)

pygame.image.save(image, 'blue_plane.png')
    



pygame.quit()
