class Base(pygame.sprite.Sprite):
    """
    MARS COORDINATE: location+=velocity(* SPEED_RATIO / FPS), acc+=velocity, velocity
    EARTH COORDINATE: rect,
    """

    def __init__(self, location, image):
        pygame.sprite.Sprite.__init__(self)
        # cloud.png has transparent color ,use "convert_alpha()"

        # image = Surface对象
        self.image = image  # pygame.image.load(image).convert_alpha()  # image of Sprite

        # self.image.set_colorkey(WHITE)

        self.location = Vector(location)  # 采用 self.location记录位置，因为self.rect里面的值都是个整数
        # print self.location
        self.rect = self.image.get_rect(center=location)  # rect of Sprite
        self.rect.center = Map.mars_translate((self.location.x, self.location.y))  # !!!!!!!!!!这个坐标需要转换，这里需要重新设计

        # 图像翻转
        self.origin_image = self.image.copy()
        self.velocity = Vector(0, 1)  # 默认朝上

        # self.location = Vector(0, 0)  # ...

        self.min_speed = 0
        self.max_speed = 3000  # m/s
        self.speed = None  # Vector
        self.turn_acc = 0
        self.acc_speed = 0

        self.health = 0
        self.damage = 0
        self.alive = True

        self.acc = Vector(0, 0)

        self.sound_kill = None
        self.destruct_image_index = 0  # 爆炸图片不在这个里面，未设计To be continue
        self.self_destruction = 0
        self.hit = None
        self.catalog = None

    def rotate(self):
        angle = math.atan2(self.velocity.x, self.velocity.y) * 360 / 2 / math.pi - 180  # 这个角度是以当前方向结合默认朝上的原图进行翻转的
        self.image = pygame.transform.rotate(self.origin_image, angle)

    def update(self):
        self.velocity += self.acc
        self.location.x += self.velocity.x * SPEED_RATIO / FPS
        self.location.y += self.velocity.y * SPEED_RATIO / FPS
        # if self.location.x < 0:
        #     self.location.x = 0
        # elif self.location.x > MARS_MAP_SIZE[0]:
        #     self.location.x = MARS_MAP_SIZE[0]
        # if self.location.y < 0:
        #     self.location.y = 0
        # elif self.location.y > MARS_MAP_SIZE[1]:
        #     self.location.y = MARS_MAP_SIZE[1]
        if self.location.x < 10 * MAP_RATIO:
            self.velocity.x = - self.velocity.x
            self.location.x = 10 * MAP_RATIO
        elif self.location.x > MARS_MAP_SIZE[0] - 10 * MAP_RATIO:
            self.velocity.x = - self.velocity.x
            self.location.x = MARS_MAP_SIZE[0] - 10 * MAP_RATIO
        if self.location.y < 10 * MAP_RATIO:
            self.velocity.y = - self.velocity.y
            self.location.y = 10 * MAP_RATIO
        elif self.location.y > MARS_MAP_SIZE[1] - 10 * MAP_RATIO:
            self.velocity.y = - self.velocity.y
            self.location.y = MARS_MAP_SIZE[1] - 10 * MAP_RATIO
        self.rect.center = Map.mars_translate((self.location.x, self.location.y))
        # logging.info('acc: %s' % str(self.acc))
        self.acc = Vector(0, 0)
        self.rotate()
        # logging.info('location:%s, rect:%s' % (str(self.location), str(self.rect)))

    def delete(self, hit=False):
        if self.alive:  # 第一次进行的操作
            self.hit = hit
            # self.kill()  # remove the Sprite from all Groups
            self.alive = False
            if self.sound_kill:
                self.sound_kill.play()

        # 启动自爆动画
        # self.self_destruction += 0.25
        self.self_destruction += 0.5
        # if self.catalog == 'Gun':
        #     print self.self_destruction
        #     print self.hit,self.self_destruction,self.self_destruction // 1, self.destruct_image_index
        if self.hit and self.self_destruction < self.destruct_image_index:
            # print [self.self_destruction//2*40, 0, 39, 39],self.self_destruction,self.image.get_rect()
            self.origin_image = self.image = self.image_original.subsurface(
                [self.self_destruction //
                 1 * self.image_original.get_height(), 0, self.image_original.get_height() - 1,
                 self.image_original.get_height() - 1])

            self.image.set_colorkey(WHITE)
            self.rotate()
            return False
        else:
            self.kill()
            return True

    def hitted(self, base_lst):
        for base in base_lst:
            if id(self) == id(base):  # spritecollide如果是自己和自己就不需要碰撞了
                continue
            # print base.rect, self.rect
            self.health -= base.damage
            base.health -= self.damage
            if self.catalog == 'Gun' and isinstance(base, Plane):
                self.sound_collide_plane.play()
                self.delete(hit=True)
            elif self.catalog in ['Rocket', 'Cobra'] and isinstance(base, Plane):
                self.sound_collide_plane.play()
                self.delete(hit=True)


class Box(Base):
    def __init__(self, location, catalog):
        image_path = BOX_CATALOG[catalog]['image']
        self.image = pygame.image.load(image_path).convert()
        self.image.set_colorkey(WHITE)
        super(Box, self).__init__(location=location, image=self.image)

        self.sound_kill = pygame.mixer.Sound("./sound/beep.wav")
        self.catalog = catalog
        if catalog == 'Medic':
            self.health = BOX_CATALOG[catalog]['health']
        elif catalog == 'Power':
            pass
        elif catalog in ['Gunfire_num', 'Rocket_num', 'Cobra_num']:
            self.num = BOX_CATALOG[catalog]['num']

    def effect(self, plane_object):
        if self.catalog == 'Medic':
            plane_object.change_health(self.health)
        # elif catalog == 'Power':  # 这个后面再做威力加强，武器是发射时，加载在飞机的weapon_group上
        #     pass
        elif self.catalog == 'Gunfire_num':
            plane_object.change_weapon('Gun', self.num)
        elif self.catalog == 'Rocket_num':
            plane_object.change_weapon('Rocket', self.num)
        elif self.catalog == 'Cobra_num':
            plane_object.change_weapon('Cobra', self.num)


class Tail(Base):
    def __init__(self, location, catalog='Point'):
        image_path = TAIL_CATALOG[catalog]['image']
        self.image = pygame.image.load(image_path).convert()
        self.image.set_colorkey(WHITE)
        super(Tail, self).__init__(location=location, image=self.image)
        self.life = TAIL_CATALOG[catalog]['life']

        self.live_time = TAIL_CATALOG[catalog]['init_time']
        self.rect_mark = self.rect
        self.rect = (0, 0)
        # print self.location

    def update(self):
        self.live_time += 1
        # print self.live_time,self.life
        if self.live_time == 0:  # 越过0点的时候，恢复位置
            self.rect = self.rect_mark
        if self.live_time > self.life:
            self.delete()

    # def draw(self):
    #     """SpriteGroup.draw() 是单独运行的"""
    #     if self.live_time <= 0:
    #         super(Tail,self).draw()


class HealthBar(Base):
    def __init__(self, location):
        self._max_length = 200
        self.health_surface = pygame.Surface((self._max_length, 5))  # 最多是默认血条的5*40被长度
        self.health_surface.fill(LIGHT_GREEN)
        self.health_surface.convert()
        _image = self.health_surface.subsurface((0, 0, 40, 5))  # 默认是200的血量，对应40格血条长度
        super(HealthBar, self).__init__(location=location, image=_image)
        self.update(rect_topleft=Map.mars_translate(location), num=200)

    def update(self, rect_topleft, num):
        if num <= 0:
            _num = 0
        elif num > self._max_length:
            _num = 200
        self.image = self.health_surface.subsurface((0, 0, num / 5, 5))  # 默认是5的血量，对应1格血条长度
        self.rect.topleft = rect_topleft
        self.rect.move_ip(0, 50)  # 血条向下移50个像素点


class Plane(Base):

    def __init__(self, location, catalog='J20'):
        image_path = PLANE_CATALOG[catalog]['image']
        self.sound_kill = pygame.mixer.Sound("./sound/explode3.wav")
        if catalog in ['J20', 'F35']:  # 非透明图
            self.image_original = pygame.image.load(image_path).convert()
            self.image = self.image_original.subsurface((0, 0, 39, 39))
            self.image.set_colorkey(WHITE)
        else:
            self.image = pygame.image.load(image_path).convert_alpha()  # 透明色的搞法
        super(Plane, self).__init__(location=location, image=self.image)

        self.max_speed = PLANE_CATALOG[catalog]['max_speed']
        self.min_speed = PLANE_CATALOG[catalog]['min_speed']
        self.turn_acc = PLANE_CATALOG[catalog]['turn_acc']
        self.acc_speed = PLANE_CATALOG[catalog]['acc_speed']
        self.damage = PLANE_CATALOG[catalog]['damage']
        self.health = PLANE_CATALOG[catalog]['health']

        self.speed = (self.max_speed + self.min_speed) / 2  # 初速度为一半
        self.velocity = Vector(randint(-100, 100), randint(-100, 100)).normalize_vector() * self.speed  # Vector
        self.acc = Vector(0, 0)

        self.weapon = {1: {}, 2: {}, 3: {}}  # 默认没有武器

        self.sound_kill = pygame.mixer.Sound("./sound/explode3.wav")
        self.destruct_image_index = self.image_original.get_width() / self.image_original.get_height()
        # self.catalog = catalog

        self.health_bar = HealthBar(location=self.location)

        # self.last_health_rect = None
        # # print self.rect.width
        # self.health_surface = pygame.Surface((self.rect.width*5, 5))  # 最多是默认血条的5被长度
        # self.health_surface.fill(WHITE)
        # self.health_surface.convert()
        # self.image.set_colorkey(WHITE)

    def turn_left(self):
        self.acc += self.velocity.vertical_left() * self.turn_acc

    def turn_right(self):
        self.acc += self.velocity.vertical_right() * self.turn_acc

    def speedup(self):
        acc_tmp = self.acc + self.velocity.normalize_vector() * self.acc_speed
        if (self.velocity + acc_tmp).length() < self.max_speed:
            self.acc = acc_tmp

    def speeddown(self):
        acc_tmp = self.acc - self.velocity.normalize_vector() * self.acc_speed
        if (self.velocity - acc_tmp).length() > self.min_speed:
            self.acc = acc_tmp

    def change_health(self, num):
        self.health += num

    def load_weapon(self, catalog='Cobra', number=6):
        """self.weapon = { 1: {catalog:<Gun>, number=500},
            2:{catalog:<Cobra>, number=6},
            3: None
        }"""
        index = 3  # 默认为非Gun子弹和Rocket火箭弹的其他类
        if catalog == 'Gun':
            index = 1
        elif catalog == 'Rocket':
            index = 2
        self.weapon[index]['catalog'] = catalog
        self.weapon[index]['number'] = number

    def change_weapon(self, catalog, number):
        if catalog == 'Gun':
            self.weapon[1]['number'] += number
        elif catalog == 'Rocket':
            self.weapon[2]['number'] += number
        elif catalog == 'Cobra':
            self.weapon[3]['number'] += number

    def update(self):
        if not self.alive:  # 如果挂了,就启动自爆动画
            self.health_bar.delete()  # 删除血条
            super(Plane, self).update()
            return self.delete(hit=True)

        super(Plane, self).update()
        self.health_bar.update(rect_topleft=self.rect.topleft, num=self.health)  # 更新血条
        # self.health -= 50
        if self.health <= 0:
            # if self.last_health_rect:  # 最后删除血条
            #     surface.blit(source=self.health_surface, dest=self.last_health_rect)
            #     self.last_health_rect=pygame.Rect(self.rect.left, self.rect.top+self.rect.height+10, self.rect.width*(self.health*1.0/200), 5)
            return self.delete(hit=True)

    def draw_health(self, surface):
        pass
        # # """sprite.Group()是单独blit的"""
        # # if self.last_health_rect:
        # #     surface.blit(source=self.health_surface, dest=self.last_health_rect)
        # health_rect = pygame.Rect(self.rect.left, self.rect.top+self.rect.height+10, self.rect.width*(self.health*1.0/200), 5)
        # # self.last_health_rect = health_rect
        # # self.health_surface.blit(source=surface, dest=(0, 0), area=health_rect)  # 从map_surface获取底图到health_surface
        # # # self.screen.blit(source=self.map.surface, dest=(0, 0), area=self.current_rect)
        # if self.health > 0:
        #     pygame.draw.rect(surface, (10,200,100), health_rect, 0)


class Weapon(Base):
    def __init__(self, catalog, location, velocity):
        if catalog == 'Gun':
            image_path = WEAPON_CATALOG['Gun']['image'][randint(0, len(WEAPON_CATALOG['Gun']['image']) - 1)]
            self.image_original = pygame.image.load(image_path).convert()
            self.image_original.set_colorkey(WHITE)
            self.image = self.image_original.subsurface(
                (0, 0, self.image_original.get_height() - 1, self.image_original.get_height() - 1))
            super(Weapon, self).__init__(location=location, image=self.image)
            self.sound_fire = pygame.mixer.Sound("./sound/minigun_fire.wav")
            self.sound_fire.play(maxtime=200)
            self.sound_collide_plane = pygame.mixer.Sound(WEAPON_CATALOG['Gun']['sound_collide_plane'][randint(0, len(
                WEAPON_CATALOG['Gun']['sound_collide_plane']) - 1)])
            self.destruct_image_index = self.image_original.get_width() / self.image_original.get_height()
        else:
            image_path = WEAPON_CATALOG[catalog]['image']
            self.image_original = pygame.image.load(image_path).convert()
            self.image_original.set_colorkey(WHITE)
            self.image = self.image_original.subsurface(
                (0, 0, self.image_original.get_height() - 1, self.image_original.get_height() - 1))
            # self.image = self.image_original.subsurface((0, 0, self.image_original.get_width() - 1, self.image_original.get_height() - 1))
            super(Weapon, self).__init__(location=location, image=self.image)
            self.sound_fire = pygame.mixer.Sound("./sound/TPhFi201.wav")
            self.sound_fire.play()
            self.sound_kill = pygame.mixer.Sound("./sound/ric5.wav")
            self.sound_collide_plane = pygame.mixer.Sound("./sound/shotgun_fire_1.wav")
            self.destruct_image_index = self.image_original.get_width() / self.image_original.get_height()
        if catalog == 'Cobra':
            self.detect_range = WEAPON_CATALOG[catalog]['dectect_range']

        self.health = WEAPON_CATALOG[catalog]['health']
        self.damage = WEAPON_CATALOG[catalog]['damage']
        self.init_speed = WEAPON_CATALOG[catalog]['init_speed']
        self.max_speed = WEAPON_CATALOG[catalog]['max_speed']
        self.turn_acc = WEAPON_CATALOG[catalog]['turn_acc']
        self.acc_speed = WEAPON_CATALOG[catalog]['acc_speed']
        self.acc = self.velocity.normalize_vector() * self.acc_speed
        self.fuel = WEAPON_CATALOG[catalog]['fuel'] * FPS  # 单位为秒

        self.velocity = velocity + velocity.normalize_vector() * self.init_speed  # 初始速度为飞机速度+发射速度

        self.rotate()

        self.catalog = catalog
        self.target = None

        self.destruct_image_index = self.image_original.get_width() / self.image_original.get_height()

    def update(self, plane_group):
        if self.catalog == 'Cobra':
            """
            飞机、枪弹是一回事，加速度在不去动的情况下，为0；
            """
            if self.target and abs(self.velocity.angle() - (self.target.location - self.location).angle()) < math.pi / 3 \
                    and (self.location - self.target.location).length() < self.detect_range:
                angle_between = self.velocity.angle() - (self.target.location - self.location).angle()
                # print 'on target~',
                # 预计垂直速度的长度, 带正s负的一个float数值
                expect_acc = (self.target.location - self.location).length() * math.sin(angle_between)
                if abs(expect_acc) < self.turn_acc:  # 如果期望转向速度够了，就不用全力
                    acc = abs(expect_acc) * (1 and 0 < angle_between < math.pi or -1)
                else:  # 期望转向速度不够，使用全力转向
                    acc = self.turn_acc * (1 and 0 < angle_between < math.pi or -1)
                self.acc.x += acc * math.sin(self.velocity.angle())
                self.acc.y += - acc * math.cos(self.velocity.angle())
                # print 'target on:',self.target
            else:
                self.target = None
                for plane in plane_group:
                    if abs(self.velocity.angle() - (plane.location - self.location).angle()) < math.pi / 3 and \
                            (self.location - plane.location).length() < self.detect_range:
                        self.target = plane
                        break
        # print self.min_speed, self.velocity.length(), self.max_speed
        if self.min_speed < self.velocity.length() < self.max_speed:
            self.acc += self.velocity.normalize_vector() * self.acc_speed  # 加上垂直速度

        if self.fuel <= 0 or self.health <= 0:
            if self.catalog in ['Rocket', 'Cobra']:
                self.delete(hit=True)
            else:
                self.delete()
        else:
            super(Weapon, self).update()  # 正常更新
            self.fuel -= 1


class SlotWidget():
    """show local plane weapon slots' number"""

    def __init__(self, screen):
        """
        self.line_list = [{'key_obj':key_obj, 'value_obj':value_obj, 'num':num, 'sprite_group':sprite_group, 'sprite_list':[]}, {},..]
        self.slot_group = <slot1_obj, slot2_obj,.. .instance at pygame.sprite.Group>
        """
        self.screen_surface = screen
        self.weapon_name_list = ['Gun', 'Rocket', 'Cobra']
        self.slot_name_list = ['Gunfire_num', 'Rocket_num', 'Cobra_num']
        self.line_index = {k: v for v, k in enumerate(self.weapon_name_list)}  # {'Gun':1, ..}
        self.line_list = []
        self.slot_group = pygame.sprite.Group()
        self.make_body()

    def make_body(self):
        # zip 等价于 [('Gunfire_num', 'Gun'), ('Rocket_num', 'Rocket'), ('Cobra_num', 'Cobra')]
        slot_dict = {k: v for k, v in zip(self.slot_name_list, self.weapon_name_list)}

        for catalog in self.slot_name_list:
            image_path = BOX_CATALOG[catalog]['image']
            image = pygame.image.load(image_path).convert()
            image.set_colorkey(WHITE)
            # image = image.subsurface((0, 0, image.get_height() - 1, image.get_height() - 1))
            slot_obj = Base(location=(5, 5), image=image)

            image_path = WEAPON_CATALOG[slot_dict[catalog]]['image_slot']
            # print WEAPON_CATALOG[slot_dict[catalog]]['image'], image_path, slot_dict[catalog]
            image = pygame.image.load(image_path).convert()
            image.set_colorkey(WHITE)
            weapon_obj = Base(location=(5, 15), image=image)

            self.add_line(weapon_name=slot_dict[catalog], key_obj=slot_obj, value_obj=weapon_obj, num=0)

    def add_line(self, weapon_name, key_obj, value_obj, num):
        # deal key_obj: add into self.slot_group
        key_obj.rect.topleft = (7, 7 + 20 * len(self.slot_group.sprites()))
        self.slot_group.add(key_obj)

        # deal value_obj
        sprite_group = pygame.sprite.Group()
        line_dict = {'key_obj': key_obj, 'value_obj': value_obj, 'num': 0, 'sprite_group': sprite_group,
                     'sprite_list': []}
        self.line_list.append(line_dict)

        self.update_line(weapon_name=weapon_name, weapon_num=num)

    def update_line(self, weapon_name, weapon_num, gap=1):
        """line_dict = {'key_obj':key_obj, 'value_obj':value_obj, 'num':0, 'sprite_group':sprite_group, 'sprite_list':[]}"""
        index = self.line_index[weapon_name]
        line_dict = self.line_list[index]
        if weapon_num > line_dict['num']:
            slot_obj = line_dict['key_obj']  # 指定slot_obj
            image_path = WEAPON_CATALOG[weapon_name]['image_slot']  # 创建weapon_obj
            image = pygame.image.load(image_path).convert()
            image.set_colorkey(WHITE)
            weapon_obj = Base(location=(5, 5), image=image)
            # weapon_obj = copy.copy(line_dict['value_obj'])  # 采用copy.copy, 不知道会不会有其他风险, 果然有问题，删除
            weapon_obj.rect.center = slot_obj.rect.center
            weapon_obj.rect.left = slot_obj.rect.left + slot_obj.rect.width + gap + line_dict[
                'num'] * weapon_obj.rect.width
            line_dict['num'] += 1
            line_dict['sprite_group'].add(weapon_obj)
            line_dict['sprite_list'].append(weapon_obj)
        elif weapon_num < line_dict['num']:
            weapon_obj_list = line_dict['sprite_group'].sprites()
            if len(weapon_obj_list) > 0:
                line_dict['sprite_group'].remove(line_dict['sprite_list'].pop())
                line_dict['num'] -= 1

    def draw(self):
        """draw slot and draw weapon"""
        self.slot_group.draw(self.screen_surface)
        for line in self.line_list:
            line['sprite_group'].draw(self.screen_surface)

    def clear(self, callback):
        self.slot_group.clear(self.screen_surface, callback)
        for line in self.line_list:
            line['sprite_group'].clear(self.screen_surface, callback)