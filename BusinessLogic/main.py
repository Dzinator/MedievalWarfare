from GUI import Gui
import math, random

class Player:
    def __init__(self, Id, name, number):
        self.Id = Id
        self.name = name
        self.villages = []
        self.n = number

    def addVillage(self,v):
        self.villages.append(v)

class Village:
    def __init__(self, h, p, t):
        self.type = 0
        self.gold = 0
        self.wood = 0
        self.hex = h
        self.units = []
        self.owner = p
        self.territory = t
        for h in t:
            h.village = self
            
    def killUnits(self):
        for unit in self.units:
            unit.hex.hasTombstone
            unit.hex.occupant = None

        del self.units[:]
        self.units = []

    #tempmethod
    def spawnUnit(self,h):
        self.units.append(Unit(1,h,self))

class Unit:
    upkeeps = {0 : 2, 1:6, 2: 18, 3:54}
    costs = {0:10,1:20,2:30,3:40}
    upgradeCosts = {}
    def __init__(self, ut, h, v):
        self.unitType = ut
        self.currentAction = 'ready'
        self.cost = 0 #have cost array by unittype
        self.hex = h
        self.owner = v
        self.moved = False
        h.occupant = self

    def update(self):
        pass

    def setBuildingRoad(self):
        pass

    def upgradePrice(self, newLevel):
        return

    def buildRoad(self):
        self.hex.putRoad()

    def buildMeadow(self):
        self.hex.hasMeadow = True
        self.moved = True


class Hex:
    def __init__(self, x, y, d, s,n, p = True):
        self.place = (x,y)
        self.centre = [x+d/2, y+d*math.sin(math.pi/3)]
        self.hasRoad = False
        self.hasTombstone = False
        self.hasWatchTower = False
        self.occupant = None
        self.village = None
        self.number = n
        f = lambda q: 1-min((2**(q-1)-1)/1000, 1)
        self.water = True if random.random()>f(s) else False
        self.hasTree = True if random.random()<.2 and not self.water else False 
        self.hasMeadow = True if not self.hasTree and not self.water and random.random()<.1 else False
        self.neighbours = []
        self.owner = random.randint(1,4) if not self.water else 0

    def removeTomb(self):
        self.hasTombstone = False
        self.hasTrees = True

    def putTomb(self):
        self.hasTombstone = True

    def putTree(self):
        if not self.hasWatchTower and not self.hasRoad:
            self.hasTree = True
            self.meadow = False

    def putRoad(self):
        self.hasRoad = True

    def removeTree(self):
        self.hasTree = False

    def getIncome(self):
        return 0 if self.hasTree else (2 if self.hasMeadow else 1)

    def buildWatchTower(self):
        self.hasTree = False
        self.hasWatchTower = True

    def trample(self):
        self.hasMeadow = False

class Grid:
    def __init__(self, mapId, width, height):
        self.Id = mapId
        self.tn = 0
        self.sp = .09
        self.d = self.sp/1.05
        ratio = width/height
        self.hexes = [Hex(self.sp*1.5*(x*2+(y%2)+1/3)-30*self.sp,y*self.sp*math.sin(math.pi/3)-20*self.sp,self.d, math.sqrt(abs((x-9)*1.5)**2+abs((y-22)/1.7)**2), x*100+y)  for y in range(45) for x in range(20)]
        self.land = [h for h in self.hexes if not h.water]
        for h in self.land:
            h.neighbours = [g for g in self.land if h != g and inCircle(h.centre,g.centre, self.sp*2+.02)]

    def populateMap(self, players):
        for h in self.hexes:
            if not h.water and not h.village and h.owner:
                territory = self.BFS(h, lambda g: True, lambda g: True if g.owner == h.owner else False)
                if len(territory)<=2:
                    for g in territory:
                        g.owner = 0
                    continue
                v = random.choice(territory)
                v.hasTree = False
                players[h.owner].addVillage(Village(v, players[h.owner], territory))

    def BFS(self, start, propertyFunc, siftFunc):
        unchecked, checked = set(), set()
        nodes = []
        unchecked.add(start)
        while len(unchecked)>0:
            next = unchecked.pop()
            checked.add(next)
            if propertyFunc(next):
                nodes.append(next)
            for node in next.neighbours:
                if siftFunc(node) and node not in checked and node not in unchecked:
                    unchecked.add(node)
        return nodes

class Engine:
    def __init__(self, Id):
        self.gameId = Id
        self.turn = 0;
        self.roundsPlayed = 0
        self.initPlayers()
        self.width = 1600
        self.height = 900
        self.grid = Grid(1, self.width, self.height)
        self.grid.populateMap(self.players)
        self.Gui = Gui(self, self.width, self.height)
    
    def initPlayers(self):
        self.players = {x : Player(1,"name",x) for x in range(1,5)}

    def buildRoad(self, unit):
        pass

    def ungradeVillage(self, village):
        if village.type<2 and village.wood>=5:
            village.type+=1
            village.wood-=5

    def upgradeUnit(self, unit, newLevel):
        if 4>newLevel>unit.type<3 and unit.owner.gold>10*(newLevel-unit.type):
            unit.type=newLevel
            unit.owner.gold-= 10*(newLevel-unit.type)

    def isValidMove(self):
        pass

    def takeOver(self, h, unit):
        pass

    def moveUnit(self, h, unit):
        self.isValidMove(h, unit)

    def newGame(self, players, mapData):
        pass

    def beginTurn(self, player): #player or turn?
        pass

    def run(self):
        self.Gui.run()

def inCircle(p1,p2,r):
    return math.sqrt(pow(p1[0]-p2[0],2)+pow(p1[1]-p2[1],2))<r

engine = Engine(1)
engine.run()
