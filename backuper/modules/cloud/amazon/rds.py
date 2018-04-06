import trafaret as tr

from time import sleep

from ....main import AbstractRunner
from ....modules.cloud.amazon import get_amazon_client
from ....utils.constants import (
    amazon_regions, wait_timeout, engines, snapshot_types,
)


class RDSValidator:

    def create_validate(self, parameters):
        parameters_schema = tr.Dict({
            tr.Key('region'): tr.Enum(*amazon_regions),
            tr.Key('snapshot_type'): tr.Enum(*snapshot_types),
            tr.Key('engine'): tr.Enum(*engines['rds']),
            tr.Key('DBSnapshotIdentifier'): tr.String,
            tr.Key('DBInstanceIdentifier'): tr.String,
            tr.Key('Tags', optional=True): tr.List(
                tr.Dict().allow_extra("*")),
            tr.Key('copy_to_region', optional=True): tr.Enum(
                *amazon_regions),
            tr.Key('wait_timeout', optional=True): tr.Int
        })

        parameters_schema(parameters)

    def restore_validate(self, parameters):
        parameters_schema = tr.Dict({
            tr.Key('region'): tr.Enum(*amazon_regions),
            tr.Key('engine'): tr.Enum(*engines['rds']),
            tr.Key('snapshot_type'): tr.Enum(*snapshot_types),
            tr.Key('snapshot_id'): tr.String,
            tr.Key('database_id'): tr.String,
            tr.Key('wait_timeout', optional=True): tr.Int
        })

        parameters_schema(parameters)

    def delete_validate(self, parameters):
        parameters_schema = tr.Dict({
            tr.Key('region'): tr.Enum(*amazon_regions),
            tr.Key('snapshot_type'): tr.Enum(*snapshot_types),
            tr.Key('snapshot_id'): tr.String,
            tr.Key('fail_on_error', optional=True): tr.Bool
        })

        parameters_schema(parameters)


class Main(AbstractRunner):
    choices = ['create', 'delete', 'restore']
    validator = RDSValidator()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.client = get_amazon_client(
            self.service, self.params['region'])

    def get_snapshots(self):

        response = self.client.describe_db_snapshots()

        return response

    def create_snapshot(self):

        response = self.client.create_db_snapshot(
            DBSnapshotIdentifier=self.params['DBSnapshotIdentifier'],
            DBInstanceIdentifier=self.params['DBInstanceIdentifier'],
            Tags=self.params.get('Tags')
        )
        return response

    def restore_from_snapshot(self):

        response = self.client.restore_db_instance_from_db_snapshot(
            DBSnapshotIdentifier=self.params['DBSnapshotIdentifier'],
            DBInstanceIdentifier=self.params['DBInstanceIdentifier']
        )

        return response

    def instance_is_available(self):

        instance = self.client.describe_db_instances(
            DBInstanceIdentifier=self.params['DBInstanceIdentifier'])
        status = instance['DBInstances'][0]['DBInstanceStatus']

        return status

    def delete_snapshot(self, snapshots):

        r = []
        for snapshot in snapshots:
            response = self.client.delete_db_snapshot(
                DBSnapshotIdentifier=snapshot['DBSnapshotIdentifier']
            )
            self.logger.debug(' is in progress...')
            r.append(response)

        return r

    def copy_snapshot(self, resource, region):

        source_db_snapshot_identifier = resource['DBSnapshot']['DBSnapshotArn']
        self.client = get_amazon_client(self.service, region)
        response = self.client.copy_db_snapshot(
            SourceDBSnapshotIdentifier=source_db_snapshot_identifier,
            TargetDBSnapshotIdentifier=self.params['DBSnapshotIdentifier'],
            CopyTags=True,
            SourceRegion=self.params['region'],
        )

        return response

    def snapshot_status(self, snapshot_id, region):

        self.client = get_amazon_client(self.service, region)
        snapshots = self.get_snapshots()
        for snapshot in snapshots['DBSnapshots']:
            if snapshot['DBSnapshotIdentifier'] == snapshot_id:
                status = snapshot['Status']
        return status

    def wait_snapshot(self, snapshot_id, region):

        if self.params.get('wait_timeout') is None:
            counter = wait_timeout
        else:
            counter = self.params['wait_timeout']

        self.logger.debug(' is in progress...')
        while counter >= 0:
            status = self.snapshot_status(snapshot_id, region)
            if status == 'available':
                self.logger.debug(
                    '{} snapshot is available in region...\n'.format(
                        snapshot_id))
                break
            else:
                sleep(30)
                counter -= 30

    def filter_snapshots_by_type(self, snapshots, snapshot_type):

        filtered = []
        for snapshot in snapshots['DBSnapshots']:
            if snapshot['SnapshotType'] == snapshot_type:
                filtered.append(snapshot)
        return filtered

    def adapted_snapshots(self, snapshots):

        for snapshot in snapshots:
            snapshot['snapshotName'] = snapshot['DBSnapshotIdentifier']
            snapshot['creationTime'] = snapshot['SnapshotCreateTime']
        return snapshots

    # def run(self):
    #
    #     if self.params.get('fail_on_error') is None:
    #         fail_on_error = f_on_e
    #     else:
    #         fail_on_error = self.params.get('fail_on_error')
    #
    #     if self.kwargs['action'] == 'create':
    #         resource = self.create_snapshot()
    #         self.wait_snapshot(
    #             self.params['DBSnapshotIdentifier'],
    #             self.params['region'])
    #         if self.params.get('copy_to_region') is not None:
    #             jobs = []
    #             for region in self.params.get('copy_to_region'):
    #                 self.copy_snapshot(resource, region)
    #                 p = Process(target=self.wait_snapshot,
    #                             args=(self.params['DBSnapshotIdentifier'],
    #                                   region))
    #                 jobs.append(p)
    #                 p.start()
    #
    #     if self.kwargs['action'] == 'delete':
    #
    #         snapshots = self.get_snapshots()
    #         validate_empty_snapshots(
    #             snapshots['DBSnapshots'],
    #             get_msg(self.kwargs['type']) + ' There are no snapshots in {} region...\n'.format(self.params['region']),  # noqa
    #             fail_on_error)
    #
    #         if self.params['snapshot_type'] != 'all':
    #             snapshots_by_type = self.filter_snapshots_by_type(
    #                 snapshots, self.params['snapshot_type'])
    #         else:
    #             snapshots_by_type = [
    #                 snapshot for snapshot in snapshots['DBSnapshots']]
    #
    #         validate_empty_snapshots(
    #             snapshots_by_type, get_msg(self.kwargs['type']) +
    #                                ' There are no {} snapshots in {} region...\n'.format(self.params['snapshot_type'],  # noqa
    #                                                                                      self.params['region']),  # noqa
    #             fail_on_error)
    #
    #         adapted = self.adapted_snapshots(snapshots_by_type)
    #
    #         snapshots_filtered = f_main(
    #             self.params.get('filters'), adapted)
    #
    #         self.delete_snapshot(snapshots_filtered)

        # if self.kwargs['action'] == 'restore':
        #     restore = self.restore_from_snapshot()
        #     print(get_msg(self.kwargs['type']) +
        #           self.kwargs['action'] + ' is in progress...\n')
        #     i = 0
        #     while i != 'available':
        #         i = self.instance_is_available()
        #         sleep(60)
        #
        # print(get_msg(self.kwargs['type']) + self.kwargs['action'] +
        #       ' completed in {} region...\n'.format(self.params['region']))
