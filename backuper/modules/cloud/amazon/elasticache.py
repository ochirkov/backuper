from time import sleep
import trafaret as tr
from backuper.executor import AbstractRunner
from backuper.modules.cloud.amazon import get_amazon_client
from backuper.utils import get_msg
from backuper.utils.constants import amazon_regions
from backuper.utils.validate import BaseValidator


class ElasticacheValidator(BaseValidator):
    _schema = tr.Dict({
                tr.Key('region'): tr.Enum(*amazon_regions),
                tr.Key('snapshot_name'): tr.String,
            })

    replication_group_id = tr.Dict({tr.Key(
        'replication_group_id', optional=True): tr.String})
    cache_cluster_id = tr.Dict({tr.Key(
        'cache_cluster_id', optional=True): tr.String})

    _schema_db = _schema + replication_group_id + cache_cluster_id

    #TODO: create one req param from two optional

    def create_validate(self, params):
        self._schema_db(params)

    def restore_validate(self, params):
        self._schema_db(params)

    def delete_validate(self, params):
        self._schema(params)


class Main(AbstractRunner):

    choices = ['create', 'delete', 'restore']
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

    def _restore_from_snapshot(self, snapshot_name, database_id):
        response = self.client.create_cache_cluster(
            SnapshotName=snapshot_name,
            CacheClusterId=database_id
        )
        return response

    def _delete_snapshot(self, snapshot_name):
        response = self.client.delete_snapshot(
            SnapshotName=snapshot_name,
        )
        return response

    def _describe_snapshots(self, snapshot_name):
        response = self.client.describe_snapshots(SnapshotName=snapshot_name)
        return response

    def _cache_cluster_is_available(self, database_id):
        response = self.client.describe_cache_clusters(
            CacheClusterId=database_id
        )
        response_status = response['CacheClusters'][0]['CacheClusterStatus']
        return response_status


    def create(self, params):

        cache_cluster_id = params.get('cache_cluster_id')
        replication_group_id = params.get('replication_group_id')

        self._create_snapshot(
            params['snapshot_name'],
            cache_cluster_id=cache_cluster_id,
            replication_group_id=replication_group_id
        )

        snapshot_meta = self._describe_snapshots(params['snapshot_name'])
        status = snapshot_meta['Snapshots'][0]['SnapshotStatus']

        while status != 'available':
            self.logger.info(
                get_msg(self.type, self.action + ' is in progress...\n'))
            sleep(60)


    def delete(self, params):
        pass

    def restore(self, params):
        pass


        # if self.kwargs['action'] == 'restore':
        #     self.restore_from_snapshot()
        #     print(get_msg(self.kwargs['type']) +
        #           self.kwargs['action'] + ' is in progress...\n')
        #     i = 0
        #     while i != 'available':
        #         i = self.cache_cluster_is_available()
        #         sleep(60)
        #
        # if self.kwargs['action'] == 'delete':
        #     self.delete_snapshot()



        # print(get_msg(self.kwargs['type']) + self.kwargs['action'] +
        #       ' completed in {} region...\n'.format(self.parameters['region']))
