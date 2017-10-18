from backuper.utils.validate import ValidateBase
from backuper.utils import get_msg
from backuper.utils.constants import wait_timeout, mongodb_port
from backuper.utils.filters import main as f_main
from subprocess import Popen, PIPE


class ValidateMongo(ValidateBase):

    def params_validate(self, **kwargs):

        if kwargs['action'] == 'create':

            parameters_schema = self.tr.Dict({
                self.tr.Key('host'): self.tr.String,
                self.tr.Key('port', optional=True): self.tr.String,
                self.tr.Key('dbname'): self.tr.String,
                self.tr.Key('collection'): self.tr.String,
                self.tr.Key('gzip'): self.tr.Bool,
                self.tr.Key('out'): self.tr.String,
                self.tr.Key('wait_timeout', optional=True): self.tr.Int
            })

        # if kwargs['action'] == 'delete':
        #
        #     parameters_schema = self.tr.Dict({
        #         self.tr.Key('region'): self.tr.Enum(*amazon_regions),
        #         self.tr.Key('snapshot_type'): self.tr.Enum(
        #             *['standard', 'manual', 'all'])
        #     })

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
                      a_out=None,
                      a_wait_timeout=None)

        choices = ['create', 'restore']

        self.validate.action_validate(choices, **self.kwargs)
        self.validate.params_validate(**self.kwargs)

        if self.kwargs['action'] == 'create':
            parameters = self.kwargs['parameters']
            params['a_type'] = self.kwargs['type']
            params['a_host'] = parameters['host']
            params['a_port'] = parameters['port']
            params['a_dbname'] = parameters['dbname']
            params['a_collection'] = parameters['collection']
            params['a_gzip'] = parameters['gzip']
            params['a_out'] = parameters['out']
            params['a_wait_timeout'] = parameters.get('wait_timeout')

        return params

    def dump(self, args):

        command = "mongodump {}".format(args)
        proc = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
        response = proc.communicate(timeout=15)

        return (proc.returncode,) + response

    # def restore(self, region, snapshots):
    #
    #     c = get_amazon_client(self.config()['a_type'], region)
    #
    #     r = []
    #     for i in snapshots:
    #         response = c.delete_db_snapshot(
    #             DBSnapshotIdentifier=i['DBSnapshotIdentifier']
    #         )
    #         print(get_msg(self.config()['a_type']) +
    #               'Deleting snapshot {} in {} region...'.format(
    #             i['DBSnapshotIdentifier'], region))
    #         r.append(response)
    #
    #     return r

    def run(self):

        if self.kwargs['action'] == 'create':

            if self.config()['a_wait_timeout'] is None:
                port = mongodb_port
            else:
                port = self.config()['a_port']

            args = "--db {} --collection {} --out {} --host {}".format(
                self.config()['a_dbname'],
                self.config()['a_collection'],
                self.config()['a_out'],
                self.config()['a_host'],
            )

            create_r = self.dump(args)
            print(args)
            if create_r[0] == 0:
                print(get_msg(self.config()['a_type']) +
                      'Snapshot created successfully...')
            else:
                print(get_msg(self.config()['a_type']) +
                      '{} ...'.format(create_r[2].decode("utf-8").rstrip()))
