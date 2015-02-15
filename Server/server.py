# todo the event driven I/O cannot respond fast enough because of the
# sequential code server execute right after. Multiple client could send
# message at the same time and sequence of message could got mixed up
# use process pool and use CV on individual socket to synchronize send and recv
# or a simpler solution is to fire up a thread every time a request comes in

# todo add threading support to ClientSocket


# Assumption: the problem with select is that after it returns, during that
# time,
# buffer could accumulate more than one msg or connection on a single socket
# there's no way to tell how many connection request and messages received
# solution: it turns out select is monitoring the socket buffer
# so when one message is handled and returned to select, it will read
# immediately the next message and send it to handler
import socket
import select
import logging
import sys
import pickle

import Server.gameMessage.clientMessage as clientMessage


# initialize logging

logging.basicConfig(level="INFO",
                    format='%(asctime)s(%(threadName)-10s)[%(levelname)s] '
                           '%(message)s')
logger = logging.getLogger(__name__)


# define global varaibles
SERVER_ADDR = ("localhost", 8000)


class ClientSocket():
    """a wrapper on the socket from clients"""

    def __init__(self, sock, server):
        """
        initilized with a raw socket returned by server_socket.accept()
        :type server: Server
        :type sock: socket.socket
        """
        self.server = server
        self.socket = sock
        self.socket_addr = self.socket.getpeername()

    def send(self, message):
        """
        wrap sendall method to provide additional features:
        pickle the message
        calculating the size of message
        and make sure the entire message is delivered.
        :type message: clientMessage.BaseClientMessage
        """
        # todo use a synchronization machanism to restrict access to one thread
        try:
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
                self.socket.getpeername()))
            logger.exception(ose)
            logger.debug(message)
        return

    def recv(self):
        """
        wrap recv method to provide additional features:
        unpickle the message
        and make sure receive one and only one message
        :rtype : None
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
            self.close(ose)
            return None
        if new_pmsg:  # received message successfully
            try:
                new_msg = pickle.loads(new_pmsg)
                logger.debug(
                    "received message from client {}: {}"
                    .format(self.socket.getpeername(), new_msg))
            except Exception as e:
                logger.error("message cannot be unpickled, "
                             "message format might be wrong.")
                logger.debug(new_pmsg)
                logger.exception(e)
            else:  # successfully received new message
                # todo move handle out of recv method
                self.handle_message(new_msg)
                return new_msg
        else:  # connection dropped
            self.close()  # handle client connection dropped
        return None

    def close(self, an_exception=None):
        """
        gracefully close the socket and do the clean up
        :type an_exception: Exception
        """
        logger.info("client disconnected: {}"
                    .format(self.socket_addr))
        if an_exception:
            # todo temprory ignore exception because constant
            # ConnectionResetError during stress test caused
            # by server's slow response time
            logger.warning("exception occured during disconnection: {"
                           "}".format(an_exception.__class__.__name__))
            # logger.exception(an_exception)
        self.socket.close()
        self.server.drop_connection(self.socket)


    def handle_chat_message(self, chat_message):
        # todo change receiver to only people in same game
        # consider making a server method instead of directly doing this
        receivers = self.server.all_connections
        for c in receivers:
            if c != self.socket:
                self.server.clients[c].send(chat_message)
        logger.info("handle chat messaeg")


    def handle_login(self, login_message):
        """link client socket to client username"""
        logger.info("client logged in as {}: {}"
                    .format(login_message.username, self.socket.getpeername()))


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
            handler = dispatcher[msg.__class__.__name__]
            logger.info("handling {} message for client {}".format(
                msg.__class__.__name__, self.socket.getpeername()))
            handler(msg)
        except KeyError as ke:
            logger.error(
                "message class does not exist {}".format(msg.__class__))
            logger.debug(msg)
        except Exception as e:
            logger.error("failed to handle message")
            logger.debug(msg)
            logger.exception(e)


class Server():
    """the one and only Server itself"""

    def __init__(self, server_addr=("localhost", 8000),
                 max_connections_allowed=10):
        self.all_connections = []  # used to store clients
        self.clients = {}  # temporary store for instances of ClientSocket

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

    def drop_connection(self, dropped_client_socket):
        """
        handler for connection drop
        will remove the connection from connection pool
        :type dropped_client_socket: socket.socket
        """
        self.clients.pop(dropped_client_socket)
        self.all_connections.remove(dropped_client_socket)


    def accept_new_connection(self):
        try:
            new_client_socket = self.server_socket.accept()[0]
        except OSError as ose:
            logger.error("failed to accept client connection")
        else:
            self.clients[new_client_socket] = ClientSocket(new_client_socket,
                                                           self)
            self.all_connections.append(new_client_socket)
            logger.info("new client connected {}"
                        .format(new_client_socket.getpeername()))

    def summary(self):
        logger.info("Summary: clients still connected: {}".format(
            [c for c in self.all_connections]))

    def shut_down(self):
        [c.close() for c in self.clients]
        self.server_socket.close()
        self.summary()


    def run(self):
        # main loop
        try:
            while True:
                read_sockets, _, _ = select.select(
                    self.all_connections + [self.server_socket], [], [])
                for incoming_socket in read_sockets:
                    # new connection
                    if incoming_socket == self.server_socket:
                        self.accept_new_connection()
                    # client message
                    else:
                        client_sender_socket = incoming_socket
                        self.clients[client_sender_socket].recv()

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

