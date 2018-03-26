import argparse
from .validate import *


parser = argparse.ArgumentParser()
parser.add_argument('--conf-file', required=False,
                    help='Backuper configuration file',
                    type=argparse.FileType('r'))
parser.add_argument('--action-file', required=True,
                    help='Backuper action file',
                    type=argparse.FileType('r'))
parser.add_argument('--vars-file', required=False,
                    help='Backuper vars file',
                    type=argparse.FileType('r'))
parser.add_argument('--extra-vars', required=False,
                    help='Extra vars from command line',
                    action='store')
args = parser.parse_args()
