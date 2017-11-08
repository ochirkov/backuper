import abc
import trafaret as t
from .exceptions import BackuperNoSnapshotMatchError


class ValidateBase(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.tr = t

    def action_validate(self, choices, **kwargs):

        action_schema = self.tr.Dict({
            self.tr.Key('type'): t.String,
            self.tr.Key('action'): t.Enum(*choices),
            self.tr.Key('description', optional=True): t.String(max_length=200),
            self.tr.Key('parameters'): t.Dict().allow_extra("*"),
            self.tr.Key('filters', optional=True): t.List(
                t.Dict().allow_extra("*"))
        })

        action_schema(kwargs)

    @abc.abstractmethod
    def params_validate(self):
        """Your params validation implementation."""
        pass

    def filters_validate(self, **kwargs):

        regex_filter_schema = self.tr.Dict({
            t.Key('pattern'): self.tr.String,
            t.Key('type'): self.tr.String
        })

        age_filter_schema = self.tr.Dict({
            t.Key('term'): self.tr.String,
            t.Key('type'): self.tr.String,
            t.Key('unit'): self.tr.Enum(*['hours', 'days', 'weeks', 'months']),
            t.Key('count'): self.tr.Int
        })

        checks = {'regex': regex_filter_schema,
                  'age': age_filter_schema}

        for filter in kwargs['filters']:
            checks[filter['type']](filter)


def validate_empty_snapshots(snapshots):

    if not snapshots:
        # raise BackuperNoSnapshotMatchError(msg)
        print("No snapshots were found.")
