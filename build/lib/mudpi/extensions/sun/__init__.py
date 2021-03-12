""" 
    Sun Extension
    Includes interfaces for getting
    sunrise and sunset.
"""
from mudpi.extensions import BaseExtension


class Extension(BaseExtension):
    namespace = 'sun'
    update_interval = (60 * 60 * 4) # Every 4 hours

    def init(self, config):
        """ Prepare the api connection and sun components """
        self.config = config

        return True

    def validate(self, config):
        """ Validate the api connection info """
        config = config[self.namespace]
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('latitude'):
                raise ConfigError('Missing `latitude` in sun configs.')

            if not conf.get('longitude'):
                raise ConfigError('Missing `longitude` in sun configs.')
        return config
