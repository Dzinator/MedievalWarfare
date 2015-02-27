from message import *
import queue, threading, socket, time, select, pickle, sys, os
class Client:
    def __init__(self, h, p, n, e):
        self.inQueue = queue.Queue()
        self.outGameQueue = queue.Queue()
        self.outLauncherQueue = queue.Queue()
        self.lock = threading.Lock()

        self.host = h
        self.port = p
        self.name = n
        self.engine = e
         
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(2)

        try :
            self.s.connect((self.host, self.port))
        except :
            print ('Unable to connect')
            sys.exit()
         
        print ('Connected to remote host. Start sending messages')
        #self.prompt()

        self.inputThread = threading.Thread(target=self.send)
        self.inputThread.daemon = True

        self.outputThread = threading.Thread(target=self.receive)
        self.outputThread.daemon = True

        self.inputThread.start()
        self.outputThread.start()

    def receive(self):
        while True:
            socket_list = [self.s]
            read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])
            for sock in read_sockets:
                if sock == self.s:
                    with self.lock:
                        try:
                            temp = self.recv_from_server(self.s)
                        except Exception:
                            return
                        if not temp:
                            print ('\nDisconnected from chat server')
                            sys.exit()
                        else :
                            if type(temp) == ChatMessage or type(temp) == TurnData:
                                self.outGameQueue.put(temp)
                            else:
                                self.outLauncherQueue.put(temp)

    def recv_from_server(self, my_sock):
        # ----START HELPER FUNCTION----
        def receive_len_header(sock):
            buf = b''
            while not buf.endswith(b'\n'):
                temp_buf = sock.recv(1)
                if len(temp_buf) == 0:  # client disconnected
                    return 0
                buf += temp_buf
            length = int(buf)
            #logger.debug("message length should be {}".format(length))
            return length

        def recv_real_message(sock, length):
            buf = b''
            while length != len(buf):
                temp_buf = sock.recv(length)
                if len(temp_buf) == 0:  # client disconnected
                    return b''
                buf += temp_buf
            return buf

        # ----END------------
        pmsg_len = receive_len_header(my_sock)
        pmsg = recv_real_message(my_sock, pmsg_len)

        msg = pickle.loads(pmsg)
        return msg

    def send(self):
        while True:
            if not self.inQueue.empty():
                with self.lock:
                    temp = self.inQueue.get()
                    pMsg = pickle.dumps(temp, -1)
                    self.s.sendall("{}{}".format(len(pMsg), "\n").encode())
                    self.s.sendall(pMsg)
            else:
                time.sleep(0.1)