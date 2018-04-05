import pytest
from pathlib import Path

ASSETS_DIR = Path('.').parent / 'assets' / 'tests'


@pytest.fixture(scope='session')
def read_from_assets():

    def read_file(path):
        f = ASSETS_DIR / path
        return f.read_text()

    return read_file
