import socket
from ClientAgent.mockClient import send_to_server, recv_from_server

# noinspection PyUnresolvedReferences
from Shared.message import ClientLogin, JoinRoom, CreateRoom, \
    ReadyForGame, LeaveRoom, ChangeMap, TurnData, LeaveGame, ChatMessage


class ClientAgent():
    def __init__(self, server_addr):
        """
        wrap around the client socket
        """
        self.socket = socket.socket()
        self.socket.connect(server_addr)
        self.username = None

    def login(self, username):
        """
        send a login message to the server
        :return: bool
        """
        # todo maybe later we can have server send a response back
        self.username = username
        login_msg = ClientLogin(self.username)
        return send_to_server(self.socket, login_msg)

if __name__ == "__main__":
    SERVER_ADDR = ("localhost", 8000)
    client_networking_agent = ClientAgent(SERVER_ADDR)
    client_networking_agent.login('Yanis')


