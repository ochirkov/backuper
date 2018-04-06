import trafaret as tr
from backuper.modules.cloud.digital_ocean import get_digitalocean_client
from multiprocessing import Process

from ....main import AbstractRunner

REGIONS = []


class DigitalOceanValidator:

    def create_validate(self, parameters):
        parameters_schema = tr.Dict({
            tr.Key('snapshot_name'): tr.String,
            tr.Key('region'): tr.Enum(*REGIONS),
            tr.Key('droplet_name'): tr.String,
            tr.Key('copy_to_region', optional=True): tr.List(
                tr.String, min_length=1),
            tr.Key('wait_timeout', optional=True): tr.Int
        })

        parameters_schema(parameters)


class Main(AbstractRunner):
    choices = ['create', 'delete', 'restore']
    validator = DigitalOceanValidator()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kwargs = kwargs
        self.config()

    def config(self):

        params = dict(a_region=None,
                      a_snap_name=None,
                      a_d_name=None,
                      a_wait_timeout=None)

        parameters = self.params
        params['a_region'] = parameters['region']
        params['a_type'] = self.service

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

        c = get_amazon_client(self.config()['a_type'], region)  # noqa

        response = c.copy_db_snapshot(
            SourceDBSnapshotIdentifier=SourceDBSnapshotIdentifier,  # noqa
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
