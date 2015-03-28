from functools import wraps
import queue
import socket
import logging
import sys
import pickle
from pickle import UnpicklingError, PicklingError
import threading
import os.path
from random import randint
import time

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
SERVER_ADDR = ("", 8000)

# region decorator
def logged_in(f):
    @wraps(f)
    def _wrapper(self, msg):
        return f(self, msg) if self.is_logged_in else logger.error(
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


def host_only(f):
    @in_room
    @wraps(f)
    def _wrapper(self, msg):
        return f(self, msg) if self.room.host == self else \
            logger.error("Unable to handle {} message, player must be room "
                         "host".format(msg.__class__.__name__))

    return _wrapper


def in_game(f):
    @in_room
    @wraps(f)
    def _wrapper(self, msg):
        return f(self, msg) if self.is_in_game else \
            logger.error("Unable to handle {} message, player must be in game."
                         .format(msg.__class__.__name__))

    return _wrapper
# endregion


class Room():
    def __init__(self, host):
        """
        :type host: ClientSocket
        """
        self._players = set()
        self.host = host
        self.add_player(host)
        self.game_id = ""
        self.saved_game = None
        self.ID = id(self)
        self._room_lock = threading.RLock()
        self.is_closed = False
        self.game_started = False

    def get_all_players(self):
        with self._room_lock:
            return list(self._players)

    def add_player(self, p):
        """
        :type p: ClientSocket
        """
        with self._room_lock:
            if not self.is_closed:
                self._players.add(p)
            else:
                raise Exception("Cannot join a closed room {}".format(self.ID))

    def remove_player(self, p):
        """
        :type p: ClientSocket
        """
        with self._room_lock:
            self._players.remove(p)
            if self.is_empty:
                return
            else:
                # swap host
                self.host = self._players.pop()
                self._players.add(self.host)

    @property
    def is_empty(self):
        with self._room_lock:
            return not self._players

    def change_map(self, game_id, saved_game):
        """pass in a saved_game"""
        with self._room_lock:
            self.game_id = game_id
            self.saved_game = saved_game

    def close(self):
        """set _is_closed to True"""
        with self._room_lock:
            if self.is_closed:
                # someone else already closed it
                return False
            self.is_closed = True
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
        ":type: str"
        # make a temporary unique name before username is available
        self.thread_name = str(format(str(hex(id(self)))[:5:-1]))
        self.send_thread = None
        self.recv_thread = None
        self.sendQ = queue.Queue()
        self.room = None
        """:type : Room"""  # type hint for self.room
        self.ready_for_room = False
        self._close_lock = threading.Lock()
        self.is_closed = False
        self.connection_broken = False
        self.is_taken_over = False

    # region property
    @property
    def _player_list(self):
        """used to sendRoom"""
        player_l = []  # player_l = {}
        for p in self.room.get_all_players():
            username, ready = p.username, p.ready_for_room
            p_stats = self.server.get_player_stats(p.username)
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
                        self.room.game_id,  # game id no longer used
                        self._player_list,
                        self.room.host.username)

    @property
    def _sendroomlist(self):
        """helper to create a SendRoomList msg
        only return rooms not in game
        :return: SendRoomList"""
        room_ids = self.server.get_room_ids_in_lobby()
        return SendRoomList(room_ids)

    @property
    def is_logged_in(self):
        return bool(self.username)

    @property
    def is_in_game(self):
        return self.room and self.room.game_started

    # endregion

    # ----START HELPER FUNCTION----
    def update_thread_name(self):
        """set thread name for nicer logging"""
        if self.is_logged_in:
            self.thread_name = self.username
        self.setName(self.thread_name + "-m")
        self.recv_thread.setName(self.thread_name + "-r")
        self.send_thread.setName(self.thread_name + "-s")

    def _leave_room(self):
        """leave room and push new room status to everyone
        if 2 player game, other player win"""
        if not self.is_logged_in:
            return False
        if not self.room:
            return False
        self.room.remove_player(self)
        # room empty, close the room
        if self.room.is_empty:
            if self.room.close():
                self.server.remove_room(self.room.ID)
        # other player(s) still in game
        elif self.is_in_game:
            self.broadcast_msg(PlayerLeft(self.username), exclude_self=True)
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
        if not self.is_logged_in:
            return False
        player_stats = self.server.get_player_stats(self.username)
        if player_stats:
            if new_win:
                player_stats["wins"] += 1
            if new_game:
                player_stats["games"] += 1
            if status is not None:
                player_stats["status"] = status

    def broadcast_msg(self, msg, exclude_self=False):
        """send to all players in the same room or game"""
        if not self.room:
            return
        if exclude_self:
            players = (p for p in self.room.get_all_players() if p is not self)
        else:
            players = self.room.get_all_players()
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
            pmessage = pickle.dumps(message)
        except Exception:
            raise PicklingError(message)

        header = "{}{}".format(len(pmessage), "\n").encode()

        try:
            self.socket.sendall(header + pmessage)
        except Exception:
            raise

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
            while length > 0:
                temp_buf = sock.recv(length)
                if len(temp_buf) == 0:  # client disconnected
                    return b''
                length -= len(temp_buf)
                buf += temp_buf
            return buf

        try:
            message_len = _receive_len_header(self.socket)
            if not message_len:
                raise Exception("connection broken")
            new_pmsg = _recv_real_message(self.socket, message_len)  # pickled
            if not new_pmsg:
                raise Exception("connection broken")
        except Exception:  # connection broken
            raise Exception("connection broken")
        try:
            new_msg = pickle.loads(new_pmsg)
        except Exception:
            raise UnpicklingError(new_pmsg)
        else:
            return new_msg

    def close(self):
        """
        gracefully close the socket and do the clean up
        """
        with self._close_lock:
            if self.is_closed:
                return
            elif self.is_taken_over:
                pass
            else:
                logger.info("client disconnected: {}".format(self.socket_addr))
                self.update_player_stats(status="Offline")
            # leave any room that client is in
            if self.room:
                self._leave_room()
            self.socket.close()
            self.server.drop_client(self.socket)
            self.is_closed = True

    def try_restore_connection(self, timeout=60):
        """after connection is broken, wait for reconnection,
        return false after timeout.
        :return : bool"""
        if not self.is_logged_in:
            return False
        if not self.is_in_game:
            return False
        logger.info("waiting for client to reconnect...")
        while timeout > 0:
            # sleep 1 sec
            timeout -= 1
            time.sleep(1)
            # other clientsocket has taken over
            if self.is_taken_over:
                return False
            # reconnected
            elif not self.connection_broken:
                logger.info("client reconnected")
                return True
        logger.warning("client connection time out")

    def take_over(self, old_clientsocket):
        """take over the old_clientsocket
        :type old_clientsocket: ClientSocket
        """
        old_clientsocket.is_taken_over = True
        self.update_player_stats(status="Online")

    def reconnect(self, old_clientsocket):
        """reconnect to the old_clientsocket
        :type old_clientsocket: ClientSocket"""
        old_clientsocket.socket = self.socket
        old_clientsocket.socket_addr = self.socket_addr
        self.socket = self.socket_addr = None
        old_clientsocket.connection_broken = False
        self.close()

    def handle_clientlogin(self, login_message):
        """link client socket to client username"""
        # check if this username exists
        username = login_message.username
        userstat = self.server.get_player_stats(username)
        if userstat:
            # check if this username is already logged in
            if userstat["status"] == "Online":
                logger.warning(
                    "Re-login attempt detected: {}".format(username))
                self.sendQ.put(LoginAck(False))
                return
            # the user is trying to login again while suspended
            elif userstat["status"] == "Suspend":
                old_clientsocket = self.server.get_clientsocket_by_username(
                    username)
                """:type : ClientSocket"""
                if not old_clientsocket.connection_broken or \
                        old_clientsocket.is_taken_over:
                    logger.info("re-login failed {}: {}"
                                .format(username, self.socket_addr))
                # take over
                self.take_over(old_clientsocket)
                logger.info("client re-logged in as {}: {}"
                            .format(username, self.socket_addr))
            elif userstat["status"] == "Offline":
                if userstat["password"] == login_message.passwd:
                    logger.info("client logged in as {}: {}"
                                .format(username, self.socket_addr))
                else:
                    logger.info("password wrong! {}".format(username))
                    self.sendQ.put(LoginAck(False))
                    return
        else:
            logger.info("username does not exist! {}".format(username))
            self.sendQ.put(LoginAck(False))
            return
        self.username = username
        self.update_player_stats(status="Online")
        self.update_thread_name()
        self.sendQ.put(LoginAck(True))
        self.sendQ.put(self._sendroomlist)

    def handle_signup(self, signup_dat):
        username = signup_dat.username
        userstat = self.server.get_player_stats(username)
        # check if this username exists
        if userstat:
            logger.info("username exist already! {}".format(username))
            self.sendQ.put(LoginAck(False))
            return
        else:
            if signup_dat.username and signup_dat.passwd:
                # create this name
                self.server.create_player_profile(signup_dat.username,
                                                  signup_dat.passwd)
                logger.info("new profile created: {}".format(username))
            else:
                logger.info("username or password not supplied for signup")
                self.sendQ.put(LoginAck(False))
                return
        logger.info("client logged in as {}: {}"
                    .format(username, self.socket_addr))
        self.username = username
        self.update_player_stats(status=True)
        self.update_thread_name()
        self.sendQ.put(LoginAck(True))
        self.sendQ.put(self._sendroomlist)


    @logged_in
    def handle_getroomlist(self, dat):
        self.sendQ.put(self._sendroomlist)

    @in_room
    def handle_chatmessage(self, chat_message):
        self.broadcast_msg(chat_message, exclude_self=True)

    @logged_in
    def handle_joinroom(self, room_data):
        """joining a existed room by id"""
        try:
            self.room = self.server.get_room(room_data.roomId)
            self.room.add_player(self)
        except Exception:
            logger.info("trying to join a room that does not exist: {}"
                        .format(room_data.roomId))
            # send a new room list
            self.sendQ.put(self._sendroomlist)
        else:
            self.broadcast_msg(self._sendroom_msg)

    @logged_in
    def handle_createroom(self, dat):
        """create a room for client"""
        # generate room
        self.room = self.server.create_room(self)
        self.broadcast_msg(self._sendroom_msg)

    @in_room
    def handle_readyforgame(self, dat):
        """set client to ready and push the room status to everyone
        will start game if everyone is ready"""
        self.ready_for_room = True
        self.broadcast_msg(self._sendroom_msg)
        # start game if everyone is ready
        if all(p.ready_for_room for p in self.room.get_all_players()):
            seed = randint(0, 10000000) if not self.room.saved_game else None
            temp = self._player_list
            self.room.game_started = True
            for i, p in enumerate(self.room.get_all_players()):
                p.ready_for_room = False
                p.sendQ.put(startGame(seed=seed,
                                      player_list=temp,
                                      player_turn=i + 1,
                                      saved_game=self.room.saved_game))

    @in_room
    def handle_leaveroom(self, dat):
        """call _leave_room and send a room list to client"""
        self._leave_room()
        self.sendQ.put(self._sendroomlist)

    @host_only
    def handle_changemap(self, game_dat):
        """change a map, game_dat needs to contain a saved game
        :type game_dat: ChangeMap
        """
        game_id, saved_game = game_dat.game_id, game_dat.saved_game
        self.room.change_map(game_id=game_id, saved_game=saved_game)
        logger.info("host changed map, map will be send at game start")

    @in_game
    def handle_turndata(self, turndata):
        self.broadcast_msg(turndata, exclude_self=True)

    @in_game
    def handle_wingame(self, dat):
        """update player_stats
        send GameEnd msg to everyone in room
        send SendRoomList msg to everyone in room
        """
        # todo make this work
        for p in self.room.get_all_players():
            if p is self:
                p.update_player_stats(new_game=True, new_win=True)
            else:
                p.update_player_stats(new_game=True)
        self.room.game_started = False
        self.broadcast_msg(GameEnd())
        # self.broadcast_msg(self._sendroomlist)
        self.broadcast_msg(self._sendroom_msg)

    @in_game
    def handle_leavegame(self, login_data):
        pass

    def handle_reconnectrequest(self, reconnect_data):
        """reconnect request to try to reconnect while in game
        :type reconnect_data: ReconnectRequest"""
        username = reconnect_data.username
        userstats = self.server.get_player_stats(username)
        if userstats and userstats["status"] == "Suspend":
            # let the old clientSocket swap its socket
            cs = self.server.get_clientsocket_by_username(username)
            ":type: ClientSocket"
            if cs.connection_broken and not cs.is_taken_over and cs.is_in_game:
                self.reconnect(cs)
            else:
                logger.warning("client try to reconnect but connection is "
                               "not broken")
        else:
            logger.warning("reconnection msg does not have username or "
                           "username is un-registered with server")

    def handle_message(self, msg):
        """
        verify and dispatch messages to different handler
        :type msg: BaseClientMessage
        """
        msg_class = msg.__class__.__name__
        handler = getattr(self, "handle_%s" % msg_class.lower(), None)
        if not handler:
            logger.error("No handler for message class {}".format(msg_class))
            return

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
        while not self.is_closed and self.socket:
            # send the message
            msg = self.sendQ.get()  # block on get from sendQ
            ":type: BaseClientMessage"
            try:
                self._send(msg)
                logger.debug("sent message: {}".format(msg.__class__.__name__))
            except PicklingError as e:
                logger.error("failed to pickle message")
                logger.debug(e.args[0])
            except Exception:
                # put back the message get from the queue in case of exception
                self.sendQ.put(msg)
                if not self.connection_broken:
                    self.connection_broken = True
                    logger.info("client connection is broken")
                return

    def do_recv(self):
        """
        a sub receive-thread execute this function to receive and handle msg
        """
        while not self.is_closed and self.socket:
            try:
                # block on recv
                new_msg = self._recv()
            except UnpicklingError as upe:
                logger.error("message cannot be unpickled, "
                             "message format might be wrong.")
                logger.debug(upe.args[0])
            except Exception:
                if not self.connection_broken:
                    self.connection_broken = True
                    logger.info("client connection is broken")
                return
            if not new_msg:
                if not self.connection_broken:
                    self.connection_broken = True
                    logger.info("client connection is broken")
                return
            self.handle_message(new_msg)

    def run(self):
        """
        the main thread of client that will spawn send_thread and
        recv_thread and will be in charge of monitoring the health of the
        connection
        """
        # spawn the sending thread
        self.send_thread = threading.Thread(target=self.do_send)
        self.send_thread.daemon = True
        self.recv_thread = threading.Thread(target=self.do_recv)
        self.recv_thread.daemon = True
        # update threads name first before starting them
        self.update_thread_name()
        self.send_thread.start()
        self.recv_thread.start()
        logger.info("new client connected: {}".format(self.socket_addr))
        while not self.is_closed:
            if self.connection_broken:
                # try to wait for reconnect
                if self.try_restore_connection():
                    # reconnected successfully
                    # check if threads are still up
                    # send_thread is likely to be alive if it's blocking on
                    # the sendQ, if so, it's ok because we will already
                    # swaped our socket. Otherwise, we restart it
                    if not self.send_thread.isAlive():
                        self.send_thread = threading.Thread(
                            target=self.do_send)
                        self.send_thread.daemon = True
                        self.update_thread_name()
                        self.send_thread.start()
                    # recv_thread is likely to be dead, if so, we restart
                    # it as well. Otherwise, we do the same thing, because
                    # it is not listening on an active socket anymore, so
                    # it won't do interfere our connection
                    self.recv_thread = threading.Thread(target=self.do_recv)
                    self.recv_thread.daemon = True
                    self.update_thread_name()
                    self.recv_thread.start()
                    continue

                # reconnect failed
                else:
                    break

            # check connection in 1 second
            else:
                time.sleep(1)
        self.close()


class Server():
    """the one and only Server itself"""

    def __init__(self, max_connections_allowed=10):
        self._server_addr = SERVER_ADDR or ("localhost", 8000)
        self._data_file = "datafile.dat"
        # all the clients: {socket: ClientSocket}
        self._clients = {}
        self._clients_lock = threading.RLock()
        # all the rooms: {int: Room}
        self._rooms = {}
        self._rooms_lock = threading.RLock()
        # all the player stats: {str: dict}
        self._player_stats = {}
        self._player_stats_lock = threading.RLock()

        try:
            server_socket = socket.socket()
            # enable reuse port when restart server
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(self._server_addr)
            server_socket.listen(max_connections_allowed)
        except Exception as e:
            logger.error("server socket init failed")
            logger.exception(e)
            sys.exit()
        else:
            self.server_socket = server_socket
            logger.info("server started at {}".format(self._server_addr))

    # region self.room
    def get_room(self, room_id):
        """
        :type room_id: int
        """
        with self._rooms_lock:
            return self._rooms.get(room_id)

    def create_room(self, host):
        """
        use this method to create a room
        :type host: ClientSocket
        :rtype : Room
        """
        with self._rooms_lock:
            new_room = Room(host)
            self._rooms[new_room.ID] = new_room
            return new_room

    def remove_room(self, room_id):
        """
        :type room_id: int
        """
        with self._rooms_lock:
            return self._rooms.pop(room_id)

    @property
    def all_room_ids(self):
        """return a list of all room ids"""
        with self._rooms_lock:
            return list(self._rooms.keys())

    def get_room_ids_in_lobby(self):
        """return a list of rooms not in game"""
        with self._rooms_lock:
            ret = [k for k, v in self._rooms if not v.game_started]
            assert (ret <= list(self._rooms.keys()))  # lobby room is a subset
            return ret

    # endregion

    # region player_stats
    def get_player_stats(self, username):
        with self._player_stats_lock:
            return self._player_stats.get(username)

    def _get_all_player_profile(self):
        with self._player_stats_lock:
            return list(self._player_stats.values())

    def create_player_profile(self, username, password):
        """create a new player profile and add to player_stats"""
        with self._player_stats_lock:
            if self.get_player_stats(username):
                return False
            new_player_stats = {"wins": 0, "games": 0, "status": "Offline",
                                "password": password}
            self._player_stats[username] = new_player_stats
            return new_player_stats

    # endregion

    # region _clients
    def new_client_connected(self, new_sock, new_clientsocket):
        with self._clients_lock:
            if not self._clients.get(new_sock):
                self._clients[new_sock] = new_clientsocket

    def drop_client(self, dropped_client_sock):
        """
        handler for connection drop
        will remove the connection from connection pool
        :type dropped_client_sock: socket.socket
        """
        with self._clients_lock:
            if self._clients.get(dropped_client_sock):
                self._clients.pop(dropped_client_sock)

    def get_all_clients(self):
        with self._clients_lock:
            return list(self._clients.values())

    def get_clientsocket_by_username(self, name):
        """get a clientsocket from clients by username
        this operation is not efficient"""
        with self._clients_lock:
            for _, v in self._clients.items():
                if v.username and v.username == name:
                    return v

    # endregion

    def summary(self):
        logger.debug("Summary: clients still connected: {}"
                     .format(self.get_all_clients() or None))
        logger.debug("Summary: rooms not removed: {}"
                     .format(self._rooms or None))
        logger.debug("Summary: remaining threads: {}"
                     .format(threading.enumerate()))

    def shut_down(self):
        client_list = self.get_all_clients()
        for c in client_list:
            c.close()
        self.server_socket.close()
        logger.info("server socket is closed")
        # set all player status to Offline
        for prof in self._get_all_player_profile():
            prof["status"] = "Offline"
        # write profile to disk
        with open(self._data_file, "wb") as f:
            pickle.dump(self._player_stats, f)
        logger.info("player stats saved")
        self.summary()

    def start(self):
        # initilize player_stats
        if os.path.exists(self._data_file):
            with open(self._data_file, "rb") as f:
                # put a try except because data in file might be corrupted
                try:
                    self._player_stats = pickle.load(f)
                except Exception:
                    pass
        else:
            open(self._data_file, 'wb').close()
        # initialize all player status to offline
        for prof in self._get_all_player_profile():
            prof["status"] = "Offline"

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
                    with self._clients_lock:
                        self.new_client_connected(new_client_socket,
                                                  new_client)
                    new_client.start()

        # server shutdown
        except KeyboardInterrupt:
            logger.info("Server Shutting down from Keyboard")
        except Exception as e:
            logger.critical("Unexpected Exception: Server Shutdown")
            logger.exception(e)
        finally:
            self.shut_down()


if __name__ == "__main__":
    server = Server()
    server.start()  # listening on address and port specified in 'SERVER_ADDR'

