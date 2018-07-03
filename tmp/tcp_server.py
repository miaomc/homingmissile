# -*- coding: cp936 -*-
# server  
  
import socket  
# 关闭防火墙，设置为自己的公网ip  
address = ('192.168.1.121', 31500)  
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # s = socket.socket()  
s.bind(address)  
s.listen(5)  
  
ss, addr = s.accept()  
print 'got connected from',addr  
  
ss.send('byebye')  
ra = ss.recv(512)  
print ra  
  
ss.close()  
s.close() 
