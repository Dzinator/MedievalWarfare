class DateTime :
	def now():
		return;
		
from enum import Enum
ActionType = Enum('ActionType', 'buildingRoad choppingTree clearingTombstone upgradingCombining cultivating1 cultivating2 ready')

TerrainType = Enum('TerrainType', 'sea grass tree meadow')