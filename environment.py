
import logging, time, math
from spade import quit_spade
from spade.template import Template
from spade.agent import Agent
from spade_fix.behaviour import CyclicBehaviour
from defaults import PROJECT_VARS
from surface import Surface
import numpy as np

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
            
class EnvironmentAgent(Agent):
    class TimeBehav(CyclicBehaviour):
        def __init__(self):
            super().__init__()
            self._firstRun = False
            self.lastLogTime = time.time_ns()

            self.behavTemplate = Template()
            self.behavTemplate.thread = "EnvBehaviour"
            self.behavTemplate.metadata = {"performative": "query"}

        async def on_start(self) -> None:
            self.logger = logging.getLogger(PROJECT_VARS['ENV_LOGGER_NAME'])
            self.logger.info("Starting behaviour . . .")

            if(PROJECT_VARS['ENV_SLEEP_TYPE'] == 'SLEEP'):
                self.sleepTypeF = EnvironmentAgent.TimeBehav.sleep_f
            elif(PROJECT_VARS['ENV_SLEEP_TYPE'] == 'LOOP'):
                self.sleepTypeF = EnvironmentAgent.TimeBehav.loop_f
            else:
                raise Exception(f"Unknown sleep type: {PROJECT_VARS['ENV_SLEEP_TYPE']}")

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
            scale = 1. / PROJECT_VARS['ENV_TICKS']
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

            if(time.time_ns() - self.lastLogTime >= 1e+9):
                self.logger.info(f"Environment -step: {self.stepCounter} -fps: {self.fps.get()}"
                    + f" -simulatedSec: {simtime} -runtime {runtime}")
                self.lastLogTime = time.time_ns()

        def _initKnowledgeItems(self):
            self.set('fps', 0.)
            self.set('stepCounter', self.stepCounter)
            self.set(ENV_TIME_RUNTIME_SECONDS, 0.)
            self.set(ENV_TIME_SIM_SECONDS, 0.)

        def _calcRuntime(self) -> float:
            return (time.time_ns() - self.startTimeRuntime) * 1e-9

        def _calcSimulatedTime(self) -> float:
            scale = PROJECT_VARS['ENV_SIM_SPEED'] / PROJECT_VARS['ENV_TICKS']
            return (time.time_ns() - self.startTimeRuntime) * 1e-9 * scale

        async def run(self):
            self.currentTime = time.time_ns()
            self.stepCounter += 1
            self.fps()

            self._setKnowledgeItems()
            self._firstRun = True
            self._customAwait()        

    async def setup(self):
        self.logger = logging.getLogger(PROJECT_VARS['ENV_LOGGER_NAME'])

        self.logger.info("Agent starting . . .")
        self.timebehav = self.TimeBehav()
        self.add_behaviour(self.timebehav)

        self.surface = Surface()

    def isSetup(self):
        """
            Check if the setup of the environment behaviour is done.
            Use this as:
            
            while envAgent.isSetup():
                continue
        """
        return not self.timebehav._firstRun

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

if __name__ == "__main__":
    envAgent = EnvironmentAgent(
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