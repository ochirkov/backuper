from datetime import datetime
from pathlib import PurePath  # FIXME: Py3 only

from fabric.api import run, settings
from fabric.network import disconnect_all, join_host_strings

from backuper.utils.validate import ValidateBase


class TarValidator(ValidateBase):

    defaults = {
        'port': 22,
    }

    def parse_and_validate(self, options):
        tr = self.tr
        schema = tr.Dict({
            tr.Key('host'): tr.String,
            self.tr.Key('port', optional=True): self.tr.Int,
            tr.Key('username'): tr.String,
            tr.Key('password', optional=True): tr.String,
            tr.Key('key', optional=True): tr.String,
            tr.Key('backup_path'): tr.String,
            tr.Key('backup_to'): tr.String,
        })
        opts = dict(self.defaults, **schema(options))

        if not (('password' in opts) ^ ('identity' in opts)):
            raise ValueError(
                'Either password or identity (private key) must be provided '
                'but not both'
            )

        return opts



class Main(object):

    def __init__(self, **kwargs):
        self.config = self.configure(kwargs)

    def configure(self, opts):
        conf = TarValidator().parse_and_validate(opts['parameters'])
        conf['tar_name'] = conf['backup_to'].format(time=datetime.now())
        return conf

    def build_command(self):
        conf = self.config
        return 'tar -czf {tar_name} {backup_path}'.format(**conf)

    def run(self):
        conf = self.config

        fab_settings = {
            'host_string': join_host_strings(
                conf['username'], conf['host'], port=conf['port']
            ),
        }
        fab_settings.update({
            key: val for key, val in conf.items()
            if key in ('password', 'key')
        })

        cmds = (
            'mkdir -p ' + str(PurePath(conf['tar_name']).parent),
            self.build_command(),
        )

        try:
            with settings(**fab_settings):
                for cmd in cmds:
                    run(cmd)
        finally:
            disconnect_all()
