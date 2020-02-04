# -*- coding: utf-8 -*-

import numpy as np

INT32 = np.int32
GROUP_NUM = 500  # 一组增加的数量
pos_array = np.zeros((GROUP_NUM, 2))
add_array = np.zeros((GROUP_NUM, 2))

length = GROUP_NUM
left_list = list(range(length - 1, -1, -1))


def add(xy):
    """xy: 2 elements, tuple or list type"""
    global length, pos_array, add_array, left_list
    # print(length)
    if not left_list:  # 没有剩余位置了，就加一组
        pos_array = np.row_stack((pos_array, np.zeros((GROUP_NUM, 2))))
        add_array = np.row_stack((add_array, np.zeros((GROUP_NUM, 2))))
        length += GROUP_NUM
        left_list += list(range(length - 1, length - GROUP_NUM - 1, -1))
    index = left_list.pop()
    pos_array[index] = xy
    add_array[index] = (0, 0)
    return index


def update():
    global pos_array, add_array
    pos_array += add_array

def delete(index):
    global left_list
    left_list.append(index)

def set(index, xy):
    global pos_array
    pos_array[index] = xy

def change_add(index, xy):
    global add_array
    # add_array[index] += xy  # 采用累加的方式
    add_array[index] = xy

def pick(index):
    global  pos_array
    return pos_array[index]

def test():
    global length, pos_array
    for i in range(1000):
        add((i, i + 1))

    delete(3)
    delete(5)

    for i in range(99):
        add((i, i + 1))

    for i in range(333):
        update()

    print(pos_array[1090:1100])
    print(length)


if __name__ == '__main__':
    test()
