from backuper.modules.cloud.digital_ocean import get_digitalocean_client
from backuper.utils.validate import ValidateBase, validate_empty_snapshots
from backuper.utils import get_msg
from backuper.utils.constants import digital_ocean_regions, wait_timeout
from backuper.utils.filters import main as f_main
from time import sleep
from multiprocessing import Process


class ValidateDO(ValidateBase):

    def params_validate(self, **kwargs):

        if kwargs['action'] == 'create':
            parameters_schema = self.tr.Dict({
                self.tr.Key('snapshot_name'): self.tr.String,
                self.tr.Key('region'): self.tr.Enum(*digital_ocean_regions),
                self.tr.Key('droplet_name'): self.tr.String,
                self.tr.Key('copy_to_region', optional=True): self.tr.List(
                    self.tr.String, min_length=1),
                self.tr.Key('wait_timeout', optional=True): self.tr.Int
            })
        #
        # if kwargs['action'] == 'restore':
        #     parameters_schema = self.tr.Dict({
        #         self.tr.Key('snapshot_identifier'): self.tr.String,
        #         self.tr.Key('region'): self.tr.Enum(*amazon_regions),
        #         self.tr.Key('db_identifier'): self.tr.String
        #     })
        #
        # if kwargs['action'] == 'delete':
        #     parameters_schema = self.tr.Dict({
        #         self.tr.Key('region'): self.tr.Enum(*amazon_regions),
        #         self.tr.Key('snapshot_type'): self.tr.Enum(
        #             *['standard', 'manual', 'all'])
        #     })

        parameters_schema(kwargs['parameters'])


class Main(object):
    def __init__(self, **kwargs):

        self.kwargs = kwargs
        self.validate = ValidateDO()
        self.config()

    def config(self):

        params = dict(a_region=None,
                      a_snap_name=None,
                      a_d_name=None,
                      a_wait_timeout=None)

        parameters = self.kwargs['parameters']
        params['a_region'] = parameters['region']
        params['a_type'] = self.kwargs['type']

        choices = ['create', 'delete', 'restore']

        self.validate.action_validate(choices, **self.kwargs)
        self.validate.params_validate(**self.kwargs)

        if self.kwargs['action'] == 'create':
            params['a_snap_name'] = parameters['snapshot_name']
            params['a_d_name'] = parameters['droplet_name']
            params['a_wait_timeout'] = parameters.get('wait_timeout')

        # if self.kwargs['action'] == 'restore':
        #     params['a_db_identifier'] = parameters['db_identifier']
        #     params['a_snap_id'] = parameters['snapshot_identifier']
        #
        # if self.kwargs['action'] == 'delete':
        #     params['a_snapshot_type'] = parameters['snapshot_type']
        #     params['a_filters'] = self.kwargs['filters']
        #     self.validate.filters_validate(**self.kwargs)

        return params

    def get_snapshots(self, region):

        c = get_digitalocean_client(region)
        response = c.get_all_snapshots()

        return response

    def get_droplet(self, region):

        c = get_digitalocean_client(region)
        response = c.get_all_droplets()

        return response

    def create_snapshot(self, droplet, name):

        response = droplet.take_snapshot(
            snapshot_name=name)

        return response

    def copy_snapshot(self, resource, region):

        c = get_amazon_client(self.config()['a_type'], region)

        response = c.copy_db_snapshot(
            SourceDBSnapshotIdentifier=SourceDBSnapshotIdentifier,
            TargetDBSnapshotIdentifier=self.config()['a_snap_id'],
            CopyTags=True,
            SourceRegion=self.config()['a_region']
        )

        return response

    def run(self):

        if self.kwargs['action'] == 'create':

            for d in self.get_droplet(self.config()['a_region']):
                if d.name == self.config()['a_d_name']:
                    droplet = d

            create_r = self.create_snapshot(droplet,
                                            self.config()['a_snap_name'])

            if self.config()['a_copy_to_region'] is not None:
                jobs = []
                for region in self.config()['a_copy_to_region']:
                    self.copy_snapshot(create_r, region)
                    p = Process(target=self.wait_snapshot,
                                args=(region, self.config()['a_snap_id']))
                    jobs.append(p)
                    p.start()