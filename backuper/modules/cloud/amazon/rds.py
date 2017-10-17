from backuper.modules.cloud.amazon import get_amazon_client
from backuper.utils.validate import ValidateBase, validate_empty_snapshots
from backuper.utils import get_msg
from backuper.utils.constants import amazon_regions
from backuper.utils.filters import main as f_main
from time import sleep
from multiprocessing import Process


class ValidateRDS(ValidateBase):

    def params_validate(self, **kwargs):

        if kwargs['action'] == 'create':

            parameters_schema = self.tr.Dict({
                self.tr.Key('snapshot_identifier'): self.tr.String,
                self.tr.Key('region'): self.tr.String,
                self.tr.Key('db_identifier'): self.tr.String,
                self.tr.Key('copy_to_region', optional=True): self.tr.List(
                    self.tr.String, min_length=1)
            })

        if kwargs['action'] == 'delete':

            parameters_schema = self.tr.Dict({
                self.tr.Key('region'): self.tr.Enum(*amazon_regions),
                self.tr.Key('snapshot_type'): self.tr.Enum(
                    *['standard', 'manual', 'all'])
            })

        parameters_schema(kwargs['parameters'])


class Main(object):

    def __init__(self, **kwargs):

        self.kwargs = kwargs
        self.validate = ValidateRDS()
        self.config()

    def config(self):

        params = dict(a_region=None,
                      a_snap_id=None,
                      a_db_identifier=None,
                      a_type=None,
                      a_copy_to_region=None,
                      a_snapshot_type=None,
                      a_filters=None)

        parameters = self.kwargs['parameters']
        params['a_region'] = parameters['region']
        params['a_type'] = self.kwargs['type']

        choices = ['create', 'delete', 'restore']

        self.validate.action_validate(choices, **self.kwargs)
        self.validate.params_validate(**self.kwargs)

        if self.kwargs['action'] == 'create':
            params['a_copy_to_region'] = parameters['copy_to_region']
            params['a_snap_id'] = parameters['snapshot_identifier']
            params['a_db_identifier'] = parameters['db_identifier']

        if self.kwargs['action'] == 'delete':
            params['a_snapshot_type'] = parameters['snapshot_type']
            params['a_filters'] = self.kwargs['filters']
            self.validate.filters_validate(**self.kwargs)

        return params

    def get_snapshots(self, region):

        c = get_amazon_client(self.config()['a_type'], region)
        response = c.describe_db_snapshots()

        return response

    def create_snapshot(self):

        c = get_amazon_client(self.config()['a_type'],
                              self.config()['a_region'])
        response = c.create_db_snapshot(
            DBSnapshotIdentifier=self.config()['a_snap_id'],
            DBInstanceIdentifier=self.config()['a_db_identifier']
        )

        return response

    def delete_snapshot(self, region, snapshots):

        c = get_amazon_client(self.config()['a_type'], region)

        r = []
        for i in snapshots:
            response = c.delete_db_snapshot(
                DBSnapshotIdentifier=i['DBSnapshotIdentifier']
            )
            print(get_msg(self.config()['a_type']) +
                  'Deleting snapshot {} in {} region...'.format(
                i['DBSnapshotIdentifier'], region))
            r.append(response)

        return r

    def copy_snapshot(self, resource, region):

        SourceDBSnapshotIdentifier = resource['DBSnapshot']['DBSnapshotArn']

        c = get_amazon_client(self.config()['a_type'], region)

        response = c.copy_db_snapshot(
            SourceDBSnapshotIdentifier=SourceDBSnapshotIdentifier,
            TargetDBSnapshotIdentifier=self.config()['a_snap_id'],
            CopyTags=True,
            SourceRegion=self.config()['a_region']
        )

        return response

    def snapshot_status(self, region, DBSnapshotIdentifier):

        snapshots = self.get_snapshots(region)
        for i in snapshots['DBSnapshots']:
            if i['DBSnapshotIdentifier'] == DBSnapshotIdentifier:
                status = i['Status']

        return status

    def wait_snapshot(self, region, snapshot_identifier):

        counter = 4800
        #TODO: counter from config

        while counter >= 0:

            status = self.snapshot_status(region, snapshot_identifier)

            print(get_msg(self.config()['a_type']) +
                  'Creating of {} is in process in {} region...'.format(
                snapshot_identifier, region))
            if status == 'available':
                print(get_msg(self.config()['a_type']) +
                      '{} snapshot is available in {} region...\n'.format(
                          snapshot_identifier, region))
                break
            else:
                sleep(30)
                counter -= 30

    def filter_snaps_by_type(self, snapshots, type):

        filtered = []

        for i in snapshots['DBSnapshots']:
            if i['SnapshotType'] == type:
                filtered.append(i)

        return filtered

    def adapty_snapshots(self, snapshots):

        for snap in snapshots:
            snap['snapshot_name'] = snap['DBSnapshotIdentifier']
            snap['creation_time'] = snap['SnapshotCreateTime']

        return snapshots

    def run(self):

        if self.kwargs['action'] == 'create':

            create_r = self.create_snapshot()
            self.wait_snapshot(self.config()['a_region'],
                               self.config()['a_snap_id'])

            if self.config()['a_copy_to_region'] is not None:
                jobs = []
                for region in self.config()['a_copy_to_region']:
                    self.copy_snapshot(create_r, region)
                    p = Process(target=self.wait_snapshot,
                                args=(region, self.config()['a_snap_id']))
                    jobs.append(p)
                    p.start()

        if self.kwargs['action'] == 'delete':
            snapshots = self.get_snapshots(self.config()['a_region'])

            validate_empty_snapshots(snapshots['DBSnapshots'],
                                     get_msg(self.config()['a_type']) +
                      'There are no snapshots in {} region...\n'.format(
                          self.config()['a_region']))

            if self.config()['a_snapshot_type'] != 'all':
                snaps_by_type = self.filter_snaps_by_type(snapshots,
                                            self.config()['a_snapshot_type'])
            else:
                snaps_by_type = [i for i in snapshots['DBSnapshots']]

            validate_empty_snapshots(snaps_by_type,
                                     get_msg(self.config()['a_type']) +
                      'There are no {} snapshots in {} region...\n'.format(
                          self.config()['a_snapshot_type'],
                          self.config()['a_region']))

            adapted = self.adapty_snapshots(snaps_by_type)
            snaps_filtered = f_main(self.config()['a_filters'], adapted)

            self.delete_snapshot(self.config()['a_region'], snaps_filtered)
