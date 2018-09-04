import logging

from backuper.adapters import Action
from backuper.backup import Backup
from backuper.params import Int, Param, List


logger = logging.getLogger(__name__)


class BackupInfo(Param):
    """A helper that creates a Backup instance from a dict of backup params."""

    @classmethod
    def cast(cls, value):
        if isinstance(value, Backup):
            return value
        return Backup(**value)


class SleepingAdapter:

    sleep: Int = 3

    def _sleep(self, action, sec):
        logger.info('started %s, sleeping %d seconds...', action, sec)
        from time import sleep
        sleep(sec)
        logger.info('finished %s after sleeping %d seconds', action, sec)


class Create(SleepingAdapter, Action):

    result_backup: BackupInfo

    def run(self):
        self._sleep('create', self.sleep)
        return self.result_backup


class Retrieve(SleepingAdapter, Action):

    result_backups: List

    def run(self):
        self._sleep('retrieve', self.sleep)
        return [BackupInfo.cast(item) for item in self.result_backups]


class Delete(SleepingAdapter, Action):

    backup: BackupInfo

    def run(self):
        self._sleep('delete', self.sleep)
        return self.backup
