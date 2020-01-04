class Player(object):

    def __init__(self, ip, weapon_group=None):
        """self.weapon_group = pygame.sprite.Group() in Class Game()"""
        self.ip = ip
        self.plane = None
        self.weapon_group = weapon_group
        self.fire_status = {1: 0, 2: 0, 3: 0}
        self.alive = True

    def add_plane(self, plane):
        self.plane = plane

    def update(self):
        return self.plane.update()

    def weapon_fire(self, slot):
        # print 'Plane:', self.plane.velocity
        if self.plane.weapon[slot]:
            if self.plane.weapon[slot]['number'] > 0:
                self.plane.weapon[slot]['number'] -= 1
                # print dir(self.plane)
                tmp_rect = Map.mars_unti_translate((
                    self.plane.velocity.normalize_vector().x * self.plane.rect.height,
                    self.plane.velocity.normalize_vector().y * self.plane.rect.height))
                location_x = self.plane.location.x + tmp_rect[0]
                location_y = self.plane.location.y + tmp_rect[1]
                # print location_x,location_y, '<------------', self.plane.location, self.plane.rect
                weapon = Weapon(catalog=self.plane.weapon[slot]['catalog'],
                                location=(location_x, location_y),
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
                self.weapon_fire(1)
            elif key == 'o' and syn_frame - self.fire_status[2] > FPS:
                self.fire_status[2] = syn_frame
                return self.weapon_fire(2)
            elif key == 'p' and syn_frame - self.fire_status[3] > FPS:
                self.fire_status[3] = syn_frame
                return self.weapon_fire(3)
