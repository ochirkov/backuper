import logging

from subprocess import check_output

from backuper.adapters import Action
from backuper.params import Bool, HostNameOrIP, Int, Port, Str


logger = logging.getLogger(__name__)


class Mongo:

    host: HostNameOrIP
    port: Port = 27017
    dbname: Str = ''
    collection: Str = ''
    gzip: Bool = False
    path: Str
    wait_timeout: Int = 4800


class Create(Mongo, Action):

    def run(self):
        command = "{command} --out {path} --host {host} --port {port}".format(
            path=self.path,
            host=self.host,
            port=self.port,
            command='mongodump',
        )

        if self.gzip:
            command += ' --gzip'

        if self.collection:
            command += ' --collection {}'.format(self.collection)

        if self.db:
            command += ' --db {}'.format(self.db)

        check_output(command, shell=True, timeout=self.wait_timeout)

        logger.info('MongoDB snapshot created successfully')


class Restore(Mongo, Action):

    def run(self):
        command = "{command} --host {host} --port {port} {path}".format(
            path=self.path,
            host=self.host,
            port=self.port,
            command='mongorestore',
        )

        check_call(command, shell=True, timeout=self.wait_timeout)

        logger.info('MongoDB snapshot restored successfully')
