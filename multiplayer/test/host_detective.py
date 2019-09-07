import socket
import time

target_IP = "192.168.0."
IP_range = 256
IP_up = []
port_range = 1024
delay = 0.001
print('Max delay: %ss' % (delay))
print('Port range: 0~%s' % (port_range - 1))

time_start = time.time()
for j in range(IP_range):
    print('Scan %s: ' % (target_IP + str(j)))
    up = 0
    # for port in range(port_range):
    for port in [80]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(delay)
        result = s.connect_ex((target_IP + str(j), port))
        if result == 0:
            print('Port %d: open' % (port))
            up = 1
        s.close()
    if up != 0:
        IP_up.append(target_IP + str(j))
time_end = time.time()
print('PortScan done! %d IP addresses (%d hosts up) scanned in %f seconds.' % (
IP_range, len(IP_up), time_end - time_start))
print('Up hosts:')
for i in IP_up:
    print i