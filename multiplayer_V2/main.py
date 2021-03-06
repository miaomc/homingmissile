# -*- coding: utf-8 -*-
"""
增加血量和子弹百分比
多人进去黑屏
网络延迟，飞跃
no广播发送，是否可以修改位直接发送255广播地址来实现 ip_list = [ip_head + '.255'] 无效

进入游戏的时候玩家列表不同步，非主机的玩家不显示主机玩家，用tcp改写

中途有一帧时间特别的长，大致在Frame No：45的样子
全屏情况下，对方坐标不停的闪烁(可能根据不同主机的分辨率导致rect不一样，可以采用pygame.transform去做变换)
尝试一下全屏硬件加速

键盘操作选项坐上去
可以根据区域型的update，在map中找到所有精灵（变化的精灵以及静态的精灵云彩）的位置，根据这个screen的相对位置相减，可以得出_rects,去除非screen之外的rects进行update
把说明做进去 左手操作 右手武器
武器自毁爆炸特效：Base有delete(hit=False),hitted,Weapon有collide里面的update之后的delete还有，hitted之后的delete
老机器建主机 新机器进去黑屏 超时
自定义化，自己定义导弹和子弹血量：子弹威力，子弹射程(fuel),飞机血量，飞机弹药，飞机最大速度，飞机转向速度
玩家战机不同颜色的区分，或者选择
菜单上显示当前版本 __version__
列表无映射，字典有映射，key无排序，可以新建结构处理
SlotWidget反正是一个一个对象创建，可以自己建立列表结合sprite.Group()来管理对象
content.py start游戏会概率报Errno 9
需要把颜色设置，不同的飞机
飞机受伤烟雾，随机产生在飞机身上
13.209.137.170
被导弹跟踪了之后的滴滴滴声音

ok优化血量显示，修改成sprite 2019-11-22
ok导弹特效制作 2019-11-22
ok飞机血量显示，计划采用手画矩阵涂色填充，位置跟随飞机rect底部，自带draw忘记是否会自动消除了 2019-11-21
ok子弹和导弹的爆炸效果 2019-11-21
ok把生成的背景变成一副图片，然后每次blit这个图片中的一部分就好了，这样就不需要clear了 2019-11-20 这个同样很占性能，达到75ms一帧
ok设置弹药剩余数量,因为sprite.Group.sprites列表不是按顺序来的，所以消耗弹药的时候不是连续的，新增的弹药的位置会与原有残余弹药位置重叠，但是数量不会错
ok可以单独绘制image_slot
ok在边缘很难旋转转向出来
ok关闭防火墙之后，还是会概率性进不去，程序bug
ok进入游戏不关闭防火墙都看不到主机->启动程序时，允许防火墙弹出的提示; 
ok需要使用管理员模式进入?，否则无法加入主机; 快速加入，客户端会黑屏， 反向加入，进不去，关闭防火墙就可以进去，程序bug
ok进入主机之后，开始，有时候会一边卡死，无法进入（管理员？）程序bug
ok加入主机，要等其他玩家反馈进入主机信息, 主机建快了就进入的话，客机进去之后收不到列表消息，程序bug
ok血条同步问题会导致有些玩家死了，但是另外一边还活着
ok建立主机时，有时候扫描会消失
ok删除restart
ok开始菜单、游戏操作说明、restart game
ok随机弹药包, 补血包,还需要同步才行，要不然每个玩家得到的Box不一样
ok转弯+加速不能同时使用
ok飞机爆炸之后要可以继续游戏，显示win lose ， press esc to exit
ok空格键回到飞机位置
ok爆炸效果（目前只制作了F35和J20飞机的效果）
"""

import logging
import widget
import menu
import engin


def main():
    logging.basicConfig(level=logging.DEBUG,  # CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
                        format='%(asctime)s [line:%(lineno)d] [%(levelname)s] %(message)s',
                        filename='logger.log',
                        filemode='w')  # 每次真正import logging之后，filemode为w就会清空内容
    w = widget.Widget()
    m = menu.Menu()  # 菜单界面
    restart = True
    if m.main():
        while restart:
            g = engin.Game()  # 游戏主逻辑
            restart = g.main()
            del g
            # engin.test_calc_frame_cost()
    del w


if __name__ == "__main__":
    main()
