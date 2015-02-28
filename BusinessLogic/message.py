class BaseClientMessage():
    """This is the base message that all client message should inherite
    Don't use this class directly"""
    def __init__(self):
        pass

# log in

class ClientLogin(BaseClientMessage):
    """send by client: log in with a username"""

    def __init__(self, username):
        super().__init__()
        self.username = username

class LoginAck(BaseClientMessage):
    """send by server: response for ClientLogin msg"""
    def __init__(self, success):
        """:type param success: bool"""
        super().__init__()
        self.success = success

# in lobby

class GetRoomList(BaseClientMessage):
    """send by client: get a list of rooms in lobby"""
    def __init__(self):
        super().__init__()

class SendRoomList(BaseClientMessage):
    """send by server: respond for GetRoomList msg"""
    def __init__(self, room_list):
        super().__init__()
        self.room_list = room_list

class JoinRoom(BaseClientMessage):
    """send by client: to join a room indicate by room id"""
    def __init__(self, roomId):
        super().__init__()
        self.roomId = roomId

class CreateRoom(BaseClientMessage):
    """send by client: to create a new room"""
    def __init__(self):
        super().__init__()

class startGame(BaseClientMessage):
    """send by server: to indicate start game"""
    def __init__(self, seed, player_list, player_turn):
        """in the parameters: seed is a random number to seed game creation
        player_turn is a number between 1-4
        :type seed: int
        :type player_turn: int"""
        super().__init__()
        self.seed = seed
        self.player_list = player_list
        self.player_turn = player_turn


# in room

class sendRoom(BaseClientMessage):
    """send by server: a new copy of the room data"""
    def __init__(self, roomId, current_game, playerlist):
        """
        :type roomId: int
        :type current_game: str
        """
        super().__init__()
        self.roomId = roomId
        self.current_game = current_game
        self.playerlist = playerlist

class LeaveRoom(BaseClientMessage):
    """send by client: indicate leaving a room"""
    def __init__(self):
        super().__init__()

class ReadyForGame(BaseClientMessage):
    """send by client: indicate ready for a game"""
    def __init__(self):
        super().__init__()



# in game
class TurnData(BaseClientMessage):
    """send by client: for a game turn"""
    def __init__(self, f, args):
        super().__init__()
        self.fname = f
        self.fargs = args


class ChatMessage(BaseClientMessage):
    def __init__(self, sender, message):
        super().__init__()
        self.sender = sender
        self.message = message

# not used
class sendSavedGame(BaseClientMessage):
    """send by client when trying to load a game from disk"""
    def __init__(self, saved_game):
        super().__init__()
        self.saved_game = saved_game

class LeaveGame(BaseClientMessage):
    """send by client: leave game"""
    def __init__(self):
        super().__init__()

class ChangeMap(BaseClientMessage):
    """This message is send by the host to change the current map
    send either a saved_game or a game_id of the default games"""
    def __init__(self, game_id=None, saved_game=None):
        super().__init__()
        self.game_id = game_id
        self.saved_game = saved_game

class NewMap(BaseClientMessage):
    """send by server: a new bit map loaded from client"""
    def __init__(self, new_game, game_id=None):
        super().__init__()
        self.new_game = new_game

class WinGame(BaseClientMessage):
    """send by client: won current game"""
    def __init__(self):
        super().__init__()

class GameEnd(BaseClientMessage):
    """send by server: indicate the end of current game"""
    def __init__(self):
        super().__init__()





