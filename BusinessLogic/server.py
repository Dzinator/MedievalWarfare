from functools import wraps
import queue
import socket
import logging
import sys
import pickle
import threading
import os.path
from random import randint

try:
    from message import *
except:
    from .message import *



# initialize logging

logging.basicConfig(level="DEBUG",
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
        return f(self, msg) if self.username else logger.error(
            "Unable to handle {} message, player needs to be "
            "logged in".format(msg.__class__.__name__))

    return _wrapper


def in_room(f):
    @logged_in
    @wraps(f)
    def _wrapper(self, msg):
        return f(self, msg) if self.room else logger.error(
            "Unable to handle {} message, player needs to be "
            "in a room".format(msg.__class__.__name__))

    return _wrapper


def synchronized(loc=None):
    from threading import Lock

    _loc = loc or Lock()

    def _dec(f):
        @wraps(f)
        def _wrapper(*args, **kwargs):
            with _loc:
                return f(*args, **kwargs)

        return _wrapper

    return _dec
# decorators end---------------


class Room():
    def __init__(self):
        self._players = set()
        self.game_id = ""
        self.game = None
        self.ID = id(Room)
        self._lock = threading.RLock()
        self._is_closed = False

    @property
    def players(self):
        with self._lock:
            return tuple(self._players)

    def add_player(self, p):
        with self._lock:
            if not self._is_closed:
                self._players.add(p)
            else:
                raise Exception("Cannot join a closed room {}".format(self.ID))

    def remove_player(self, p):
        with self._lock:
            self._players.remove(p)

    @property
    def is_empty(self):
        with self._lock:
            return not self._players

    def change_map(self, game_id=None, saved_game=None):
        """pass in either a saved_game or a map_id
        if saved_game is passed, game_id is calculated"""
        with self._lock:
            if saved_game:
                self.game = saved_game
                self.game_id = id(self.game)
            elif game_id:
                # if game_id in default_games:
                self.game_id = game_id

    def close(self):
        """set _is_closed to True"""
        with self._lock:
            if self._is_closed:
                # someone else already closed it
                return False
            self._is_closed = True
            return True


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
        self.username = None
        # make a temporary unique name before username is available
        self.thread_name = str(format(str(hex(id(self)))[:5:-1]))
        self.send_thread = None
        self.sendQ = queue.Queue()
        self.room = None
        """:type : Room"""  # type hint for self.room
        self.ready_for_room = False
        self.close_lock = threading.Lock()
        self.is_closed = False

    # ----START HELPER FUNCTION----
    @property
    def player_list(self):
        """used to sendRoom"""
        player_l = []  # player_l = {}
        for p in self.room.players:
            username, ready = p.username, p.ready_for_room
            p_stats = self.server.player_stats[p.username]
            wins, games = p_stats["wins"], p_stats["games"]
            player_l.append({
                "username": username,
                "ready": ready,
                "wins": wins,
                "games": games})
        return player_l

    @property
    def _sendroom_msg(self):
        """helper to create a sendRoom msg
        :return: sendRoom"""
        return sendRoom(self.room.ID,
                        self.room.game_id,
                        self.player_list)

    def update_thread_name(self):
        """set thread name for nicer logging"""
        if self.username:
            self.thread_name = self.username
        self.setName(self.thread_name)
        self.send_thread.setName("{}-s".format(self.thread_name))

    def _leave_room(self):
        """leave room and push new room status to everyone"""
        # todo add host support
        self.room.remove_player(self)
        if self.room.is_empty:
            if self.room.close():
                self.server.rooms.pop(self.room.ID)
        self.broadcast_msg(self._sendroom_msg, exclude_self=True)
        self.room = None
        self.ready_for_room = False

    def update_player_stats(self, new_win=False, new_game=False, status=None):
        """
        increment wins and games, update player status
        :type param new_win: bool
        :type param new_game: bool
        :type param status: bool
        :return:
        """
        player_stats = self.server.player_stats.get(self.username)
        if player_stats:
            if new_win:
                player_stats["wins"] += 1
            if new_game:
                player_stats["games"] += 1
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

    def _send(self, message):
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
            return
        try:
            header = "{}{}".format(len(pmessage), "\n").encode()
            self.socket.sendall(header + pmessage)
        except Exception as e:
            self.close()
            # Exception is expected as connection may be broken
        return

    def _recv(self):
        """
        wrap recv method to provide additional features:
        unpickle the message
        and make sure receive one and only one message
        :rtype : BaseClientMessage
        """

        def _receive_len_header(sock):
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
            return length

        def _recv_real_message(sock, length):
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
            message_len = _receive_len_header(self.socket)
            if not message_len:
                return None
            new_pmsg = _recv_real_message(self.socket, message_len)  # pickled
            if not new_pmsg:
                return None
        except Exception:  # connection broken
            return None
        try:
            new_msg = pickle.loads(new_pmsg)
        except Exception as e:
            logger.error("message cannot be unpickled, "
                         "message format might be wrong.")
            return None
        return new_msg

    def close(self):
        """
        gracefully close the socket and do the clean up
        """
        with self.close_lock:
            if self.is_closed:
                return
            logger.info("client disconnected: {}".format(self.socket_addr))
            # leave any room that client is in
            if self.room:
                self._leave_room()
            # set the player_stat to logged out
            self.update_player_stats(status=False)
            self.socket.close()
            self.server.drop_connection(self.socket)
            self.is_closed = True

    def handle_login(self, login_message):
        """link client socket to client username"""
        self.username = login_message.username
        self.update_thread_name()
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
        self.sendQ.put(SendRoomList(self.server.all_room_ids))

    @logged_in
    def handle_getroomlist(self, dat):
        self.sendQ.put(SendRoomList(self.server.all_room_ids))

    @in_room
    def handle_chat_message(self, chat_message):
        self.broadcast_msg(chat_message, exclude_self=True)

    @logged_in
    def handle_joinroom(self, room_data):
        """joining a existed room by id"""
        try:
            self.room = self.server.rooms[room_data.roomId]
            self.room.add_player(self)
        except Exception:
            logger.info("trying to join a room that does not exist: {}"
                        .format(room_data.roomId))
            # send a new room list
            self.sendQ.put(SendRoomList(self.server.all_room_ids))
        else:
            self.broadcast_msg(self._sendroom_msg)

    @logged_in
    def handle_createroom(self, dat):
        """create a room for client"""
        # generate room
        self.room = Room()
        self.room.add_player(self)
        # put the room to server
        self.server.rooms[self.room.ID] = self.room
        self.broadcast_msg(self._sendroom_msg)

    @in_room
    def handle_readyforgame(self, dat):
        """set client to ready and push the room status to everyone
        will start game if everyone is ready"""
        self.ready_for_room = True
        self.broadcast_msg(self._sendroom_msg)
        # check if everyone is ready
        if all(p.ready_for_room for p in self.room.players):
            seed = randint(0, 10000000)
            temp = self.player_list
            for i, p in enumerate(self.room.players):
                p.ready_for_room = False
                p.sendQ.put(startGame(seed, temp, i + 1))

    @in_room
    def handle_leaveroom(self, dat):
        """call _leave_room and send a room list to client"""
        self._leave_room()
        self.sendQ.put(SendRoomList(self.server.all_room_ids))

    @in_room
    def handle_changemap(self, game_dat):
        """change a map, by id(default maps) or by object(saved game)"""
        # todo make this work, consider using a pull model
        if game_dat.game_id:
            self.room.change_map(game_id=game_dat.game_id)
            self.broadcast_msg(self._sendroom_msg)
        elif game_dat.saved_game:
            self.room.change_map(saved_game=game_dat.saved_game)
            # todo client code needs to be unready to change map to avoid race
            # cond
            if self.ready_for_room:
                self.ready_for_room = False
                self.broadcast_msg(self._sendroom_msg)
            self.broadcast_msg(NewMap(game_dat.saved_game), exclude_self=True)

    @in_room
    def handle_turndata(self, turndata):
        self.broadcast_msg(turndata, exclude_self=True)

    @in_room
    def handle_wingame(self, dat):
        """update player_stats
        send GameEnd msg to everyone in room
        send SendRoomList msg to everyone in room
        """
        # todo make this work
        for p in self.room.players:
            if p is self:
                p.update_player_stats(new_game=True, new_win=True)
            else:
                p.update_player_stats(new_game=True)
        self.broadcast_msg(GameEnd())
        self.broadcast_msg(SendRoomList(self.server.all_room_ids))

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
            WinGame.__name__: self.handle_wingame,
            LeaveGame.__name__: self.handle_leavegame,
            ChatMessage.__name__: self.handle_chat_message,
        }
        try:
            handler = dispatcher[msg.__class__.__name__]
        except KeyError as ke:
            logger.error(
                "message class does not exist {}".format(msg.__class__))
        else:  # found handler for the message
            logger.info("handling {} message".format(msg.__class__.__name__))
            try:
                handler(msg)
            except Exception as e:
                logger.error("failed to handle message")
                logger.exception(e)

    def do_send(self):
        """
        a sub send-thread execute this function to send message stored in sendQ
        """
        try:
            while 1:
                # send the message
                msg = self.sendQ.get()  # block on get from sendQ
                self._send(msg)
        # we don't care about the exception because it is expected when
        # connection broke
        finally:
            self.close()

    def run(self):
        """
        first spawn a thread to send
        then it block on recv and put new message on sendQ
        """
        # spawn the sending thread
        self.send_thread = threading.Thread(target=self.do_send)
        self.send_thread.daemon = True
        # update sender threads name first before starting send_thread
        self.update_thread_name()
        self.send_thread.start()
        logger.info("new client connected: {}".format(self.socket_addr))

        # main recv and handle loop
        try:
            while 1:
                # block on recv
                new_msg = self._recv()
                if new_msg:
                    self.handle_message(new_msg)
                else:
                    # assume the connection is broken
                    self.close()
                    break
        finally:
            self.close()
            # raise


class Server():
    """the one and only Server itself"""

    def __init__(self, max_connections_allowed=10):
        self.server_addr = SERVER_ADDR or ("localhost", 8000)
        self.data_file = "datafile.dat"
        # all the clients: {socket: ClientSocket}
        self.clients = {}
        self.clients_lock = threading.RLock()
        # all the rooms: {int: Room}
        self.rooms = {}
        # all the player stats: {str: dict}
        self.player_stats = {}

        try:
            server_socket = socket.socket()
            # enable reuse port when restart server
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(self.server_addr)
            server_socket.listen(max_connections_allowed)
        except Exception as e:
            logger.error("server socket init failed")
            logger.exception(e)
            sys.exit()
        else:
            self.server_socket = server_socket
            logger.info("server started at {}".format(self.server_addr))

    @property
    def all_room_ids(self):
        """return a list of all room ids"""
        return list(self.rooms.keys())

    def make_new_player(self, username):
        """create a new player profile and add to player_stats"""
        if not self.player_stats.get(username):
            new_player_stats = {"wins": 0, "games": 0, "status": False}
            self.player_stats[username] = new_player_stats

    def drop_connection(self, dropped_client_socket):
        """
        handler for connection drop
        will remove the connection from connection pool
        :type dropped_client_socket: socket.socket
        """
        # dropped_client_socket may already be dropped, if so, skip
        if self.clients.get(dropped_client_socket):
            with self.clients_lock:
                if self.clients.get(dropped_client_socket):
                    self.clients.pop(dropped_client_socket)

    def summary(self):
        logger.debug("Summary: clients still connected: {}"
                     .format(self.clients or None))
        logger.debug("Summary: rooms not removed: {}".format(self.rooms or
                                                             None))

    def shut_down(self):
        with self.clients_lock:
            client_list = tuple(self.clients.values())
        for c in client_list:
            c.close()
        self.server_socket.close()
        logger.info("server socket is closed")
        if self.player_stats:
            # just to make sure all player status if off
            for ps in self.player_stats.values():
                ps["status"] = False
            with open(self.data_file, "wb") as f:
                pickle.dump(self.player_stats, f)
        logger.info("player stats saved")
        self.summary()

    def start(self):
        # initilize player_stats
        if os.path.exists(self.data_file):
            with open(self.data_file, "rb") as f:
                # put a try except because data in file might be corrupted
                try:
                    self.player_stats = pickle.load(f)
                except Exception:
                    pass
        else:
            open(self.data_file, 'wb').close()
        # initialize all player status to offline
        for p in self.player_stats.values():
            p["status"] = False

        # main loop
        try:
            # accept new connection
            while True:
                try:
                    # block until a new client connect
                    new_client_socket = self.server_socket.accept()[0]
                except OSError:
                    # this is expected: some connection may break during accept
                    logger.error("failed to accept client connection")
                else:
                    new_client = ClientSocket(new_client_socket, self)
                    new_client.setDaemon(True)
                    with self.clients_lock:
                        self.clients[new_client_socket] = new_client
                    new_client.start()

        # server shutdown
        except KeyboardInterrupt:
            logger.info("Server Shutting down from Keyboard")
            self.shut_down()
        except Exception as e:
            logger.critical("Unexpected Exception: Server Shutdown")
            logger.exception(e)
            self.shut_down()


if __name__ == "__main__":
    server = Server()
    server.start()  # listening on address and port specified in 'SERVER_ADDR'

