import socket
import pickle
from Server.gameMessage.clientMessage import *
from Server.server import SERVER_ADDR
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
        Juliet.send(pLoginM)
        Juliet.close()
        # reconnect and re-login
        Juliet = socket.socket()
        Juliet.connect(SERVER_ADDR)
        Juliet.send(pLoginM)
        Juliet.close()

