# todo the event driven I/O cannot respond fast enough because of the
# sequential code server execute right after. Multiple client could send
# message at the same time and sequence of message could got mixed up
# use process pool and use CV on individual socket to synchronize send and recv
# or a simpler solution is to fire up a thread every time a request comes in
import queue
import socket
import logging
import sys
import pickle
import threading



# initialize logging
import clientMessage

logging.basicConfig(level="INFO",
                    format='%(asctime)s(%(threadName)-10s)[%(levelname)s] '
                           '%(message)s')
logger = logging.getLogger(__name__)


# define global varaibles
SERVER_ADDR = ("localhost", 8000)
send_queue = queue.Queue()


class ClientSocket(threading.Thread):
    """a wrapper on the socket from clients"""

    def __init__(self, sock, server):
        """
            initilized with a raw socket returned by server_socket.accept()
            :type server: Server
            :type sock: socket.socket
            """
        super().__init__()
        self.server = server
        self.socket = sock
        self.socket_addr = self.socket.getpeername()
        self.username = None
        self.closing = False
        self.sendQ = queue.Queue()

    def send(self, message):
        """
        wrap sendall method to provide additional features:
        pickle the message
        calculating the size of message
        and make sure the entire message is delivered.
        :type message: clientMessage.BaseClientMessage
        """
        try:
            logger.info("sending message to {}".format(self.username))
            pmessage = pickle.dumps(message)
        except Exception as e:
            logger.error("failed to pickle message")
            logger.exception(e)
            logger.debug(message)
            return
        try:
            header = "{}{}".format(len(pmessage), "\n").encode()
            self.socket.sendall(header + pmessage)
        except OSError as ose:
            logger.error("failed to send to socket: {}".format(
                self.socket_addr))
            logger.debug(ose)
            self.close()
        return

    def recv(self):
        """
        wrap recv method to provide additional features:
        unpickle the message
        and make sure receive one and only one message
        :rtype : clientMessage.BaseClientMessage
        """

        # ----START HELPER FUNCTION----
        def receive_len_header(sock):
            """
            return then length of the message
            return 0 if connection broken
            :rtype : int
            """
            buf = b''
            while not buf.endswith(b'\n'):
                temp_buf = sock.recv(1)
                if len(temp_buf) == 0:  # client disconnected
                    return 0
                buf += temp_buf
            length = int(buf)
            logger.debug("message length should be {}".format(length))
            return length

        def recv_real_message(sock, length):
            """
            receive data until size of length reached
            :rtype : clientMessage.BaseClientMessage
            :type socket.socket
            :type length: int
            """
            buf = b''
            while length != len(buf):
                temp_buf = sock.recv(length)
                if len(temp_buf) == 0:  # client disconnected
                    return b''
                buf += temp_buf
            return buf

        # ----END HELPER FUNCTION----

        try:
            message_len = receive_len_header(self.socket)
            new_pmsg = recv_real_message(self.socket, message_len)  # pickled
        except OSError as ose:  # connection dropped lead to exception
            return None
        if new_pmsg:  # received message successfully
            try:
                new_msg = pickle.loads(new_pmsg)
                logger.debug(
                    "received message from client {}: {}"
                    .format(self.socket_addr, new_msg))
            except Exception as e:
                logger.error("message cannot be unpickled, "
                             "message format might be wrong.")
                logger.debug(new_pmsg)
                logger.exception(e)
            else:  # successfully received new message
                return new_msg
        return None

    def close(self, an_exception=None):
        """
        gracefully close the socket and do the clean up
        :type an_exception: Exception
        """
        if self.closing:
            return
        self.closing = True
        logger.info("client disconnected: {}"
                    .format(self.socket_addr))
        if an_exception:
            logger.warning("exception occured during disconnection: {"
                           "}".format(an_exception.__class__.__name__))
            logger.debug(an_exception)
        self.socket.close()
        self.server.drop_connection(self.socket)


    def handle_chat_message(self, chat_message):
        # todo change receiver to only people in same game
        # consider making a server method instead of directly doing this
        receivers = self.server.all_connections
        for c in receivers:
            if c != self.socket:
                self.server.clients[c].sendQ.put(chat_message)
        logger.info("handle chat messaeg")


    def handle_login(self, login_message):
        """link client socket to client username"""
        self.username = login_message.username
        self.name = self.username  # change the thread name to username as well
        logger.info("client logged in as {}: {}"
                    .format(self.username, self.socket_addr))


    def handle_logout(self):  # todo write change to disk
        pass


    def handle_joinroom(self):
        pass


    def handle_createroom(self, login_data):
        # generate room
        # get random id for room
        # put room in variable rooms
        # return respond
        pass


    def handle_readyforgame(self, login_data):
        pass


    def handle_leaveroom(self, login_data):
        pass


    def handle_changemap(self, login_data):
        pass


    def handle_turndata(self, login_data):
        pass


    def handle_leavegame(self, login_data):
        pass


    def handle_message(self, msg):
        """
        verify and dispatch messages to different handler
        :type msg: clientMessage.BaseClientMessage
        """
        dispatcher = {
            # a mapping of clientMessage classes to handler functions
            clientMessage.ClientLogin.__name__: self.handle_login,
            clientMessage.JoinRoom.__name__: self.handle_joinroom,
            clientMessage.CreateRoom.__name__: self.handle_createroom,
            clientMessage.ReadyForGame.__name__: self.handle_readyforgame,
            clientMessage.LeaveRoom.__name__: self.handle_leaveroom,
            clientMessage.ChangeMap.__name__: self.handle_changemap,
            clientMessage.TurnData.__name__: self.handle_turndata,
            clientMessage.LeaveGame.__name__: self.handle_leavegame,
            clientMessage.ChatMessage.__name__: self.handle_chat_message,
        }
        try:
            # todo special treatment for login message
            # client must be logged in before sending other messages
            handler = dispatcher[msg.__class__.__name__]
            logger.info("handling {} message for client {}".format(
                msg.__class__.__name__, self.socket_addr))
            handler(msg)
        except KeyError as ke:
            logger.error(
                "message class does not exist {}".format(msg.__class__))
            logger.debug(msg)
        except Exception as e:
            logger.error("failed to handle message")
            logger.debug(msg)
            logger.exception(e)

    def do_send(self):
        """
        a sub thread execute this function to send message stored on sendQ
        """
        while not self.closing:
            # block on get from Q
            msg = self.sendQ.get()
            # check if client has a username
            if self.username:
                threading.currentThread().setName(self.username + "-s")
            # send the message
            self.send(msg)

    def run(self):
        """
        first spawn a thread to send
        then it block on recv and put new message on sendQ
        """
        # spawn the sending thread
        threading.Thread(target=self.do_send, daemon=True,
                         name=self.name + "-s").start()
        # main recv and handle loop
        while not self.closing:
            # block on recv
            new_msg = self.recv()
            if new_msg:
                # handle message could be slow depending on message size
                # we will not thread this for now
                self.handle_message(new_msg)


class Server():
    """the one and only Server itself"""

    def __init__(self, server_addr=("localhost", 8000),
                 max_connections_allowed=10, worker_threads=4):
        self.all_connections = []  # used to store clients
        self.clients = {}  # temporary store for instances of ClientSocket
        self.WORKER_THREADS = worker_threads

        try:
            server_socket = socket.socket()
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(server_addr)
            server_socket.listen(max_connections_allowed)
        except Exception as e:
            logger.error("server socket init failed")
            logger.exception(e)
            sys.exit()
        else:
            self.server_socket = server_socket
            logger.info("server started at {}".format(server_addr))

    def work(self):
        """used by worker thread"""
        try:
            while 1:
                client_sock, message = send_queue.get()
                client = self.clients.get(client_sock)
                if client:
                    client.handle_message(message)
        except KeyboardInterrupt as kie:
            pass
        except Exception as e:
            logger.error("Exception Occured in thread")
            logger.exception(e)
        finally:
            logger.info("thread terminating")


    def drop_connection(self, dropped_client_socket):
        """
        handler for connection drop
        will remove the connection from connection pool
        :type dropped_client_socket: socket.socket
        """
        self.clients.pop(dropped_client_socket)
        self.all_connections.remove(dropped_client_socket)


    def accept_new_connection(self):
        """
        block until a new client connected
        then add this client to pool and return
        """
        try:
            new_client_socket = self.server_socket.accept()[0]
        except OSError as ose:
            logger.error("failed to accept client connection")
        else:
            new_client = ClientSocket(new_client_socket, self)
            self.clients[new_client_socket] = new_client
            self.all_connections.append(new_client_socket)
            new_client.start()
            logger.info("new client connected {}"
                        .format(self.clients[new_client_socket].socket_addr))

    def summary(self):
        logger.info("Summary: clients still connected: {}"
                    .format(self.all_connections))

    def shut_down(self):
        try:
            while 1:
                _, client = self.clients.popitem()
                client.close()
        except KeyError as ke:
            pass
        self.server_socket.close()
        self.summary()


    def run(self):
        # launch thread pool on send queue
        send_queue.put(("hello", "world"))

        # main loop
        try:
            while True:
                self.accept_new_connection()
        # server shutdown
        except KeyboardInterrupt:
            logger.info("Server Shutting down from Keyboard")
            self.shut_down()
        except Exception as e:
            logger.critical("Unexpected Exception: Server Shutdown")
            logger.exception(e)
            self.shut_down()


if __name__ == "__main__":
    server = Server(SERVER_ADDR)
    server.run()

