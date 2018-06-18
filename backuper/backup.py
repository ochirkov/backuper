from backuper.params import Tags, TimestampTZ, ParamsBase


class Backup(ParamsBase):

    created: TimestampTZ
    tags: Tags = {}

    def __repr__(self):
        return '{0.__class__.__name__} {0.created:%c} {1}'.format(
            self,
            ', '.join('{0}={1}'.format(k, v) for k, v in self.tags.items()),
        )
