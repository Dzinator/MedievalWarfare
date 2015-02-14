import socket
import pickle
import time
from Server.gameMessage.clientMessage import *
from Server.server import SERVER_ADDR
from Server.client import send_to_server
import unittest


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

        chatM = ChatMessage("Romeo", msg)
        pChatM = pickle.dumps(chatM)
        # time.sleep(1)
        send_to_server(Romeo, pChatM)
        # time.sleep(1)
        print("before")
        pReceivedM = Juliet.recv(1024)
        print("after")
        receivedM = pickle.loads(pReceivedM)
        assert(receivedM.sender == "Romeo")
        assert(receivedM.message == msg)
        Juliet.close()
        Romeo.close()

