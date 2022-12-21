
import logging
import os

PROJECT_VARS = {
    'SERVER': 'localhost',
    'ENV_PASSW': 'polskagora',
    'ENV_AGENT_NAME': 'environment',
    'GLOB_ENV_LOGGER_NAME': 'Global Environment',
    'LOCAL_ENV_LOGGER_NAME': 'Local Environment',
    'LOG_LEVEL': logging.INFO,
    'ENV_TICKS': 1.,  # per seconds, env ticks in one update, the more the faster simulation is
    'ENV_SIM_SPEED': 1., # per second, the speed at which simulated clock is ticking
    'ENV_SLEEP_TYPE': 'LOOP', # 'SLEEP' or 'LOOP'
    'LOG_DIR': os.path.join('logs', ''), 
}


# uncomment for global logs all in one file
#logging.basicConfig(
#    filename='app.log',
#    filemode='a',
#    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
#    datefmt='%H:%M:%S',
#    level=PROJECT_VARS['LOG_LEVEL'],
#)