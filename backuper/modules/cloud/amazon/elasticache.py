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
    _schema_db = _schema + tr.Dict({tr.Key('database_id'): tr.String})

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

    def _create_snapshot(self, snapshot_name, database_id):
        response = self.client.create_snapshot(
            SnapshotName=snapshot_name,
            CacheClusterId=database_id
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

    def _snapshot_is_available(self, snapshot_name):
        response = self.client.describe_snapshots(SnapshotName=snapshot_name)
        response_status = response['Snapshots'][0]['SnapshotStatus']
        return response_status

    def _cache_cluster_is_available(self, database_id):
        response = self.client.describe_cache_clusters(
            CacheClusterId=database_id
        )
        response_status = response['CacheClusters'][0]['CacheClusterStatus']
        return response_status


    def create(self, params):
        self._create_snapshot(
            params['snapshot_name'],
            params['database_id']
        )

        i = None
        while i != 'available':
            self.logger.info(
                get_msg(self.type, self.action + ' is in progress...\n'))
            i = self._snapshot_is_available(params['snapshot_name'])
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
