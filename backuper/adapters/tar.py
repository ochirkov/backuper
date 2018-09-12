from datetime import datetime
from pathlib import PurePath

import fabric

from backuper.adapters import Action
from backuper.backup import Backup
from backuper.params import HostNameOrIP, ParamError, Port, Str


class Create(Action):

    host: HostNameOrIP
    port: Port = 22
    username: Str
    password: Str = ''
    identity: Str = ''
    backup_path: Str
    backup_to: Str

    def __init__(self):
        if not bool(self.password) ^ bool(self.identity):
            raise ParamError(
                'Either password or identity (private key) must be provided '
                'but not both'
            )

    def run(self):
        tar_name = PurePath(self.backup_to.format(time=datetime.now()))

        if self.password:
            connect_kwargs = {'password': self.password}
        else:
            connect_kwargs = {'pkey': self.identity}

        with fabric.Connection(
            host=self.host,
            port=self.port,
            connect_kwargs=connect_kwargs,
        ) as conn:
            for cmd in (
                'mkdir -p ' + str(tar_name.parent),
                'tar -czf {0} {1.backup_path}'.format(tar_name, self),
            ):
                conn.run(cmd)

        return Backup(created=datetime.utcnow())
