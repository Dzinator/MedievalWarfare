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
        self.VillageType = 0
        self.gold = 0
        self.wood = 0
        self.hex = h
        self.units = []
        self.owner = p
        self.territory = t
        for h in t:
            h.village = self

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
    def __init__(self, x, y, d, s,n, p = True):
        self.place = (x,y)
        self.centre = [x+d/2, y+d*math.sin(math.pi/3)]
        self.hasRoad = False
        self.occupant = None
        self.type = 0 #later
        self.village = None
        self.number = n
        f = lambda q: 1-min((2**(q-1)-1)/1000, 1)
        self.water = True if random.random()>f(s) else False
        self.hasTree = True if random.random()<.2 and not self.water else False 
        self.meadow = False
        self.neighbours = []
        self.owner = random.randint(1,4)

    def buildRoad(self,delay):
        pass

    def removeTomb(self):
        pass

    def putTomb(self):
        pass

    def putTree(self):
        self.hasTree = True
        self.meadow = False

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
    def __init__(self, mapId, width, height):
        self.Id = mapId
        self.tn = 0
        self.sp = .09
        self.d = self.sp/1.05
        ratio = width/height
        self.hexes = [Hex(self.sp*1.5*(x*2+(y%2)+1/3)-30*self.sp,y*self.sp*math.sin(math.pi/3)-20*self.sp,self.d, math.sqrt(abs((x-9)*1.5)**2+abs((y-22)/1.7)**2), x*100+y)  for y in range(45) for x in range(20)]
        self.usable = [h for h in self.hexes if not h.water]

        for h in self.hexes:
            h.neighbours = [g for g in self.hexes if h != g and inCircle(h.centre,g.centre, self.sp*2+.02) and not g.water and not h.water]

        for h in self.hexes:
            self.keepHex(h)

        for h in self.hexes:
            self.keepHex(h)


    def populateMap(self, players):
        for h in self.hexes:
            if not h.water and not h.village and h.owner:
                territory = self.BFS(h, lambda g: True, lambda g: True if g.owner == h.owner else False)
                v = random.choice(territory)
                v.hasTree = False
                players[h.owner].addVillage(Village(v, players[h.owner], territory))

    def keepHex(self, h):
        if h.water:
            h.owner = 0
            return False
        checked = []
        while(True):
            s = sum([1 if g.owner == h.owner else 0 for g in h.neighbours])
            if s>1:
                return True
            elif s == 1:
                temp = None
                for g in h.neighbours:
                    if g.owner == h.owner and g not in checked:
                        checked.append(h)
                        temp = g
                        break
                if not temp:
                    h.owner = 0
                    return False
                h = g
            else:
                h.owner = 0
                return False

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
        self.grid = Grid(1, 1600, 900)
        self.grid.populateMap(self.players)


        self.Gui = Gui(self, 1600, 900)
    
    def initPlayers(self):
        self.players = {x : Player(1,"name",x) for x in range(1,5)}

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

    def run(self):
       
        self.Gui.run()
def inCircle(p1,p2,r):
    return math.sqrt(pow(p1[0]-p2[0],2)+pow(p1[1]-p2[1],2))<r

engine = Engine(1)
engine.run()
