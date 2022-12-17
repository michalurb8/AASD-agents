
import logging, time, math
from spade import quit_spade
from spade.template import Template
from spade.agent import Agent
from spade_fix.behaviour import CyclicBehaviour
import defaults

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

        async def on_start(self) -> None:
            self.logger = logging.getLogger(defaults.PROJECT_VARS['ENV_LOGGER_NAME'])
            self.logger.info("Starting behaviour . . .")

            if(defaults.PROJECT_VARS['ENV_SLEEP_TYPE'] == 'SLEEP'):
                self.sleepTypeF = EnvironmentAgent.TimeBehav.sleep_f
            elif(defaults.PROJECT_VARS['ENV_SLEEP_TYPE'] == 'LOOP'):
                self.sleepTypeF = EnvironmentAgent.TimeBehav.loop_f
            else:
                raise Exception('Unknown sleep type')

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
            scale = defaults.PROJECT_VARS['ENV_UPDATE_SPEED'] / defaults.PROJECT_VARS['ENV_TICKS']
            next_update_time = self.currentTime + nanosecInSec * scale
            #next_second = float(math.ceil(t / nanosecInSec))
            #next_update_time = next_second - nanosecInSec * scale
            self.sleepTypeF(next_update_time)

        def _setKnowledgeItems(self):
            runtime = self._calcRuntime()
            simtime = self._calcSimulatedRuntime()
            fps = self.fps.get()
            self.set('fps', fps)
            self.set('stepCounter', self.stepCounter)
            self.set(ENV_TIME_RUNTIME_SECONDS, runtime)
            self.set(ENV_TIME_SIM_SECONDS, simtime)

            self.logger.info(f"Environment -step: {self.stepCounter} -fps: {self.fps.get()}"
                + f" -simulatedSec: {simtime} -runtime {runtime}")

        def _initKnowledgeItems(self):
            self.set('fps', 0.)
            self.set('stepCounter', self.stepCounter)
            self.set(ENV_TIME_RUNTIME_SECONDS, 0.)
            self.set(ENV_TIME_SIM_SECONDS, 0.)

        def _calcRuntime(self) -> float:
            return (time.time_ns() - self.startTimeRuntime) * 1e-9

        def _calcSimulatedRuntime(self) -> float:
            scale = defaults.PROJECT_VARS['ENV_TICKS'] / defaults.PROJECT_VARS['ENV_UPDATE_SPEED']
            return (time.time_ns() - self.startTimeRuntime) * 1e-9 * scale

        async def run(self):
            self.currentTime = time.time_ns()
            self.stepCounter += 1
            self.fps()

            self._setKnowledgeItems()
            self._firstRun = True
            self._customAwait()        

    async def setup(self):
        self.logger = logging.getLogger(defaults.PROJECT_VARS['ENV_LOGGER_NAME'])

        self.logger.info("Agent starting . . .")
        self.timebehav = self.TimeBehav()
        self.add_behaviour(self.timebehav)

    def isSetup(self):
        """
            Check if the setup of the environment behaviour is done.
            Use this as:
            
            while envAgent.isSetup():
                continue
        """
        return not self.timebehav._firstRun

if __name__ == "__main__":
    envAgent = EnvironmentAgent(
        defaults.PROJECT_VARS['ENV_AGENT_NAME'] + '@' + defaults.PROJECT_VARS['SERVER'], 
        defaults.PROJECT_VARS['ENV_PASSW']
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