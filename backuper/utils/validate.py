import abc
import trafaret as t


class ValidateBase(object):
    __metaclass__ = abc.ABCMeta

    def action_validate(self, choices, **kwargs):

        action_schema = t.Dict({
            t.Key('type'): t.String,
            t.Key('action'): t.Enum(*choices),
            t.Key('description', optional=True): t.String(max_length=200),
            t.Key('parameters'): t.Dict().allow_extra("*"),
            t.Key('filters', optional=True): t.List(t.Dict().allow_extra("*"))
        })

        action_schema(kwargs)

    @abc.abstractmethod
    def params_validate(self):
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
            t.Key('unit'): t.String,
            t.Key('count'): t.Int
        })

        checks = {'regex': regex_filter_schema,
                  'age': age_filter_schema}

        for filter in kwargs['filters']:
            checks[filter['type']](filter)
