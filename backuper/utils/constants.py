modules = {
    'rds': 'backuper.modules.cloud.amazon.rds',
    'elasticache': 'backuper.modules.cloud.amazon.elasticache',
    'mongodb': 'backuper.modules.mongodb.mongodb'
}

amazon_regions = ['us-east-2', 'us-east-1', 'us-west-1', 'us-west-2',
                 'ap-south-1', 'ap-northeast-2', 'ap-southeast-1',
                 'ap-southeast-2', 'ap-northeast-1', 'ca-central-1',
                 'eu-central-1', 'eu-west-1', 'eu-west-2', 'sa-east-1']

time_mapper = {'hours': 3600,
              'days': 86400,
              'weeks': 604800,
              'months': 2592000}

engines = {'rds': ['postgres', 'mysql', 'mariadb', 'oracle-ee', 'oracle-se',
                   'oracle-se1', 'oracle-se2', 'sqlserver-ex', 'sqlserver-web',
                   'sqlserver-se', 'sqlserver-ee']}

snapshot_types = ['all', 'standard', 'manual']
fail_on_error = True
wait_timeout = 4800
