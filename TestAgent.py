from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message


class TestAgent(Agent):
    class InformBehav(OneShotBehaviour):
        async def run(self):
            print("InformBehav running")
            msg = Message(to="frodo@hookipa.net")
            msg.body = "Hello from Python"

            await self.send(msg)
            print("Message sent!")
            self.exit_code = "Job Finished!"
            await self.agent.stop()

    async def setup(self):
        print("Agent {0} melduje sie".format(str(self.jid)))
        print("SenderAgent started")
        self.b = self.InformBehav()
        self.add_behaviour(self.b)
