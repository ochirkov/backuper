import trafaret as tr
from datetime import datetime
from functools import partial
from pathlib import Path

from backuper.main import AbstractRunner
from backuper.utils.filters import FilterMixin
from backuper.utils.helpers import (
    get_files_from_dir, remove_in_parallel, SnapshotInfo,
)
from subprocess import Popen, PIPE

HOST = '127.0.0.1'
PORT = '27017'

OptKey = partial(tr.Key, optional=True)


class MongoValidator:
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
        tr.Dict({
            tr.Key('path'): tr.String,
        })(parameters)


class Main(AbstractRunner, FilterMixin):
    choices = ['create', 'delete', 'restore']
    validator = MongoValidator()

    _cmd = '{bin} --host {host} --port {port}'

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
        # get snapshots
        snapshots_path = Path(params['path'])
        if not snapshots_path.exists():
            raise ValueError(
                'Provided path "{}" doesn\'t exist'.format(params['path']))

        files = list(get_files_from_dir(snapshots_path))
        self.logger.debug(
            'Found {} snapshots'.format(len(files)))

        # adapt snapshots
        snapshots = [MongoSnapshotInfo(f) for f in files]
        self.logger.debug(
            'Found {} adapted snapshots'.format(len(snapshots)))

        # filter snapshots
        filtered_snapshots = self.filter(self.filters, snapshots)
        self.logger.debug(
            '{} snapshots will be deleted'.format(len(filtered_snapshots)))

        remove_in_parallel(filtered_snapshots)

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


class MongoSnapshotInfo(SnapshotInfo):
    def __init__(self, path: Path):
        self._path = path.absolute()

        self._name = path.name

        self._creation_date = datetime.fromtimestamp(
            path.lstat().st_birthtime)

        self._modification_date = datetime.fromtimestamp(
            path.lstat().st_mtime)

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return self._name

    @property
    def creation_date(self):
        return self._creation_date

    @property
    def modification_date(self):
        return self._modification_date
