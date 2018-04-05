import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List


from backuper.utils.helpers import SnapshotInfo


class AbstractFilter(ABC):

    def __init__(self, meta):
        self.meta = meta

    def __call__(self, snapshots: List[SnapshotInfo]):
        return self.filter(snapshots)

    @abstractmethod
    def filter(self, snapshots: List[SnapshotInfo]) -> List[SnapshotInfo]:
        pass


class AgeFilter(AbstractFilter):

    def filter(self, snapshots: List[SnapshotInfo]):
        raise NotImplementedError()


class RegexFilter(AbstractFilter):

    def filter(self, snapshots: List[SnapshotInfo]):
        pattern = re.compile(self.meta['pattern'])
        filtered = []

        for snapshot in snapshots:
            if pattern.match(snapshot.name):
                filtered.append(snapshot)

        return filtered


class PeriodFilter(AbstractFilter):

    def filter(self, snapshots: List[SnapshotInfo]):
        raise NotImplementedError()


class FilterMixin:

    @staticmethod
    def filter(
            filters: List[AbstractFilter],
            snapshots: List[SnapshotInfo],
    ) -> List[SnapshotInfo]:

        filtered = snapshots.copy()

        for f in filters:
            filtered = f(filtered)

        return filtered
