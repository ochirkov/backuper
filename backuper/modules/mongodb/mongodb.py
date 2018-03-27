import trafaret as tr
from backuper.executor import AbstractRunner
from backuper.utils.validate import BaseValidator
from backuper.utils import get_msg
from backuper.utils.constants import wait_timeout, mongodb_port
from subprocess import Popen, PIPE


class MongoValidator(BaseValidator):

    def params_validate(self, parameters):

        parameters_schema = tr.Dict({
            tr.Key('host'): tr.String,
            tr.Key('port', optional=True): tr.String,
            tr.Key('dbname', optional=True): tr.String,
            tr.Key('collection', optional=True): tr.String,
            tr.Key('gzip', optional=True): tr.Bool,
            tr.Key('path'): tr.String,
            tr.Key('wait_timeout', optional=True): tr.Int
        })

        parameters_schema(parameters)


class Main(AbstractRunner):
    choices = ['create', 'delete', 'restore']
    validator = MongoValidator()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _processing(self, command, timeout, type):
        proc = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate(timeout=timeout)

        if proc.returncode == 0:
            self.logger.info(
                get_msg(type +
                        ' Snapshot created successfully ...'))
        else:
            self.logger.error(
                get_msg(type +
                        ' {} ...'.format(err.decode("utf-8").rstrip())))

    def restore(self, params):
        command = "{command} --host {host} --port {port} {path}".format(
            path=params['path'],
            host=params['host'],
            port=params.get('port') or mongodb_port,
            command='mongorestore'
        )

    def create(self, params):
        timeout = params['wait_timeout'] or wait_timeout

        command = "{command} --out {path} --host {host} --port {port}".format(
            path=params['path'],
            host=params['host'],
            port=params.get('port') or mongodb_port,
            command='mongodump',
        )

        if params.get('gzip'):
            command += ' --gzip'

        coll = params.get('collection')
        if coll:
            command += ' --collection {}'.format(coll)

        db = params.get('dbname')
        if db:
            command += ' --db {}'.format(db)

        self._processing(command, timeout, self.type)

    def delete(self, params):
        pass
