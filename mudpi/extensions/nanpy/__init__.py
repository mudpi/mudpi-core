""" 
    Nanpy Extension
    Allows arduino boards and ESP based devices 
    to be controlled via serial or wifi.
"""
import time
import random
import socket
import threading
from mudpi.workers import Worker
from mudpi.extensions import BaseExtension
from mudpi.exceptions import MudPiError, ConfigError
from nanpy import (ArduinoApi, SerialManager)
from mudpi.logger.Logger import Logger, LOG_LEVEL
from nanpy.serialmanager import SerialManagerError
from nanpy.sockconnection import (SocketManager, SocketManagerError)

NAMESPACE = 'nanpy'

class Extension(BaseExtension):
    namespace = NAMESPACE
    update_interval = 30

    def init(self, config):
        """ Setup the nodes for components """
        self.config = config
        self.nodes = {}
        self.connections = {}

        if not isinstance(config, list):
            config = [config]

        for conf in config:
            key = conf.get('key')
            if key not in self.nodes:
                self.nodes[key] = Node(self.mudpi, conf)

        return True

    def validate(self, config):
        """ Validate the Node configs """
        config = config[self.namespace]
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            key = conf.get('key')
            if key is None:
                raise ConfigError('Nanpy node missing a `key` in config')

            address = conf.get('address')
            if address is None:
                raise ConfigError('Nanpy node missing an `address` in config')
        return config


class Node(Worker):
    """ Worker to manage a node connection """
    def __init__(self, mudpi, config):
        self.mudpi = mudpi
        self.config = config
        self.connection = None
        self.api = None

        self._thread = None
        self._lock = threading.Lock()
        self._node_ready = threading.Event()
        self._node_connected = threading.Event()
        self._run_once = None

        self.mudpi.workers.register(self.key, self)

    @property
    def key(self):
        return self.config.get('key')
    
    @property
    def ready(self):
        """ Return if node is initialized """
        return self._node_ready.is_set()

    @property
    def connected(self):
        """ Return if node is connected to MudPi """
        return self._node_connected.is_set()
    
    def work(self, func=None):
        # Node reconnection cycle
        delay_multiplier = 1
        while self.mudpi.is_prepared:
            if self.mudpi.is_running:
                if not self._run_once:
                    self.connect()
                    self._run_once = True
                if not self.connected:
                    # Random delay before connections to offset multiple attempts (1-5 min delay)
                    random_delay = (random.randrange(5, self.config.get(
                        "max_reconnect_delay", 60)) * delay_multiplier) / 2
                    self._wait(10)
                    Logger.log_formatted(LOG_LEVEL["info"], 
                        f'{self.key} -> Retrying Connection in {random_delay}s', 'Retrying', 'notice')
                    # Two separate checks for MudPi status to prevent re-connections during shutdown
                    if self.mudpi.is_running:
                        self._wait(random_delay)
                    if self.mudpi.is_running:
                        self.connection = self.connect()
                    if self.connection is None:
                        delay_multiplier += 1
                        if delay_multiplier > 6:
                            delay_multiplier = 6
                    else:
                        delay_multiplier = 1
                else:
                    time.sleep(1)
        # MudPi Shutting Down, Perform Cleanup Below
        Logger.log_formatted(LOG_LEVEL["debug"],
                   f"Worker {self.key} ", "Stopping", "notice")
        self.connection.close()
        self.reset_connection()
        Logger.log_formatted(LOG_LEVEL["info"],
                   f"Worker {self.key} ", "Offline", "error")

    def connect(self):
        """ Setup connection to a node over wifi or serial """
        if self.connected:
            return True

        with self._lock:
            # Check again if node connected while waiting on lock
            if self.connected:
                return True

            attempts = 3
            conn = None
            if self.config.get('use_wifi', False):
                while attempts > 0 and self.mudpi.is_running:
                    try:
                        Logger.log_formatted(LOG_LEVEL["debug"],
                                   f'{self.config["name"]} -> Wifi ', 'Connecting', 'notice')
                        attempts -= 1
                        conn = SocketManager(
                            host=str(self.config.get('address', 'mudpi-nanpy.local')))
                        # Test the connection with api
                        self.api = ArduinoApi(connection=conn)
                    except (SocketManagerError, BrokenPipeError, ConnectionResetError,
                    socket.timeout) as e:
                        Logger.log_formatted(LOG_LEVEL["warning"],
                                   f'{self.config["name"]} -> Failed Connection ', 'Timeout', 'notice')
                        if attempts > 0:
                            Logger.log_formatted(LOG_LEVEL["info"],
                                   f'{self.config["name"]} -> Preparing Reconnect ', 'Pending', 'notice')
                        else:
                            Logger.log_formatted(LOG_LEVEL["error"],
                                   f'{self.config["name"]} -> Connection Attempts ', 'Failed', 'error')
                        conn = None
                        self.reset_connection()
                        self._wait(5)
                    except (OSError, KeyError) as e:
                        Logger.log(LOG_LEVEL["error"],
                                   f"[{self.config['name']}] Node Not Found. (Is it online?)")
                        conn = None
                        self.reset_connection()
                        self._wait(5)
                    else:
                        Logger.log_formatted(LOG_LEVEL["info"],
                                   f"{self.config['name']} -> Wifi Connection ", 'Connected', 'success')
                        break
            else:
                while attempts > 0 and self.mudpi.is_running:
                    try:
                        attempts -= 1
                        conn = SerialManager(device=str(self.config.get('address', '/dev/ttyUSB1')))
                        self.api = ArduinoApi(connection=conn)
                    except SerialManagerError:
                        Logger.log_formatted(LOG_LEVEL["warning"],
                                   f"{self.config['name']} -> Connecting ", 'Timeout', 'notice')
                        if attempts > 0:
                            Logger.log_formatted(LOG_LEVEL["info"],
                                       f'{self.config["name"]} -> Preparing Reconnect ', 'Pending', 'notice')
                        else:
                            Logger.log_formatted(LOG_LEVEL["error"],
                                       f'{self.config["name"]} -> Connection Attempts ', 'Failed', 'error')
                        self.reset_connection()
                        conn = None
                        self._wait(5)
                    else:
                        if conn is not None:
                            Logger.log_formatted(LOG_LEVEL["info"],
                                       f'[{self.config["name"]}] -> Serial Connection ', 'Connected', 'success')
                        break
        if conn is not None:
            self.connection = conn
            self._node_connected.set()
            self._node_ready.set()
        return conn

    def reset_connection(self):
        """ Reset the connection """
        self.connection = None
        self._node_connected.clear()
        self._node_ready.clear()
        return True
