.. _vars_yaml:

Vars Yaml
=========


Let's imagine that we have next two actions. There are several options which have
the same values::

    ---

    actions:

        service: mongodb
        action: create
        description: "Create employees collection dump"
        parameters:
          collection: "employees"
          dbname: "my-dev-db"
          host: "mongodb-dev.example.com"
          gzip: True
          path: "/mnt/backup-mongo/mongo-backup-employees-2018-04-03"

        service: mongodb
        action: create
        description: "Create salaries collection dump"
        parameters:
          collection: "salaries"
          dbname: "my-dev-db"
          host: "mongodb-dev.example.com"
          gzip: True
          path: "/mnt/backup-mongo/mongo-backup-salaries-2018-04-03"


We simply can specify common pieces in Vars Yaml file. Backuper uses Jinja2
templating to enable dynamic expressions and access to variables.

Take a look into Vars Yaml::

    ---

    mongo_host: mongodb-dev.example.com
    mongo_dbname: my-dev-db
    mongo_gzip: True


And how Action File will looks like with vars from Vars File::

    ---

    actions:

        service: mongodb
        action: create
        description: "Create employees collection dump"
        parameters:
          collection: "employees"
          dbname: {{ mongo_dbname }}
          host: {{ mongo_host }}
          gzip: {{ mongo_gzip }}
          path: "/mnt/backup-mongo/mongo-backup-employees-2018-04-03"

        service: mongodb
        action: create
        description: "Create salaries collection dump"
        parameters:
          collection: "salaries"
          dbname: {{ mongo_dbname }}
          host: {{ mongo_host }}
          gzip: {{ mongo_gzip }}
          path: "/mnt/backup-mongo/mongo-backup-salaries-2018-04-03"