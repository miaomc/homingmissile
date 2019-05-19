零.命令：
git clone https://github.com/miaomc/homingmissile.git
git add ReadMe.txt
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
git commit -m "add git command"
git push

一.有效文件: 
1).PNG
plane_red.png, plane_blue.png, homingmissile.png

2).py
single_player/ 主程序，还未拆解：main.py(all in one)
tmp/ 其他能运行,都在tmp目录下： missileV3_can_run.py,...,其中,mainV3.0_can_play.py已经可以玩了，真实的对战。
multiplayer/ 已经拆分,入口能够运行，正在增加联机模式
例外：main_tmp.py  之前的轨迹思路，之前还没编写完成

二.操作说明：
single_player/main.py
（1）空格切换
（2）F键发射普通导弹（走直线，射程长）
（3）H键发射跟踪导弹（能跟踪，射程短），需要右键选择飞机对象，才算是完成操作

multiplayer/main.py
(1)制作中，计划联机玩
(2)暂时先不去修改了, 菜单选择ji
(3)to be continue...

三.总结：
1)多写注释，真心会看不懂
2)至少要编到能运行，不能运行的都是瞎编

