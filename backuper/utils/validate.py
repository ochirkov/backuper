import trafaret as t
from .exceptions import BackuperNoSnapshotMatchError
import sys


class BaseValidator:

    def actions_validate(self, **kwargs):

        actions_schema = t.Dict({
            t.Key('actions'): t.List(
                t.Dict({
                    t.Key('type'): t.String,
                    t.Key('action'): t.String,
                    t.Key('description', optional=True): t.String(
                        max_length=200),
                    t.Key('parameters'): t.Dict().allow_extra("*"),
                    t.Key('filters', optional=True): t.List(
                        t.Dict().allow_extra("*"))
                }), min_length=1),
        })

        actions_schema(kwargs)

    def params_validate(self, action, parameters):
        """Your params validation implementation."""
        pass

    def filters_validate(self, **kwargs):

        regex_filter_schema = t.Dict({
            t.Key('pattern'): t.String,
            t.Key('type'): t.String
        })

        age_filter_schema = t.Dict({
            t.Key('term'): t.String,
            t.Key('type'): t.String,
            t.Key('unit'): t.Enum(*['hours', 'days', 'weeks', 'months']),
            t.Key('count'): t.Int
        })

        checks = {'regex': regex_filter_schema,
                  'age': age_filter_schema}

        for filter in kwargs['filters']:
            checks[filter['type']](filter)


def validate_empty_snapshots(snapshots, msg, fail):

    if not snapshots:
        if fail:
            raise BackuperNoSnapshotMatchError(msg)
        else:
            print(msg)
            sys.exit(0)
