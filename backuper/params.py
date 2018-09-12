import re

from collections import namedtuple
from datetime import datetime
from importlib import import_module
from typing import get_type_hints


class ParamError(Exception):
    def __init__(self, *args, param=None, value=None, errors=None, ctx=None):
        super().__init__(*args)
        self.param = param
        self.value = value
        self.errors = errors or []
        self.ctx = ctx

    @classmethod
    def from_errors(cls, errors):
        return cls('Multiple param errors', errors=errors)

    def __str__(self):
        if self.errors:
            return '\n' + '\n\n'.join(str(err) for err in self.errors)

        res = super().__str__()
        if self.ctx:
            res += '\n' + self.ctx.format()
        return res


class Param:

    @classmethod
    def cast(cls, value):
        return value


class SimpleParam(Param):

    @classmethod
    def cast(cls, value):
        value = super().cast(value)
        return cls.base_type(value)


class Str(SimpleParam):
    base_type = str


class Int(SimpleParam):
    base_type = int


class List(SimpleParam):
    base_type = list


class Tags(Param):

    @classmethod
    def cast(cls, value):
        ktype, vtype = Str, Str
        value = super().cast(value)
        return {ktype.cast(key): vtype.cast(val) for key, val in value.items()
                if key != '@ctx'}


class Bool(Param):

    @classmethod
    def cast(cls, value):
        if not isinstance(value, bool):
            raise ValueError('Expecting bool')
        return value


class TimestampTZ(Param):

    @classmethod
    def cast(cls, value):
        value = super().cast(value)
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            fmt = '%Y-%m-%dT%H:%M:%S'
            _, time = value.split('T')
            if '+' in time or '-' in time:
                fmt += '%z'
            return datetime.strptime(value, fmt)


AdapterDescriptor = namedtuple('AdapterDescriptor', 'cls description')


class AdapterParam(Str):

    @classmethod
    def cast(cls, value):
        if isinstance(value, AdapterDescriptor):
            return value
        value = super().cast(value)
        action_info = value.splitlines()[0].strip()
        action_type, adapter_type, *_ = action_info.split()
        module = 'backuper.adapters.{0}'.format(adapter_type)
        try:
            module = import_module(module)
            adapter_cls = getattr(module, action_type.capitalize())
        except (ImportError, AttributeError) as err:
            raise ParamError('Invalid adapter spec: {0}'.format(err))
        return AdapterDescriptor(adapter_cls, action_info)


class HostNameOrIP(Str):

    host_re = re.compile(r'^[a-zA-Z0-9-]{1,63}(?:\.[a-zA-Z0-9-]{1,63})*\.?$')
    ip_re = re.compile(r'\d{1,3}(?:\.\d{1,3})')

    @classmethod
    def is_host(cls, value):
        return bool(cls.host_re.match(value)) and len(value) <= 253

    @classmethod
    def is_ip(cls, value):
        if cls.ip_re.match(value):
            oct, *octs = [int(oct) for oct in value.split('.')]
            return 0 < oct <= 255 and all(0 <= oct <= 255 for oct in octs)
        return False

    @classmethod
    def cast(cls, value):
        value = super().cast(value)
        if cls.is_host(value) or cls.is_ip(value):
            return value
        raise ParamError('Not a valid host name or IP address')


class Port(Int):

    @classmethod
    def cast(cls, value):
        value = super().cast(value)
        if not 0 < value <= 65535:
            raise ParamError('Not a valid port')
        return value


# TODO: implement a proper generic one-of param
def one_of(name, param_type, *choices):
    def cast(self, value):
        value = super(type(self), self).cast(value)
        if value not in choices:
            choices = [str(choice) for choice in choices]
            raise ParamError('Must be one of ' + ', '.join(choices))
        return value
    return type(name, (param_type,), {'cast': cast})


class ParamSpec:

    _no_default = object()

    def __init__(self, param_type, default=_no_default):
        self.type = param_type
        if default is self._no_default:
            self.required = True
        else:
            self.required = False
            self.default = param_type.cast(default)

    def __repr__(self):
        kwargs = {'param_type': self.type}
        if not self.required:
            kwargs['default'] = self.default
        kwargs = ', '.join('{0}={1}'.format(key, val)
                           for key, val in kwargs.items())
        return 'ParamSpec({0})'.format(kwargs)


class ParamSchema:

    def __init__(self, cls):
        for name, spec in self._get_specs(cls).items():
            setattr(self, name, spec)

    def _get_specs(self, cls):
        hints = get_type_hints(cls)
        types = {name: param_type for name, param_type in hints.items()
                 if issubclass(param_type, Param)}
        defaults = {name: getattr(cls, name) for name in types
                    if hasattr(cls, name)}
        specs = {}
        for name, param_type in types.items():
            spec = {'param_type': param_type}
            if name in defaults:
                spec['default'] = defaults[name]
            specs[name] = ParamSpec(**spec)

        return specs

    def select_from(self, params):
        return {name: value for name, value in params.items()
                if hasattr(self, name) or name == '@ctx'}

    def apply_to(self, params):
        errors = []
        ctx = params.pop('@ctx', {})
        selected = self.select_from(params)

        errors.extend(
            ParamError('Unconsumed param: {0}'.format(name),
                       param=name, ctx=ctx.get(name)[0])
            for name in params if name not in selected
        )

        for name, spec in self.__dict__.items():
            try:
                name_ctx, value_ctx = ctx.get(name)
            except TypeError:
                name_ctx = value_ctx = ctx.get('@self')

            try:
                raw = selected.pop(name)
            except KeyError:
                if not spec.required:
                    selected[name] = spec.default
                else:
                    errors.append(ParamError(
                        '{0} is a required param'.format(name),
                        param=name, ctx=name_ctx
                    ))
                    continue
            else:
                try:
                    selected[name] = spec.type.cast(raw)
                except Exception as err:  # TODO: ParamError
                    errors.append(ParamError(
                        f'{name}: {err}', param=name, ctx=value_ctx
                    ))

        if errors:
            raise ParamError.from_errors(errors)

        return selected


def get_combined_schema(clsa, clsb, *clss):
    clss = (clsb,) + clss
    schema = ParamSchema(clsa)
    errors = []
    for cls in clss:
        cls_schema = ParamSchema(cls)
        for name, spec in cls_schema.__dict__.items():
            if hasattr(schema, name):
                errors.append(ParamError(
                    'Reserved param {0} requested by {1}'.format(name, cls),
                    param=name
                ))
            else:
                setattr(schema, name, spec)
    if errors:
        raise ParamError.from_errors(errors)
    return schema


class ParamSchemaBase:

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.param_schema = ParamSchema(cls)


class ParamSetterBase:

    def __init__(self, **params):
        params = self.param_schema.apply_to(params)
        for name, value in params.items():
            setattr(self, name, value)
        super().__init__()


class ParamsBase(ParamSchemaBase, ParamSetterBase):
    pass
