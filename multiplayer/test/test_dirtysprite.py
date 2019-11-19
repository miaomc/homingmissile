# -*- coding: cp936 -*-
import pygame, os


def load_image(fullname, colorkey=None):
    try:
        image = pygame.image.load(fullname)
    except pygame.error:
        print('Cannot load image:', fullname)
        raise SystemExit(str(geterror()))
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, pygame.RLEACCEL)
    return image, image.get_rect()


class Dirty(pygame.sprite.DirtySprite):
    def __init__(self):
        pygame.sprite.DirtySprite.__init__(self)  # call Sprite initializer
        self.image, self.rect = load_image('plane_blue.png',-1)
        self.rect.move_ip(100,100)
        self.dirty = 2

    def update(self):
        self.rect.move_ip(0, 2)


# Initialize Everything
pygame.init()
screen = pygame.display.set_mode((480, 480))
pygame.display.set_caption('DirtySprite')
pygame.mouse.set_visible(0)

# Create The Backgound
background = pygame.Surface(screen.get_size())
background = background.convert()
background.fill((175, 175, 175))

# Display The Background
screen.blit(background, (0, 0))
pygame.display.flip()

# Prepare Game Objects
clock = pygame.time.Clock()
d = Dirty()
allsprites = pygame.sprite.LayeredDirty(d)

# Main Loop
going = True
allsprites.clear(screen, background)  # set dirty group‘s background
pygame.draw.rect(background, (10,200,100), (100,100,100,100), 0)
while going:
    clock.tick(60)

    # Handle Input Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            going = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            going = False

    allsprites.update()

    # Draw Everything
    rects = allsprites.draw(screen)
    pygame.display.update(rects)

pygame.quit()
