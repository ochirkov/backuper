import boto3


aws_regions = [
    'ap-northeast-1',
    'ap-northeast-2',
    'ap-south-1',
    'ap-southeast-1',
    'ap-southeast-2',
    'ca-central-1',
    'eu-central-1',
    'eu-west-1',
    'eu-west-2',
    'sa-east-1',
    'us-east-1',
    'us-east-2',
    'us-west-1',
    'us-west-2',
]

snapshot_types = ['all', 'standard', 'manual']


def get_aws_client(service, region):

    s = boto3.session.Session(region_name=region)
    client = s.client(service)

    return client
