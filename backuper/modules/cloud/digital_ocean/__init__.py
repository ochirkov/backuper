import digitalocean
import os


def get_digitalocean_client(region):

    client = digitalocean.Manager(region=region,
                                  token=os.environ['DO_TOKEN'])

    return client