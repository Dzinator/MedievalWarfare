import socket
import pickle
import time
import unittest

from clientMessage import *
from server import SERVER_ADDR
from mockClient import send_to_server, recv_from_server


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
        pLoginM = pickle.dumps(loginM)
        send_to_server(Juliet, pLoginM)
        Juliet.close()
        # reconnect and re-login
        Juliet = socket.socket()
        Juliet.connect(SERVER_ADDR)
        send_to_server(Juliet, pLoginM)
        Juliet.close()

    def testChat(self):
        msg = "Juliet O Juliet!"
        # client
        Romeo = socket.socket()
        Romeo.connect(SERVER_ADDR)
        send_to_server(Romeo, pickle.dumps(ClientLogin("Romeo")))

        # another client
        Juliet = socket.socket()
        Juliet.connect(SERVER_ADDR)
        send_to_server(Juliet, pickle.dumps(ClientLogin("Juliet")))

        time.sleep(1) # wait for Juliet to finish log in before sending her msg
        chatM = ChatMessage("Romeo", msg)
        pChatM = pickle.dumps(chatM)
        send_to_server(Romeo, pChatM)
        pReceivedM = recv_from_server(Juliet)
        receivedM = pickle.loads(pReceivedM)
        assert(receivedM.sender == "Romeo")
        assert(receivedM.message == msg)
        Juliet.close()
        Romeo.close()

