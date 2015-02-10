from BusinessLogic import Player, Map, Village, Hex, Unit, Peasant, Infantry, Knight, Soldier

#define variables------------------

#integers
gameID	
turn
roundsPlayed

#players
players
#----------------------------------

#functions-------------------------
def initPlayers():
	return; #Player list

def buildRoad(unit):
	myHex = getMyHex()
	isRoad = hasRoad()
	if(isRoad)
		return;
	type = getType()
	
	if type == 'peasant'
		type.setBuildingRoad()
			buildRoad(1)
		setCurrentAction(ActionType.BUILDINGROAD)
	
	return;

def upgradeVillage(village):
	type = getType()
	wood = getWood()
	
	if(type == 'fort')
		return;
	if(wood < 8)
		return
	if type == 'hovel'
		setType('town')
	else if type == 'town'
		setType('fort')
	wood = wood - 8
	setWood(wood)	
	return;
	
def upgradeUnit(unit, newLevel):
	village = getVillage()
	gold = getGold()
	upgradePrice = upgradePrice(newLevel)
	if(gold < upgradePrice)
		return
	type = getType()
	if(type == newLevel)
		return
	setType(newLevel)
	gold = gold - upgradePrice
	setGold(gold)
	return;
	
def takeOver(hex, unit):
	enemyVillage = getVillage()
	if enemyVillage.getMyLocation == hex
		myVillage = getMyVillage()
		gold = getGold()
		wood = getWood()
		addGold(gold)
		addWood(wood)
		setMyType(TerrainType.MEADOW)
		setVillage(myVillage)
	return;

def moveUnit(hex, unit):
	myVillage = getMyVillage()
	myHex = getMyHex()
	path = getPath(myHex, hex)
	if path == null
		return false;
	if unit.getType() == 'knight'
		trample(path)
	if hex.hasTree()
		addWood(1)
		removeTree()
	if hex.hasTomb()
		removeTomb()
	canCapture = canCapture(unit, hex)
	addHex(hex)
	setVillage(myVillage)
	moveUnit2 = moveUnit2(unit, hex)
	return; #boolean

def getPath(hex1, hex2):
	return; #Hex list
	
def newGame(participants, mapData):

	players = initPlayers()
	for p in participants
		player = create(participants)
	map = create(mapData, players)
	for hexs in map
		setMyHex(mapDate)
	populateMap(players)
	#compute territory
	for hex in territory
		addHex(myHex)
	for area in territory
		area = create(players)	
	return;

def beginTurn(engine, player):
	#replaceTombs
	for hex in myTerritory
		isTomb = hasTombstone()
		if(isTomb)
			removeTomb()
			putTree()
	#buildPhase
	for unit in myUnits
		currentAction = getCurrentAction()
		myHex = getMyHex()
		
		if currentAction ==  BUILDINGROAD
			putRoad()
			setCurrentAction(ActionType.READY)
		else if currentAction == CULTIVATING1
			setCurrentAction(ActionType.CULTIVATING2)
		else if currentAction == CULTIVATING2
			setMyType(TerrainType.MEADOW)
			setCurrentAction(ActionType.READY)
		else 
			setCurrentAction(ActionType.READY)
	#incomePhase
	for village in myVillages
		hexs = getHexs()
		gold = getGold()
		
		for hex in hexs
			income = getIncome()
			gold = gold + income
			setGold(gold)
	#paymentPhase
	for v in myVillages
		gold = getGold()
		units = getUnits()
		totalCost = 0
		
		for u in units
			cost = getCost()
			totalCost = totalCost + cost
		
		if(gold < totalCost)
			killUnits()
		else 
			gold = gold - totalCost
			setGold(gold)
			
		
	return;
	
def getMyMap():
	return; #Map
	
def setMyMap():
	return;
	
def moveUnit2(hex, unit):
	return; #boolean
	
#----------------------------------	
