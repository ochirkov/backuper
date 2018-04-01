import trafaret as t
from .exceptions import BackuperNoSnapshotMatchError
import sys


class OneOptKey(t.Key):

    def __init__(self, *args, **kwargs):
        kwargs['optional'] = True
        name = '[%s]' % ', '.join(args)

        super().__init__(name, **kwargs)
        self.keys = args

    def __call__(self, data):
        subdict = {k: data[k] for k in self.keys if k in data}
        if not subdict:
            for key in self.keys:
                yield (
                    key,
                    t.DataError(f'one of keys {self.name} is required'),
                    (key,),
                )

        for key, value in subdict.items():
            try:
                result = self.trafaret(value)
            except t.DataError as de:
                error = de
                yield key, error, (key,)
            else:
                yield key, result, (key,)


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
