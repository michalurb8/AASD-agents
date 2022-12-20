
import logging

PROJECT_VARS = {
    'SERVER': 'localhost',
    'ENV_PASSW': 'polskagora',
    'ENV_AGENT_NAME': 'environment',
    'ENV_LOGGER_NAME': 'Environment',
    'LOG_LEVEL': logging.INFO,
    'ENV_TICKS': 1.,  # per seconds, env ticks in one update, the more the faster simulation is
    'ENV_SIM_SPEED': 1., # per second, the speed at which simulated clock is ticking
    'ENV_SLEEP_TYPE': 'LOOP', # 'SLEEP' or 'LOOP'
    'SURFACE_SQUARE_LENGTH': 100 # in meters
}

logging.basicConfig(
    filename='app.log',
    filemode='a',
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt='%H:%M:%S',
    level=PROJECT_VARS['LOG_LEVEL'],
)