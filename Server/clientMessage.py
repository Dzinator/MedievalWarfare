# log in

class BaseClientMessage():
    """This is the base message that all client message should inherite
    Don't use this class directly"""

    def __init__(self, ):
        pass


class ClientLogin(BaseClientMessage):
    """This is the message sent by the client when loggin in"""

    def __init__(self, username):
        super().__init__()
        # todo add document
        self.username = username


# in lobby
class JoinRoom(BaseClientMessage):
    """The message send when client had chosen a room to join"""

    def __init__(self):
        super().__init__()
        pass
        # todo add document
        # self.room = room


class CreateRoom(BaseClientMessage):
    """The message send when the client choose to create a new room"""

    def __init__(self):
        super().__init__()
        pass


# in room
class LeaveRoom(BaseClientMessage):
    """This message is send by the client when leaving a room he/she is in"""

    def __init__(self):
        super().__init__()
        pass


class ReadyForGame(BaseClientMessage):
    """This message is send to indicate client ready for a game to start"""

    def __init__(self):
        super().__init__()
        pass


class ChangeMap(BaseClientMessage):
    """This message is send by the host to change the current map"""

    def __init__(self):
        super().__init__()
        pass


# in game
class TurnData(BaseClientMessage):
    """active player send this when she finished her turn"""

    def __init__(self):
        super().__init__()
        pass
        # todo add document
        # self.turn_data = turn_data


class LeaveGame(BaseClientMessage):
    """while in a game, client indicate she wants to leave the game"""

    def __init__(self):
        super().__init__()
        pass


class ChatMessage(BaseClientMessage):
    def __init__(self, sender, message):
        super().__init__()
        self.sender = sender
        self.message = message
