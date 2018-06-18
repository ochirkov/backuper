import argparse
import logging

from .actionfile import load_action_file
from .pool import get_pool


def setup_logger(level=logging.WARNING):
    fmt = (
        '%(levelname)s %(asctime)s %(processName)s[%(process)d] '
        '%(threadName)s %(module)s -- %(message)s'
    )
    logging.basicConfig(level=level, format=fmt)


def entrypoint():
    parser = argparse.ArgumentParser()

    parser.add_argument('--action-file', required=True,
                        help='Backuper action file')

    parser.add_argument('--log-level', default='WARNING',
                        help='Log levels',
                        choices=('CRITICAL', 'ERROR', 'WARNING', 'INFO',
                                 'DEBUG'))

    # multiprocessing.log_to_stderr(logging.DEBUG)

    args = parser.parse_args()

    setup_logger(getattr(logging, args.log_level))

    executor = load_action_file(vars(args)['action_file'])

    # with get_pool(log_level=logging.INFO) as pool:
    with get_pool() as pool:
        try:
            executor.start()
            result = executor.get_result()
        finally:
            pool.close()

    from pprint import pprint
    pprint(result)


if __name__ == '__main__':
    entrypoint()
