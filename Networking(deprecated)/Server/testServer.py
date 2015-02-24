import socket
import time
import unittest
import sys

from Shared.message import ClientLogin, ChatMessage
from Server.server import SERVER_ADDR
from ClientAgent.mockClient import send_to_server, recv_from_server


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
        Juliet = socket.socket()
        Juliet.connect(SERVER_ADDR)
        send_to_server(Juliet, loginM)
        Juliet.close()

    def testChat(self):
        msg = "Juliet O Juliet!"
        # client
        Romeo = socket.socket()
        Romeo.connect(SERVER_ADDR)
        send_to_server(Romeo, ClientLogin("Romeo"))

        # another client
        Juliet = socket.socket()
        Juliet.connect(SERVER_ADDR)
        send_to_server(Juliet, ClientLogin("Juliet"))

        time.sleep(1) # wait for Juliet to finish log in before sending her msg
        chatM = ChatMessage("Romeo", msg)
        send_to_server(Romeo, chatM)
        receivedM = recv_from_server(Juliet)
        assert(receivedM.sender == "Romeo")
        assert(receivedM.message == msg)
        Juliet.close()
        Romeo.close()

