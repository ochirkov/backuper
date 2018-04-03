.. _running_backuper:

Running Backuper
================

.. code-block:: shell

    backuper -h
    usage: backuper [-h] [--conf-file CONF_FILE] --action-file ACTION_FILE
                    [--vars-file VARS_FILE] [--extra-vars EXTRA_VARS] [-v]

    optional arguments:
      -h, --help            show this help message and exit
      --conf-file CONF_FILE
                            Backuper configuration file
      --action-file ACTION_FILE
                            Backuper action file
      --vars-file VARS_FILE
                            Backuper vars file
      --extra-vars EXTRA_VARS
                            Extra vars from command line

There is only one REQUIRED parameter **--action-file**.

Backuper could be executed with only one **--action-file** like this:


.. code-block:: shell

    backuper --action-file ../my.action.file.yaml


OPTIONALLY you can add some variables in Vars File or/and with --extra-vars:

.. code-block:: shell

    backuper \
        --action-file ../my.action.file.yaml \
        --extra-vars "mongo_host=mongodb-dev.example.com" \
        --vars-file ../mongo.vars.yaml


If needed some extra Backuper configuration use --config-file directive:

.. code-block:: shell

    backuper \
        --action-file ../my.action.file.yaml \
        --conf-file /etc/backuper_conf.yaml


Detailed Backuper configuration could be retrieved from :ref:`Configuration File`.