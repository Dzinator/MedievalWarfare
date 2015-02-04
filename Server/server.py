import socket
import select
import logging
import sys
import pickle

from Server.gameMessage import clientMessage


# initialize loggin
logging.basicConfig(level="DEBUG")
logger = logging.getLogger(__name__)


# define varaibles
ALL_CONNECTIONS = []
RECV_BUFFERSIZE = 4096
MAX_CONNECTIONS_ALLOWED = 10
SERVER_ADDR = ('localhost', 8000)


def handle_joinroom():
    pass


def handle_login(client_socket, data, **kwargs):
    # todo implement
    return True


def handle_createroom(client_socket, login_data):
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
        # a mapping of clientMessageHeader to handler functions
        clientMessage.ClientHeader.CLIENTLOGIN: handle_login,
        clientMessage.ClientHeader.JOINROOM: handle_joinroom,
        clientMessage.ClientHeader.CREATEROOM: handle_createroom,
        clientMessage.ClientHeader.READYFORGAME: handle_readyforgame,
        clientMessage.ClientHeader.LEAVEROOM: handle_leaveroom,
        clientMessage.ClientHeader.CHANGEMAP: handle_changemap,
        clientMessage.ClientHeader.TURNDATA: handle_turndata,
        clientMessage.ClientHeader.LEAVEGAME: handle_leavegame,
    }
    try:
        handler = dispatcher[data.header]
        return handler(client_socket, data, **kwargs)
    except KeyError as ke:
        logger.error("message msg_header does not exist {}".format(data.header))
        logger.debug(data)
        return False
    except Exception as e:
        logger.error("failed to handle message")
        logger.debug(data)
        logger.exception(e)
        return False


def handle_connection_drop():
    pass


if __name__ == "__main__":
    try:
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(SERVER_ADDR)
        server_socket.listen(MAX_CONNECTIONS_ALLOWED)
    except Exception as e:
        logger.error("server socket init failed")
        logger.exception(e)
        server_socket.close()
        sys.exit()
    else:
        logger.info("server started at {}".format(SERVER_ADDR))

    ALL_CONNECTIONS.append(server_socket)
    logger.debug("added server socket to ALL_CONNECTIONS")

    # main loop
    while True:
        read_sockets, write_sockets, error_sockets = select.select(ALL_CONNECTIONS, [], [])
        for incoming_socket in read_sockets:
            if incoming_socket == server_socket:
                # accept new connection
                new_client_socket = server_socket.accept()[0]
                ALL_CONNECTIONS.append(new_client_socket)
                logger.info("new client connected {}".format(new_client_socket.getsockname()))
            else:
                client_sender_socket = incoming_socket
                # receive client message
                try:
                    message = client_sender_socket.recv(RECV_BUFFERSIZE)
                    logger.debug(
                        "received message from client {}: {}".format(client_sender_socket.getsockname(), message))
                    if message:
                        try:
                            data = pickle.loads(message)
                        except Exception as e:
                            logger.error("message cannot be unpickled, message format might be wrong.")
                            logger.debug(message)
                            logger.exception(e)
                        else:
                            handle_message(client_sender_socket, data)
                except OSError as e:
                    logger.warning("client disconnected: {}".format(client_sender_socket.getsockname()))
                    handle_connection_drop()




