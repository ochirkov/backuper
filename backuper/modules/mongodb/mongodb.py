from backuper.utils.validate import ValidateBase
from backuper.utils import get_msg
from backuper.utils.constants import waitTimeout, mongodbPort
from backuper.utils.filters import main as f_main
from subprocess import Popen, PIPE


class ValidateMongo(ValidateBase):

    def params_validate(self, **kwargs):

        parameters_schema = self.tr.Dict({
            self.tr.Key('host'): self.tr.String,
            self.tr.Key('port', optional=True): self.tr.String,
            self.tr.Key('dbname', optional=True): self.tr.String,
            self.tr.Key('collection', optional=True): self.tr.String,
            self.tr.Key('gzip'): self.tr.Bool,
            self.tr.Key('path'): self.tr.String,
            self.tr.Key('waitTimeout', optional=True): self.tr.Int
        })

        parameters_schema(kwargs['parameters'])


class Main(object):

    def __init__(self, **kwargs):

        self.kwargs = kwargs
        self.validate = ValidateMongo()
        self.config()

    def config(self):

        params = dict(a_host=None,
                      a_port=None,
                      a_dbname=None,
                      a_type=None,
                      a_collection=None,
                      a_gzip=None,
                      a_path=None,
                      a_waitTimeout=None)

        choices = ['create', 'restore']

        self.validate.action_validate(choices, **self.kwargs)
        self.validate.params_validate(**self.kwargs)

        parameters = self.kwargs['parameters']
        params['a_type'] = self.kwargs['type']
        params['a_host'] = parameters['host']
        params['a_port'] = parameters.get('port')
        params['a_dbname'] = parameters.get('dbname')
        params['a_collection'] = parameters.get('collection')
        params['a_waitTimeout'] = parameters.get('waitTimeout')
        params['a_gzip'] = parameters['gzip']
        params['a_path'] = parameters['path']

        return params

    def processing(self, command, timeout):

        proc = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
        response = proc.communicate(timeout=timeout)

        return (proc.returncode,) + response

    def run(self):

        #TODO: add all mongodump params

        if self.kwargs['action'] == 'create':
            command = 'mongodump'
        if self.kwargs['action'] == 'restore':
            command = 'mongorestore'

        if self.config()['a_port'] is None:
            port = mongodbPort
        else:
            port = self.config()['a_port']

        if self.config()['a_waitTimeout'] is not None:
            if self.config()['a_waitTimeout'] == 0:
                timeout = None
            else:
                timeout = self.config()['a_waitTimeout']
        else:
            timeout = waitTimeout

        if self.kwargs['action'] == 'create':
            args = "{command} --out {path} --host {host} --port {port}".format(
                path=self.config()['a_path'],
                host=self.config()['a_host'],
                port=port,
                command=command
            )
        if self.kwargs['action'] == 'restore':
            args = "{command} --host {host} --port {port} {path}".format(
                path=self.config()['a_path'],
                host=self.config()['a_host'],
                port=port,
                command=command
            )

        if self.config()['a_gzip'] is not None and self.config()['a_gzip']:
            args += ' --gzip'
        if self.config()['a_collection'] is not None:
            args += ' --collection {}'.format(
                self.config()['a_collection'])
        if self.config()['a_dbname'] is not None:
            args += ' --db {}'.format(
                self.config()['a_dbname'])

        print(args)

        create_r = self.processing(args, timeout)

        if create_r[0] == 0:
            print(get_msg(self.config()['a_type']) +
                  'Snapshot created successfully ...')
        else:
            print(get_msg(self.config()['a_type']) +
                  '{} ...'.format(create_r[2].decode("utf-8").rstrip()))
