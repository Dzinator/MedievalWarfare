import socket
import time
import unittest
import sys
import pickle

try:
    from server import SERVER_ADDR
except:
    from BusinessLogic.server import SERVER_ADDR
try:
    from message import *
except:
    from BusinessLogic.message import *


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


class testServer(unittest.TestCase):
    def testDisconnectAndReconnect(self):
        Juliet = socket.socket()
        Juliet.connect(SERVER_ADDR)
        Juliet.close()
        # reconnect
        Juliet = socket.socket()
        Juliet.connect(SERVER_ADDR)
        Juliet.close()

    def testLoginAndRelogin(self):
        """test disconnect and reconnect and login
        to server, server should not crash"""
        Juliet = socket.socket()
        Juliet.connect(SERVER_ADDR)
        loginM = ClientLogin("Juliet")
        send_to_server(Juliet, loginM)
        Juliet.close()
        # reconnect and re-login
        time.sleep(0.5)
        Juliet = socket.socket()
        Juliet.connect(SERVER_ADDR)
        send_to_server(Juliet, loginM)
        Juliet.close()

    def old_testChat(self):
        """this test is deprecated because now needs two person to be in the
         same room to chat"""
        print("this test is deprecated because now needs two person to "
              "be in the same room to chat")
        msg = "Juliet O Juliet!"
        # client
        Romeo = socket.socket()
        Romeo.connect(SERVER_ADDR)
        send_to_server(Romeo, ClientLogin("Romeo"))

        # another client
        Juliet = socket.socket()
        Juliet.connect(SERVER_ADDR)
        send_to_server(Juliet, ClientLogin("Juliet"))

        time.sleep(
            1)  # wait for Juliet to finish log in before sending her msg
        chatM = ChatMessage("Romeo", msg)
        send_to_server(Romeo, chatM)
        receivedM = recv_from_server(Juliet)
        assert (receivedM.sender == "Romeo")
        assert (receivedM.message == msg)
        Juliet.close()
        Romeo.close()

    def testRoom(self):
        """test creating and destroying a room"""
        Juliet = socket.socket()
        Juliet.connect(SERVER_ADDR)
        send_to_server(Juliet, ClientLogin("Juliet"))
        recv_from_server(Juliet) # LoginAck msg
        recv_from_server(Juliet) # RoomList msg
        Romeo = socket.socket()
        Romeo.connect(SERVER_ADDR)
        send_to_server(Romeo, ClientLogin("Romeo"))
        recv_from_server(Romeo) # LoginAck msg
        recv_from_server(Romeo) # RoomList msg

        # Juliet create a room
        send_to_server(Juliet, CreateRoom())
        # recv the room
        receivedM = recv_from_server(Juliet)
        self.assertIsInstance(receivedM, sendRoom)
        self.assertTrue(receivedM.roomId)
        # Romeo join the room
        send_to_server(Romeo, JoinRoom(receivedM.roomId))
        # recv the room
        receivedM2 = recv_from_server(Romeo)
        self.assertIsInstance(receivedM2, sendRoom)
        self.assertEqual(receivedM.roomId, receivedM2.roomId)
        # Juliet would recv a sendRoom msg from server as well
        receivedM3 = recv_from_server(Juliet)
        self.assertIsInstance(receivedM3, sendRoom)
        self.assertTrue(receivedM3.playerlist)
        self.assertEqual(receivedM3.playerlist, receivedM2.playerlist)
        Juliet.close()
        Romeo.close()

    def testLoggedInDecorator(self):
        """test the decorator logged_in in server.py"""
        Juliet = socket.socket()
        Juliet.connect(SERVER_ADDR)
        # try to create a room without logging in, this should appear as a
        # error on the server log
        send_to_server(Juliet, CreateRoom())
        Juliet.close()






