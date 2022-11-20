import os
import logging
from logging.handlers import TimedRotatingFileHandler

from pathlib import Path

file = Path(__file__).resolve()
package_root_directory = file.parents[1]


class log_events:
    def __init__(self, filename, debug=False):
        """
        A class used to log events.
        Call log_events() below Python imports with debug=True to capture

        Parameters
        -------------
        :param filename:
        :param debug:
        """
        if not os.path.exists(f'{package_root_directory}/logs'):
            os.makedirs(name=f'{package_root_directory}/logs')

        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)

        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                TimedRotatingFileHandler(filename=f'{package_root_directory}/logs/'+filename, when='D', interval=1, backupCount=7),
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
    def info(message):
        logging.info(msg=message)
