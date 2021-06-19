import os
import json
import yaml
from mudpi.constants import (FONT_YELLOW, RED_BACK, FONT_RESET, IMPERIAL_SYSTEM, PATH_MUDPI,
                             PATH_CONFIG, DEFAULT_CONFIG_FILE)
from mudpi.exceptions import ConfigNotFoundError, ConfigError, ConfigFormatError


class Config(object):
    """ MudPi Config Class

    A class to represent the MudPi configuration that 
    is typically pulled from a file.
    """

    def __init__(self, config_path=None):
        self.config_path = config_path or os.path.abspath(os.path.join(os.getcwd(), PATH_CONFIG))

        self.config = {}
        self.set_defaults()

    """ Properties """

    @property
    def name(self):
        return self.config.get('mudpi', {}).get('name', 'MudPi')

    @name.setter
    def name(self, value):
        self.config.get('mudpi', {})['name'] = value

    @property
    def debug(self):
        return self.config.get('mudpi', {}).get('debug', False)

    @debug.setter
    def debug(self, value):
        self.config.setdefault('mudpi', {})['debug'] = value

    @property
    def unit_system(self):
        return self.config.get('mudpi', {}).get('unit_system', 'imperial').lower()

    @property
    def latitude(self):
        return self.config.get('mudpi', {}).get('location', {}).get('latitude', 43)

    @property
    def longitude(self):
        return self.config.get('mudpi', {}).get('location', {}).get('longitude', -88)


    """ Methods """
    def path(self, *path):
        """ Returns path relative to the config folder. """
        return os.path.join(self.config_path, *path)

    def set_defaults(self):
        """ Set default configurations for any null values """
        core_config = {
            "name": self.config.get('mudpi', {}).get('name', 'MudPi'),
            "debug": self.config.get('mudpi', {}).get('debug', False),
            "unit_system": self.config.get('mudpi', {}).get('unit_system', "imperial"),
        }
        self.config['mudpi'] = core_config
        self.config['api'] = {
            "port": self.config.get('api', {}).get('port', 8080),
            "debug": self.config.get('api', {}).get('debug', False)
        }

    def to_dict(self):
        """ Return Config as Dict """
        return dict(self.config)

    def to_json(self):
        """ Return Config as JSON """
        return json.dumps(self.to_dict())

    def keys(self):
        """ Return the keys of the config """
        return self.config.keys()

    def values(self):
        """ Return the values of the config """
        return self.config.values()

    def setdefault(self, key, default):
        """ Provide setdefault on config """
        return self.config.setdefault(key, default)

    def file_exists(self, file=None):
        """ Check if config files exists at given path """
        file = file or self.path(DEFAULT_CONFIG_FILE)
        return os.path.exists(file)

    def load_from_file(self, file=None, format=None):
        """ 
        Load configurations from a file. 
        Format: 'JSON' or 'YAML' 
        """

        if file is not None:
            file = self.validate_file(file)
        else:
            file = self.path(DEFAULT_CONFIG_FILE)

        if format is None:
            format = self.config_format(file)

        try:
            with open(file) as f:
                config = f.read()
                f.close()
                if format is not None:
                    if format.lower() == 'json':
                        config = self.load_from_json(config)
                    elif format.lower() == 'yaml':
                        config = self.load_from_yaml(config)
                else:
                    config = dict(config)
                if config:
                    self.config = config
                    self.config_path = os.path.split(file)[0]
                self.set_defaults()
                return config
        except FileNotFoundError:
            print(
                f'{RED_BACK}There is no configuration file found on the '
                f'filesystem{FONT_RESET}\n\r'
            )
            raise ConfigNotFoundError()
        except Exception as e:
            print(
                f'{RED_BACK}There was an error loading config file. {FONT_RESET}\n\r'
            )
            raise ConfigError()

    def load_from_json(self, json_data):
        """ Load configs from JSON """
        try:
            self.config = json.loads(json_data)
            return self.config
        except Exception as e:
            print(
                f'{RED_BACK}Problem loading configs from JSON {FONT_RESET}\n{FONT_YELLOW}{e}{FONT_RESET}\r')

    def load_from_yaml(self, yaml_data):
        """ Load configs from YAML """
        try:
            self.config = yaml.load(yaml_data, yaml.FullLoader)
            return self.config
        except Exception as e:
            print(
                f'{RED_BACK}Problem loading configs from YAML {FONT_RESET}\n{FONT_YELLOW}{e}{FONT_RESET}\r')

    def save_to_file(self, file=None, format=None, config=None):
        """ Save current configs to a file 
            File: Full path to file
            Format: 'json' or 'yaml'
            Config: Dict of data to write to file (Default: self)
        """
        if file is not None:
            file = self.validate_file(file, exists=False)
        else:
            file = self.path(DEFAULT_CONFIG_FILE)

        if format is None:
            format = self.config_format(file)

        config = config or self.config
        if format == 'json':
            config = json.dumps(config, indent=4)
        elif format == 'yaml':
            config = yaml.dump(config)
        else:
            config = str(config)
        with open(file, 'w') as f:
            f.write(config)
        return True

    def validate_file(self, file, exists=True):
        """ Validate a file path and return a prepared path to save
            Set exists to False to prevent file exists check
        """
        if '.' in file:
            if not self.file_exists(file) and exists:
                raise ConfigNotFoundError(f"The config path {file} does not exist.")

            extensions = ['.config', '.json', '.yaml', '.conf']

            if not any([file.endswith(extension) for extension in extensions]):
                raise ConfigFormatError(
                    "An unknown config file format was provided in the config path.")
        else:
            # Path provided but not file
            file = os.path.join(file, DEFAULT_CONFIG_FILE)
        return file

    def config_format(self, file):
        """ Returns the file format if supported """

        config_format = None
        if '.' in file:
            if any(extension in file for extension in ['.config', '.json', '.conf']):
                config_format = 'json'
            elif '.yaml' in file:
                config_format = 'yaml'

        return config_format

    def get(self, key, default=None, replace_char=None):
        """ Get an item from the config with a default 
            Use replace_char to slug the config value
        """
        value = self.config.get(key, default)

        if replace_char:
            if type(value) == str:
                value = value.replace(" ", replace_char).lower()

        return value

    def __repr__(self):
        """ Debug print of config """
        return f'<Config {self.config_path}>'
