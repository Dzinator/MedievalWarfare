import socket
import unittest


class testClientSocket(unittest.TestCase):
    def testCreate(self):
        """ClientSocket is a subclass of socket"""
        cs = socket.socket()
        cs.close()

if __name__ == '__main__':
    unittest.main()
