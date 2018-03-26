import os.path


PROJECT_ROOT = os.path.abspath(os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), os.pardir))

modules = {
    'rds': 'backuper.modules.cloud.amazon.rds',
    'mongodb': 'backuper.modules.mongodb.mongodb',
    'digital_ocean': 'backuper.modules.cloud.digital_ocean.digital_ocean',
    'tar': 'backuper.modules.tar',
}

amazon_regions = ['us-east-2', 'us-east-1', 'us-west-1', 'us-west-2',
                  'ap-south-1', 'ap-northeast-2', 'ap-southeast-1',
                  'ap-southeast-2', 'ap-northeast-1', 'ca-central-1',
                  'eu-central-1', 'eu-west-1', 'eu-west-2', 'sa-east-1']

digital_ocean_regions = ['nyc1', 'ams1', 'sfo1', 'nyc2', 'ams2', 'sgp1',
                         'lon1', 'nyc3', 'ams3', 'fra1', 'tor1', 'sfo2',
                         'blr1']

time_mapper = {'hours': 3600,
               'days': 86400,
               'weeks': 604800,
               'months': 2592000}

wait_timeout = 4800
mongodb_port = 27017
