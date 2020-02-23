# How to Play
- Based on python3, module needed: "numpy" + "pygame"
- Run homingmissile/multiplayer_V2/main.py
# KEYBOARD Operation:  
-  '↑', '↓' to select, 'Enter'or'→' to enter, '←' ot back up_level
-  'w'or's' to speed plane up or down, 'a'or'd' to turn plane left or right  
-  'u', 'i', 'o', 'p' to fire different weapons  
-  'Space' to focus back on plane    
-  'Esc' to quit game anytime
# Tips:
- slowing the plane can make a big turn
# Screenshot
![menu gui](https://raw.githubusercontent.com/miaomc/homingmissile/master/multiplayer_V2/screenshot/menu1.png)
![menu gui](https://raw.githubusercontent.com/miaomc/homingmissile/master/multiplayer_V2/screenshot/menu2.png)
![main gui](https://raw.githubusercontent.com/miaomc/homingmissile/master/multiplayer_V2/screenshot/engine1.png)
![main gui](https://raw.githubusercontent.com/miaomc/homingmissile/master/multiplayer_V2/screenshot/engine2.png)
# Other Detail Introductions:
## ------V1.00:"回合制，多人单机，鼠标操作"-----
- single_player/ 主程序，还未拆解：main.py(all in one)
- multiplayer/main.py 以及拆解了的版本，类似于single_player目录下的main.py
- 操作说明：
- （1）"空格"切换飞机和玩家，鼠标右键点点设定飞行目的地
- （2）"F"键发射普通导弹（走直线，射程长）
- （3）"H"键发射跟踪导弹（能跟踪，射程短），需要右键选择飞机对象，才算是完成操作
## ------V2.00:"即时制，多机联网，键盘操作，大小地图"------
- multiplayer/content.py
- 操作说明：
- 1）键盘上的w,a,s,d: 控制飞机加速减速和转向, control the plane turn left, right, speed up or down
- 2）键盘上的 i,o,p: 控制发射武器槽位-机炮/火箭弹/跟踪导弹, upon main keyboard, control fire weapon slot
- 3）键盘方向键↑,↓,←,→: 观察者模式下，控制小地图移动, control mini-map move
- 4）空格键(Space): 在跟踪导弹镜头或者观察者模式下，将当前地图切换到以己方飞机为中心的位置, find&swift window on your plane's location
## -----V2.10:重构Refactor V2.00版本------
- multiplayer_V2/main.py
## Release Version -- Old, not recommended
- basing on Win7, with old version(V2.00, which code is before refactoring)
## ------其他------
- tmp/ 其他能运行,都在tmp目录下： missileV3_can_run.py,...,其中,mainV3.0_can_play.py已经可以玩了，真实的对战。
- multiplayer/ 已经拆分,入口能够运行，正在增加联机模式
- main_tmp.py  之前的轨迹思路，之前还没编写完成
- multiplayer/main.py 做了菜单选择的代码
- pygame网站参考：https://www.cnblogs.com/yjmyzz/p/pygame-tutorial-7-life-diaplay.html 菩提树下的杨过 
# P.S. 命令
- Git使用方法（精心整理，绝对够用）https://blog.csdn.net/xukai0110/article/details/80637902：
- git clone https://github.com/miaomc/homingmissile.git
- git add ReadMe.txt
- git config --global user.email "you@example.com"
- git config --global user.name "Your Name"
- git commit -m "add git command"
- git push
- git pull
- git checkout ReadMe.txt
- touch .gitignore
- vi .gitignre
- *.pyc
- pyinstaller -F main.py --noconsole
# 总结：
- 多写注释，真心会看不懂
- 至少要编到能运行，不能运行的都是瞎编
