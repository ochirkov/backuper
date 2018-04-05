.. _elasticache:

ELASTICACHE
===========

ElastiCache module create/delete ElastiCache snapshots. Restore ElastiCache cache cluster or replication group from snapshot.

Requirements
````````````

The below requirements are needed on the host that executes this module.

* boto3
* python >= 2.6


Actions
```````

.. list-table::
   :header-rows: 1

   * - Actions
     - Choices
     - Description

   * - action
     - * create
       * delete
       * restore
       * copy_to_region
     -

Parameters
``````````

.. list-table::
   :header-rows: 1

   * - Parameter
     - Choices
     - Required for Actions
     - Description

   * - region
     -
     - | create
       | delete
       | restore
       | copy_to_region
     - The AWS region to use.

   * - snapshot_name
     -
     - | create
       | restore
       | copy_to_region
     - The name of an existing ElastiCache snapshot.

   * - replication_group_id
     -
     -
     - The identifier of an replication group for create snapshot or restore from one.

   * - cache_cluster_id
     -
     -
     - The identifier of an cluster for create snapshot or restore from one.

   * - copy_to_region
     -
     -
     - Copy existed snapshot to specified AWS regions.


Examples
````````

 ::

   # Create ElastiCache cache cluster snapshot action
   type: elasticache
   action: create
   description: "Create elasticache snapshot from cluster"
   parameters:
     region: "eu-west-2"
     snapshot_name: "my-elasticache-cluster-snap-2018-04-05-23-00-00"
     cache_cluster_id: "my-elasticache-cluster"

   # Create ElastiCache replication group snapshot action
   type: elasticache
   action: create
   description: "Create elasticache snapshot from replication group"
   parameters:
     region: "eu-west-2"
     snapshot_name: "my-elasticache-replgroup-snap-2018-04-05-23-00-00"
     replication_group_id: "my-elasticache-replication-group"

   # Copy ElastiCache snapshot to another regions
   type: elasticache
   action: copy_to_regions
   description: "Copy elasticache snapshot"
   parameters:
     regions:
       - "eu-west-1"
       - "eu-central-1"

   # Restore ElastiCache cluster from snapshot
   type: elasticache
   action: restore
   description: "Restore elasticache from snapshot"
   parameters:
   parameters:
     region: "eu-west-2"
     snapshot_name: "my-elasticache-cluster-snap-2018-04-05-23-00-00"
     cache_cluster_id: "my-elasticache-cluster"

   # Rotate ElastiCache snapshots
   type: elasticache
   action: delete
   description: "Rotate elasticache snapshots"
   parameters:
     region: "eu-west-2"
   filters:
   - type: age
     term: older
     unit: days
     count: 3

Author
``````

* Oleksandr Chyrkov (@Iloriin)