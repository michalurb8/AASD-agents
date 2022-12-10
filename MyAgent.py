from aioxmpp import PresenceShow
from spade import agent


class MyAgent(agent.Agent):
    async def setup(self) -> None:
        print("Agent {0} melduje sie".format(str(self.jid)))
        self.presence.set_available(show=PresenceShow.CHAT)
