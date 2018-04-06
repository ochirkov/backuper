from abc import ABC, abstractmethod
from datetime import datetime
from os import remove as os_remove
from pathlib import Path
from typing import List
from concurrent.futures import ProcessPoolExecutor


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
    os_remove(path.absolute())


def fn_in_parallel(fn, it):
    with ProcessPoolExecutor() as executor:
        executor.map(fn, it)


def remove_in_parallel(snapshots: List[SnapshotInfo]):
    abs_paths = [snapshot.path for snapshot in snapshots]
    fn_in_parallel(remove, abs_paths)
