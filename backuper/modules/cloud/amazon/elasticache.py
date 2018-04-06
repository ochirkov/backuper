from time import sleep
import trafaret as tr
from backuper.main import AbstractRunner
from backuper.modules.cloud.amazon import get_amazon_client
from backuper.utils.constants import amazon_regions
from backuper.utils.validate import OneOptKey


class ElasticacheValidator:
    _schema = tr.Dict({
                tr.Key('region'): tr.Enum(*amazon_regions),
                tr.Key('snapshot_name'): tr.String,
            })
    _cluster_id = tr.Dict({OneOptKey(
        'replication_group_id', 'cache_cluster_id'): tr.String})
    _s3_bucket_name = tr.Dict({tr.Key('s3_bucket_name'): tr.String})

    _schema_db = _schema + _cluster_id
    _schema_s3 = _schema + _s3_bucket_name

    def create_validate(self, params):
        self._schema_db(params)

    def copy_to_s3_validate(self, params):
        self._schema_s3(params)

    def restore_validate(self, params):
        self._schema_db(params)

    def delete_validate(self, params):
        self._schema(params)


class Main(AbstractRunner):

    choices = ['create', 'delete', 'restore', 'copy_to_s3']
    validator = ElasticacheValidator()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = get_amazon_client(
            self.type, self.params['region']
        )

    def _create_snapshot(
            self,
            snapshot_name,
            cache_cluster_id=None,
            replication_group_id=None
    ):
        if cache_cluster_id:
            response = self.client.create_snapshot(
                SnapshotName=snapshot_name,
                CacheClusterId=cache_cluster_id
            )
        elif replication_group_id:
            response = self.client.create_snapshot(
                SnapshotName=snapshot_name,
                ReplicationGroupId=replication_group_id
            )
        return response

    def _restore_from_snapshot(
            self,
            snapshot_name,
            cache_cluster_id=None,
            replication_group_id=None
    ):
        if cache_cluster_id:
            response = self.client.create_cache_cluster(
                SnapshotName=snapshot_name,
                CacheClusterId=cache_cluster_id
            )
        elif replication_group_id:
            response = self.client.create_cache_cluster(
                SnapshotName=snapshot_name,
                ReplicationGroupId=replication_group_id
            )
        return response

    def _delete_snapshot(self, snapshot_name):
        response = self.client.delete_snapshot(
            SnapshotName=snapshot_name,
        )
        return response

    def _describe_snapshots(self, snapshot_name):
        response = self.client.describe_snapshots(
            SnapshotName=snapshot_name
        )
        return response

    def _copy_snapshot(
            self,
            source_snapshot_name,
            target_snapshot_name,
            target_bucket
    ):
        response = self.client.copy_snapshot(
            SourceSnapshotName=source_snapshot_name,
            TargetSnapshotName=target_snapshot_name,
            TargetBucket=target_bucket
        )
        return response

    def _wait_snapshot_available(self, snapshot_name):

        status = None

        while status != 'available':
            snapshot_meta = self._describe_snapshots(snapshot_name)
            status = snapshot_meta['Snapshots'][0]['SnapshotStatus']
            self.logger.info('is in progress...\n')
            sleep(60)


    def create(self, params):
        self._create_snapshot(
            params['snapshot_name'],
            cache_cluster_id=params.get('cache_cluster_id'),
            replication_group_id=params.get('replication_group_id')
        )
        self._wait_snapshot_available(params['snapshot_name'])


    def copy_to_s3(self, params):
        self._copy_snapshot(
            params['snapshot_name'],
            params['snapshot_name'],
            params['s3_bucket_name']
        )
        self._wait_snapshot_available(params['snapshot_name'])


    def restore(self, params):
        self._restore_from_snapshot(
            params['snapshot_name'],
            cache_cluster_id=params.get('cache_cluster_id'),
            replication_group_id=params.get('replication_group_id')
        )
        self._wait_snapshot_available(params['snapshot_name'])


    def delete(self, params):
        pass
