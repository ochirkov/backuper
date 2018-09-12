import logging

from time import sleep

from backuper.adapters import Action
from backuper.params import one_of, Str

from .common import aws_regions, get_aws_client


logger = logging.getLogger(__name__)


Region = one_of('Region', Str, *aws_regions)


class Elasticache:

    region: Region
    snapshot_id: Str

    def __init__(self):
        self.client = get_aws_client('elasticache', self.region)
        self.action = type(self).__name__.lower()


class Create(Elasticache, Action):

    database_id: Str

    def run(self):
        self._create_snapshot(SnapshotName=self.snapshot_id,
                              CacheClusterId=self.database_id)

        response = self._snapshot_is_available(self.snapshot_id)
        while response != 'available':
            logger.info(
                'Elasticache {0} is in progress...'.format(self.action)
            )
            sleep(60)
            response = self._snapshot_is_available(self.snapshot_id)

    def _create_snapshot(self, snapshot_id, database_id):
        return self.client.create_snapshot(
            SnapshotName=snapshot_id,
            CacheClusterId=database_id
        )

    # Move to base class?
    def _snapshot_is_available(self, snapshot_id):
        response = self.client.describe_snapshots(SnapshotName=snapshot_id)
        response_status = response['Snapshots'][0]['SnapshotStatus']
        return response_status

    # Move to base class?
    def _cache_cluster_is_available(self, database_id):
        response = self.client.describe_cache_clusters(
            CacheClusterId=database_id
        )
        response_status = response['CacheClusters'][0]['CacheClusterStatus']
        return response_status


class Delete(Elasticache, Action):

    def run(self):
        pass

    def _delete_snapshot(self, snapshot_id):
        return self.client.delete_snapshot(
            SnapshotName=snapshot_id,
        )


class Restore(Elasticache, Action):

    database_id: Str

    def run(self):
        pass

    def _restore_from_snapshot(self, snapshot_id, database_id):
        return self.client.create_cache_cluster(
            SnapshotName=snapshot_id,
            CacheClusterId=database_id
        )
