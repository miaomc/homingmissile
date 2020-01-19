# -*- coding: utf-8 -*-
class Map(object):

    def __init__(self, size=MARS_MAP_SIZE):
        self.size = Map.mars_translate(size)  # print size, self.size
        self.surface = pygame.Surface(self.size)
        self.surface.fill(BACKGROUND_COLOR)

    @staticmethod
    def mars_translate(coordinate):
        """translate Mars Coordinate to current Display Coordinate"""
        return [int(coordinate[i] / MARS_RATIO[i]) for i in [0, 1]]

    @staticmethod
    def mars_unti_translate(coordinate):
        return [int(coordinate[i] * MARS_RATIO[i]) for i in [0, 1]]

    # @staticmethod
    # def mars_translate(coordinate):
    #     """translate Mars Coordinate to current Display Coordinate"""
    #     return [int(coordinate[i] / (float(MARS_SCREEN_SIZE[i]) / SCREEN_SIZE[i])) for i in [0, 1]]
    #
    # @staticmethod
    # def mars_unti_translate(coordinate):
    #     return [int(coordinate[i] * (float(MARS_SCREEN_SIZE[i]) / SCREEN_SIZE[i])) for i in [0, 1]]

    def add_cloud(self, cloud_num=100):
        sprite_group = pygame.sprite.Group()
        for i in range(cloud_num):  # make 100 clouds randomly
            location = [randint(0, MARS_MAP_SIZE[0]), randint(0, MARS_MAP_SIZE[1])]
            cloud = Base(location=location)
            sprite_group.add(cloud)
        sprite_group.draw(self.surface)

    @staticmethod
    def adjust_rect(rect, big_rect):
        """调节rect，不出big_rect的大框框"""
        if rect.left < big_rect.left:
            rect.left = big_rect.left
        if rect.top < big_rect.top:
            rect.top = big_rect.top
        if rect.right > big_rect.right:
            rect.right = big_rect.right
        if rect.bottom > big_rect.bottom:
            rect.bottom = big_rect.bottom


class MiniMap(object):

    def __init__(self, screen, map_rect, current_rect, plane_group):
        self.screen = screen
        self.screen_rect = self.screen.get_rect()
        left = 10
        width = self.screen_rect.width / 5
        height = self.screen_rect.height / 4
        # logging.info('screen size:%s,  minimap_pos(w,h):%s'%(str(self.screen_rect), str(width, height))
        top = self.screen_rect.height - 10 - height
        self.rect = pygame.Rect(left, top, width, height)

        self.current_rect = current_rect
        self.map_rect = map_rect
        self.mini_width = int(self.rect.width / (float(MARS_MAP_SIZE[0]) / MARS_SCREEN_SIZE[0]))
        self.mini_height = int(self.rect.height / (float(MARS_MAP_SIZE[1]) / MARS_SCREEN_SIZE[1]))
        self.mini_left = self.rect.left + int(
            self.rect.width * self.current_rect.left / float(self.map_rect.left + 1))
        self.mini_top = self.rect.top + int(self.rect.height * self.current_rect.top / float(self.map_rect.top + 1))
        self.mini_rect = pygame.Rect(self.mini_left, self.mini_top, self.mini_width, self.mini_height)

        self.unit_rect_list = []
        self.mini_plane_group = plane_group
        for plane in plane_group:
            self.unit_rect_list.append(plane.rect)

    def update(self):
        self.mini_left = self.rect.left + int(
            self.current_rect.left / float(self.map_rect.width) * self.rect.width)  # 当前比例*小图宽度
        self.mini_top = self.rect.top + int(
            self.current_rect.top / float(self.map_rect.height) * self.rect.height)  # 当前比例*小图高度
        self.mini_rect = pygame.Rect(self.mini_left, self.mini_top, self.mini_width, self.mini_height)

    def draw(self):
        pygame.draw.rect(self.screen, (0, 0, 0), self.rect, 1)  # Big Rect in MiniMap
        pygame.draw.rect(self.screen, (0, 225, 10), self.mini_rect, 1)  # Small(current display) Rect in MiniMap

        for rect in self.unit_rect_list:
            left = self.rect.left + int(rect.left / float(self.map_rect.width) * self.rect.width)
            top = self.rect.top + int(rect.top / float(self.map_rect.height) * self.rect.height)
            pygame.draw.rect(self.screen, (255, 0, 255), pygame.Rect(left, top, 2, 2), 4)
