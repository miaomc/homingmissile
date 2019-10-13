import socket


ip_list = ['192.168.0.' + str(i) for i in range(256)]
port_list = [8987]

n=0
for ip in ip_list:
    up = False
    n+=1
    for port in port_list:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.1)
        print '.',
        if n%80==0:
            print
        result = s.connect_ex((ip, port))
        # print (ip,port),
        if result == 0:
            print ip
            up = True
        s.close()