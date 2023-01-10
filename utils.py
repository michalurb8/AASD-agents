import logging
from defaults import PROJECT_VARS

def prepareDefaultLogger(loggerName: str, fileName: str):
    logger = logging.getLogger(loggerName)
    handler = logging.FileHandler(PROJECT_VARS['LOG_DIR'] + fileName, 'a')
    handler.setFormatter(logging.Formatter(fmt="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s", datefmt='%H:%M:%S'))
    logger.addHandler(handler)
    logger.setLevel(level=PROJECT_VARS['LOG_LEVEL'])
    return logger