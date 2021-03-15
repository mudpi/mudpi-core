""" 
    Redis Extension
    Includes interfaces for redis to
    get data and manage events.
"""
import redis
from mudpi.extensions import BaseExtension


class Extension(BaseExtension):
    namespace = 'redis'
    update_interval = 30

    def init(self, config):
        """ Prepare the redis connection and components """
        self.connections = {}
        self.config = config

        if not isinstance(config, list):
            config = [config]

        # Prepare connections to redis
        for conf in config:
            host = conf.get('host', '127.0.0.1')
            port = conf.get('port', 6379)
            if conf['key'] not in self.connections:
                self.connections[conf['key']] = redis.Redis(host=host, port=port)

        return True

    def validate(self, config):
        """ Validate the redis connection info """
        config = config[self.namespace]
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            key = conf.get('key')
            if key is None:
                raise ConfigError('Redis missing a `key` in config for connection')

            host = conf.get('host')
            if host is None:
                conf['host'] = '127.0.0.1'

            port = conf.get('port')
            if port is None:
                conf['port'] = 6379
        return config