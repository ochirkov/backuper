import argparse
import importlib
import logging
from abc import abstractmethod, ABC
from collections import Callable
from inspect import signature
from typing import List

from .utils.config import Config
from .utils.constants import modules
from .utils import filters


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

    @property
    @abstractmethod
    def choices(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def validator(self):
        pass

    @property
    def service(self) -> str:
        return self._service

    @property
    def filters(self) -> List[filters.AbstractFilter]:
        return self._filters

    def __init__(self, **kwargs):
        self._service = kwargs['service']
        self.action = kwargs['action']
        self.params = kwargs['parameters']
        self._filters = kwargs.get('filters', [])

        self.logger = logging.LoggerAdapter(
            kwargs['logger'],
            {'service': self.service.upper()},
        )

        self._validate_choices()
        self._validate_params()
        self._setup_filters()

    def _validate_choices(self):
        for choice in self.choices:
            choice_attr = getattr(self, choice, None)
            if not choice_attr:
                raise NotImplementedError(
                    '"{}" is declared but not implemented'.format(choice),
                )

            if not isinstance(choice_attr, Callable):
                raise TypeError(
                    '"{}" is not a callable object'.format(choice),
                )

            params_count = len(signature(choice_attr).parameters)
            if params_count != 1:
                raise Exception(
                    '"{}" implementation should accept only one parameter,'
                    ' "{}" received'.format(choice, params_count),
                )

            choice_validator = getattr(
                self.validator,
                '{}_validate'.format(choice),
                None,
            )
            if not choice_validator:
                raise NotImplementedError(
                    '"{}_validator" is not implemented'.format(choice),
                )

            if not isinstance(choice_validator, Callable):
                raise TypeError(
                    '"{}_validator" is not a callable object'.format(choice),
                )

    def _validate_params(self):
        validate_callable = '{}_validate'.format(self.action)
        getattr(self.validator, validate_callable)(self.params)

    def _setup_filters(self):
        def instant_filter(conf):
            filter_cls_name = '{}Filter'.format(conf['type'].capitalize())
            filter_cls = getattr(filters, filter_cls_name, None)
            return filter_cls(conf) if filter_cls else None

        self._filters = [instant_filter(f_conf) for f_conf in self._filters]
        self._filters = [f for f in self._filters if f]

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
                modules[action_dict['service']],
            )
        except (TypeError, ModuleNotFoundError, ValueError) as err:
            # TODO more detailed exceptions handling
            raise err
        else:
            exec_module.Main(**action_dict, logger=logger).run()


if __name__ == '__main__':
    entrypoint()
