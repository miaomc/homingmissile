# -*- coding: utf-8 -*-
import time
import socket
import json
import threading
from queue import Queue
import logging
import pygame

UDP_PORT = 8988
TCP_PORT = 8987


class Sock:
    """
    当前主机探测直接采用udp群发消息，没有采用多线程tcp探测主机端口和arp缩小主机范围
    目前已经打开 8987 TCP 主机探测端口； 8988 UDP 游戏初始化端口
    发现就算将UDP切换为TCP协议，也无法改变类似UDP一样采用多线程，一样要统计每个玩家是否发送成功，跟自己构造回复消息类似，只是多了TCP的重传机制
    """

    def __init__(self, tcp_bool=True):
        self.port_udp = UDP_PORT
        self.port_tcp = TCP_PORT
        self.tcp_bool = tcp_bool

        # UDP connect
        address = (self.localip(), self.port_udp)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(address)
        logging.info('Bind UDP socket %s ok.' % str(address))
        self.done = False

        # UDP MSG QUEUE
        self.q = Queue()  # GET  [((info,msg), ip), (), ...]
        self.q_send = Queue()  # SEND [((info,msg), ip), (), ...]

        # UDP sending
        thread_send = threading.Thread(target=self.msg_send)
        thread_send.setDaemon(True)
        thread_send.start()

        # UDP listening
        thread1 = threading.Thread(target=self.msg_recv)
        thread1.setDaemon(True)  # True:不关注这个子线程，主线程跑完就结束整个python process
        thread1.start()

        # TCP listening
        if self.tcp_bool:
            thread_tcp = threading.Thread(target=self.tcp_server)
            thread_tcp.setDaemon(True)  # True:不关注这个子线程，主线程跑完就结束整个python process
            thread_tcp.start()

    def close(self):
        self.done = True
        if self.tcp_bool:
            self.close_tcp()
        self.sock.close()
        logging.info('done Sock.sock.close().')

    def close_tcp(self):
        self.sock_tcp.close()
        logging.info('done Sock.sock_tcp.close().')


    def tcp_server(self):
        """任何程序都开启这个TCP监听"""
        self.sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_tcp.bind((self.localip(), self.port_tcp))
        self.sock_tcp.listen(20)
        while not self.done:
            try:
                client_connect, client_address = self.sock_tcp.accept()  # 是阻塞的
                # data, address = self.sock_tcp.recv(1024)
                client_connect.close()
            except Exception as msg:
                logging.warning('SOCK_TCP ERROR-->%s' % msg)

    def msg_send(self):
        """
        self.q_send是普通数据对象，传输的时候会加json.dumps
        注： 消息队列不包含port，port都集成在这里
        """
        while not self.done:
            if not self.q_send.empty():
                msg, ip = self.q_send.get()
                tmp = json.dumps(msg, )
                logging.info('SEND [%s]:%s' % (ip + ':' + str(self.port_udp), json.dumps(msg)))
                self.sock.sendto(tmp.encode('utf-8'), (ip, self.port_udp))
            else:
                pygame.time.wait(1)  # 卧槽，加了这一句就神奇之至了！瞬间不卡了。


    def msg_recv(self):
        """
        注： 消息队列不包含port，port在这里直接剔除了
        这里有个error: [Errno 10054]，有可能是winsock自身的bug：
        If sending a datagram using the sendto function results in an "ICMP port unreachable" response and the select
        function is set for readfds, the program returns 1 and the subsequent call to the recvfrom function does not
        work with a WSAECONNRESET (10054) error response. In Microsoft Windows NT 4.0, this situation causes the select
         function to block or time out.
        """
        while not self.done:
            try:
                data, address = self.sock.recvfrom(1024)  # data=JSON, address=(ip, port)  是阻塞的
                logging.info('RECV [%s]:%s' % (address[0] + ':' + str(self.port_udp), data))
                self.q.put((json.loads(data), address[0]))
            except Exception as msg:
                logging.warning('SOCK RECV ERROR-->%s' % msg)
                    # logging.info('RECV [%s]:%s' % (address[0] + ':' + str(self.port_udp), data))
                    # self.q.put((json.loads(data), address[0]))  # 获取数据，将数据转换为正常数据，并且只提取ip，不提取port

    def localip(self):
        return socket.gethostbyname(socket.gethostname())

    def scan_ip_tcp(self):
        time_start = time.time()
        ip_up = []
        ip_head = '.'.join(self.localip().split('.')[0:3])
        ip_list = [ip_head + '.' + str(i) for i in range(256)]
        port_list = [self.port_tcp]
        for ip in ip_list:
            # logging.info('Scan %s' % ip)
            up = False
            for port in port_list:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.1)  # 100ms,需要采用多线程来编写，要不然主机探测时间将达到接近25s， to be coninue..
                # print 'scan..'
                result = s.connect_ex((ip, port))
                # print (ip,port),
                if result == 0:
                    # print(ip)
                    logging.info('Port %d: open' % (port))
                    up = True
                s.close()
            if up:
                ip_up.append(ip)
        time_end = time.time()
        # logging.info('IP Scan:%s'%ip_list)
        # logging.info('IP Scan:%s'%port_list)
        logging.info('PortScan done! %d IP addresses (%d hosts up) scanned in %f seconds.' % (
            len(ip_list), len(ip_up), time_end - time_start))
        logging.info('Up hosts:')
        for i in ip_up:
            logging.info(i)
        # return [self.localip()]
        return ip_up

    def scan_ip_arp(self):
        pass

    def scan_hostip(self):
        hostip_list = []
        other_msg = []
        while not self.q.empty():
            (info, msg), ip = self.q.get()
            if info == 'host created':
                hostip_list.append(ip)  # 记录ip地址，port就不记录了
            else:
                other_msg.append(((info, msg), ip))
        for i in other_msg:  # 将剩余非建主机的消息放回队列
            self.q.put(i)
        return hostip_list

    def broadcast(self, messages, ip_list):
        for i in ip_list:
            self.q_send.put((messages, i))

    def host_broadcast(self):
        """群发这么多人也不是个办法，to be continue.."""
        ip_head = '.'.join(self.localip().split('.')[0:3])
        # ip_list = [ip_head + '.' + str(i) for i in range(100, 111, 1)]  # test, to be con...
        ip_list = [ip_head + '.' + str(i) for i in range(256)]
        # ip_list = self.scan_ip_tcp()
        logging.info('broadcast host ip list:%s' % str(ip_list))
        self.broadcast(messages=('host created', ''), ip_list=ip_list)
