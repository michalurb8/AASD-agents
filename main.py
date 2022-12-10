import time

from aioxmpp import PresenceShow, PresenceState
from spade import quit_spade

from MyAgent import MyAgent
from TestAgent import TestAgent


def main():
    agents_names = ['frodo', 'aragorn', 'pippin', 'sam']

    agents = create_agents(agents_names)
    start_agents(agents)
    for a in agents:
        print(f'{a.jid} alive: {a.is_alive()}; available: {a.presence.is_available()}')
    start_web_interface(agents)

    gandalf = TestAgent("gandalf@hookipa.net", "polskagora")
    future = gandalf.start()
    future.result()

    gandalf.presence.subscribe(str(agents[0].jid))
    agents[0].presence.subscribe(str(gandalf.jid))

    print("Wait until user interrupts with ctrl+C")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")

    for a in agents:
        a.stop().result()
        print(f'{a.jid} alive: {a.is_alive()}; available: {a.presence.is_available()}')
    quit_spade()


def create_agents(defined_agents):
    return [MyAgent(f'{name}@hookipa.net', 'polskagora') for name in defined_agents]


def start_agents(agents):
    for agent in agents:
        future = agent.start()
        future.result()


def start_web_interface(agents):
    for index, agent in enumerate(agents):
        agent.web.start(hostname='127.0.0.1', port=10000 + index)
        agent.presence.set_available(show=PresenceShow.CHAT)
        agent.presence.set_presence(state=PresenceState(True, PresenceShow.CHAT), status="Lunch", priority=2)


if __name__ == '__main__':
    main()
