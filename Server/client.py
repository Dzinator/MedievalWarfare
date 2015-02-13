# todo implement a sample client using select and socket that can send and receive messages
import logging
import socket
import select

# initialize loggin
logging.basicConfig(level="DEBUG")
logger = logging.getLogger(__name__)



if __name__ == "__main__":
    SERVER_ADDR = ("localhost", 8000)
    s = socket.socket()
    s.connect(SERVER_ADDR)
    logger.info("connected to server {}".format(SERVER_ADDR))

