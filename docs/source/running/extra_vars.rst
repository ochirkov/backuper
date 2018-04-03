.. _extra_vars:

Extra Vars
==========


You also can specify needed parameters from command line **--extra-vars** option.
**--extra-vars** is more priority than variables from Vars File. If variable with
same name exists in both Vars File and --extra-vars, than value from --extra-vars
will be used.

Let's look at example with --extra-vars. We'll specify all possible vars from
command line and render them via Jinja2 template engine in our Action File::

    $ backuper --action-file mongodb.backup.action.yaml \
        --extra-vars \
            "mongo_dbname=my-dev-db \
             mongo_host=mongodb-dev.example.com \
             mongo_gzip=True \
             mongo_collection=employees"


And our Action File::

    ---

    actions:

        service: mongodb
        action: create
        description: "Create {{ mongo_collection }} collection dump"
        parameters:
          collection: {{ mongo_collection }}
          dbname: {{ mongo_dbname }}
          host: {{ mongo_host }}
          gzip: {{ mongo_gzip }}
          path: "/mnt/backup-mongo/mongo-backup-{{ mongo_collection }}-2018-04-03"


Vars File and --extra-vars could be used simultaneously. We could specify variables
in Vars File and redefine some of them via --extra-vars.

**Vars File**::

    ---

    mongo_host: mongodb-dev.example.com
    mongo_dbname: my-dev-db
    mongo_gzip: True
    mongo_collection=employees

Let's redefine mongo host::

    $ backuper --action-file mongodb.backup.action.yaml \
        --extra-vars "mongo_host=mongodb-prod.example.com"