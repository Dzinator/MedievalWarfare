from Server.gameMessage import ClientHeader, ClientState

# todo Consider timestamp

class BaseMessage():
    """This is the most basic template for defining a message,
    Not to be used directly"""

    def __init__(self):
        # todo add document
        self.header = None
        self.state = None


class ClientLogin(BaseMessage):
    """This is the message sent by the client when loggin in"""

    def __init__(self, username):
        # todo add document
        super(ClientLogin, self).__init__()
        self.header = ClientHeader.CLIENTLOGIN
        self.state = ClientState.LOGGING
        self.username = username


class JoinRoom(BaseMessage):
    """The message send when client had chosen a room to join"""

    def __init__(self, room):
        # todo add document
        """

        """
        super(JoinRoom, self).__init__()
        self.header = ClientHeader.JOINROOM
        self.state = ClientState.INLOBBY
        self.room = room


class CreateRoom(BaseMessage):
    """The message send when the client choose to create a new room"""

    def __init__(self):
        super(CreateRoom, self).__init__()
        self.header = ClientHeader.CREATEROOM
        self.state = ClientState.INLOBBY


class LeaveRoom(BaseMessage):
    """This message is send by the client when leaving a room he/she is in"""

    def __init__(self):
        super(LeaveRoom, self).__init__()
        self.header = ClientHeader.LEAVEROOM
        self.state = ClientState.INROOM


class ReadyForGame(BaseMessage):
    """This message is send to indicate client ready for a game to start"""

    def __init__(self):
        super(ReadyForGame, self).__init__()
        self.header = ClientHeader.READYFORGAME
        self.state = ClientState.INROOM


class ChangeMap(BaseMessage):
    """This message is send by the host to change the current map"""

    def __init__(self):
        super(ChangeMap, self).__init__()
        self.header = ClientHeader.CHANGEMAP
        self.state = ClientState.INROOM


class TurnData(BaseMessage):
    """active player send this when she finished her turn"""

    def __init__(self, turn_data):
        # todo add document
        super(TurnData, self).__init__()
        self.header = ClientHeader.TURNDATA
        self.state = ClientState.INGAME
        self.turn_data = turn_data


class LeaveGame(BaseMessage):
    """while in a game, client indicate she wants to leave the game"""

    def __init__(self):
        super(LeaveGame, self).__init__()
        self.header = ClientHeader.LEAVEGAME
        self.state = ClientState.INGAME















