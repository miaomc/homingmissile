# -*- coding: cp936 -*-


SINGLE_TEST = True
MAP_RATIO = 4
RESTART_MODE = False
LOCALIP = '192.168.0.106'
HOSTIP = '192.168.0.103'
PLANE_TYPE = 'J20'
C_OR_J = ''

SPEED_RATIO = 0.25
FPS = 20  # 设置在20帧比较有价值，要不然，LOCK帧就会跑到前面去

PINK = (255, 228, 225)
DARK_GREEN = (49, 79, 79)
GRAY = (168, 168, 168)
BACKGROUND_COLOR = DARK_GREEN
WHITE = (255, 255, 255)
LIGHT_GREEN = (10,200,100)

SCREEN_SIZE = (1300, 800)
MARS_SCREEN_SIZE = (8000, 4500)
MARS_MAP_SIZE = (8000 * MAP_RATIO, 4500 * MAP_RATIO)  # topleft starts: width, height
MARS_RATIO = (float(MARS_SCREEN_SIZE[0]) / SCREEN_SIZE[0], float(MARS_SCREEN_SIZE[1]) / SCREEN_SIZE[1])
CLOUD_IMAGE_LIST = ['./image/cloud1.png', './image/cloud2.png', './image/cloud3.png', './image/cloud4.png']

BOX_CATALOG = {
    'Medic': {
        'image': './image/box_medic.png',
        'health': 80,
    },
    # 'Power':{
    #     'image': './image/box_power.png',
    # },
    'Gunfire_num': {
        'image': './image/box_gunfire_num.png',
        'num': 100,
    },
    'Rocket_num': {
        'image': './image/box_rocket_num.png',
        'num': 5,
    },
    'Cobra_num': {
        'image': './image/box_cobra_num.png',
        'num': 3,
    },
}

TAIL_CATALOG = {
    'Point': {
        'image': './image/point.png',
        'init_time': -3,
        'life': 250,
    },
    # 'Plane_tail': {
    #     'image': './image/plane_tail.png',
    #     'init_time': -5,
    #     'life': 100,
    # },
}

PLANE_CATALOG = {
    'J20': {
        'health': 200,
        'max_speed': 3000,
        'min_speed': 540,
        'acc_speed': 60,
        'turn_acc': 35,  # 20
        'image': './image/plane_red.png',
        'damage': 100,
    },
    'F35': {
        'health': 200,
        'max_speed': 2400,  # 2400
        'min_speed': 540,
        'acc_speed': 50,
        'turn_acc': 25,
        'image': './image/plane_blue.png',
        'damage': 100,
    },
    'PDH': {
        'health': 300,
        'max_speed': 2400,
        'min_speed': 540,
        'acc_speed': 50,
        'turn_acc': 25,
        'image': './image/airplane.png',
        'damage': 100,
    },
    'PPDH': {
        'health': 500,
        'max_speed': 2400,
        'min_speed': 540,
        'acc_speed': 50,
        'turn_acc': 25,
        'image': './image/airplane1.png',
        'damage': 100,
    },
}

WEAPON_CATALOG = {
    'Gun': {
        'health': 10,
        'init_speed': 5000,
        'max_speed': 2500,
        'acc_speed': 0,
        'turn_acc': 0,
        'damage': 2,
        'image': ['./image/gunfire1.png'],
        'image_slot': './image/gunfire.png',
        'image_explosion':'./image/gunfire_explosion.png',  # https://github.com/joshuaskelly/trouble-in-cloudland
        'fuel': 8,  # 8
        'sound_collide_plane': ['./sound/bulletLtoR08.wav', './sound/bulletLtoR09.wav', './sound/bulletLtoR10.wav',
                                './sound/bulletLtoR11.wav', './sound/bulletLtoR13.wav', './sound/bulletLtoR14.wav']
    },
    'Rocket': {
        'health': 10,
        'init_speed': 0,
        'max_speed': 8000,
        'acc_speed': 65,
        'damage': 35,
        'turn_acc': 0,
        'image': './image/rocket.png',
        'image_slot': './image/homingmissile2.png',
        'fuel': 20,
    },
    'Cobra': {
        'health': 10,
        'init_speed': 0,
        'max_speed': 4500,  # 1360
        'acc_speed': 25,
        'turn_acc': 35,
        'damage': 25,
        'image': './image/homingmissile.png',
        'image_slot': './image/homingmissile1.png',
        'fuel': 16,
        'dectect_range': 10000 * 30
    },
    'Pili': {
        # ...,
    }
}
