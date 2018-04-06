import pytest
from unittest.mock import Mock

from backuper.utils.config import Config


@pytest.fixture
def args(read_from_assets):
    good_yaml = read_from_assets('action-files/good.yaml')
    mocked_action_file = Mock(read=Mock(return_value=good_yaml))

    return Mock(
        extra_vars=None,
        vars_file=None,
        action_file=mocked_action_file,
    )


def test_parse_action_file(args):
    parsed_actions = Config(args).parse_actions()

    assert isinstance(parsed_actions, dict)
    assert parsed_actions['actions']
    assert isinstance(parsed_actions['actions'], list)
    assert len(parsed_actions['actions']) == 2

    action = parsed_actions['actions'][0]
    assert action['service'] == 'mongodb'
    assert action['action'] == 'create'
    assert action['description'] == 'Dump MongoDB Collection'
    assert action['parameters'] == {
        'dbname': 'users',
        'host': '127.0.0.1',
        'gzip': True,
        'path': '/tmp/mongo-backups-dir',
    }

    action = parsed_actions['actions'][1]
    assert action['service'] == 'elasticache'
    assert action['action'] == 'delete'
    assert action['description'] == 'Rotating elasticache'
    assert action['parameters'] == {
        'region': 'eu-west-2',
    }
    assert action['filters'] == [
        {'type': 'regex',
         'pattern': '[a-zA-Z]+'},
    ]
