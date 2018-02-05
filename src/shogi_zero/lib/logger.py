"""
Logging helper methods
"""

from logging import StreamHandler, basicConfig, DEBUG, getLogger, Formatter, FileHandler


def setup_logger(log_filename):
    logger = getLogger(None)
    log_fmt = Formatter('%(asctime)s %(name)s %(lineno)d [%(levelname)s][%(funcName)s] %(message)s ')

    handler = StreamHandler()
    handler.setLevel(DEBUG)
    handler.setFormatter(log_fmt)
    logger.setLevel(DEBUG)
    logger.addHandler(handler)

    handler = FileHandler(log_filename)
    handler.setLevel(DEBUG)
    handler.setFormatter(log_fmt)
    logger.setLevel(DEBUG)
    logger.addHandler(handler)
