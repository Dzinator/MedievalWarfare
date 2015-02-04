import socket
import unittest

from Server.gameMessage import clientMessage
from server import handle_message, logger, handle_login


class TestHandler(unittest.TestCase):
    def setUp(self):
        super(TestHandler, self).setUp()
        self.sock = socket.socket()
        logger.disabled = True

    def test_handle_message_invalid_message_header(self):
        msg_no_header = clientMessage.BaseMessage()
        self.assertFalse(handle_message(self.sock, msg_no_header))
        msg_wrong_header = clientMessage.BaseMessage()
        msg_wrong_header.header = "bad header"
        self.assertFalse(handle_message(self.sock, msg_wrong_header))

    def test_handle_message_valid_message(self):
        login_msg = clientMessage.ClientLogin('bob')
        self.assertTrue(handle_message(self.sock, login_msg))

    def test_handle_login(self):
        login_msg = clientMessage.ClientLogin('bob')
        self.assertTrue(handle_login(handle_message(self.sock, login_msg)))



