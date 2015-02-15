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
    server_sock.sendall("{}{}".format(len(message), "\n").encode())
    server_sock.sendall(message)


def recv_from_server(my_sock):
    """takes care of the lower level communication
    i.e. first read the size of message to make sure
    the entire message is received."""
    # ----START HELPER FUNCTION----
    def receive_len_header(sock):
        """return then length of the message
        return 0 if connection broken"""
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
        """
        buf = b''
        while length != len(buf):
            temp_buf = sock.recv(length)
            if len(temp_buf) == 0:  # client disconnected
                return b''
            buf += temp_buf
        return buf

    # ----END------------
    pmsg_len = receive_len_header(my_sock)
    pmsg = recv_real_message(my_sock, pmsg_len)
    return pmsg


if __name__ == "__main__":
    SERVER_ADDR = ("localhost", 8000)
    s = socket.socket()
    s.connect(SERVER_ADDR)
    logger.info("connected to server {}".format(SERVER_ADDR))

