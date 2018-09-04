import logging

from time import sleep

from backuper.adapters import Action
from backuper.params import Int, one_of, Str, Tags

from .common import aws_regions, get_aws_client, snapshot_types


logger = logging.getLogger(__name__)


Region = one_of('Region', Str, *aws_regions)
SnapshotType = one_of('SnapshotType', Str, *snapshot_types)
Engine = one_of('Engine', Str, 'oracle-se1', 'oracle-se2', 'sqlserver-ee'
                'sqlserver-ex', 'sqlserver-se', 'sqlserver-web')


class RDS:

    region: Region
    snapshot_type: SnapshotType
    snapshot_identifier: Str
    instance_identifier: Str

    def __init__(self):
        self.client = get_aws_client('rds', self.region)
        self.action = type(self).__name__.lower()

    def get_snapshots(self):
        return self.client.describe_db_snapshots()

    def create_snapshot(self):
        return self.client.create_db_snapshot(
            DBSnapshotIdentifier=self.snapshot_identifier,
            DBInstanceIdentifier=self.instance_identifier,
            Tags=Tags,
        )

    def restore_from_snapshot(self):
        return self.client.restore_db_instance_from_db_snapshot(
            DBSnapshotIdentifier=self.snapshot_identifier,
            DBInstanceIdentifier=self.instance_identifier,
        )

    def instance_is_available(self):
        instance = self.client.describe_db_instances(
            DBInstanceIdentifier=self.instance_identifier,
        )
        return instance['DBInstances'][0]['DBInstanceStatus']

    def delete_snapshot(self, snapshots):
        responses = []
        for snapshot in snapshots:
            snapshot_id = snapshot['DBSnapshotIdentifier']
            response = self.client.delete_db_snapshot(
                DBSnapshotIdentifier=snapshot_id,
            )
            logger.info('rds {0} is in progress...'.format(self.action))
            responses.append(response)
        return responses

    def copy_snapshot(self, resource, region):
        client = get_aws_client('rds', region)
        source_db_snapshot_identifier = resource['DBSnapshot']['DBSnapshotArn']
        response = client.copy_db_snapshot(
            SourceDBSnapshotIdentifier=source_db_snapshot_identifier,
            TargetDBSnapshotIdentifier=self.snapshot_identifier,
            CopyTags=True,
            SourceRegion=self.region,
        )
        return response

    def snapshot_status(self, snapshot_id, region):
        client = get_aws_client('rds', region)
        snapshots = client.describe_db_snapshots()
        for snapshot in snapshots['DBSnapshots']:
            if snapshot['DBSnapshotIdentifier'] == snapshot_id:
                status = snapshot['Status']
        return status

    def wait_snapshot(self, snapshot_id, region):
        counter = self.wait_timeout

        logger.info('rds {0} is in progress...'.format(self.action))
        while counter >= 0:
            if self.snapshot_status(snapshot_id, region) != 'available':
                sleep(30)
                counter -= 30
                continue

            logger.info(
                'rds {0} is available in region {1}'
                .format(snapshot_id, region)
            )

    def filter_snapshots_by_type(self, snapshots, snapshot_type):
        return [snapshot for snapshot in snapshots
                if snapshot['SnapshotType'] == snapshot_type]

    def adapted_snapshots(self, snapshots):
        for snapshot in snapshots:
            snapshot['snapshotName'] = snapshot['DBSnapshotIdentifier']
            snapshot['creationTime'] = snapshot['SnapshotCreateTime']
        return snapshots


class Create(RDS, Action):

    engine: Engine
    tags: Tags = {}
    copy_to_region: Region
    wait_timeout: Int = 4800

    def run(self):
        resource = self.create_snapshot()
        self.wait_snapshot(self.snapshot_identifier, self.region)

        if self.copy_to_region:
            self.copy_snapshot(resource, self.copy_to_region)
            self.wait_snapshot(self.snapshot_identifier, self.copy_to_region)


class Delete(RDS, Action):

    def run(self):
        snapshots = self.get_snapshots()['DBSnapshots']
        if not snapshots:
            raise RuntimeError(
                'There are no snapshots in {0} region...'.format(self.region)
            )

        if self.snapshot_type != 'all':
            snapshots_by_type = [
                snapshot for snapshot in snapshots
                if snapshot['SnapshotType'] == self.snapshot_type
            ]
        else:
            snapshots_by_type = snapshots

        if not snapshots_by_type:
            raise RuntimeError(
                'There are no {0} snapshots in {1} region...'.
                format(self.snapshot_type, self.region)
            )

        adapted = self.adapted_snapshots(snapshots_by_type)

        # TODO: Filters
        snapshots_filtered = adapted

        self.delete_snapshot(snapshots_filtered)
