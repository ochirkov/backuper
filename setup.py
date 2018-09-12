from pathlib import Path

from setuptools import find_packages, setup
from backuper import __author__, __version__

project_root = Path(__file__).parent

requirements = project_root / 'requirements.txt'
with requirements.open(mode='rt', encoding='utf-8') as fp:
    install_requires = [l.strip() for l in fp]

package_name = 'backuper'

setup(
    name=package_name,
    version=__version__,
    description='Command line utility for services backup',
    url='https://github.com/ochirkov/backuper.git',
    author=__author__,
    author_email='ironloriin20@gmail.com',
    license='Apache-2.0',
    install_requires=install_requires,
    packages=find_packages(include=package_name + '.*'),
    include_package_data=True,
    zip_safe=False,
    entry_points={
            'console_scripts': [
                '{} = {}.cli:entrypoint'.format(*[package_name]*2),
            ],
        },
)
