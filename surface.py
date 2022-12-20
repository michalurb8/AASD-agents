from typing import Tuple
from spade.agent import Agent
import numpy as np
from defaults import PROJECT_VARS
from typing import NewType

import logging

ndTile = NewType('Tile', int)

class StaticAgent():
    def __init__(self, agent: Agent, position: np.ndarray[np.float32]) -> None:
        self.agent = agent
        self.position = position

    def getPosition(self) -> np.ndarray[np.float32]:
        return self.position

    def setPosition(self, position: np.ndarray[np.float32]):
        self.position = position

    def move(self, vector: np.ndarray[np.float32]) -> np.ndarray[np.float32]:
        logger = logging.getLogger(PROJECT_VARS['ENV_LOGGER_NAME'])
        logger.info(f"Tried to move static agent by {vector}")
        return self.position

class MobileAgent(StaticAgent):
    def __init__(self, agent: Agent, position: np.ndarray[np.float32], moveF: None) -> None:
        super().__init__(agent=agent, position=position)
        self.moveF = moveF if moveF is not None else lambda vec, pos: pos + vec

    def move(self, vector: np.ndarray[np.float32]) -> np.ndarray[np.float32]:
        self.position = self.moveF(pos=self.position, vec=vector)
        return self.getPosition()

class SquareArea():
    def __init__(self, upperLeftPos: np.ndarray[np.float32], length: float) -> None:
        self.vertices = [
            upperLeftPos,
            np.array((upperLeftPos[0] + length, upperLeftPos[1] - length)),
        ]
        self.length = length
        self.dVector = {
            1: (0., self.length),
            2: (-self.length, 0.),
            3: (0., -self.length),
            4: (self.length, 0.),
        }

    def contain(self, position: np.ndarray[np.float32]) -> bool:
        return self.vertices[0][0] < position[0] and self.vertices[0][1] > position[1] \
            and self.vertices[1][0] > position[0] and self.vertices[1][1] > position[1]

    def relativePosition(self, position: np.ndarray[np.float32]) -> int:
        '''
            0 - inside
            1 - upper
            2 - left
            3 - bottom
            4 - right
        '''
        return (self.vertices[0][1] < position[1]) + \
            (self.vertices[0][0] > position[0]) * 2 + \
            (self.vertices[1][1] > position[1]) * 3 + \
            (self.vertices[1][0] < position[0]) * 4

    def getNewUpperLeftPosition(self, idx) -> np.ndarray[np.float32]:
        '''
            1 - upper
            2 - left
            3 - bottom
            4 - right
        '''
        vec = self.dVector[idx]
        return self.vertices[0] + vec


class TileConstructor():
    def __init__(self) -> None:
        pass

    def _addAgent(self, id, agent: Agent, position: np.ndarray[np.float32], fromWhere: ndTile, toWhere: int) -> ndTile:
        newTile = Tile(
            upperLeftPos=np.array(fromWhere.area.getNewUpperLeftPosition(toWhere)),
            length=fromWhere.area.length,
        )
        fromWhere.borderTiles[toWhere] = newTile
        newTile.borderTiles[ (toWhere + 1) % 4 + 1 ] = fromWhere
        """
        dReverse = {
            1: 3,
            2: 4,
            3: 1,
            4: 2
        }
        """

        return newTile.addAgent(
            id=id,
            agent=agent,
            position=position
        )

class Tile():
    def __init__(
        self, 
        upperLeftPos: np.ndarray[np.float32], 
        length: float, 
        upperTile=None, 
        leftTile=None, 
        bottomTile=None,
        rightTile=None, 
    ) -> None:
        upperTile = TileConstructor(self) if upperTile is None else upperTile
        leftTile = self if leftTile is None else leftTile
        bottomTile = self if bottomTile is None else bottomTile
        rightTile = self if rightTile is None else rightTile

        self.borderTiles = [self, upperTile, leftTile, bottomTile, rightTile]
        self.area = SquareArea(upperLeftPos=upperLeftPos, length=length)
        self.agents = {}

    def connect(self, tile, where: str):
        d = {
            'up': 1,
            'down': 3,
            'left': 2,
            'right': 4,
        }
        self.borderTiles[d[where]] = tile

    def contain(self, position: np.ndarray[np.float32]) -> bool:
        return self.area.contain(position=position)

    def _addAgent(self, id, agent: Agent, *args, **kwargs) -> ndTile:
        self.agents[id] = agent
        return self

    def addAgent(self, id, agent: Agent, position: np.ndarray[np.float32]) -> ndTile:
        idx = self.area.relativePosition(position)
        return self.borderTiles[idx]._addAgent(
            id=id, 
            agent=agent, 
            position=position, 
            fromWhere=self, 
            toWhere=idx
        )

    def _putAgent(self, id, idx: int) -> ndTile:
        pass

    def move(self, id, vector: np.ndarray[np.float32]) -> ndTile:
        newPos = self.agents[id].move(vector)
        idx = self.area.relativePosition(newPos)
        return self._putAgent(id, idx)

class Surface():
    def __init__(self) -> None:
        self.agents = {}
        self.mobileAgentArray = {}
        self.staticAgentArray = {}

        self.tiles = []

    def addMobileAgent(self, agent: Agent, id, startPos: np.ndarray[np.float32]) -> bool:
        if(id in self.agents):
            return False
        tmp = MobileAgent(agent=agent, position=startPos)
        self.agents[id] = ('m', tmp)
        self.mobileAgentArray[id] = tmp
        return True

    def addStaticAgent(self, agent: Agent, id, position: np.ndarray[np.float32]) -> bool:
        if(id in self.agents):
            return False
        tmp = StaticAgent(agent=agent)
        self.agents[id] = ('s', tmp)
        self.staticAgentArray[id] = tmp
        return True

    def removeAgent(self, id) -> None:
        if(id in self.agents):
            typee, agent = self.agents[id]
            self.agents[id] = None
            if(typee == 'm'):
                self.mobileAgentArray[id] = None
            elif(typee == 's'):
                self.staticAgentArray[id] = None
            else:
                raise Exception(f'Unknown agent type: {typee}')
            agent.stop()

    def getPosition(self, id) -> np.ndarray[np.float32]:
        return self.agents[id][1].getPosition()

    def move(self, id, vector: np.ndarray[np.float32]) -> np.ndarray[np.float32]:
        self.agents[id][1].move(vector)

    def setPosition(self, id, position: np.ndarray[np.float32]):
        self.agents[id][1].setPosition(position)
    
    def _findAgents(self, position, radius, agentDict) -> list[(id, Agent)]:
        toReturn = []
        for id, (_, agent) in agentDict.items():
            if(np.linalg.norm(position - agent.getPosition()) < radius):
                toReturn.append((id, agent))
        return toReturn

    def findMobileAgents(self, position: np.ndarray[np.float32], radius: float) -> list[(id, Agent)]:
        return self._findAgents(position, radius, agentDict=self.mobileAgentArray)

    def findStaticAgents(self, position: np.ndarray[np.float32], radius: float) -> list[(id, Agent)]:
        return self._findAgents(position, radius, agentDict=self.staticAgentArray)

    def findAgents(self, position: np.ndarray[np.float32], radius: float) -> list[(id, Agent)]:
        tmp = self.findMobileAgents(position, radius)
        tmp.extend(self.findStaticAgents(position, radius))
        return tmp
