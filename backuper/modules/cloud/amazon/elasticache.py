from backuper.modules.cloud.amazon import get_amazon_client
from backuper.utils.validate import ValidateBase, validate_empty_snapshots
from backuper.utils import get_msg
from backuper.utils.constants import amazon_regions, wait_timeout
from backuper.utils.filters import main as f_main
from time import sleep
from multiprocessing import Process

class ValidateElasticache(ValidateBase):

    def params_validate(self, **kwargs):

        if kwargs['action'] == 'create':

            parameters_schema = self.tr.Dict({
                self.tr.Key('region'): self.tr.Enum(*amazon_regions),
                self.tr.Key('snapshot_id'): self.tr.String,
                self.tr.Key('database_id'): self.tr.String
            })

        if kwargs['action'] == 'restore':

            parameters_schema = self.tr.Dict({
                self.tr.Key('region'): self.tr.Enum(*amazon_regions),
                self.tr.Key('snapshot_id'): self.tr.String,
                self.tr.Key('database_id'): self.tr.String
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
        self.validate = ValidateElasticache()
        self.config()

    def config(self):

        params = dict(a_region=None,
                      a_snapshot_id=None,
                      a_database_id=None,
                      a_type=None,
                      a_copy_to_region=None,
                      a_snapshot_type=None,
                      a_filters=None,
                      a_wait_timeout=None,
                      a_cluster=None,
                      a_description=None)

        parameters = self.kwargs['parameters']
        params['a_region'] = parameters['region']
        params['a_type'] = self.kwargs['type']
        params['a_cluster'] = self.kwargs['cluster']
        params['a_description'] = self.kwargs['description']

        choices = ['create', 'delete', 'restore']

        self.validate.action_validate(choices, **self.kwargs)
        self.validate.params_validate(**self.kwargs)

        if self.kwargs['action'] == 'create':
            params['a_snapshot_id'] = parameters['snapshot_id']
            params['a_database_id'] = parameters['database_id']

        if self.kwargs['action'] == 'restore':
            params['a_database_id'] = parameters['database_id']
            params['a_snapshot_id'] = parameters['snapshot_id']

        if self.kwargs['action'] == 'delete':
            params['a_snapshot_type'] = parameters['snapshot_type']
            params['a_filters'] = self.kwargs['filters']
            self.validate.filters_validate(**self.kwargs)

        return params

    # def get_snapshots(self, region):

    #     c = get_amazon_client(self.config()['a_type'], region)
    #     response = c.describe_snapshots()

    #     return response

    def create_snapshot(self, region):
        c = get_amazon_client(self.config()['a_type'], region)
        if not self.config()['a_cluster']:
            response = c.create_snapshot(
                SnapshotName=self.config()['a_snapshot_id'],
                CacheClusterId=self.config()['a_database_id'] + "-001"
            )
            return response

        response = c.create_snapshot(
                SnapshotName=self.config()['a_snapshot_id'],
                ReplicationGroupId=self.config()['a_database_id']
        )
        return response


    def restore_from_snapshot(self, region):
        c = get_amazon_client(self.config()['a_type'], region)
        if not self.config()['a_cluster']:
            response = c.create_cache_cluster(
                SnapshotName=self.config()['a_snapshot_id'],
                CacheClusterId=self.config()['a_database_id']
            )
            return response
        
        response = c.create_replication_group(
            SnapshotName=self.config()['a_snapshot_id'],
            ReplicationGroupId=self.config()['a_database_id'],
            ReplicationGroupDescription='[BACKUPER] restored cluster'
        )
        return response

    def delete_snapshot(self, region, snapshots):

        c = get_amazon_client(self.config()['a_type'], region)

        r = []
        for i in snapshots:
            response = c.delete_snapshot(
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

        response = c.copy_snapshot(
            SourceDBSnapshotIdentifier=SourceDBSnapshotIdentifier,
            TargetDBSnapshotIdentifier=self.config()['a_snapshot_id'],
            CopyTags=True,
            SourceRegion=self.config()['a_region']
        )

        return response


    def run(self):

        if self.kwargs['action'] == 'create':

            create_r = self.create_snapshot(self.config()['a_region'])

        # if self.kwargs['action'] == 'delete':
            # snapshots = self.get_snapshots(self.config()['a_region'])

            # validate_empty_snapshots(snapshots['DBSnapshots'],
            #                          get_msg(self.config()['a_type']) +
            #           'There are no snapshots in {} region...\n'.format(
            #               self.config()['a_region']))

            # if self.config()['a_snapshot_type'] != 'all':
            #     snaps_by_type = self.filter_snaps_by_type(snapshots,
            #                                 self.config()['a_snapshot_type'])
            # else:
            #     snaps_by_type = [i for i in snapshots['DBSnapshots']]

            # validate_empty_snapshots(snaps_by_type,
            #                          get_msg(self.config()['a_type']) +
            #           'There are no {} snapshots in {} region...\n'.format(
            #               self.config()['a_snapshot_type'],
            #               self.config()['a_region']))

            # adapted = self.adapty_snapshots(snaps_by_type)
            # snaps_filtered = f_main(self.config()['a_filters'], adapted)

            # self.delete_snapshot(self.config()['a_region'], snaps_filtered)

        if self.kwargs['action'] == 'restore':
            restore_r = self.restore_from_snapshot(self.config()['a_region'])
            # print(get_msg(self.config()['a_type']) +
            #           'Instance creation is in progress in {} region...\n'.format(
            #               self.config()['a_region']))

            # i = 0
            # while i != 'available':
            #     i = self.instance_is_available(self.config()['a_region'])
            #     sleep(60)
            
            # print(get_msg(self.config()['a_type']) +
            #           'Instance was restored in {} region...\n'.format(
            #               self.config()['a_region']))
