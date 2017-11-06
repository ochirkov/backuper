from time import sleep
from backuper.modules.cloud.amazon import get_amazon_client
from backuper.utils import get_msg
from backuper.utils.constants import amazonRegions
from backuper.utils.validate import ValidateBase


class ValidateElasticache(ValidateBase):

    def params_validate(self, **kwargs):

        if kwargs['action'] == 'create':
            parameters_schema = self.tr.Dict({
                self.tr.Key('region'): self.tr.Enum(*amazonRegions),
                self.tr.Key('snapshotId'): self.tr.String,
                self.tr.Key('databaseId'): self.tr.String
            })

        if kwargs['action'] == 'restore':
            parameters_schema = self.tr.Dict({
                self.tr.Key('region'): self.tr.Enum(*amazonRegions),
                self.tr.Key('snapshotId'): self.tr.String,
                self.tr.Key('databaseId'): self.tr.String
            })

        if kwargs['action'] == 'delete':
            parameters_schema = self.tr.Dict({
                self.tr.Key('region'): self.tr.Enum(*amazonRegions),
                self.tr.Key('snapshotId'): self.tr.String
            })
        parameters_schema(kwargs['parameters'])


class Main(object):

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.parameters = self.kwargs['parameters']
        self.validate = ValidateElasticache()
        self.client = get_amazon_client(
            self.kwargs['type'], self.parameters['region'])

    def create_snapshot(self):
        response = self.client.create_snapshot(
            SnapshotName=self.parameters['snapshotId'],
            CacheClusterId=self.parameters['databaseId']
        )
        return response

    def restore_from_snapshot(self):
        response = self.client.create_cache_cluster(
            SnapshotName=self.parameters['snapshotId'],
            CacheClusterId=self.parameters['databaseId']
        )
        return response

    def delete_snapshot(self):
        response = self.client.delete_snapshot(
            SnapshotName=self.parameters['snapshotId']
        )
        return response

    def snapshot_is_available(self):
        response = self.client.describe_snapshots(
            SnapshotName=self.parameters['snapshotId'])
        response_status = response['Snapshots'][0]['SnapshotStatus']
        return response_status

    def cache_cluster_is_available(self):
        response = self.client.describe_cache_clusters(
            CacheClusterId=self.parameters['databaseId'])
        response_status = response['CacheClusters'][0]['CacheClusterStatus']
        return response_status

    def run(self):

        if self.kwargs['action'] == 'create':
            self.create_snapshot()
            print(get_msg(self.kwargs['type']) +
                  self.kwargs['action'] + ' is in progress...\n')
            i = 0
            while i != 'available':
                i = self.snapshot_is_available()
                sleep(60)

        if self.kwargs['action'] == 'restore':
            self.restore_from_snapshot()
            print(get_msg(self.kwargs['type']) +
                  self.kwargs['action'] + ' is in progress...\n')
            i = 0
            while i != 'available':
                i = self.cache_cluster_is_available()
                sleep(60)

        if self.kwargs['action'] == 'delete':
            self.delete_snapshot()

        print(get_msg(self.kwargs['type']) + self.kwargs['action'] +
              ' completed in {} region...\n'.format(self.parameters['region']))
