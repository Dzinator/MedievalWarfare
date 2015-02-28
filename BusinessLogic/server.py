from functools import wraps
import queue
import socket
import logging
import sys
import pickle
import threading
from random import randint

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
SERVER_ADDR = ("localhost", 8000)

# decorators---------------
def logged_in(f):
    @wraps(f)
    def _wrapper(self, msg):
        if self.username:
            f(self, msg)
        else:
            logger.error("Unable to handle {} message, player needs to be "
                         "logged in".format(msg.__class__.__name__))
    return _wrapper


def in_room(f):
    @logged_in
    @wraps(f)
    def _wrapper(self, msg):
        if self.room:
            f(self, msg)
        else:
            logger.error("Unable to handle {} message, player needs to be "
                         "in a room".format(msg.__class__.__name__))
    return _wrapper
# decorators end---------------


class Room():
    def __init__(self):
        self.players = set()
        self.current_game = ""
        self.Id = id(Room)

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
            and an refrence of the server
            :type server: Server
            :type sock: socket.socket
            """
        super().__init__()
        self.server = server
        self.socket = sock
        self.socket_addr = self.socket.getpeername()
        self.send_thread = None
        # make a temporary unique name before username is available
        self.username = None
        self.thread_name = "{}".format(str(hex(id(self)))[:5:-1])
        self.sendQ = queue.Queue()
        self.room = None
        self.ready_for_room = False
        self.close_lock = threading.Lock()
        self.is_closed = False

    # ----START HELPER FUNCTION----
    def get_player_list(self):
        """used to sendRoom"""
        player_l = []  # player_l = {}
        for p in self.room.players:
            username = p.username
            ready = p.ready_for_room
            wins = self.server.player_stats[username]["wins"]
            games = self.server.player_stats[username]["games"]
            player_l.append(
                {"username": username, "ready": ready, "wins": wins,
                 "games": games})
        return player_l

    def make_sendRoom_msg(self):
        """helper to create a sendRoom msg
        :return: sendRoom"""
        roomId = self.room.Id  # get room id
        current_game = self.room.current_game  # get current game
        # make player_list
        player_l = self.get_player_list()
        return sendRoom(roomId, current_game, player_l)

    def set_thread_name(self):
        """set thread name for nicer logging"""
        if self.username:
            self.thread_name = self.username
        self.setName(self.thread_name)
        self.send_thread.setName("{}-s".format(self.thread_name))

    def leave_room(self):
        # todo add host support
        self.room.remove_player(self)
        # this is not thread safe
        if self.room.is_empty():
            self.server.rooms.pop(self.room.Id)
        self.broadcast_msg(self.make_sendRoom_msg(), exclude_self=True)
        self.room = None
        self.ready_for_room = False

    def update_player_stats(self, wins=None, games=None, status=None):
        player_stats = self.server.player_stats.get(self.username)
        if player_stats:
            if wins is not None:
                player_stats["wins"] = wins
            if games is not None:
                player_stats["games"] = games
            if status is not None:
                player_stats["status"] = status

    def broadcast_msg(self, msg, exclude_self=False):
        """send to all players in the same room or game"""
        if exclude_self:
            players = (p for p in self.room.players if p is not self)
        else:
            players = self.room.players
        for p in players:
            p.sendQ.put(msg)


    # ----END HELPER FUNCTION----

    def send(self, message):
        """
        wrap sendall method to provide additional features:
        pickle the message
        calculating the size of message
        and make sure the entire message is delivered.
        :type message: BaseClientMessage
        """
        try:
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
            # logger.error("failed to send to socket: {}".format(
            # self.socket_addr))
            self.close()
            raise
        return

    def recv(self):
        """
        wrap recv method to provide additional features:
        unpickle the message
        and make sure receive one and only one message
        :rtype : BaseClientMessage
        """

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

        try:
            message_len = receive_len_header(self.socket)
            if not message_len:
                return None
            new_pmsg = recv_real_message(self.socket, message_len)  # pickled
            if not new_pmsg:
                return None
        except Exception: # connection broken
            return None
        try:
            new_msg = pickle.loads(new_pmsg)
        except Exception as e:
            logger.error("message cannot be unpickled, "
                         "message format might be wrong.")
            return None
        return new_msg

    def close(self, an_exception=None):
        """
        gracefully close the socket and do the clean up
        :type an_exception: Exception
        """
        with self.close_lock:
            if self.is_closed:
                return
            logger.info("client disconnected: {}".format(self.socket_addr))
            if an_exception:
                logger.warning("exception occured during disconnection: {"
                               "}".format(an_exception.__class__.__name__))
                logger.debug(an_exception)
            # leave any room that client is in
            if self.room:
                self.leave_room()
            # set the player_stat to logged out
            self.update_player_stats(status=False)
            self.socket.close()
            self.server.drop_connection(self.socket)
            self.is_closed = True

    def handle_login(self, login_message):
        """link client socket to client username"""
        self.username = login_message.username
        self.set_thread_name()
        # check if this username exists
        if self.server.player_stats.get(self.username):
            # check if this username is already logged in
            if self.server.player_stats[self.username]["status"]:
                logger.warning(
                    "Re-login attempt detected: {}".format(self.username))
                self.sendQ.put(LoginAck(False))
                return
            else:
                self.update_player_stats(status=True)
                logger.info("welcome back! {}".format(self.username))
        else:
            self.server.make_new_player(self.username)  # create this name
            logger.info("new profile created: {}".format(self.username))
        logger.info("client logged in as {}: {}"
                    .format(self.username, self.socket_addr))
        self.sendQ.put(LoginAck(True))
        self.sendQ.put(SendRoomList(self.server.get_all_room_ids()))

    @logged_in
    def handle_getroomlist(self, dat):
        self.sendQ.put(SendRoomList(self.server.get_all_room_ids()))

    @in_room
    def handle_chat_message(self, chat_message):
        self.broadcast_msg(chat_message, exclude_self=True)

    @logged_in
    def handle_joinroom(self, dat):
        try:
            self.room = self.server.rooms[dat.roomId]
            self.room.add_player(self)
        except Exception:
            logger.info("trying to join a room that does not exist: {}".format(
                dat.roomId))
            return  # todo probably want to send a failure msg
        else:
            self.broadcast_msg(self.make_sendRoom_msg())

    @logged_in
    def handle_createroom(self, dat):
        # generate room
        self.room = Room()
        self.room.add_player(self)
        # put the room to server
        self.server.rooms[self.room.Id] = self.room
        self.broadcast_msg(self.make_sendRoom_msg())

    @in_room
    def handle_readyforgame(self, dat):
        self.ready_for_room = True
        self.broadcast_msg(self.make_sendRoom_msg())
        # check if everyone is ready
        if all(p.ready_for_room for p in self.room.players):
            seed = randint(0, 10000000)
            temp = self.get_player_list()
            for i, p in enumerate(self.room.players):
                p.sendQ.put(startGame(seed, temp, i + 1))


    @in_room
    def handle_leaveroom(self, msg):
        self.leave_room()
        self.sendQ.put(SendRoomList(self.server.get_all_room_ids()))


    @in_room
    def handle_changemap(self, login_data):
        pass


    @in_room
    def handle_turndata(self, turndata):
        if self.room:
            self.broadcast_msg(turndata, exclude_self=True)

    @in_room
    def handle_end_game(self, dat):
        """send end game msg to all player in room
        call server method updatePlayerStats
        :param: dat: win/lose"""
        # do_send(all_other_player_in_room, EndGameMsg(bool))
        # self.server.updatePlayerStats()
        # everybody go back to the room page
        pass


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
            handler = dispatcher[msg.__class__.__name__]
        except KeyError as ke:
            logger.error(
                "message class does not exist {}".format(msg.__class__))
        else:  # found handler for the message
            try:
                logger.info("handling {} message".format(msg.__class__.__name__))
                handler(msg)
            except Exception as e:
                logger.error("failed to handle message")
                logger.exception(e)

    def do_send(self):
        """
        a sub thread execute this function to send message stored in sendQ
        """
        while 1:
            # send the message
            try:
                msg = self.sendQ.get()  # block on get from sendQ
                self.send(msg)
            except Exception:
                self.close()

    def run(self):
        """
        first spawn a thread to send
        then it block on recv and put new message on sendQ
        """
        # spawn the sending thread
        self.send_thread = threading.Thread(target=self.do_send)
        self.send_thread.daemon = True
        self.set_thread_name()
        self.send_thread.start()
        logger.info("new client connected: {}".format(self.socket_addr))

        # main recv and handle loop
        while 1:
            # block on recv
            new_msg = self.recv()
            if new_msg:
                self.handle_message(new_msg)
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
        self.player_stats = {}  # map username to their status

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

    def get_all_room_ids(self):
        """return a list of all room ids"""
        return list(self.rooms.keys())

    def make_new_player(self, username):
        """create a new player profile and add to player_stats"""
        new_player = {"wins": 0, "games": 0, "status": False}
        if not self.player_stats.get(username):
            self.player_stats[username] = new_player

    def drop_connection(self, dropped_client_socket):
        """
        handler for connection drop
        will remove the connection from connection pool
        :type dropped_client_socket: socket.socket
        """
        if self.clients.get(dropped_client_socket):
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
            new_client.setDaemon(True)
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
        if self.player_stats:
            for ps in self.player_stats.values():
                ps["status"] = False
            with open(self.data_file, "wb") as f:
                pickle.dump(self.player_stats, f)
        logger.info("player stats saved")
        self.summary()

    def start(self):
        # initilize player_stats
        import os.path
        if os.path.exists(self.data_file):
            with open(self.data_file, "rb") as f:
                try:
                    self.player_stats = pickle.load(f)
                except Exception as e:
                    pass
        else:
            open(self.data_file, 'wb+').close()
        for p in self.player_stats.values():
            p["status"] = False

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

