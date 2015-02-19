from GUI import Gui
import math, random, heapq

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
        self.gold = 100
        self.wood = 10
        self.hex = h
        self.units = []
        self.owner = p
        self.territory = t
        for h in t:
            h.village = self
            
    def killUnits(self):
        for unit in self.units:
            unit.hex.hasTombstone =True
            unit.hex.occupant = None

        del self.units[:]
        self.units = []

    def killUnit(self,unit):
        unit.hex.occupant =None
        self.units.remove(unit)

    def spawnUnit(self,h,t):
        if self.gold >=Unit.costs[t]:
            self.units.append(Unit(t,h,self))
            self.gold-=Unit.costs[t]
            if h.hasTree:
                self.units[-1].gatherWood()

    def upgrade(self):
        if self.type<2 and self.wood>=8:
            self.type+=1
            self.wood-=8

    def addVillage(self, v):
        self.gold+= v.gold
        self.wood +=v.wood
        for t in v.territory:
            self.territory.append(t)
            t.village = self
        for u in v.units:
            self.units.append(u)
            u.village = self

    def canCombinetoInfantry(self, unit1, unit2):
        if not unit2 or not unit1:
            return False
        return (unit1 in self.units and unit2 in self.units and unit1.type == unit2.type == 0)

    def canCombinetoSoldier(self, unit1, unit2):
        if not unit2 or not unit1:
            return False
        return (self.type>0 and unit1 in self.units and unit2 in self.units and ((unit1.type == 1 and unit2.type ==0) or (unit1.type == 0 and unit2.type ==1)))

    def canCombinetoKnight(self, unit1, unit2):
        if not unit2 or not unit1:
            return False
        return (self.type>1 and unit1 in self.units and unit2 in self.units and (((unit1.type == 2 and unit2.type ==0) or (unit1.type == 0 and unit2.type ==2)) or (unit1.type == unit2.type == 1)))

    def combine(self,unit1, unit2):
        if not unit2 or not unit1:
            return False
        if self.canCombinetoInfantry(unit1,unit2):
            unit1.type=1
            unit2.hex.occupant = None
            self.units.remove(unit2)
            del unit2
        elif self.canCombinetoSoldier(unit1,unit2):
            unit1.type=2
            unit2.hex.occupant = None
            self.units.remove(unit2)
            del unit2
        elif self.canCombinetoKnight(unit1,unit2):
            unit1.type=3
            unit2.hex.occupant = None
            self.units.remove(unit2)
            del unit2

class Unit:
    upkeeps = {0 : 2, 1:6, 2: 18, 3:54}
    costs = {0:10,1:20,2:30,3:40}
    def __init__(self, ut, h, v):
        self.type = ut
        self.currentAction = 'ready'
        self.cost = 0 #have cost array by unittype
        self.hex = h
        self.village = v
        self.moved = False
        h.occupant = self

    def update(self):
        pass

    def setBuildingRoad(self):
        pass

    def getUpkeep(self):
        return upkeeps[self.type]

    def buildRoad(self):
        self.hex.putRoad()

    def buildMeadow(self):
        self.hex.hasMeadow = True
        self.moved = True

    def upgrade(self, newLevel):
        if 4>newLevel>self.type<3 and self.village.gold>=10*(newLevel-self.type):
            self.village.gold-= 10*(newLevel-self.type)
            self.type=newLevel

    def gatherWood(self):
        self.village.wood+=1
        self.hex.removeTree()

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
        self.parent = None
        self.owner = random.randint(1,4) if not self.water else 0

    def removeTomb(self):
        self.hasTombstone = False

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
        if self.village.wood>=5:
            self.hasTree = False
            self.hasWatchTower = True
            self.village.wood-=5

    def trample(self):
        self.hasMeadow = False

class Grid:
    def __init__(self, mapId, width, height, engine, mapInfo = None):
        self.Id = mapId
        self.engine = engine
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

    def Astar(self, start, target):
        path, unchecked, checked, start.parent = [],[],[],None
        heapq.heappush(unchecked,(abs(start.centre[0]-target.centre[0])+abs(start.centre[1]-target.centre[1]),0, start.number, start))
        while len(unchecked)>0:
            best = heapq.heappop(unchecked)
            checked.append(best)   
            if best[3] == target:
                break
            if best[3].owner == start.owner and not best[3].hasTree:
                for node in best[3].neighbours:
                    if not any([node == item[3] for item in checked]) and not any([node == item[3] for item in unchecked]) and not node.occupant and not (start.occupant.type ==3 and node.hasTree) and not (node.village == start.village and node.village and node.village.hex == node):
                        node.parent = best
                        heapq.heappush(unchecked,((abs(node.centre[0]-target.centre[0])
                                                  +abs(node.centre[1]-target.centre[1])
                                                  +(best[1]))*(100 if start.occupant.type>1 and node.hasMeadow else 1),
                                                  best[1]+abs(node.centre[0]-best[3].centre[0])
                                                  +abs(node.centre[1]-best[3].centre[1]) ,node.number, node))
        if len(unchecked)==0:
            return []
        if best[3].owner == start.owner or self.engine.canCapture(best[3], start.occupant):
            path.append(best[3])
        while(best[3].parent):
            best = best[3].parent
            path.append(best[3])
        path.reverse()
        return path

class Engine:
    def __init__(self, Id):
        self.gameId = Id
        self.turn = 0;
        self.roundsPlayed = 0
        self.initPlayers()
        self.width = 1600
        self.height = 900
        self.grid = Grid(1, self.width, self.height, self)
        self.grid.populateMap(self.players)
        self.Gui = Gui(self, self.width, self.height)
    
    def initPlayers(self):
        self.players = {x : Player(1,"name",x) for x in range(1,5)}

    def buildRoad(self, unit):
        pass

    def canCapture(self, h, unit):
        if not h.village:
            return True
        if unit.type==0:
            return False
        if unit.type == 1 and h.village.hex == h:
            return False
        if (h.occupant and h.occupant.type>unit.type) or (h.hasWatchTower and unit.type==1) or (h.village.type ==2 and h==h.village.hex and unit.type<3):
                return False
        for g in h.neighbours:
            if(g.occupant and g.occupant.type>unit.type and g.village.owner == h.village.owner) or (g.hasWatchTower and unit.type==1 and g.village.owner == h.village.owner) or (h.village.type ==2 and g==h.village.hex and unit.type<3):
                return False
        return True

    def join(self, h, unit):
        joinVillages = {g.village for g in  h.neighbours if g.village and g.village.owner == unit.village.owner}

        if len(joinVillages)>1:
            temp = max(joinVillages, key = lambda v: v.type)
            temp2 = [t for t in joinVillages if t.type == temp.type]
            main = max(temp2, key = lambda v: len(v.territory))
            joinVillages.remove(main)
            for v in joinVillages:
                main.addVillage(v)
                v.hex.hasMeadow = True
                main.owner.villages.remove(v)
            del list(joinVillages)[:]

    def splitTerritory(self,h,unit):
        splitStarts = [g for g in h.neighbours if g.village == h.village]

        #maybe fix later
        if len(splitStarts)>=2:
            temp = self.grid.BFS(splitStarts[0], lambda g: True if g != splitStarts[0] else False, lambda g: True if g in splitStarts else False)
            for x in temp:
                splitStarts.remove(x)
        if len(splitStarts)>=2:
            temp = self.grid.BFS(splitStarts[1], lambda g: True if g != splitStarts[1] else False, lambda g: True if g in splitStarts else False)
            for x in temp:
                splitStarts.remove(x)

        splitTerrities = [self.grid.BFS(start, lambda g: True, lambda g: True if g.village == start.village and g != h else False) for start in splitStarts]

        for split in splitTerrities:
            if len(split)<3:
                for g in split:
                    h.village.territory.remove(g)
                    g.village = None
                    g.owner = 0
            elif h.village.hex not in split:
                h.village.owner.addVillage(Village(random.choice(split), h.village.owner, split))
                for g in split:
                    h.village.territory.remove(g)

        if h.occupant:
            h.village.killUnit(h.occupant)
            del h.occupant
            h.occupant = None
        h.village.territory.remove(h)
        if h.village.hex == h and len(h.village.territory)>2:
            h.village.hex = random.choice(h.village.territory)
        if h.village.hex.owner ==0 or h.village.hex == h:
            h.village.owner.villages.remove(h.village)
            h.village.killUnits()
            if h.village.hex != h:
                h.village.hex.hasTree = True
            if h.village.hex == h:
                unit.village.gold += h.village.gold
                unit.village.wood += h.village.wood
                h.hasMeadow = True
            del h.village

    def movePath(self, h, unit):
        path = self.grid.Astar(unit.hex, h)
        if unit.type>=2:
            for h in path[1:]:
                if h.hasMeadow and not h.hasRoad:
                    h.trample()

        return self.moveUnit(h, unit)
                    
    def moveUnit(self, h, unit):
        ret = False
        if unit.moved:
            return False
        if h.hasTree and unit.type == 3:
            return False
        if h.village == unit.village and not h.occupant:
            unit.hex.occupant = None
            unit.hex = h
            h.occupant = unit
            ret = True
        elif not h.village and not h.occupant:
            self.join(h,unit)
            unit.hex.occupant = None
            unit.hex = h
            unit.village.territory.append(h)
            h.village = unit.village
            h.owner = unit.village.hex.owner
            h.occupant = unit
            ret = True
        elif self.canCapture(h, unit):
            self.join(h,unit)
            self.splitTerritory(h,unit)
            unit.hex.occupant = None
            unit.hex = h
            unit.village.territory.append(h)
            h.village = unit.village
            h.owner = unit.village.hex.owner
            h.occupant = unit
            h.hasWatchTower = False
            ret = True
        if h.hasTree and unit.type<3:
            unit.gatherWood()
        if h.hasTombstone and unit.type<3:
            h.removeTomb()
        return ret
    def newGame(self, players, mapData):
        pass

    def tombPhase(self, player):
        for v in player.villages:
            for t in v.territory:
                t.removeTombstone()
                t.putTree()

    def buildPhase(self,player):
        pass

    def incomePhase(self,player):
        for v in player.villages:
            v.gold += sum(t.getIncome() for t in v.territory)

    def paymentPhase(self, player):
        for v in player.villages:
            v.gold -= sum(u.getUpkeep() for u in v.units)

    def beginTurn(self, player): #player or turn?
        #recieve data beforehand
        self.tombPhase(player)
        self.buildPhase(player)
        self.incomePhase(player)
        self.paymentPhase(player)
        for v in player.villages:
            for u in v.units:
                u.moved = False
        self.turn = True

    def endTurn(self):
        self.turn = False
        #sen data

    def run(self):
        self.Gui.run()

def inCircle(p1,p2,r):
    return math.sqrt(pow(p1[0]-p2[0],2)+pow(p1[1]-p2[1],2))<r

engine = Engine(1)
engine.run()
