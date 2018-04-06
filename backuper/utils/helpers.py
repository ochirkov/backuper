import logging
from abc import ABC, abstractmethod
from datetime import datetime
from os import remove as os_remove
from pathlib import Path
from typing import List
from concurrent.futures import ProcessPoolExecutor

logger = logging.getLogger('backuper.main')


def get_files_from_dir(p: Path):
    if p.is_dir():
        for pp in p.iterdir():
            yield from get_files_from_dir(pp)
    else:
        yield p


class SnapshotInfo(ABC):

    @property
    @abstractmethod
    def creation_date(self) -> datetime:
        pass

    @property
    @abstractmethod
    def modification_date(self) -> datetime:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def path(self) -> Path:
        pass


def remove(path: Path):
    abs_path = path.absolute()
    try:
        os_remove(abs_path)
    except OSError as err:
        logger.error(
            'Unable to remove the file "{}"'.format(abs_path),
            exc_info=err,
        )
    finally:
        logger.debug('File "{}" was successfully removed'.format(abs_path))


def fn_in_parallel(fn, it):
    with ProcessPoolExecutor() as executor:
        executor.map(fn, it)


def remove_in_parallel(snapshots: List[SnapshotInfo]):
    abs_paths = [snapshot.path for snapshot in snapshots]
    fn_in_parallel(remove, abs_paths)
