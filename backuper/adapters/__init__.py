from backuper.params import ParamSchemaBase


class Action(ParamSchemaBase):

    def __init_subclass__(cls):
        super().__init_subclass__()
        if not hasattr(cls, 'run'):
            raise RuntimeError('Adapter action must define run(self) method')
