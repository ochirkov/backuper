import argparse
import logging
import importlib
from abc import ABC

from .utils.config import Config
from .utils.constants import modules

logger = logging.getLogger(__name__)


class AbstractRunner(ABC):
    pass


def entrypoint():
    parser = argparse.ArgumentParser()

    parser.add_argument('--conf-file', required=False,
                        help='Backuper configuration file',
                        type=argparse.FileType('r'))

    parser.add_argument('--action-file', required=True,
                        help='Backuper action file',
                        type=argparse.FileType('r'))

    parser.add_argument('--vars-file', required=False,
                        help='Backuper vars file',
                        type=argparse.FileType('r'))

    parser.add_argument('--extra-vars', required=False,
                        help='Extra vars from command line',
                        action='store')

    config = Config(parser.parse_args())

    action = config.parse_action()

    try:
        exec_module = importlib.import_module(modules[action['type']])
    except (TypeError, ModuleNotFoundError, ValueError) as err:
        # TODO more detailed exceptions handling
        logger.error('Something went wrong, exiting...')
        raise err
    else:
        exec_client = exec_module.Main(**action)
        exec_client.run()


if __name__ == '__main__':
    entrypoint()
