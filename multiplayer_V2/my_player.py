import my_sprite
import config
import random
import pygame


class Player(object):

    def __init__(self, ip, weapon_group=None):
        """self.weapon_group = pygame.sprite.Group() in Class Game()"""
        self.ip = ip
        self.plane = None
        self.healthbar = None
        self.weapon_group = weapon_group
        self.fire_status = {1: -100, 2: -100, 3: -100,4:-100}
        self.slot1_sound_fire = pygame.mixer.Sound("./sound/minigun_fire.wav")
        self.alive = True

    def add_plane(self, plane):
        self.plane = plane
        self.healthbar = my_sprite.HealthBar(stick_obj=self.plane)
        self.plane.add_healthbar(self.healthbar)

    def update(self):
        if not self.plane.alive:
            self.alive = False
            # self.plane = None

    def weapon_fire(self, slot, syn_frame=0):
        # print 'Plane:', self.plane.velocity
        if self.plane.weapon[slot]:
            if self.plane.weapon[slot]['number'] > 0:
                self.plane.weapon[slot]['number'] -= 1
                # Bullet单独处理声音
                if slot == 1 and syn_frame - self.fire_status[1]>config.FPS/5:  # 180/(1000/FPS)=200/1000 *FPS
                    self.slot1_sound_fire.play(maxtime=200)
                    self.fire_status[1] = syn_frame
                # print dir(self.plane)
                tmp_rect = self.plane.velocity.normalize() * self.plane.rect.height  # 朝飞机前进的方向+velocity*角度
                tmp_rect.rotate_ip(random.choice((-15, 15)))
                # tmp_rect = (self.plane.velocity.normalize().x * self.plane.rect.height,self.plane.velocity.normalize().y * self.plane.rect.height)
                tmp_location = self.plane.location + tmp_rect
                # location_x = self.plane.location.x + tmp_rect[0]
                # location_y = self.plane.location.y + random.choice((tmp_rect[1]/2,-tmp_rect[1]/2))
                # print location_x,location_y, '<------------', self.plane.location, self.plane.rect
                if slot==4:
                    weapon = my_sprite.ClusterWeapon(location=tmp_location, velocity=self.plane.velocity)
                else:
                    weapon = my_sprite.Weapon(catalog=self.plane.weapon[slot]['catalog'],
                                          location=tmp_location,
                                          velocity=self.plane.velocity)

                self.weapon_group.add(weapon)
                return weapon

    def operation(self, key_list, syn_frame):
        # print key_list
        for key in key_list:
            if key == 'a':
                self.plane.turn_left()
            elif key == 'd':
                self.plane.turn_right()
            elif key == 'w':
                self.plane.speedup()
            elif key == 's':
                self.plane.speeddown()

            elif key == 'i':
                self.weapon_fire(1, syn_frame=syn_frame)
            elif key == 'o' and syn_frame - self.fire_status[2] > config.FPS:  # 射击间隔
                self.fire_status[2] = syn_frame
                return self.weapon_fire(2)
            elif key == 'p' and syn_frame - self.fire_status[3] > config.FPS:
                self.fire_status[3] = syn_frame
                return self.weapon_fire(3)
            elif key == 'u'and syn_frame - self.fire_status[4] > config.FPS:
                self.fire_status[4] = syn_frame
                self.weapon_fire(4)
