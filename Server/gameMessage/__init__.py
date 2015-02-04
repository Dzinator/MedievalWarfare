class ClientHeader():
    """all the possible messages header sent by client"""
    # loggin
    CLIENTLOGIN = "CLIENTLOGIN"
    # lobby
    JOINROOM = "JOINROOM"
    CREATEROOM = "CREATEROOM"
    # room
    LEAVEROOM = "LEAVEROOM"
    READYFORGAME = "READYFORGAME"
    CHANGEMAP = "CHANGEMAP"
    # game
    TURNDATA = "TURNDATA"
    LEAVEGAME = "LEAVEGAME"


class ClientState():
    """all the possible state sent by the client"""
    LOGGING = "LOGGING"
    INLOBBY = "INLOBBY"
    INROOM = "INROOM"
    INGAME = "INGAME"
