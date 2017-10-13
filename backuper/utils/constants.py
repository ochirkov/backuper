import os.path


PROJECT_ROOT = os.path.abspath(os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), os.pardir))

modules = {
    'rds': 'backuper.modules.cloud.amazon.rds'
}