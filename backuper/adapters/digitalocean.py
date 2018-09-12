import logging
import os

import digitalocean

from backuper.adapters import Action
from backuper.params import Int, List, one_of, Str


logger = logging.getLogger(__name__)


Region = one_of('Region', Str, *digitalocean_regions)


class DigitalOcean:

    snapshot_name: Str
    region: Region
    droplet_name: Str
    copy_to_region: List = []
    wait_timeout: Int = 0

    def __init__(self):
        self.client = get_digitalocean_client(self.region)


class Create(DigitalOcean, Action):

    def run(self):

        for d in self.get_droplet(self.region):
            if d.name == self.droplet_name:
                droplet = d
                break
        else:
            raise RuntimeError(
                'Droplet {0} not found'.format(self.droplet_name)
            )

        snap_rscr = self.create_snapshot(droplet, self.snapshot_name)

        #TODO: copy to regions

    def get_droplet(self, region):
        return self.client.get_all_droplets()

    def create_snapshot(self, droplet, name):
        return droplet.take_snapshot(snapshot_name=name)


def get_digitalocean_client(region):
    return digitalocean.Manager(region=region, token=os.environ['DO_TOKEN'])
