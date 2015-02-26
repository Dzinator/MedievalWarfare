from functools import wraps
import queue
import socket
import logging
import sys
import pickle
import threading

try:
    from message import *
except:
    from .message import *



# initialize logging

logging.basicConfig(level="INFO",
                    format='%(asctime)s(%(threadName)-10s)[%(levelname)s]<%('
                           'lineno)s> '
                           '%(message)s')
logger = logging.getLogger(__name__)


# define global varaibles
SERVER_ADDR = ("", 8000)

# decorators---------------
def logged_in(f):
    @wraps(f)
    def _wrapper(self, *args, **kwargs):
        if self.username:
            f(self, *args, **kwargs)
        else:
            logger.error("Unable to handle last message because player not "
                         "logged in")

    return _wrapper


def in_room(f):
    @wraps(f)
    def _wrapper(self, *args, **kwargs):
        if self.room:
            f(self, *args, **kwargs)
        else:
            logger.error("Unable to handle last message because player not "
                         "in a room")

    return _wrapper


# todo add in_game and in_lobby decorators maybe
# decorators end---------------


class room():
    # todo consider using lock on this class
    def __init__(self):
        self.players = set()
        self.current_game = None

    def add_player(self, p):
        self.players.add(p)

    def remove_player(self, p):
        self.players.remove(p)

    def is_empty(self):
        return not self.players


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
        self.send_thread = None
        self.username = None
        # make a unique name for thread before username is available
        self.thread_name = "{}".format(str(hex(id(self)))[:5:-1])
        self.sendQ = queue.Queue()
        self.room = None
        self.ready_for_room = False


    def send(self, message):
        """
        wrap sendall method to provide additional features:
        pickle the message
        calculating the size of message
        and make sure the entire message is delivered.
        :type message: BaseClientMessage
        """
        try:
            # todo message class
            logger.info(
                "sending {} message".format(message.__class__.__name__))
            pmessage = pickle.dumps(message)
        except Exception as e:
            logger.error("failed to pickle message")
            logger.exception(e)
            logger.debug(message)
            return
        try:
            header = "{}{}".format(len(pmessage), "\n").encode()
            self.socket.sendall(header + pmessage)
        except Exception as e:
            logger.error("failed to send to socket: {}".format(
                self.socket_addr))
            raise
        return

    # ----START HELPER FUNCTION----
    def receive_len_header(self, sock):
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

    def recv_real_message(self, sock, length):
        """
        receive data until size of length reached
        :rtype : BaseClientMessage
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

    def recv(self):
        """
        wrap recv method to provide additional features:
        unpickle the message
        and make sure receive one and only one message
        :rtype : BaseClientMessage
        """

        try:
            message_len = self.receive_len_header(self.socket)
            new_pmsg = self.recv_real_message(self.socket,
                                              message_len)  # pickled
        except Exception:
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
        called by thread(the recv thread)
        gracefully close the socket and do the clean up
        :type an_exception: Exception
        """
        logger.info("client disconnected: {}".format(self.socket_addr))
        if an_exception:
            logger.warning("exception occured during disconnection: {"
                           "}".format(an_exception.__class__.__name__))
            logger.debug(an_exception)
        # leave any room that is in
        if self.room:
            self.handle_leaveroom(None)
        # set the player_stat to logged out
        self.server.player_stats[self.username]["status"] = False
        self.socket.close()
        self.server.drop_connection(self.socket)

    def handle_login(self, login_message):
        """link client socket to client username"""
        self.username = login_message.username
        self.thread_name = self.username  # thread_name to username
        self.setName(self.thread_name)
        self.send_thread.setName(self.thread_name + "-s")
        try:
            if self.server.player_stats[self.username]["status"]:
                # Someone else already logged in using this name
                # todo send a warning message to client
                logger.info(
                    "Re-login attempt detected: {}".format(self.username))
            else:
                self.server.player_stats[self.username]["status"] = True
                logger.info("welcome back! {}".format(self.username))
        except KeyError as ke:
            # create this name
            self.server.player_stats[self.username] = \
                {"wins": 0, "status": True, "games": 0}
            logger.info("new profile created: {}".format(self.username))
        logger.info("client logged in as {}: {}"
                    .format(self.username, self.socket_addr))

    @logged_in
    def handle_getroomlist(self, dat):
        self.sendQ.put(SendRoomList([id(r) for r in self.server.rooms]))

    @logged_in
    @in_room
    def handle_chat_message(self, chat_message):
        if self.room:
            for p in self.room.players:
                if p is not self:
                    p.sendQ.put(chat_message)

    @logged_in
    def handle_joinroom(self, dat):
        try:
            self.room = self.server.rooms[dat.roomId]
            self.room.add_player(self)
        except Exception:
            logger.info("trying to join a room that does not exist: {}".format(
                dat.roomId))
            return # todo probably want to send a failure msg
        else:
            # todo how do we identify a game
            # todo what need to send about a player
            self.sendQ.put(sendRoom(id(self.room), self.room.current_game,
                                    self.room.players))



        # room_to_join = next(iter(self.server.rooms.values()))
        # self.room = room_to_join
        # if room_to_join:
        #     self.room.add_player(self)


    @logged_in
    def handle_createroom(self, login_data):
        # generate room
        self.room = room()
        self.room.add_player(self)
        # put the room to server
        self.server.rooms[id(self.room)] = self.room
        self.sendQ.put(sendRoom(id(self.room), None, None))

    @logged_in
    @in_room
    def handle_readyforgame(self, dat):
        self.ready_for_room = True
        for p in self.room.players:
            if not p.ready_for_room:
                return
        # everyone's ready, start game



    @logged_in
    @in_room
    def handle_leaveroom(self, msg):
        # todo if we need host, change host if self is host
        # todo maybe we don't need host, everybody is host
        self.room.remove_player(self)
        if self.room.is_empty():
            self.server.rooms.pop(id(self.room))
        self.room = None
        self.ready_for_room = False


    @logged_in
    @in_room
    def handle_changemap(self, login_data):
        pass


    @logged_in
    @in_room
    def handle_turndata(self, turndata):
        if self.room:
            for p in self.room.players:
                if p is not self:
                    p.sendQ.put(turndata)

    @logged_in
    @in_room
    def handle_end_game(self, dat):
        """send end game msg to all player in room
        call server method updatePlayerStats
        :param: dat: win/lose"""
        # do_send(all_other_player_in_room, EndGameMsg(bool))
        # self.server.updatePlayerStats()
        # everybody go back to the room page
        pass


    @logged_in
    @in_room
    def handle_leavegame(self, login_data):
        pass


    def handle_message(self, msg):
        """
        verify and dispatch messages to different handler
        :type msg: BaseClientMessage
        """
        dispatcher = {
            # a mapping of clientMessage classes to handler functions
            ClientLogin.__name__: self.handle_login,
            GetRoomList.__name__: self.handle_getroomlist,
            JoinRoom.__name__: self.handle_joinroom,
            CreateRoom.__name__: self.handle_createroom,
            ReadyForGame.__name__: self.handle_readyforgame,
            LeaveRoom.__name__: self.handle_leaveroom,
            ChangeMap.__name__: self.handle_changemap,
            TurnData.__name__: self.handle_turndata,
            LeaveGame.__name__: self.handle_leavegame,
            ChatMessage.__name__: self.handle_chat_message,
        }
        try:
            # todo special treatment for login message
            # client must be logged in before sending other messages
            handler = dispatcher[msg.__class__.__name__]
            logger.info("handling {} message".format(msg.__class__.__name__))
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
        while 1:
            # block on get from Q
            msg = self.sendQ.get()
            # check if client has a username
            if self.username:
                threading.currentThread().setName(self.username + "-s")
            # send the message
            try:
                self.send(msg)
            except Exception:
                break

    def run(self):
        """
        first spawn a thread to send
        then it block on recv and put new message on sendQ
        """
        self.setName(self.thread_name)
        logger.info("new client connected: {}".format(self.socket_addr))
        # spawn the sending thread
        self.send_thread = threading.Thread(target=self.do_send,
                                            name=(self.thread_name + "-s"))
        self.send_thread.daemon = True
        self.send_thread.start()

        # main recv and handle loop
        while 1:
            # block on recv
            new_msg = self.recv()
            if new_msg:
                self.handle_message(new_msg)
                # check if client has a username
                if self.username:
                    threading.currentThread().setName(self.username + "-s")
            else:
                # assume the connection is broken
                self.close()
                break


class Server():
    """the one and only Server itself"""

    def __init__(self, server_addr=("localhost", 8000),
                 max_connections_allowed=10, worker_threads=4):
        self.data_file = "datafile.dat"
        self.clients = {}  # temporary store for instances of ClientSocket
        self.WORKER_THREADS = worker_threads
        self.rooms = {}
        self.player_stats = None  # initialized in method start

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
            new_client.start()

    def summary(self):
        logger.info("Summary: clients still connected: {}"
                    .format(self.clients))
        logger.info("Summary: rooms not removed: {}".format(self.rooms))

    def shut_down(self):
        try:
            while 1:
                _, client = self.clients.popitem()
                client.close()
        except KeyError as ke:
            pass
        self.server_socket.close()
        logger.info("server socket is closed")
        with open(self.data_file, "wb") as f:
            pickle.dump(self.player_stats, f)
        logger.info("player stats saved")
        self.summary()


    def start(self):
        with open(self.data_file, "rb") as f:
            self.player_stats = pickle.load(f)
        if not self.player_stats:
            self.player_stats = {}

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
    server.start()

