from .constants import modules
from .config import action
import importlib

exec_module = importlib.import_module(modules[action['type']])
#TODO: validate type from action

exec_client = exec_module.Main(**action)
exec_client.run()
