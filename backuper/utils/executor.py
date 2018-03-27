from .constants import modules
from .config import actions
import importlib
from . import validate


for action in actions['actions']:

    # Validate action
    #
    validate.action_validate(**action)

    exec_module = importlib.import_module(modules[action['type']])
    #TODO: validate type from action

    exec_client = exec_module.Main(**action)
    exec_client.run()