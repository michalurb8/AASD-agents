import time
from spade import agent,quit_spade

lista = ['frodo', 'gandalf', 'aragorn', 'pippin']
class MyAgent(agent.Agent):
    async def setup(self):
        print("Agent {0} melduje sie".format(str(self.jid)))

agents = []
for name in lista:
    myAgent=MyAgent(name+"@hookipa.net", "polskagora")
    agents.append(myAgent)
    future=myAgent.start()
agents[0].web.start(hostname = "127.0.0.1", port = '10000')
agents[1].web.start(hostname = "127.0.0.1", port = '10001')
agents[2].web.start(hostname = "127.0.0.1", port = '10002')
agents[3].web.start(hostname = "127.0.0.1", port = '10003')
time.sleep(60)
for a in agents:
    a.stop()
quit_spade()