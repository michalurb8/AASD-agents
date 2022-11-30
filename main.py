import time
from spade import agent, quit_spade
from aioxmpp import PresenceShow

lista = ['frodo', 'gandalf', 'aragorn', 'pippin']
lista = ['frodo', 'gandalf']
class MyAgent(agent.Agent):
    async def setup(self) -> None:
        print("Agent {0} melduje sie".format(str(self.jid)))
        self.presence.set_available(show = PresenceShow.CHAT)

agents = []
for name in lista:
    myAgent=MyAgent(name+"@hookipa.net", "polskagora")
    agents.append(myAgent)
    future=myAgent.start()
    future.result()

agents[0].web.start(hostname = "127.0.0.1", port = '10000')
agents[1].web.start(hostname = "127.0.0.1", port = '10001')
agents[0].presence.subscribe(str(agents[1].jid))
agents[1].presence.subscribe(str(agents[0].jid))
time.sleep(120)
for a in agents:
    a.stop()
quit_spade()