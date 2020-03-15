import config
import pygame
import my_sprite


class Arrows:
    def __init__(self):
        self.w = my_sprite.Button(location=(config.SCREEN_SIZE[0] - 140, config.SCREEN_SIZE[1] - 140), angle=0)
        self.a = my_sprite.Button(location=(config.SCREEN_SIZE[0] - 200, config.SCREEN_SIZE[1] - 80), angle=90)
        self.s = my_sprite.Button(location=(config.SCREEN_SIZE[0] - 140, config.SCREEN_SIZE[1] - 80), angle=180)
        self.d = my_sprite.Button(location=(config.SCREEN_SIZE[0] - 80, config.SCREEN_SIZE[1] - 80), angle=-90)
        self.group = pygame.sprite.Group()
        self.group.add(self.w)
        self.group.add(self.s)
        self.group.add(self.a)
        self.group.add(self.d)
        self.left_right = 0
        self.up_down = 0
        self.last_keys = ''

    def status(self, keys):
        if 'w' not in self.last_keys and 'w' in keys:
            self.up_down += 1
            if self.up_down > 1:
                self.up_down = 1
        if 's' not in self.last_keys and 's' in keys:
            self.up_down += -1
            if self.up_down < -1:
                self.up_down = -1
        if 'a' not in self.last_keys and 'a' in keys:
            self.left_right += -1
            if self.left_right < -1:
                self.left_right = -1
        if 'd' not in self.last_keys and 'd' in keys:
            self.left_right += 1
            if self.left_right > 1:
                self.left_right = 1
        self.last_keys = keys

        keys_ret = keys
        if self.up_down < 0:
            self.w.off()
            self.s.on()
            keys_ret = keys_ret.replace('w','')
            keys_ret = keys_ret.replace('s', '')  # only one character in keys_ret
            keys_ret += 's'
        elif self.up_down == 0:
            self.w.off()
            self.s.off()
            keys_ret = keys_ret.replace('w', '')
            keys_ret = keys_ret.replace('s', '')
        else:
            self.w.on()
            self.s.off()
            keys_ret = keys_ret.replace('s', '')
            keys_ret = keys_ret.replace('w', '')
            keys_ret += 'w'

        if self.left_right < 0:
            self.a.on()
            self.d.off()
            keys_ret = keys_ret.replace('d', '')
            keys_ret = keys_ret.replace('a', '')
            keys_ret += 'a'
        elif self.left_right == 0:
            self.a.off()
            self.d.off()
            keys_ret = keys_ret.replace('d', '')
            keys_ret = keys_ret.replace('a', '')
        else:
            self.a.off()
            self.d.on()
            keys_ret = keys_ret.replace('a', '')
            keys_ret = keys_ret.replace('d', '')
            keys_ret += 'd'

        return keys_ret

