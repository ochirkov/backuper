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

    @abc.abstractmethod
    def filters_validate(self):
        """Your filters validation implementation."""
        pass
