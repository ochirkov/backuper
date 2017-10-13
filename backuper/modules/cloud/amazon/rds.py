from backuper.modules.cloud.amazon import get_amazon_client
from backuper.utils import get_msg
import trafaret as t
from backuper.utils.validate import ValidateBase
from time import sleep
from multiprocessing import Process


class ValidateRDS(ValidateBase):

    def params_validate(self, **kwargs):

        if kwargs['action'] == 'create':

            parameters_schema = t.Dict({
                t.Key('snapshot_identifier'): t.String,
                t.Key('region'): t.String,
                t.Key('db_identifier'): t.String,
                t.Key('copy_to_region', optional=True): t.List(
                    t.String, min_length=1)
            })

        parameters_schema(kwargs['parameters'])


class Main(object):

    def __init__(self, **kwargs):

        self.kwargs = kwargs
        self.validate = ValidateRDS()
        self.config()

    def config(self):

        choices = ['create', 'delete', 'restore']

        self.validate.action_validate(choices, **self.kwargs)
        self.validate.params_validate(**self.kwargs)

    def get_snapshots(self, region):

        c = get_amazon_client(self.kwargs['type'], region)
        response = c.describe_db_snapshots()

        return response

    def create_snapshot(self):

        c = get_amazon_client(self.kwargs['type'],
                              self.kwargs['parameters']['region'])
        response = c.create_db_snapshot(
            DBSnapshotIdentifier=self.kwargs['parameters']['snapshot_identifier'],
            DBInstanceIdentifier=self.kwargs['parameters']['db_identifier']
        )

        return response

    def delete_snapshot(self, region, snapshots):

        c = get_amazon_client(self.module, region)

        r = []
        for i in snapshots:
            response = c.delete_db_snapshot(
                DBSnapshotIdentifier=i
            )
            print(get_msg(
                self.module) + 'Deleting snapshot {} in {} region...'.format(
                i, region))
            print(get_msg(
                self.module) + 'Snapshot status of {} in {} region is {}'.format(
                i, region, response['DBSnapshot']['Status']))
            print('\n')
            r.append(response)

        return r

    def copy_snapshot(self, resource, region):

        SourceDBSnapshotIdentifier = resource['DBSnapshot']['DBSnapshotArn']

        c = get_amazon_client(self.kwargs['type'], region)

        response = c.copy_db_snapshot(
            SourceDBSnapshotIdentifier=SourceDBSnapshotIdentifier,
            TargetDBSnapshotIdentifier=self.kwargs['parameters']['snapshot_identifier'],
            CopyTags=True,
            SourceRegion=self.kwargs['parameters']['region']
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

        while counter >= 0:

            status = self.snapshot_status(region, snapshot_identifier)

            print(get_msg(self.kwargs['type']) +
                  'Creating of {} is in process in {} region...'.format(
                snapshot_identifier, region))
            if status == 'available':
                print(get_msg(self.kwargs['type']) +
                      '{} snapshot is available in {} region...\n'.format(
                          snapshot_identifier, region))
                break
            else:
                sleep(30)
                counter -= 30

    def run(self):

        if self.kwargs['action'] == 'create':

            create_r = self.create_snapshot()
            self.wait_snapshot(self.kwargs['parameters']['region'],
                               self.kwargs['parameters']['snapshot_identifier'])

            if self.kwargs['parameters']['copy_to_region'] is not None:
                jobs = []
                for region in self.kwargs['parameters']['copy_to_region']:
                    self.copy_snapshot(create_r, region)
                    p = Process(target=self.wait_snapshot,
                                args=(region, self.kwargs['parameters']['snapshot_identifier']))
                    jobs.append(p)
                    p.start()
