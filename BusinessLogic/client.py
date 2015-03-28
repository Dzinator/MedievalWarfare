from message import *
import queue, threading, socket, time, select, pickle, sys, os
from pickle import UnpicklingError
class Client:
    def __init__(self, h, p, n, e, reconnect=True):
        self.inQueue = queue.Queue()
        self.outGameQueue = queue.Queue()
        self.outLauncherQueue = queue.Queue()
        self.lock = threading.Lock()
        self.connection_broken = False

        self.host = h
        self.port = p
        self.name = n
        self.engine = e
        self.reconnect = reconnect

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

        if self.reconnect:
            self.monitorThread = threading.Thread(target=self.do_reconnect)
            self.monitorThread.daemon = True
            self.monitorThread.start()

    def do_reconnect(self):
        """a monitor thread will run this function and monitor if connection
        is broken, if so, will try to re-establish connection to server"""
        while True:
            if self.reconnect and self.connection_broken:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(2)
                    s.connect((self.host, self.port))
                except Exception:
                    print("reconnection failed, try again in 1 second")
                    time.sleep(1)
                else:
                    self.connection_broken = False
                    self.s = s
                    # we empty the inQueue and just ignore any input made
                    # by player during connection drop for synchronization
                    # reason
                    while not self.inQueue.empty():
                        self.inQueue.get()
                    # put the ReconnectRequest message on the top of inQueue
                    self.inQueue.put(ReconnectRequest(self.name))
                    # inputThread is likely to be alive if it's blocking on
                    # the inQueue, if so, it's ok because we will already
                    # swaped our socket. Otherwise, we restart it
                    if not self.inputThread.isAlive():
                        self.inputThread = threading.Thread(target=self.send)
                        self.inputThread.daemon = True
                        self.inputThread.start()
                    # outputThread is likely to be dead, if so, we restart
                    # it as well
                    if not self.outputThread.isAlive():
                        self.outputThread = threading.Thread(target=self.receive)
                        self.outputThread.daemon = True
                        self.outputThread.start()
                    else:
                        # this is too unpredictable and shouldn't have
                        # happened. It's better just terminate the program
                        print("outputThread still alive after connection "
                              "broken, this should not have happened. Exiting")
                        return
                    print("reconnected to server")
            else:
                # just wait for connection to break
                time.sleep(1)


    def receive(self):
        while True:
            socket_list = [self.s]
            try:
                read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])
            except Exception:
                self.connection_broken = True
                print("connection broken")
                return

            for sock in read_sockets:
                if sock == self.s:
                    with self.lock:
                        try:
                            temp = self.recv_from_server(self.s)
                        except UnpicklingError as upe:
                            print("message format is bad: {}".format(
                                upe.args[0]))
                        except Exception:
                            self.connection_broken = True
                            print("connection broken")
                            return
                        if not temp:
                            self.connection_broken = True
                            print("connection borken")
                            return
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
            while length > 0:
                temp_buf = sock.recv(length)
                if len(temp_buf) == 0:  # client disconnected
                    return b''
                length -= len(temp_buf)
                buf += temp_buf
            return buf

        # ----END------------
        try:
            message_len = receive_len_header(self.socket)
            if not message_len:
                raise Exception("connection broken")
            new_pmsg = recv_real_message(self.socket, message_len)  # pickled
            if not new_pmsg:
                raise Exception("connection broken")
        except Exception:  # connection broken
            raise Exception("connection broken")
        try:
            msg = pickle.loads(new_pmsg)
        except Exception:
            raise UnpicklingError(new_pmsg)
        return msg

    def send(self):
        while True:
            if not self.inQueue.empty():
                with self.lock:
                    temp = self.inQueue.get()
                    pMsg = pickle.dumps(temp, -1)
                    try:
                        self.s.sendall("{}{}".format(len(pMsg), "\n").encode())
                        self.s.sendall(pMsg)
                    except Exception:
                        self.connection_broken = True
                        return
            else:
                time.sleep(0.1)