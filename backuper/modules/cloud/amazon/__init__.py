import boto3
import os
# import os.path
# import configparser
#
#
# config = configparser.ConfigParser()
# conf_path = os.path.join(os.path.expanduser("~"), '.aws/credentials')
# config.read(conf_path)


if os.environ.get('AWS_ACCESS_KEY_ID'):
    access_key = os.environ['AWS_ACCESS_KEY_ID']
elif os.environ.get('AWS_ACCESS_KEY'):
    access_key = os.environ['AWS_ACCESS_KEY']
# elif bool(config) and config.has_option('default', 'aws_access_key_id'):
#     access_key = config.get('default', 'aws_access_key_id')


if os.environ.get('AWS_SECRET_ACCESS_KEY'):
    secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
elif os.environ.get('AWS_SECRET_KEY'):
    secret_key = os.environ['AWS_SECRET_KEY']
# elif bool(config) and config.has_option('default', 'aws_secret_access_key'):
#     secret_key = config.get('default', 'aws_secret_access_key')


def get_amazon_client(service, region):

    s = boto3.session.Session(region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    client = s.client(service)

    return client
