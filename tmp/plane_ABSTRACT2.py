# -*- coding: cp936 -*-
class Plane(pygame.sprite.Sprite):
    def __init__(self,VELOCITY=100):
        self.velocity = VELOCITY  # 恒定的
        self.accelerate = [0,0]  # 没有加速度指导列表的时候，加速度默认为0
        pass

    def update(self, trace):
        self.accelerate = self.pop_first()
        self.velocity += self.accelerate
        self.position += self.velocity
        self.rect.center = self.position

    def draw(self):
        pass

    def pop_first():
        """取加速度列表第一个值，如果列表为空，则加速度为（0,0）
        """
        pass

    def plane_form_trace(self):
        end_point = get_mouse_pos()
        start_point = self.position

class Curve(self):
    pass
        
class Player():
    def __init__(self):
        self.plane_lst = []
        self.plane_lst.append(Plane())
        self.state = State('select,select_ok,set_plane,None')
        
    def operation(self):
        
        if state == 'select':
            res = select_plane()  # None , select_plane_obj
            if res:
                select_plane = res
                state.next()
        elif state = 'set_plane': 
            res = select_plane.planeform_trace()  # [set_plane_ok, plane_parameters_lst]
            set_ok = res[0]
            if set_ok:
            select_plane.accelerate_lst = res[1]
            state.next()

class State():
    def __init__(self):
        pass

    def __str__(self):
        pass
    
    def next(self):
        """取下一个值，如果列表为空，则取None
        """
        pass

class Control():
    def __init__(self):
        pass

    def event_loop(self):
        """To be continue..."""
        for event in pg.event.get():
            self.keys = pg.key.get_pressed()
            if event.type == pg.QUIT or self.keys[pg.K_ESCAPE]:
                self.done = True
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            objects.add(Laser(self.rect.center, self.angle))
        elif event.type == pg.MOUSEMOTION:
            self.get_angle(event.pos)

    def main(self):
        #self.init()  # init player1/player2s
        senario = {0:'Player1', 1:'Player2', 2:'Run'}
        
        i = 0
        while True:
            
            if senario[i] == 'Player1':
                self.player1.operation()
            elif senario[i] == 'Player2':
                self.player2.operation()
            else:
                self.running(steps = 20)
        
            self.update()
            i = (i+1) % len(senario.keys()) 
