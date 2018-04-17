from time import sleep
import trafaret as tr
from backuper.main import AbstractRunner
from backuper.utils.filters import FilterMixin
from backuper.modules.cloud.amazon import get_amazon_client
from backuper.utils.validate import OneOptKey
from backuper.utils.helpers import remove_in_parallel, SnapshotInfo
from backuper.utils.constants import amazon_regions


class RDSValidator:

    _schema = tr.Dict({
        tr.Key('region'): tr.Enum(*amazon_regions),
        tr.Key('snapshot_name'): tr.String
    })

    _create = tr.Dict({OneOptKey(
        'db_cluster_id', 'db_instance_id'): tr.String})
    _copy_to_region = tr.Dict({
        tr.Key('copy_to_region', optional=True):
            tr.Enum(*amazon_regions)}
    )

    _create_schema = _schema + _create

    def create_validate(self, params):
        self._create_schema(params)

    def copy_to_region_validate(self, params):
        self._schema(params)

    def restore_validate(self, params):
        self._schema(params)

    def delete_validate(self, params):
        self._schema(params)


class Main(AbstractRunner, FilterMixin):

    choices = ['create', 'delete', 'restore', 'copy_to_region']
    validator = RDSValidator()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = get_amazon_client(
            self.service, self.params['region']
        )

    def _create_snapshot(
            self,
            snapshot_name,
            db_instance_id,
            db_cluster_id
    ):
        if db_instance_id:
            response = self.client.create_db_snapshot(
                DBSnapshotIdentifier=snapshot_name,
                DBInstanceIdentifier=db_instance_id
            )
        elif db_cluster_id:
            response = self.client.create_db_snapshot(
                DBSnapshotIdentifier=snapshot_name,
                DBClusterIdentifier=db_cluster_id
            )

        return response

    def _describe_snapshots(
        self,
        snapshot_name,
        db_instance_id,
        db_cluster_id

    ):
        if db_instance_id:
            response = self.client.describe_db_snapshots(
                DBSnapshotIdentifier=snapshot_name
                )
        elif db_cluster_id:
            response = self.client.describe_db_cluster_snapshots(
                DBClusterSnapshotIdentifier=snapshot_name
                )

        return response

    def _wait_snapshot_available(
            self,
            snapshot_name,
            db_instance_id,
            db_cluster_id
    ):

        status = None

        while status != 'available':
            snapshot_meta = self._describe_snapshots(
                snapshot_name,
                db_instance_id,
                db_cluster_id
            )
            status = snapshot_meta['DBSnapshots'][0]['Status']
            self.logger.info('is in progress...\n')
            sleep(60)


    def create(self, params):
        self._create_snapshot(
            snapshot_name=params['snapshot_name'],
            db_instance_id=params.get('db_instance_id'),
            db_cluster_id=params.get('db_cluster_id')
        )
        self._wait_snapshot_available(
            params['snapshot_name'],
            params.get('db_instance_id'),
            params.get('db_cluster_id')
        )

    def copy_to_region(self, params):
        pass


    def restore(self, params):
        pass


    def delete(self, params):
        pass
