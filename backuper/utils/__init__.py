from .validate import ValidateBase


def get_msg(service):

    msg = '[ BACKUPER {} ]  |  '.format(service.upper())

    return msg


validate = ValidateBase()