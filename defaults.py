
import logging

PROJECT_VARS = {
    'SERVER': 'localhost',
    'ENV_PASSW': 'polskagora',
    'ENV_AGENT_NAME': 'environment',
    'ENV_LOGGER_NAME': 'Environment',
    'LOG_LEVEL': logging.INFO,
    'ENV_TICKS': 1.,  # per seconds, env ticks in one update, the more the faster simulation is
    'ENV_UPDATE_SPEED': 1., # per seconds, how often update env in one second, the more the less fps are
    'ENV_SLEEP_TYPE': 'LOOP', # 'SLEEP' or 'LOOP'
}

logging.basicConfig(
    filename='app.log',
    filemode='a',
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt='%H:%M:%S',
    level=PROJECT_VARS['LOG_LEVEL'],
)