# log in
class ClientLogin():
    """This is the message sent by the client when loggin in"""

    def __init__(self, username):
        # todo add document
        self.username = username


# in lobby
class JoinRoom():
    """The message send when client had chosen a room to join"""

    def __init__(self):
        pass
        # todo add document
        # self.room = room


class CreateRoom():
    """The message send when the client choose to create a new room"""

    def __init__(self):
        pass


# in room
class LeaveRoom():
    """This message is send by the client when leaving a room he/she is in"""

    def __init__(self):
        pass


class ReadyForGame():
    """This message is send to indicate client ready for a game to start"""

    def __init__(self):
        pass


class ChangeMap():
    """This message is send by the host to change the current map"""

    def __init__(self):
        pass


# in game
class TurnData():
    """active player send this when she finished her turn"""

    def __init__(self):
        pass
        # todo add document
        # self.turn_data = turn_data


class LeaveGame():
    """while in a game, client indicate she wants to leave the game"""

    def __init__(self):
        pass


class ChatMessage():
    def __init__(self, sender, message):
        self.sender = sender
        self.message = message
