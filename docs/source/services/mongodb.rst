.. _mongodb:

MONGODB
=======

MongoDB module create/delete/restore MongoDB snapshots.

Requirements
````````````

The below requirements are needed on the host that executes this module.

* mongodb-org-tools package `Installation guide <https://docs.mongodb.com/manual/administration/install-on-linux/>`_
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
       * copy_to_s3
     -

Parameters
``````````

.. list-table::
   :header-rows: 1

   * - Parameter
     - Choices
     - Required for Actions
     - Description

   * - host
     - | **Default:**
       | None
     - | create
       | restore
     - Specifies a resolvable hostname for the mongod to which to connect.
       By default, the mongodump attempts to connect to a MongoDB instance running on the localhost.

   * - port
     - | **Default:**
       | 27017
     - | create
       | restore
     - Specifies the TCP port on which the MongoDB instance listens for client connections.

   * - dbname
     - | **Default:**
       | None
     -
     - Specifies a database to backup. If you do not specify a database, all databases in this instance will be added into the dump files.

   * - collection
     - | **Default:**
       | None
     -
     - Specifies a collection to backup. If you do not specify a collection, this option copies all collections in the specified database to the dump files.

   * - gzip
     - * True
       * False
       | **Default:**
       | True
     -
     - Compresses the output. The files have the suffix .gz.


Examples
````````

 ::

   # Create MongoDB snapshot action
   type: mongodb
   action: create
   description: "Create mongodb dump"
   parameters:
     collection: "my_collection_name"
     dbname: "mongo_dbname"
     host: "mongo_host"
     gzip: True
     path: "/mnt/s3/backup_mongo/mongo-backup-2018-04-05"

   # Create MongoDB snapshot action with default params
   type: mongodb
   action: create
   description: "Create mongodb dump"
   parameters:
     path: "/mnt/s3/backup_mongo/mongo-backup-2018-04-05"

   # Restore MongoDB instance from snapshot
   type: mongodb
   action: restore
   description: "Restore mongodb from dump"
   parameters:
     host: "mongo_host"
     gzip: True
     path: "/mnt/s3/backup_mongo/mongo-backup-2018-04-05/"

   # Rotate MongoDB snapshots
   type: mongodb
   action: delete
   description: "Rotate mongodb snapshots"
   parameters:
     host: "mongo_host"
     path: "/mnt/s3/backup_mongo/"
   filters:
   - type: age
     term: older
     unit: days
     count: 30

   # Create MongoDB snapshot and copy to s3
   type: mongodb
   action: create
   description: "Create mongodb dump"
   parameters:
     path: "/mnt/s3/backup_mongo/mongo-backup-2018-04-05"
   copy_to_s3:
     bucket_name: mongodb-bucket-name

Author
``````

* Oleksandr Chyrkov (@Iloriin)
* Fedir Alifirenko