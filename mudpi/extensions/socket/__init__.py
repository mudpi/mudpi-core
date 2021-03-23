""" 
    Socket Extension
    Hosts a socket server for devices
    to connect and send data through to
    MudPi. 
"""
import sys
import json
import time
import socket
import threading
from mudpi.workers import Worker
from mudpi.exceptions import ConfigError
from mudpi.utils import decode_event_data
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.extensions import Component, BaseExtension


NAMESPACE = 'socket'

class Extension(BaseExtension):
    namespace = NAMESPACE
    update_interval = 0.05

    def init(self, config):
        """ Preppare the extension components """
        self.config = config #list of lists
        self.cache = self.mudpi.cache.setdefault(NAMESPACE, {})
        self.servers = {}

        if not isinstance(config, list):
            config = [config]

        for conf in config:
            key = conf.get('key')
            if key not in self.servers:
                self.servers[key] = SocketServer(self.mudpi, conf)

        self.cache['servers'] = servers

        # self.manager.register_component_actions('shutdown', action='shutdown')
        return True

    def validate(self, config):
        """ Validate the socket configs """
        _config = config[self.namespace]
        if not isinstance(_config, list):
            _config = [_config]

        for conf in _config:
            key = conf.get('key')
            if key is None:
                raise ConfigError('Socket server missing a `key` in config')

            host = conf.get('host')
            if host is None:
                raise ConfigError('Socket server missing a `host` in config')

            port = conf.get('port')
            if port is None:
                # Defaulting port
                conf['port'] = 7007
                # raise ConfigError('Socket server missing a `port` in config')
        
        return _config

class SocketServer(Worker):
    """ 
    A socket server used to allow incoming wiresless connections. 
    MudPi will listen on the socket server for clients to join and
    send a message that should be broadcast on the event system.
    """

    @property
    def host(self):
        return str(self.config.get('host', '127.0.0.1'))

    @property
    def port(self):
        return int(self.config.get('port', 7007))
    
    
    def init(self):
        """ Setup the socket """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_threads = []
        self._server_ready = threading.Event()
        self._server_ready.set()
        self._server_running = False

        try:
            self.sock.bind((self.host, self.port))
        except socket.error as msg:
            Logger.log(LOG_LEVEL['error'], f'Failed to create socket. Error Code: {str(msg[0])} Error Message: {msg[1]}')
            sys.exit()

    def work(self, func=None):
        while self.mudpi.is_prepared:
            if self.mudpi.is_running:
                if not self._server_running:
                    self._server = threading.Thread(target = self.server, args = ())
                    self._server.start()
                    self._server_running = True
            time.sleep(0.1)
        self._server_ready.clear()
        # Connect a client to prevent hanging on accept()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
        self._server.join()
        if len(self.client_threads) > 0:
            for client in self.client_threads:
                client.join()
        Logger.log_formatted(LOG_LEVEL['info'], f'Socket Server {self.key}', 'Offline', 'error')
    
    def server(self):
        """ Socket server main loop """
        self.sock.listen(0) # number of clients to listen for.
        Logger.log_formatted(LOG_LEVEL['info'], 'MudPi Server', 'Online', 'success')
        while self._server_ready.is_set():
            try:
                client, address = self.sock.accept()
                client.settimeout(600)
                ip, port = client.getpeername()
                Logger.log(LOG_LEVEL['info'], f'Socket Client {port} from {ip} Connected')
                t = threading.Thread(target = self.listenToClient, args = (client, address, ip))
                self.client_threads.append(t)
                t.start()
            except Exception as e:
                Logger.log(LOG_LEVEL['error'], e)
                time.sleep(1)
        self.sock.close()

    def listenToClient(self, client, address, ip):
        size = 1024
        while self.mudpi.is_prepared:
            try:
                data = client.recv(size)
                if data:
                    data = decode_event_data(data)
                    if data.get("topic", None) is not None:
                        self.mudpi.events.publish(data["topic"], data)
                        Logger.log(LOG_LEVEL['debug'], f"Socket Event {data['event']} from {data['source']} Dispatched")
                        # response = { "status": "OK", "code": 200 }
                        # client.send(json.dumps(response).encode('utf-8'))
                    else:
                        Logger.log(LOG_LEVEL['error'], f"Socket Data Recieved. {FONT_RED}Dispatch Failed:{FONT_RESET} Missing Data 'Topic'")
                        Logger.log(LOG_LEVEL['debug'], data)
                else:
                    pass
                    # raise error('Client Disconnected')
            except Exception as e:
                Logger.log(LOG_LEVEL['info'], f"Socket Client {ip} Disconnected")
                client.close()
                return False
        Logger.log_formatted(LOG_LEVEL['info'], 'Closing Client Connection ', 'Complete', 'success')
