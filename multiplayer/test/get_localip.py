import socket

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    ip = s.getsockname()[0]
finally:
    s.close()

# Through DNS
print ip

# All IPs
print socket.gethostbyname_ex(socket.gethostname())[-1]

import os
# Windows
print [a for a in os.popen('route print').readlines() if ' 0.0.0.0 ' in a][0].split()[-2]

# Linux
# [a for a in os.popen('/sbin/route').readlines() if 'default' in a][0].split()[1]

