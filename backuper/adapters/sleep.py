import logging

from backuper.adapters import BackupInfo, Action
from backuper.params import Int, List


logger = logging.getLogger(__name__)


class SleepingAdapter(Action):

    sleep: Int = 3

    def _sleep(self, action, sec):
        logger.info('started %s, sleeping %d seconds...', action, sec)
        from time import sleep
        sleep(sec)
        logger.info('finished %s after sleeping %d seconds', action, sec)


class Create(SleepingAdapter):

    result_backup: BackupInfo

    def run(self):
        self._sleep('create', self.sleep)
        return self.result_backup


class Retrieve(SleepingAdapter):

    result_backups: List

    def run(self):
        self._sleep('retrieve', self.sleep)
        return [BackupInfo.cast(item) for item in self.result_backups]


class Delete(SleepingAdapter):

    backup: BackupInfo

    def run(self):
        self._sleep('delete', self.sleep)
        return self.backup
