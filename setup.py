from setuptools import setup
from backuper import __version__


setup(name='backuper',
      version=__version__,
      description='Command line utility for services backup',
      url='https://github.com/ochirkov/backuper.git',
      author='Chirkov Oleksandr',
      author_email='ironloriin20@gmail.com',
      license='Apache-2.0',
      scripts=['bin/backuper'],
      install_requires=[
        'trafaret==0.12.0',
        'pyyaml==3.12',
        'pylint==1.7.1',
        'bumpversion==0.5.3',
        'jinja2==2.9.6',
        'boto3==1.4.7',
        'pymongo==3.5.1',
        'pytz==2017.2'
      ],
      package_dir={'backuper': 'backuper'},
      packages=['backuper.modules.cloud.digital_ocean',
                'backuper.modules.cloud.amazon',
                'backuper.modules.mongodb',
                'backuper.utils'],
      include_package_data=True,
      zip_safe=False)
