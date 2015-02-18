import logging
import socket
import pickle
# noinspection PyUnresolvedReferences
from Networking.Shared.message import ClientLogin, JoinRoom, CreateRoom, \
    ReadyForGame, LeaveRoom, ChangeMap, TurnData, LeaveGame, ChatMessage

# initialize loggin

logging.basicConfig(level="DEBUG")
logger = logging.getLogger(__name__)


def send_to_server(server_sock, message):
    """
    takes care of the lower level
    communication pickle the message
    calculating the size of message and
    make sure the entire message is delivered.
    :type server_sock: socket.socket
    :type message: BaseClientMessage
    """
    # todo return a boolean indicate successful sent or not
    # need exception handling
    pMsg = pickle.dumps(message)
    server_sock.sendall("{}{}".format(len(pMsg), "\n").encode())
    server_sock.sendall(pMsg)


def recv_from_server(my_sock):
    """
    takes care of the lower level communication
    first read the size of message to make sure
    the entire message is received
    final return the unpickled message.
    :type my_sock: socket.socket
    :rtype : BaseClientMessage
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
        :rtype : BaseClientMessage
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
    msg = pickle.loads(pmsg)
    return msg


if __name__ == "__main__":
    SERVER_ADDR = ("localhost", 8000)
    s = socket.socket()
    s.connect(SERVER_ADDR)
    logger.info("connected to server {}".format(SERVER_ADDR))

