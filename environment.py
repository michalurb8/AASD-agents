
import logging, time, math
from logging import Logger
from spade import quit_spade
from spade.template import Template
from spade.agent import Agent
from spade_fix.behaviour import CyclicBehaviour
from defaults import PROJECT_VARS
from surface import Surface
import numpy as np
from abc import abstractmethod
from utils import prepareDefaultLogger

ENV_TIME_SIM_SECONDS = 'simulated_runtime'
ENV_TIME_RUNTIME_SECONDS = 'runtime'
ENV_TEST_END_SECONDS = 5

class FPS():
    def __init__(self, oneSecond=1.) -> None:
        self.oneSecond = oneSecond

        self.lastT = 0.
        self.frameCounter = 0
        self.lastFPS = 0.

    def get(self):
        return self.lastFPS

    def __call__(self) -> None:
        current = time.time_ns()
        self.frameCounter += 1
        if(self.lastT + self.oneSecond * 1e+9 < current):
            calcSecond = (current - self.lastT) * 1e-9 * self.oneSecond
            self.lastFPS = self.frameCounter / calcSecond
            self.frameCounter = 0
            self.lastT = current

class CyclicLogger():
    def __init__(self, logger: Logger, loggerPrefix: str, timeout: int=1e+9) -> None:
        self.logger = logger
        self.loggerPrefix = loggerPrefix
        self.timeout = timeout
        self.storedData = {}
        self.lastLogTime = time.time_ns()

    def add(self, **kwargs) -> None:
        self.storedData = self.storedData | dict(kwargs)

    def tryFlush(self) -> None:
        if(time.time_ns() - self.lastLogTime >= self.timeout):
            s = f"{self.loggerPrefix} "
            for k, v in self.storedData.items():
                s += f"-{k}: {v} "
            self.logger.info(s)
            self.lastLogTime = time.time_ns()
            self.storedData = {}

class TimeBehaviour(CyclicBehaviour):
    def __init__(self, logger, loggerPrefix: str, sleepType: str, envTicks: float, envSimSpeed: float):
        super().__init__()
        self._firstRun = False
        self.cyclicLogger = CyclicLogger(logger=logger, loggerPrefix=loggerPrefix, timeout=1e+9 - 1e+8)
        self.logger = logger
        self.loggerPrefix = loggerPrefix
        self.sleepType = sleepType
        self.envTicks = envTicks
        self.envSimSpeed = envSimSpeed

    async def on_start(self) -> None:
        self.logger.info(f"Starting cyclic behaviour {self.loggerPrefix}. . .")

        if(self.sleepType.upper() == 'SLEEP'):
            self.sleepTypeF = TimeBehaviour.sleep_f
        elif(self.sleepType.upper() == 'LOOP'):
            self.sleepTypeF = TimeBehaviour.loop_f
        else:
            raise Exception(f"Unknown sleep type: {self.sleepType}")

        self.stepCounter = 0
        self.fps = FPS()
        self.startTimeRuntime = time.time_ns()
        self.currentTime = None

        self._initKnowledgeItems()

    def sleep_f(next_update_time):
        diff = next_update_time - time.time_ns()
        if(diff <= 0.): # better than max(diff, 0.)
            time.sleep(diff)

    def loop_f(next_update_time):
        while True:
            if time.time_ns() >= next_update_time:
                break
    
    def _customAwait(self): 
        nanosecInSec = 1e+9
        # scale based on one second
        scale = 1. / self.envTicks
        next_update_time = self.currentTime + nanosecInSec * scale
        #next_second = float(math.ceil(t / nanosecInSec))
        #next_update_time = next_second - nanosecInSec * scale
        self.sleepTypeF(next_update_time)

    def _setKnowledgeItems(self):
        runtime = self._calcRuntime()
        simtime = self._calcSimulatedTime()
        fps = self.fps.get()
        self.set('fps', fps)
        self.set('stepCounter', self.stepCounter)
        self.set(ENV_TIME_RUNTIME_SECONDS, runtime)
        self.set(ENV_TIME_SIM_SECONDS, simtime)

        self.cyclicLogger.add(
            runtime=runtime, 
            simulatedSec=simtime, 
            step=self.stepCounter,
            fps=self.fps.get(),
        )
        self.cyclicLogger.tryFlush()

    def _initKnowledgeItems(self):
        self.set('fps', 0.)
        self.set('stepCounter', self.stepCounter)
        self.set(ENV_TIME_RUNTIME_SECONDS, 0.)
        self.set(ENV_TIME_SIM_SECONDS, 0.)

    def _calcRuntime(self) -> float:
        return (time.time_ns() - self.startTimeRuntime) * 1e-9

    def _calcSimulatedTime(self) -> float:
        scale = self.envSimSpeed / self.envTicks
        return (time.time_ns() - self.startTimeRuntime) * 1e-9 * scale

    def isSetup(self) -> bool:
        return self._firstRun

    def startRun(self) -> None:
        self.currentTime = time.time_ns()
        self.stepCounter += 1
        self.fps()

    @abstractmethod
    def middleRun(self) -> None:
        pass

    def endRun(self) -> None:
        self._setKnowledgeItems()
        self._firstRun = True
        self._customAwait()    

    async def run(self):
        self.startRun()

        self.middleRun()
        
        self.endRun()

class GlobalEnvTimeBehaviour(TimeBehaviour):
    def middleRun(self) -> None:
        pass

class GlobalEnvironmentAgent(Agent):
    async def setup(self):
        self.logger = prepareDefaultLogger(loggerName=PROJECT_VARS['GLOB_ENV_LOGGER_NAME'], name = 'globalEnv.log')

        self.logger.info("Agent starting . . .")
        self.timebehav = GlobalEnvTimeBehaviour(
            logger=self.logger,
            loggerPrefix="Global Environment",
            envSimSpeed=PROJECT_VARS['ENV_SIM_SPEED'],
            envTicks=PROJECT_VARS['ENV_TICKS'],
            sleepType=PROJECT_VARS['ENV_SLEEP_TYPE'],
        )
        self.add_behaviour(self.timebehav)

        self.surface = Surface()

    def isSetup(self):
        """
            Check if the setup of the environment behaviour is done.
            Use this as:
            
            while envAgent.isSetup():
                continue
        """
        return not self.timebehav.isSetup()

    async def addAgent(self, agent, typee:str, id, startPos=None) -> bool:
        if(typee == 'mobile'):
            return self.surface.addMobileAgent(agent=agent, id=id, startPos=startPos)
        elif(typee == 'static'):
            return self.surface.addStaticAgent(agent=agent, id=id)
        else:
            raise Exception(f"Unknown type: {typee}")

    async def getAgentPosition(self, id):
        return self.surface.getPosition(id)

    async def setAgentVector(self, id, vector: np.ndarray[np.float32]) -> np.ndarray[np.float32]:
        return self.surface.move(id=id, vector=vector)

    async def setAgentPosition(self, id, position: np.ndarray[np.float32]):
        return self.surface.setPosition(id=id, position=position)

    async def findMobileAgents(self, position: np.ndarray[np.float32], radius: float) -> list[(id, Agent)]:
        return self.surface.findMobileAgents(position=position, radius=radius)

    async def findStaticAgents(self, position: np.ndarray[np.float32], radius: float) -> list[(id, Agent)]:
        return self.surface.findStaticAgents(position=position, radius=radius)

    async def findAgents(self, position: np.ndarray[np.float32], radius: float) -> list[(id, Agent)]:
        return self.surface.findAgents(position=position, radius=radius)

class LocalEnvironment(Agent):
        
    async def setup(self) -> None:
        self.logger = prepareDefaultLogger(loggerName=PROJECT_VARS['LOCAL_ENV_LOGGER_NAME'], name = f'localEnv.{self.name}.log')

        self.logger.info(f"Agent {self.name} starting . . .")
        self.timebehav = GlobalEnvTimeBehaviour(
            logger=self.logger,
            loggerPrefix=f"Local Environment of agent {self.name}",
            envSimSpeed=PROJECT_VARS['ENV_SIM_SPEED'],
            envTicks=PROJECT_VARS['ENV_TICKS'],
            sleepType=PROJECT_VARS['ENV_SLEEP_TYPE'],
        )
        self.add_behaviour(self.timebehav)

    def isSetup(self):
        """
            Check if the setup of the environment behaviour is done.
            Use this as:
            
            while envAgent.isSetup():
                continue
        """
        return not self.timebehav.isSetup()

    async def getPosition(self) -> np.ndarray[np.float32]:
        pass

    async def getTemperature(self) -> float:
        pass

    async def getPulse(self) -> float:
        pass

    async def getBloodPressure(self) -> float:
        pass

    async def getAcceleration(self) -> np.ndarray[np.float32]:
        pass

if __name__ == "__main__":
    envAgent = GlobalEnvironmentAgent(
        PROJECT_VARS['ENV_AGENT_NAME'] + '@' + PROJECT_VARS['SERVER'], 
        PROJECT_VARS['ENV_PASSW']
    )
    future = envAgent.start()
    future.result()
    
    while envAgent.isSetup():
        continue

    try:
        while(True):
            simSec = envAgent.get(ENV_TIME_SIM_SECONDS)
            runtime = envAgent.get(ENV_TIME_RUNTIME_SECONDS)
            fps = envAgent.get('fps')
            counter = envAgent.get('stepCounter')
            print(f'Env runtime: {runtime} \t SimulatedSec: {simSec} \t fps: {fps} \t counter: {counter}')
            if(runtime >= ENV_TEST_END_SECONDS):
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    envAgent.stop()
    
    quit_spade()