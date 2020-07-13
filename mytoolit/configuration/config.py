from dynaconf import Dynaconf
from os.path import abspath, dirname, join

repository_root = dirname(dirname(dirname(abspath(__file__))))

settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_file=[
        join(join(repository_root, 'Configuration'), 'config.yaml')
    ],
)
