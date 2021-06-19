""" 
    API Extension
    Exposes a simple API for interacting
    with MudPi and the core systems. Used 
    by the frontend as well.
"""
import threading
from bottle import Bottle, ServerAdapter
from mudpi.workers import Worker
from mudpi.extensions import BaseExtension
from mudpi.logger.Logger import Logger, LOG_LEVEL


NAMESPACE = 'api'

class Extension(BaseExtension):
    namespace = NAMESPACE
    update_interval = 1


    def init(self, config):
        self.cache = self.mudpi.cache.setdefault(NAMESPACE, {})
        self.apis = []
        for conf in config:
            if not conf:
                continue
            api = Api(self.mudpi, conf)
            # There should only be one api...
            self.apis.append(api)

        self.mudpi.api = api
        return True

    def validate(self, config):
        """ Validate the api configs """
        _config = config[self.namespace]

        if not isinstance(_config, list):
            _config = [_config]

        for conf in _config:
            key = conf.get('key')
            if key is None:
                # raise ConfigError('API server missing a `key` in config')
                conf['key'] = 'api'

            host = conf.get('host')
            if host is None:
                conf['host'] = 'localhost'

            port = conf.get('port')
            if port is None:
                # Defaulting port
                conf['port'] = 8080
        
        return _config


class Api(Worker):
    """ Worker to manage an api """
    def __init__(self, mudpi, config):
        self.mudpi = mudpi
        self.config = config
        self.connection = None
        self.api = Bottle()
        self.server = WSGIRefServer(port=self.port)

        self._thread = None
        self._lock = threading.Lock()
        self._api_ready = threading.Event()

        self.mudpi.workers.register(self.key, self)
        self._api_ready.set()

    @property
    def key(self):
        return self.config.get('key', 'api').lower()
    
    @property
    def ready(self):
        """ Return if api is initialized """
        return self._api_ready.is_set()

    @property
    def name(self):
        """ Friendly name of api """
        return self.config.get('name') or f"{self.key.replace('_', ' ').title()}"

    @property
    def host(self):
        """ The host of api """
        return self.config.get('host', 'localhost')

    @property
    def port(self):
        """ What port api should run on """
        return self.config.get('port', 8080)

    @property
    def debug(self):
        """ Api debug mode """
        return self.config.get('debug', False)

    @property
    def disabled(self):
        """ Disable the api """
        return self.config.get('disabled', False)


    def register_route(self, route, func, methods=['GET']):
        """ Register a route on the api """
        self.api.route(route, method=methods)(func)
        return self.api

    def work(self, func=None):
        delay_multiplier = 1
        if self.mudpi.is_prepared:
            if not self.disabled:
                self.api.run(host='localhost', port=self.port, debug=self.debug, server=self.server)
            
        # MudPi Shutting Down, Perform Cleanup Below
        Logger.log_formatted(LOG_LEVEL["debug"],
                   f"Worker Api ", "Stopping", "notice") 

        Logger.log_formatted(LOG_LEVEL["info"],
                   f"Worker Api ", "Offline", "error")

    def close(self):
        """ Reset the connection """
        self.server.close()
        return True

    def to_json(self):
        """ Return data in a json format """
        return {
            "key": self.key,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "debug": self.debug
        }

class WSGIRefServer(ServerAdapter):
    """ Adapter to take control of underlying server """
    server = None
    quiet = True

    def run(self, handler):
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            self.options['handler_class'] = QuietHandler
        self.server = make_server(self.host, self.port, handler, **self.options)
        self.server.serve_forever()

    def close(self):
        self.server.shutdown()