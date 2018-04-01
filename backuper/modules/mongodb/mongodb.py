import trafaret as tr
from functools import partial
from backuper.main import AbstractRunner
from backuper.utils.validate import BaseValidator
from subprocess import Popen, PIPE

HOST = '127.0.0.1'
PORT = '27017'

OptKey = partial(tr.Key, optional=True)


class MongoValidator(BaseValidator):
    _schema = tr.Dict({
        OptKey('host'): tr.String,
        OptKey('port'): tr.String,
        OptKey('dbname'): tr.String,
        OptKey('collection'): tr.String,
        OptKey('gzip'): tr.Bool,
    })

    def create_validate(self, parameters):
        create_schema = self._schema + tr.Dict({
            OptKey('path'): tr.String,
        })

        create_schema(parameters)

    def restore_validate(self, parameters):
        restore_schema = self._schema + tr.Dict({
            tr.Key('path'): tr.String,
        })

        restore_schema(parameters)

    def delete_validate(self, parameters):
        raise NotImplementedError()


class Main(AbstractRunner):
    choices = ['create', 'delete', 'restore']
    validator = MongoValidator()

    _cmd = '{bin} --host {host} --port {port}'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def create(self, params):
        cmd = self._cmd.format(
            bin='mongodump',
            host=params.get('host') or HOST,
            port=params.get('port') or PORT,
        )

        cmd = self._update_cmd(cmd, params)
        cmd += ' --out {}'.format(params['path'])

        ret = self._processing(cmd)

        if ret == 0:
            self.logger.info('Snapshot created successfully')
        else:
            self.logger.error('Failed to create snapshot')

    def restore(self, params):
        cmd = self._cmd.format(
            bin='mongorestore',
            host=params.get('host') or HOST,
            port=params.get('port') or PORT,
        )

        cmd = self._update_cmd(cmd, params)
        cmd += ' ' + params['path']

        ret = self._processing(cmd)

        if ret == 0:
            self.logger.info('Snapshot restored successfully')
        else:
            self.logger.error('Failed to restore snapshot')

    def delete(self, params):
        raise NotImplementedError()

    def _update_cmd(self, cmd, params):
        db = params.get('dbname')
        if db:
            cmd += ' --db {}'.format(db)

            coll = params.get('collection')
            if coll:
                cmd += ' --collection {}'.format(coll)

        if params.get('gzip'):
            cmd += ' --gzip'

        return cmd

    def _processing(self, cmd):
        self.logger.debug('Processing cmd "{}"'.format(cmd))

        with Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE) as proc:
            for pipe in (proc.stdout, proc.stderr):
                for line in pipe:
                    self.logger.debug(line.decode().rstrip('\n'))

        return proc.returncode
