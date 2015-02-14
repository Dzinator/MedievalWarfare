# todo implement a sample client using select and socket that can send and receive messages
import logging
import socket
import select
import struct

# initialize loggin

logging.basicConfig(level="DEBUG")
logger = logging.getLogger(__name__)


def send_to_server(server_sock, message):
    """takes care of the lower level communication
    i.e. calculating the size of message and make
    the entire message is delivered."""
    # todo use a synchronization machanism to restrict access to one thread
    server_sock.sendall("{}{}".format(len(message), "\n").encode())
    server_sock.sendall(message)


if __name__ == "__main__":
    SERVER_ADDR = ("localhost", 8000)
    s = socket.socket()
    s.connect(SERVER_ADDR)
    logger.info("connected to server {}".format(SERVER_ADDR))

