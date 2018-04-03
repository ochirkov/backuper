import argparse
import importlib
import logging
from abc import ABC
from collections import Iterable, Callable
from inspect import signature

from .utils.config import Config
from .utils.constants import modules
from .utils.validate import BaseValidator


def setup_logger(options, config):
    # TODO setup logger from config
    log_level = logging.INFO if not options.verbose else logging.DEBUG
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    stream_handler = logging.StreamHandler()

    fmt = logging.Formatter(
        '%(asctime)s %(levelname)-5.5s [BACKUPER] [%(service)s] '
        '[%(filename)s:%(lineno)d] [%(funcName)s] %(message)s')

    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    return logger


def setup_parser():
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

    parser.add_argument('-v', '--verbose', required=False,
                        default=False, action="store_true")

    return parser


class AbstractRunner(ABC):
    choices = None
    validator = None
    service = None

    def __init__(self, **kwargs):
        for attr in ('choices', 'validator'):
            if not hasattr(self, attr) or not getattr(self, attr, None):
                raise NotImplementedError(
                    '"{}" attr must be implemented by subclass'.format(attr))

        if not isinstance(self.choices, Iterable):
            raise TypeError(
                '`choices` attr has unsupported type "{}"'.format(
                    type(self.choices)))

        if not all(isinstance(choice, str) for choice in self.choices):
            raise TypeError(
                'All elements in `choices` should be `str` instances')

        for choice in self.choices:
            choice_attr = getattr(self, choice, None)
            if not choice_attr:
                raise NotImplementedError(
                    '"{}" is declared but not implemented'.format(choice))

            if not isinstance(choice_attr, Callable):
                raise TypeError('"{}" is not a callable object'.format(choice))

            params_count = len(signature(choice_attr).parameters)
            if params_count != 1:
                raise Exception(
                    '"{}" implementation should accept only one parameter,'
                    ' "{}" received'.format(choice, params_count))

            choice_validator = getattr(self.validator, '{}_validate'.format(choice), None)
            if not choice_validator:
                raise NotImplementedError(
                    '"{}_validator" is not implemented'.format(choice))

            if not isinstance(choice_validator, Callable):
                raise TypeError('"{}_validator" is not a callable object'.format(choice))

        if not isinstance(self.validator, BaseValidator):
            raise TypeError(
                '"validator" has unsupported type "{}"'.format(
                    type(self.validator)))

        self.action = kwargs['action']

        self.params = kwargs['parameters']
        self.service = kwargs['service']

        getattr(self.validator, '{}_validate'.format(self.action))(self.params)

        self.logger = logging.LoggerAdapter(
            kwargs['logger'],
            {'service': self.type.upper()},
        )

    def run(self):
        getattr(self, self.action)(self.params)


def entrypoint():
    parser = setup_parser()
    options = parser.parse_args()

    config = Config(options)
    logger = setup_logger(options, config)

    actions = config.parse_actions()

    for action_dict in actions['actions']:
        try:
            exec_module = importlib.import_module(
                modules[action_dict['service']]
            )
        except (TypeError, ModuleNotFoundError, ValueError) as err:
            # TODO more detailed exceptions handling
            raise err
        else:
            exec_module.Main(**action_dict, logger=logger).run()


if __name__ == '__main__':
    entrypoint()
