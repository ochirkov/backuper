from backuper.modules.cloud.amazon import get_amazon_client
from backuper.utils.validate import ValidateBase
from backuper.utils import get_msg
from backuper.utils.constants import amazon_regions
from time import sleep


class ValidateElasticache(ValidateBase):

    def params_validate(self, **kwargs):

        if kwargs['action'] == 'create':
            parameters_schema = self.tr.Dict({
                self.tr.Key('region'): self.tr.Enum(*amazon_regions),
                self.tr.Key('snapshot_id'): self.tr.String,
                self.tr.Key('database_id'): self.tr.String
            })

        if kwargs['action'] == 'restore':
            parameters_schema = self.tr.Dict({
                self.tr.Key('region'): self.tr.Enum(*amazon_regions),
                self.tr.Key('snapshot_id'): self.tr.String,
                self.tr.Key('database_id'): self.tr.String
            })

        if kwargs['action'] == 'delete':
            parameters_schema = self.tr.Dict({
                self.tr.Key('region'): self.tr.Enum(*amazon_regions),
                self.tr.Key('snapshot_id'): self.tr.String
            })
        parameters_schema(kwargs['parameters'])


class Main(object):

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.parameters = self.kwargs['parameters']
        self.validate = ValidateElasticache()

    def create_snapshot(self):
        c = get_amazon_client(self.kwargs['type'], self.kwargs['region'])
        response = c.create_snapshot(
            SnapshotName=self.parameters['snapshot_id'],
            CacheClusterId=self.parameters['database_id']
        )
        return response

    def restore_from_snapshot(self):
        c = get_amazon_client(self.kwargs['type'], self.parameters['region'])
        response = c.create_cache_cluster(
            SnapshotName=self.parameters['snapshot_id'],
            CacheClusterId=self.parameters['database_id']
        )
        return response

    def delete_snapshot(self):
        c = get_amazon_client(parameters['type'], self.parameters['region'])
        response = c.delete_snapshot(
            SnapshotName=self.parameters['snapshot_id']
        )
        return response

    def snapshot_is_available(self):
        c = get_amazon_client(self.kwargs['type'], self.parameters['region'])
        response = c.describe_snapshots(
            SnapshotName=self.parameters['snapshot_id'])
        response_status = response['Snapshots'][0]['SnapshotStatus']
        return response_status

    def cache_cluster_is_available(self):
        c = get_amazon_client(self.kwargs['type'], self.parameters['region'])
        response = c.describe_cache_clusters(
            CacheClusterId=self.parameters['database_id'])
        response_status = response['CacheClusters'][0]['CacheClusterStatus']
        return response_status

    def run(self):

        if self.kwargs['action'] == 'create':
            action = self.create_snapshot()
            print(get_msg(kwargs['type']) +
                  kwargs['action'] + 'is in progress...\n')
            i = 0
            while i != 'available':
                i = self.snapshot_is_available(parameters['region'])
                sleep(60)

        if self.kwargs['action'] == 'restore':
            action = self.restore_from_snapshot()
            print(get_msg(kwargs['type']) +
                  kwargs['action'] + 'is in progress...\n')
            i = 0
            while i != 'available':
                i = self.cache_cluster_is_available(parameters['region'])
                sleep(60)

        if self.kwargs['action'] == 'delete':
            action = self.delete_snapshot()

        print(get_msg(kwargs['type']) + kwargs['action'] +
              'completed in {} region...\n'.format(parameters['region']))
