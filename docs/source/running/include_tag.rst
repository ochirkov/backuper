.. _include_tag:

Include Tag
===========


Actions list could be large enough. Due to this actions could be described in separate files
and included into one action file via **!include** tag. Let's look how **!include** tag
could be used:


dev.mongodb.backup.yaml file example::

    ---

    service: mongodb
    action: create
    description: "Create development mongodb dump"
    parameters:
      collection: "my-dev-collection"
      dbname: "my-dev-db"
      host: "mongodb-dev.example.com"
      gzip: True
      path: "/mnt/backup-mongo/mongo-backup-dev-2018-04-03"


prod.mongodb.backup.yaml file example::

    ---

    service: mongodb
    action: create
    description: "Create production mongodb dump"
    parameters:
      collection: "my-prod-collection"
      dbname: "my-prod-db"
      host: "mongodb-prod.example.com"
      gzip: True
      path: "/mnt/backup-mongo/mongo-backup-prod-2018-04-03"


mongodb.backup.action.yaml action file example::

    ---

    actions:

        !include dev.mongodb.backup.yaml
        !include prod.mongodb.backup.yaml


In **!include** tag section could be specified relative path. So, your actions could be
in separated folders with action file::

    ---

    actions:

        !include ../actions/dev.mongodb.backup.yaml
        !include ../actions/prod.mongodb.backup.yaml