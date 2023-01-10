from spade.agent import Agent
import numpy as np
from defaults import PROJECT_VARS
import threading as th

import logging


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

class Surface():
    def __init__(self) -> None:
        self.agents = {}
        self.mobileAgentArray = {}
        self.staticAgentArray = {}
        self.lock = th.Lock()

        self.tiles = []

    def addMobileAgent(self, agent: Agent, id, startPos: np.ndarray[np.float32]) -> bool:
        self.lock.acquire()
        if(id in self.agents):
            self.lock.release()
            return False
        tmp = MobileAgent(agent=agent, position=startPos)
        self.agents[id] = ('m', tmp)
        self.mobileAgentArray[id] = tmp
        self.lock.release()
        return True

    def addStaticAgent(self, agent: Agent, id, position: np.ndarray[np.float32]) -> bool:
        self.lock.acquire()
        if(id in self.agents):
            self.lock.release()
            return False
        tmp = StaticAgent(agent=agent)
        self.agents[id] = ('s', tmp)
        self.staticAgentArray[id] = tmp
        self.lock.release()
        return True

    def removeAgent(self, id) -> None:
        self.lock.acquire()
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
        self.lock.release()

    def getPosition(self, id) -> np.ndarray[np.float32]:
        self.lock.acquire()
        tmp = self.agents[id][1].getPosition()
        self.lock.release()
        return tmp

    def move(self, id, vector: np.ndarray[np.float32]) -> np.ndarray[np.float32]:
        self.lock.acquire()
        self.agents[id][1].move(vector)
        self.lock.release()

    def setPosition(self, id, position: np.ndarray[np.float32]):
        self.lock.acquire()
        self.agents[id][1].setPosition(position)
        self.lock.release()
    
    def _findAgents(self, position, radius, agentDict) -> list[(id, Agent)]:
        self.lock.acquire()
        toReturn = []
        for id, (_, agent) in agentDict.items():
            if(np.linalg.norm(position - agent.getPosition()) < radius):
                toReturn.append((id, agent))
        self.lock.release()
        return toReturn

    def findMobileAgents(self, position: np.ndarray[np.float32], radius: float) -> list[(id, Agent)]:
        return self._findAgents(position, radius, agentDict=self.mobileAgentArray)

    def findStaticAgents(self, position: np.ndarray[np.float32], radius: float) -> list[(id, Agent)]:
        return self._findAgents(position, radius, agentDict=self.staticAgentArray)

    def findAgents(self, position: np.ndarray[np.float32], radius: float) -> list[(id, Agent)]:
        tmp = self.findMobileAgents(position, radius)
        tmp.extend(self.findStaticAgents(position, radius))
        return tmp
