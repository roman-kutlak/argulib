import os
import sys
import yaml
import logging
import logging.config


def trim(str):
    """Remove multiple spaces"""
    return ' '.join(str.strip().split())


def log():
    """ Return the default program logger. """
    return logging.getLogger('argulib')


class Settings:
    """ Class Settings reads a file with various settings such as paths to
    domain definition files, paths to file with plans, etc.

    """

    def __init__(self, filename):
        # assume the file contains key value pairs with no spaces
        self.table = dict()
        try:
            with open(filename) as f:
                for line in f:
                    kv = line.split()
                    if len(kv) > 1:
                        self.table[kv[0]] = kv[1]

        except IOError:
            # This should probably log the exception...
            print("Something wrong with the file '%s'" % filename)

    def get_setting(self, key):
        if key in self.table:
            return self.table[key]
        else:
            return None


def get_user_settings():
    """
    Look for a default settings file in $HOME/.sassy/sassy.prefs
    and create a Settings object using that file.

    """
    home = os.getenv("HOME")
    path = os.sep.join([home, ".sassy/sassy.prefs"])
    return Settings(path)


def try_setup_logging():
    config_path = default_config_file()
    if not (os.path.isfile(config_path) and os.access(config_path, os.R_OK)):
        config_path = find_config_file()
    setup_logging(config_path)


def setup_logging(
        default_path='log.config.yaml',
        default_level=logging.DEBUG,
        env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        print('Using log config file "%s"' % path)
        with open(path, 'rt') as f:
            config = yaml.load(f.read())
        logging.config.dictConfig(config)
    else:
        print('Could not open log config file "%s"' % path)
        logging.basicConfig(level=default_level)


def default_config_file():
    """Read the config file"""
    if getattr(sys, 'frozen', False):  # frozen
        mod_path = os.path.dirname(sys.executable)
    else:  # unfrozen
        mod_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.sep.join([mod_path, 'resources', 'log.config.yaml'])
    return (config_path)


def find_config_file(cwd):
    """move 3 levels up and search"""
    config_path = None
    start = '.'
    if 'Contents' in cwd:
        start = os.path.sep.join(['..', '..'])
    files = find_files(start, '.yaml')
    for root, file in files:
        if file == 'log.config.yaml':
            config_path = os.path.join(root, file)
    return config_path


def find_files(dir, extension):
    result = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.endswith(extension):
                result.append((root, file))
    return result
