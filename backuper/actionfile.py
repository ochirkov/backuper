from pathlib import Path

import yaml

from backuper.executor import (
    AdapterExecutor,
    build_executor_registry,
    GroupExecutor,
)
from backuper.params import (
    AdapterParam,
    get_combined_schema,
    ParamError,
    ParamsBase,
    ParamSetterBase,
)

from .meta import ActionFileMeta


class ParseContext:
    def __init__(self, filename, line, column):
        self.filename = filename
        self.line = line
        self.column = column

    def format(self):
        res = str(self)
        try:
            fh = open(self.filename, 'r')
        except FileNotFoundError:
            return res
        with fh:
            snip = fh.readlines()[max(self.line - 1, 0): self.line + 2]
        snip.insert(1, ' ' * self.column + '^\n')
        snip = ''.join(snip)
        return '\n'.join(('', res + ':', '...', snip, ''))

    def __str__(self):
        return '{0.filename}:{0.line},{0.column}'.format(self)


class ParseContextMapping(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def _construct_mapping_with_ctx(constructor, node):
    ctx = {
        key.value: (_node_to_parse_ctx(key), _node_to_parse_ctx(value))
        for key, value in node.value
    }
    ctx['@self'] = _node_to_parse_ctx(node)
    mapping = constructor(node)
    mapping['@ctx'] = ctx
    return mapping


def _node_to_parse_ctx(node):
    mark = node.start_mark
    return ParseContext(mark.name, mark.line + 1, mark.column)


class ContextPreservingLoader(yaml.Loader):

    def construct_mapping(self, node, deep=False):
        return _construct_mapping_with_ctx(super().construct_mapping, node)


def load_action_file(path):
    path = Path(path)
    ext = path.suffix[1:]

    with open(str(path), 'r') as stream:
        if ext in ('yml', 'yaml'):
            data = yaml.load(stream, Loader=ContextPreservingLoader)
        else:
            raise ValueError(ext + ' format not supported')

    if 'meta' in data:
        meta_params = data.pop('meta')
        meta = ActionFileMeta(**meta_params)  # noqa

    executor = build_executor(data)
    build_executor_registry(executor)
    return executor


def build_executor(params):
    if 'tasks' in params:
        if 'action' in params:
            ctx = params.get('@ctx', {})
            raise ParamError("'tasks' and 'action' present at the same time",
                             ctx=ctx.get('@self'))

        tasks_params = params.pop('tasks')
        executor = GroupExecutor(**params)
        executor.tasks = [build_executor(task) for task in tasks_params]
        return executor

    if 'action' in params:
        adapter_desc = AdapterParam.cast(params['action'])
        adapter_cls = adapter_desc.cls

        schema = get_combined_schema(AdapterExecutor, adapter_cls)
        params = schema.apply_to(params)
        exec_params = AdapterExecutor.param_schema.select_from(params)
        exec_params['action'] = adapter_desc
        adapter_params = adapter_cls.param_schema.select_from(params)

        adapter_bases = (ParamSetterBase, adapter_cls)
        adapter_cls = type(adapter_cls.__name__, adapter_bases, {})

        executor = AdapterExecutor(**exec_params)
        executor.adapter = adapter_cls(**adapter_params)
        return executor

    raise ParamError("Neither 'task' not 'action' in params",
                     ctx=ctx['@self'])
