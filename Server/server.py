import socket
import select
import logging
import sys
import pickle
from Server.gameMessage.clientMessage import *

# initialize loggin
from Server.gameMessage.clientMessage import ClientLogin, JoinRoom, CreateRoom, \
    ReadyForGame, LeaveRoom, ChangeMap, TurnData, ChatMessage, LeaveGame

logging.basicConfig(level="INFO",
                    format='[%(asctime)s] %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


# define global varaibles
RECV_BUFFERSIZE = 4096
MAX_CONNECTIONS_ALLOWED = 10
SERVER_ADDR = ("localhost", 8000)
all_connections = []  # used to store clients and server sockets
client_info = {}  # use client socket as key to retrive and store client info
rooms = {}
games = {}


def handle_chat_message(client_socket, chat_message):
    # todo change receiver to only people in same game
    receivers = all_connections
    for c in receivers:
        if c != client_socket:
            send_to_socket(c, chat_message)


def handle_login(client_socket, login_message):
    """link client socket to client username"""
    logger.info("client logged in as {}: {}".format(login_message.username,
                                               client_socket.getpeername()))


def handle_logout(client_socket):
    # todo write change to disk
    pass


def handle_joinroom():
    pass


def handle_createroom(client_socket, login_data):
    # generate room
    # get random id for room
    # put room in variable rooms
    # return respond
    pass


def handle_readyforgame(client_socket, login_data):
    pass


def handle_leaveroom(client_socket, login_data):
    pass


def handle_changemap(client_socket, login_data):
    pass


def handle_turndata(client_socket, login_data):
    pass


def handle_leavegame(client_socket, login_data):
    pass


def handle_message(client_socket, data, **kwargs):
    dispatcher = {
        # a mapping of clientMessage classes to handler functions
        ClientLogin.__name__: handle_login,
        JoinRoom.__name__: handle_joinroom,
        CreateRoom.__name__: handle_createroom,
        ReadyForGame.__name__: handle_readyforgame,
        LeaveRoom.__name__: handle_leaveroom,
        ChangeMap.__name__: handle_changemap,
        TurnData.__name__: handle_turndata,
        LeaveGame.__name__: handle_leavegame,
        ChatMessage.__name__: handle_chat_message,
    }
    try:
        handler = dispatcher[data.__class__.__name__]
        handler(client_socket, data)
    except KeyError as ke:
        logger.error(
            "message class does not exist {}".format(data.__class__))
        logger.debug(data)
        return False
    except Exception as e:
        logger.error("failed to handle message")
        logger.debug(data)
        logger.exception(e)
        return False


# send message to client
def send_unpickled_message(sock, message):
    """would not pickle message, only use this function in debugging"""
    try:
        sock.send(message)
    except Exception as e:
        logger.error("failed to send to socket: {}".format(sock.getpeername()))
        logger.debug(message)
        logger.exception(e)


def send_to_socket(sock, message):
    try:
        pmessage = pickle.dumps(message)
        sock.send(pmessage)
    except Exception as e:
        logger.error("failed to send to socket: {}".format(sock.getpeername()))
        logger.debug(message)
        logger.exception(e)


# handle client message

def handle_connection_drop(all_connections, dropped_client_socket):
    """
    handler for connection drop
    will remove the connection from connection pool
    this function is independent from function handle_message
    :type dropped_client_socket: socket.socket
    :type all_connections: list
    """
    logger.info(
        "remove socket from all_connections: {}".format(
            dropped_client_socket.getpeername()))
    dropped_client_socket.close()
    all_connections.remove(dropped_client_socket)


def handle_newclient(all_connections, new_client_socket):
    """
    handler for new connection
    will add new connection to connection pool
    this function is independent from function handle_message
    :type new_client_socket: socket.socket
    :type all_connections: list
    """
    all_connections.append(new_client_socket)


def shut_down(server_socket):
    [c.close() for c in all_connections if c != server_socket]
    server_socket.close()


def server():
    try:
        server_socket = None
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(SERVER_ADDR)
        server_socket.setblocking(False)
        server_socket.listen(MAX_CONNECTIONS_ALLOWED)
    except Exception as e:
        logger.error("server socket init failed")
        logger.exception(e)
        if server_socket: server_socket.close()
        sys.exit()
    else:
        logger.info("server started at {}".format(SERVER_ADDR))

    # main loop
    try:
        while True:
            read_sockets, _, _ = select.select(
                all_connections + [server_socket], [], [])
            for incoming_socket in read_sockets:
                if incoming_socket == server_socket:
                    try:
                        # accept new connection
                        new_client_socket = server_socket.accept()[0]
                        handle_newclient(all_connections, new_client_socket)
                    except OSError as ose:
                        logger.error(
                            "failed to accept client connection: {}".format(
                                incoming_socket.getpeername()))
                    else:
                        logger.info("new client connected {}"
                                    .format(new_client_socket.getpeername()))
                else:
                    client_sender_socket = incoming_socket
                    # receive client message
                    try:
                        # todo can we receive all data instead of using buffersize
                        message = client_sender_socket.recv(RECV_BUFFERSIZE)
                        if message != b"":
                            logger.debug(
                                "received message from client {}: {}"
                                .format(client_sender_socket.getpeername(),
                                        message))
                            try:
                                data = pickle.loads(message)
                            except Exception as e:
                                logger.error("message cannot be unpickled, "
                                             "message format might be wrong.")
                                logger.debug(message)
                                logger.exception(e)
                            else:
                                handle_message(client_sender_socket, data)
                        else:
                            # handle client connection dropped
                            logger.info("client disconnected: {}".format(
                                client_sender_socket.getpeername()))
                            handle_connection_drop(all_connections,
                                                   client_sender_socket)
                    except ConnectionError as cre:
                        # handle client connection dropped
                        logger.warning("client disconnected: {}"
                                       .format(
                            client_sender_socket.getpeername()))
                        logger.exception(cre)
                        handle_connection_drop(all_connections,
                                               client_sender_socket)
                    except OSError as ose:
                        # this should never happen
                        logger.critical("client broken connection leads to "
                                        "undersirable behaviour: ".format(
                            client_sender_socket.getpeername()))
                        logger.exception(ose)
                        handle_connection_drop(all_connections,
                                               client_sender_socket)
    # server shutdown
    except KeyboardInterrupt:
        logger.info("Server Shutting down from Keyboard")
        shut_down(server_socket)
    except Exception as e:
        logger.critical("Unexpected Exception: Server Shutdown")
        logger.exception(e)
        shut_down(server_socket)


if __name__ == "__main__":
    server()

