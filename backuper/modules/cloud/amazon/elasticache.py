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

        # if kwargs['action'] == 'delete':

        #     parameters_schema = self.tr.Dict({
        #         self.tr.Key('region'): self.tr.Enum(*amazon_regions),
        #         self.tr.Key('snapshot_type'): self.tr.Enum(
        #             *['standard', 'manual', 'all'])
        #     })

        return parameters_schema(kwargs['parameters'])

class Main(object):
    

    def __init__(self, **kwargs):

        self.kwargs = kwargs
        self.parameters = ValidateElasticache()
  

    def create_snapshot(self, region):
        c = get_amazon_client(self.parameters['type'], region)
        if not self.parameters['cluster']:
            response = c.create_snapshot(
                SnapshotName=self.parameters['snapshot_id'],
                CacheClusterId=self.parameters['database_id'] + "-001"
            )
            return response

        response = c.create_snapshot(
                SnapshotName=self.parameters['snapshot_id'],
                ReplicationGroupId=self.parameters['database_id']
        )
        return response


    def restore_from_snapshot(self, region):
        c = get_amazon_client(self.parameters['type'], region)
        if not self.parameters['cluster']:
            response = c.create_cache_cluster(
                SnapshotName=self.parameters['snapshot_id'],
                CacheClusterId=self.parameters['database_id']
            )
            return response
        
        response = c.create_replication_group(
            SnapshotName=self.parameters['snapshot_id'],
            ReplicationGroupId=self.parameters['database_id'],
            ReplicationGroupDescription='[BACKUPER] restored cluster'
        )
        return response

    # def delete_snapshot(self, region, snapshots):

    #     c = get_amazon_client(parameters['type'], region)

    #     r = []
    #     for i in snapshots:
    #         response = c.delete_snapshot(
    #             DBSnapshotIdentifier=i['DBSnapshotIdentifier']
    #         )
    #         print(get_msg(parameters['type']) +
    #               'Deleting snapshot {} in {} region...'.format(
    #             i['DBSnapshotIdentifier'], region))
    #         r.append(response)

    #     return r

    # def copy_snapshot(self, resource, region):

    #     SourceDBSnapshotIdentifier = resource['DBSnapshot']['DBSnapshotArn']

    #     c = get_amazon_client(parameters['type'], region)

    #     response = c.copy_snapshot(
    #         SourceDBSnapshotIdentifier=SourceDBSnapshotIdentifier,
    #         TargetDBSnapshotIdentifier=parameters['snapshot_id'],
    #         CopyTags=True,
    #         SourceRegion=parameters['region']
    #     )

    #     return response


    def run(self):

        if self.kwargs['action'] == 'create':

            create_r = self.create_snapshot(parameters['region'])

        # if self.kwargs['action'] == 'delete':
            # snapshots = self.get_snapshots(parameters['region'])

            # validate_empty_snapshots(snapshots['DBSnapshots'],
            #                          get_msg(parameters['type']) +
            #           'There are no snapshots in {} region...\n'.format(
            #               parameters['region']))

            # if parameters['snapshot_type'] != 'all':
            #     snaps_by_type = self.filter_snaps_by_type(snapshots,
            #                                 parameters['snapshot_type'])
            # else:
            #     snaps_by_type = [i for i in snapshots['DBSnapshots']]

            # validate_empty_snapshots(snaps_by_type,
            #                          get_msg(parameters['type']) +
            #           'There are no {} snapshots in {} region...\n'.format(
            #               parameters['snapshot_type'],
            #               parameters['region']))

            # adapted = self.adapty_snapshots(snaps_by_type)
            # snaps_filtered = f_main(parameters['filters'], adapted)

            # self.delete_snapshot(parameters['region'], snaps_filtered)

        if self.kwargs['action'] == 'restore':
            restore_r = self.restore_from_snapshot(parameters['region'])
            # print(get_msg(parameters['type']) +
            #           'Instance creation is in progress in {} region...\n'.format(
            #               parameters['region']))

            # i = 0
            # while i != 'available':
            #     i = self.instance_is_available(parameters['region'])
            #     sleep(60)
            
            # print(get_msg(parameters['type']) +
            #           'Instance was restored in {} region...\n'.format(
            #               parameters['region']))
