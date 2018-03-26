from .constants import modules
from .config import actions
import importlib


for action in actions.keys():

    exec_module = importlib.import_module(modules[actions[action]['type']])
    #TODO: validate type from action

    exec_client = exec_module.Main(**action)
    exec_client.run()