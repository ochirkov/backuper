from backuper.backup import Backup
from backuper.params import Param, ParamsBase


class BackupInfo(Param):

    @classmethod
    def cast(cls, value):
        if isinstance(value, Backup):
            return value
        return Backup(**value)


class Action(ParamsBase):
    pass
