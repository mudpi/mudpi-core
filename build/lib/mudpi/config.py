import os
import json
import yaml
from mudpi.constants import (FONT_YELLOW, RED_BACK, FONT_RESET, IMPERIAL_SYSTEM, PATH_MUDPI, PATH_CONFIG, DEFAULT_CONFIG_FILE)
from mudpi.exceptions import ConfigNotFoundError, ConfigError

class Config(object):
    """ MudPi Config Class

    A class to represent the MudPi configuration that 
    is typically pulled from a file.
    """
    def __init__(self, config={}, config_path=None):
        self.config = config
        self.config_path = config_path or os.path.abspath(os.path.join(os.getcwd(), PATH_CONFIG))
        self.set_defaults()

    def __getattr__(self, key):
        config = self.config.get(key)
        if config:
            super().__setattr__(key, config)
        return config

    def __setattr__(self, key, value):
        if key is not 'config':
            if key in self.config:
                self.config[key] = value
        super(Config, self).__setattr__(key, value)

    def __repr__(self):
        return f'<Config {self.config_path}>'

    """ Properties """
    @property
    def name(self):
        return self.config.get('name', 'MudPi')

    @name.setter
    def name(self, value):
        self.config['name'] = value


    """ Methods """
    def path(self, *path):
        """ Returns path relative to the config folder. """
        return os.path.join(self.config_path, *path)


    def set_defaults(self):
        """ Set default configurations for any null values """
        core_config = {
            "name": self.name or 'MudPi',
            "debug": self.debug or False,
            "bus": {
                "redis": self.redis or {
                    'host': '127.0.0.1',
                    'port': 6379
                }
            }
        }
        self.mudpi = self.mudpi or core_config
        self.workers = self.workers or []
        # self.logging = self.logging or {}


    def to_dict(self):
        """ Return Config as Dict """
        return dict(self.config)
        pass


    def to_json(self):
        """ Return Config as JSON """
        return json.dumps(self.to_dict())
        pass


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
            print(f'{RED_BACK}Problem loading configs from JSON {FONT_RESET}\n{FONT_YELLOW}{e}{FONT_RESET}\r')


    def load_from_yaml(self, yaml_data):
        """ Load configs from YAML """
        try:
            self.config = yaml.load(yaml_data, yaml.FullLoader)
            return self.config
        except Exception as e:
            print(f'{RED_BACK}Problem loading configs from YAML {FONT_RESET}\n{FONT_YELLOW}{e}{FONT_RESET}\r')


    def save_to_file(self, file=None, format=None, config=None, overwrite=False):
        """ Save current configs to a file 
            File: Full path to file
            Format: 'json' or 'yaml'
            Config: Dict of data to write to file (Default: self)
            Overwrite: Boolean to allow overwrite of existing file
        """
        if file is not None:
            file = self.validate_file(file)
        else:
            file = self.path(DEFAULT_CONFIG_FILE)

        if format is None:
            format = self.config_format(file)

        config = config or self.config
        if format == 'json':
            config = json.dumps(config, sort_keys=True, indent=4)
        elif format == 'yaml':
            config = yaml.dump(config)
        else:
            config = str(config)
        with open(file, 'w') as f:
            f.write(config)
        return True


    def validate_file(self, file: str):
        """ Validate a file path and return a prepared path to save """
        if '.'  in file:
            if not self.file_exists(file):
                raise ConfigNotFoundError(f"The config path {file} does not exist.")
                return False
            extensions = ['.config', '.json', '.yaml', '.conf']
            if not any([file.endswith(extension) for extension in extensions]):
                raise ConfigFormatError("An unknown config file format was provided in the config path.")
                return False
        else:
            # Path provided but not file
            file = os.path.join(file, DEFAULT_CONFIG_FILE)
        return file


    def config_format(self, file: str):
        """ Returns the file format if supported """
        if '.' in file:
            if any(extension in file for extension in ['.config', '.json', '.conf']):
                # v0.9.1 config found
                config_format = 'json'
            elif '.yaml' in file:
                config_format = 'yaml'
        else:
            config_format = None
        
        return config_format 