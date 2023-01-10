import time
from spade import agent, quit_spade
from aioxmpp import PresenceShow
import defaults

import signal, sys

def signal_handler(sig, frame):
    print('\nAll agents will be closed')
    for a in agents:
        a.stop()
    quit_spade()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

lista = ['frodo', 'gandalf', 'aragorn', 'pippin']
lista = ['frodo', 'gandalf']
class MyAgent(agent.Agent):
    async def setup(self) -> None:
        print("Agent {0} melduje sie".format(str(self.jid)))
        self.presence.set_available(show = PresenceShow.CHAT)

agents = []
for name in lista:
    # verify_security = False - ważne z powodu braku certyfikatu serwera
    # lub tego, że certyfikat jest podpisany przez samego siebie.
    myAgent=MyAgent(name + '@' + defaults.PROJECT_VARS['SERVER'], "polskagora", verify_security=False)
    agents.append(myAgent)
    future=myAgent.start()
    future.result()


agents[0].web.start(hostname = "localhost", port = '10000')
agents[1].web.start(hostname = "localhost", port = '10001')
agents[0].presence.subscribe(str(agents[1].jid))
agents[1].presence.subscribe(str(agents[0].jid))

#agents[0].presence.unsubscribe(str(agents[1].jid))
#agents[1].presence.unsubscribe(str(agents[0].jid))


print("sleep start")
time.sleep(120)
for a in agents:
    a.stop()
quit_spade()