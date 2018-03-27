import argparse
import importlib
import logging
from abc import ABC
from collections import Iterable, Callable
from inspect import signature

from .utils.config import Config
from .utils.constants import modules
from .utils.validate import BaseValidator


def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    return logger


class AbstractRunner(ABC):
    choices = None
    validator = None
    type = None

    def __init__(self, **kwargs):
        for attr in ('choices', 'validator'):
            if not hasattr(self, attr) or not getattr(self, attr):
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
            choice_attr = getattr(self, choice)
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

        if not isinstance(self.validator, BaseValidator):
            raise TypeError(
                '"validator" has unsupported type "{}"'.format(
                    type(self.validator)))

        self.action = kwargs['action']

        self.validator.params_validate(kwargs['parameters'])
        self.params = kwargs['parameters']
        self.type = kwargs['type']
        self.logger = kwargs['logger']

    def run(self):
        getattr(self, self.action)(self.params)


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

    actions = Config(parser.parse_args()).parse_actions()

    for action_dict in actions['actions']:
        try:
            exec_module = importlib.import_module(modules[action_dict['type']])
        except (TypeError, ModuleNotFoundError, ValueError) as err:
            # TODO more detailed exceptions handling
            raise err
        else:
            exec_module.Main(**action_dict, logger=setup_logger()).run()


if __name__ == '__main__':
    entrypoint()
