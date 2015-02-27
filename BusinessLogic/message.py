# log in

class BaseClientMessage():
    """This is the base message that all client message should inherite
    Don't use this class directly"""

    def __init__(self):
        pass


class ClientLogin(BaseClientMessage):
    """This is the message sent by the client when loggin in"""

    def __init__(self, username):
        super().__init__()
        self.username = username

class LoginAck(BaseClientMessage):
    """send by server: respond for ClientLogin msg"""
    def __init__(self, suc):
        """ :param suc: bool """
        super().__init__()
        self.success = suc


class GetRoomList(BaseClientMessage):
    def __init__(self):
        super().__init__()

class SendRoomList(BaseClientMessage):
    """send by server: respond for GetRoomList msg"""
    def __init__(self, ids):
        super().__init__()
        self.room_list = ids



# in lobby
class JoinRoom(BaseClientMessage):
    """The message send when client had chosen a room to join"""
    def __init__(self, id):
        super().__init__()
        self.roomId = id


class CreateRoom(BaseClientMessage):
    """The message send when the client choose to create a new room"""

    def __init__(self):
        super().__init__()

class sendRoom(BaseClientMessage):
    """Server Message: respond to client's createRoom or JoinRoom"""
    def __init__(self, id, current_game, playerlist):
        super().__init__()
        self.roomId = id
        self.current_game = current_game
        self.playerlist = playerlist

class sendSavedGame(BaseClientMessage):
    """send by client when trying to load a game from disk"""
    def __init__(self, saved_game):
        super().__init__()
        self.saved_game = saved_game

# class receivedGame(BaseClientMessage):
#     """send by client: indicate ready for game"""
class startGame(BaseClientMessage):
    """send by server: to indicate start game"""
    def __init__(self, seed):
        super().__init__()
        self.seed = seed


# in room
# todo add roomUpdate Msg
# todo consider adding a failuer msg when not log in as bad username and such
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

    def __init__(self, f, args):
        super().__init__()
        self.fname = f
        self.fargs = args
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
