# Refactor "Multiplayer",重构 homingmissile\multiplayer项目:  
·适应python3
·重新设计Sprite,引入numpy,采用矩阵进行批量运动计算-----step 1  
·仍然采用多对多方式通信，没有采用服务器架构,统一采用my_sock模块
·整合display到统一界面      
·采用pygame.math.Vector2代替自己构建的Vector()  
·取消19M的字体文件   
  
#P.S.  
·README.md在要换行的语句最后打上2个空格  
·pip install -i https://pypi.douban.com/simple/ python_docx  
·numpy:  
    b = np.array([4,1])  
    np.row_stack((b,[2,3]))  # 增加一行  
    np.random.randint(0, 10, size=(2, 5))   
·pygame.Rect:  
    self.rect.move_ip(0, 50)  # 向下移50个像素点  
·pygame.Rect:  
    a = pygame.math.Vector2(2,4)  
    a[:]  
    a.x  
·变量尽量用全称  