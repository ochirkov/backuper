import os.path


PROJECT_ROOT = os.path.abspath(os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), os.pardir))

modules = {
    'rds': 'backuper.modules.cloud.amazon.rds'
}

amazon_regions = ['us-east-2', 'us-east-1', 'us-west-1', 'us-west-2',
                  'ap-south-1', 'ap-northeast-2', 'ap-southeast-1',
                  'ap-southeast-2', 'ap-northeast-1', 'ca-central-1',
                  'eu-central-1', 'eu-west-1', 'eu-west-2', 'sa-east-1']
