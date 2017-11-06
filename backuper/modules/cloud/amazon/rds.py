from backuper.modules.cloud.amazon import get_amazon_client
from backuper.utils.validate import ValidateBase, validate_empty_snapshots
from backuper.utils import get_msg
from backuper.utils.constants import amazonRegions, waitTimeout
from backuper.utils.filters import main as f_main
from time import sleep
from multiprocessing import Process


class ValidateRDS(ValidateBase):

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
                self.tr.Key('snapshotId'): self.tr.String,
                self.tr.Key('snapshotType'): self.tr.Enum(
                    *['standard', 'manual', 'all'])
            })
        parameters_schema(kwargs['parameters'])


class Main(object):

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.parameters = self.kwargs['parameters']
        self.validate = ValidateRDS()
        self.client = get_amazon_client(
            self.kwargs['type'], self.parameters['region'])

    def get_snapshots(self):
        response = self.client.describe_db_snapshots()

        return response

    def create_snapshot(self):
        response = self.client.create_db_snapshot(
            DBSnapshotIdentifier=self.parameters['snapshotId'],
            DBInstanceIdentifier=self.parameters['databaseId']
        )
        return response

    def restore_from_snapshot(self):
        response = self.client.restore_db_instance_from_db_snapshot(
            DBSnapshotIdentifier=self.parameters['snapshotId'],
            DBInstanceIdentifier=self.parameters['databaseId']
        )

        return response

    def instance_is_available(self):
        instance = self.client.describe_db_instances(
            DBInstanceIdentifier=self.parameters['databaseId'])
        status = instance['DBInstances'][0]['DBInstanceStatus']

        return status

    def delete_snapshot(self, snapshots):
        r = []
        for snapshot in snapshots:
            response = self.client.delete_db_snapshot(
                DBSnapshotIdentifier=snapshot['DBSnapshotIdentifier']
            )
            print(get_msg(self.kwargs['type']) +
                  self.kwargs['action'] + ' is in progress...\n')
            r.append(response)

        return r

    def copy_snapshot(self, resource):
        SourceDBSnapshotIdentifier = resource['DBSnapshot']['DBSnapshotArn']
        response = self.client.copy_db_snapshot(
            SourceDBSnapshotIdentifier=SourceDBSnapshotIdentifier,
            TargetDBSnapshotIdentifier=self.client.parameters['snapshotId'],
            CopyTags=True,
            SourceRegion=self.parameters['region']
        )

        return response

    def snapshot_status(self, DBSnapshotIdentifier):
        snapshots = self.client.get_snapshots()
        for snapshot in snapshots['DBSnapshots']:
            if snapshot['DBSnapshotIdentifier'] == DBSnapshotIdentifier:
                status = snapshot['Status']
        return status

    def wait_snapshot(self, snapshotId):
        if self.client.parameters['waitTimeout'] is None:
            counter = waitTimeout
        counter = self.client.parameters['waitTimeout']
        print(get_msg(self.kwargs['type']) +
                self.kwargs['action'] + ' is in progress...\n')
        while counter >= 0:
            status = self.client.snapshot_status(snapshotId)
            if status == 'available':
                print(get_msg(self.client.parameters['type']) +
                      '{} snapshot is available in region...\n'.format(
                          snapshotId))
                break
            else:
                sleep(30)
                counter -= 30

    def filter_snapshots_by_type(self, snapshots, type):
        filtered = []
        for snapshot in snapshots['DBSnapshots']:
            if snapshot['SnapshotType'] == type:
                filtered.append(snapshot)
        return filtered

    def adapted_snapshots(self, snapshots):
        for snapshot in snapshots:
            snapshot['snapshotName'] = snapshot['DBSnapshotIdentifier']
            snapshot['creationTime'] = snapshot['SnapshotCreateTime']
        return snapshots

    def run(self):

        if self.kwargs['action'] == 'create':
            create_r = self.client.create_snapshot()
            self.client.wait_snapshot(self.client.parameters['snapshotId'])
            if self.client.parameters['copyToRegion'] is not None:
                jobs = []
                for region in self.client.parameters['copyToRegion']:
                    self.copy_snapshot(create_r)
                    p = Process(target=self.wait_snapshot,
                                args=(self.client.parameters['snapshotId']))
                    jobs.append(p)
                    p.start()

        if self.kwargs['action'] == 'delete':
            snapshots = self.client.get_snapshots()
            validate_empty_snapshots(snapshots['DBSnapshots']))
            if self.client.parameters['snapshotType'] != 'all':
                snapshots_by_type=self.client.filter_snapshots_by_type(
                    snapshots, self.client.parameters['snapshotType'])
            snapshots_by_type=[snapshot for snapshot in snapshots['DBSnapshots']]
            validate_empty_snapshots(snapshots_by_type,
                                     get_msg(self.client.parameters['type']) +
                                     'There are no {} snapshots in region...\n'.format(
                                         self.client.parameters['snapshotType']))
            adapted = self.adapted_snapshots(snapshots_by_type)
            snapshots_filtered = f_main(
                self.client.parameters['filters'], adapted)
            self.client.delete_snapshot(snapshots_filtered)

        if self.kwargs['action'] == 'restore':
            restore = self.client.restore_from_snapshot()
            print(get_msg(self.kwargs['type']) +
                  self.kwargs['action'] + ' is in progress...\n')
            i = 0
            while i != 'available':
                i = self.client.instance_is_available()
                sleep(60)

        print(get_msg(self.kwargs['type']) + self.kwargs['action'] +
              ' completed in {} region...\n'.format(self.parameters['region']))
