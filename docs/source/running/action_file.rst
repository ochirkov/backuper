.. _action_file:

Action File
===========


Action File is required for Backuper.

Action File is a list of actions. You can specify number of actions which you need.
Each action instruct Backuper what service should be snapshoted/restored/rotated etc...

For understanding what is Action File look at example below::

    ---

    actions:

        service: mongodb
        action: create
        description: "Create development mongodb dump"
        parameters:
          collection: "my-dev-collection"
          dbname: "my-dev-db"
          host: "mongodb-dev.example.com"
          gzip: True
          path: "/mnt/backup-mongo/mongo-backup-dev-2018-04-03"

        service: mongodb
        action: create
        description: "Create production mongodb dump"
        parameters:
          collection: "my-prod-collection"
          dbname: "my-prod-db"
          host: "mongodb-prod.example.com"
          gzip: True
          path: "/mnt/backup-mongo/mongo-backup-prod-2018-04-03"


**description** field is OPTIONAL. **action** field and parameters section are REQUIRED.
All possible actions and parameters index could be found in according services docs pages :ref:`Services Index`.