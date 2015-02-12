class Village:
    def __init__(self, h, p, t):
        self.VillageType = 0
        self.gold = 0
        self.wood = 0
        self.hex = h
        self.units = []
        self.owner = p
        self.territory = t

    def killUnits(self):
        pass


class Unit:
    def __init__(self, ut, h, v):
        self.unitType = ut
        self.currentAction = 'ready'
        self.cost = 0 #have cost array by unittype
        self.hex = h
        self.owner = v

    def update(self):
        pass

    def setBuildingRoad(self):
        pass

    def upgradePrice(self, newLevel):
        pass

class Hex:
    def __init__(self, t):
        self.hasTree = False
        self.hasRoad = False
        self.occupant = NULL
        self.type = 0 #later
        self.village = null

    def buildRoad(self,delay):
        pass

    def removeTomb(self):
        pass

    def putTomb(self):
        pass

    def putTree(self):
        pass

    def putRoad(self):
        pass

    def removeTree(self):
        pass

    def getIncome(self):
        pass

    def buildWatchTower(self):
        pass

    def trample(self):
        pass

class Grid:
    def __init__(self, mapId):
        self.Id = mapId
        self.hexes = []  # place gen code

    def populateMap(self, players):
        pass

class Engine:
    def __init__(self, Id):
        self.gameId = Id
        self.turn = 0;
        self.roundsPlayed = 0
        self.players = []
        self.grid = []
        
    def initPlayers(self):
        pass

    def buildRoad(self, unit):
        pass

    def ungradeVillage(self, village):
        pass

    def upgradeUnit(self, unit, newLevel):
        pass

    def takeOver(self, h, unit):
        pass

    def moveUnit(self, h, unit):
        pass

    def newGame(self, players, mapData):
        pass

    def beginTurn(self, player): #player or turn?
        pass



