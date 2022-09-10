import os
import logging
from logging.handlers import TimedRotatingFileHandler


class log_events:
    def __init__(self, filename, debug=False):

        if not os.path.exists('./logs'):
            os.makedirs(name='./logs')

        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)

        logging.basicConfig(
            format='%(asctime)s %(levelname)s %(message)s',
            handlers=[
                TimedRotatingFileHandler(filename='./logs/'+filename, when='D', interval=1, backupCount=7),
                logging.StreamHandler()
            ],
            datefmt='%m/%d/%Y %I:%M:%S %p')

    @staticmethod
    def debug(message):
        logging.debug(msg=message)

    @staticmethod
    def warning(message):
        logging.warning(msg=message)

    @staticmethod
    def error(message):
        logging.error(msg=message)

    @staticmethod
    def critical(message):
        logging.critical(msg=message)

    @staticmethod
    def warning(message):
        logging.exception(msg=message)
