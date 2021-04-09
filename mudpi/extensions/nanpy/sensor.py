""" 
    Nanpy Sensor Interface
    Connects to a unit running Nanpy to 
    get readings from the device.
"""
import socket
from mudpi.extensions import BaseInterface
from mudpi.extensions.sensor import Sensor
from mudpi.constants import IMPERIAL_SYSTEM
from nanpy import (ArduinoApi, SerialManager, DHT)
from mudpi.logger.Logger import Logger, LOG_LEVEL
from nanpy.serialmanager import SerialManagerError
from mudpi.exceptions import MudPiError, ConfigError
from nanpy.sockconnection import (SocketManager, SocketManagerError)


class Interface(BaseInterface):
    def load(self, config):
        """ Load Nanpy sensor components from configs """
        sensor = None
        if config['type'].lower() == 'gpio':
            sensor = NanpyGPIOSensor(self.mudpi, config)
        elif config['type'].lower() == 'dht':
            sensor = NanpyDHTSensor(self.mudpi, config)
        elif config['type'].lower() == 'dallas_temperature':
            # sensor = OneWireSensor(self.mudpi, config) NOT IMPLMENTED YET
            pass

        if sensor:
            node = self.extension.nodes[config['node']]
            if node:
                sensor.node = node
                self.add_component(sensor)
            else:
                raise MudPiError(f'Nanpy node {config["node"]} not found trying to connect {config["key"]}.')
        return True

    def validate(self, config):
        """ Validate the Nanpy sensor config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('key'):
                raise ConfigError('Missing `key` in Nanpy sensor config.')

            if not conf.get('node'):
                raise ConfigError(f'Missing `node` in Nanpy sensor {conf["key"]} config. You need to add a node key.')

            if not conf.get('type'):
                # Default the sensor type
                conf['type'] = 'gpio'

            if conf['type'].lower() == 'gpio':
                pin = conf.get('pin')
                if not pin and pin != 0:
                    raise ConfigError(f'Missing `pin` in Nanpy gpio sensor {conf["key"]} config.')
            elif conf['type'].lower() == 'dht':
                pin = conf.get('pin')
                if not pin and pin != 0:
                    raise ConfigError(f'Missing `pin` in Nanpy dht sensor {conf["key"]} config.')

                if not conf.get('model'):
                    # Default DHT Model
                    conf['model'] = '11'
                else:
                    # Defaulting the model to DHT11
                    if conf['model'] not in NanpyDHTSensor.models:
                        conf['model'] = '11'

                conf['classifier'] = 'climate'
            elif conf['type'].lower() == 'dallas_temperature':
                if not conf.get('address'):
                    # raise ConfigError(f'Missing `address` in Nanpy dallas_temperature sensor {conf['key']} config.')
                    pass
                conf['classifier'] = 'temperature'
                    
            if not conf.get('classifier'):
                # Default the sensor classifier
                conf['classifier'] = 'general'

        return config


class NanpyGPIOSensor(Sensor):
    """ Nanpy GPIO Sensor
        Get readings from GPIO (analog or digital)
    """

    """ Properties """
    @property
    def id(self):
        """ Return a unique id for the component """
        return self.config['key']

    @property
    def name(self):
        """ Return the display name of the component """
        return self.config.get('name') or f"{self.id.replace('_', ' ').title()}"
    
    @property
    def state(self):
        """ Return the state of the component (from memory, no IO!) """
        return self._state

    @property
    def classifier(self):
        """ Classification further describing it, effects the data formatting """
        return 'climate'

    @property
    def analog(self):
        """ Return if gpio is digital or analog """
        return self.config.get('analog', False)

    @property
    def pin(self):
        """ Return if gpio is digital or analog """
        return int(self.config.get('pin'))

    """ Methods """
    def init(self):
        """ Connect to the Parent Device """
        self._state = None
        return True

    def update(self):
        """ Get data from GPIO through nanpy"""
        if self.node.connected:
            try:
                data = None
                if self.analog:
                    data = self.node.api.analogRead(self.pin)
                else:
                    data = self.node.api.digitalRead(self.pin)
                self._state = data
            except (SerialManagerError, SocketManagerError,
                    BrokenPipeError, ConnectionResetError, OSError,
                    socket.timeout) as e:
                if self.node.connected:
                    Logger.log_formatted(LOG_LEVEL["warning"],
                           f'{self.node.key} -> Broken Connection', 'Timeout', 'notice')
                    self.node.reset_connection()
        return None

class NanpyDHTSensor(Sensor):
    """ Nanpy DHT Sensor
        Get readings from DHT device.
    """
    models = {  '11': DHT.DHT11,
                '22': DHT.DHT22,
                '2301': DHT.AM2301 }

    """ Properties """
    @property
    def id(self):
        """ Return a unique id for the component """
        return self.config['key']

    @property
    def name(self):
        """ Return the display name of the component """
        return self.config.get('name') or f"{self.id.replace('_', ' ').title()}"
    
    @property
    def state(self):
        """ Return the state of the component (from memory, no IO!) """
        return self._state

    @property
    def classifier(self):
        """ Classification further describing it, effects the data formatting """
        return self.config.get('classifier', 'general')

    @property
    def analog(self):
        """ Return if gpio is digital or analog """
        return self.config.get('analog', False)

    @property
    def pin(self):
        """ Return if gpio is digital or analog """
        return self.config.get('pin')

    @property
    def model(self):
        """ Return DHT model """
        if self.config.get('model') not in NanpyDHTSensor.models:
            conf['model'] = '11'
        return self.models[self.config.get('model', '11')]

    """ Methods """
    def init(self):
        """ Connect to the Parent Device """
        self._state = None
        self._dht = None
        # Attribute to track from DHT device
        self._attribute = self.config.get('attribute', 'temperature')
        return True

    def check_connection(self):
        """ Check connection to node and DHT """
        if self.node.connected:
            if not self._dht:
                self._dht = DHT(self.pin, self.model, connection=self.node.connection)
                
    def update(self):
        """ Get data from DHT through nanpy"""
        if self.node.connected:
            try:
                self.check_connection()
                if self._dht:
                    _temp_format = self.mudpi.unit_system == IMPERIAL_SYSTEM
                    temperature = self._dht.readTemperature(_temp_format)
                    humidity = self._dht.readHumidity()
                    data = {'temperature': round(temperature, 2),
                            'humidity': round(humidity, 2)}
                    self._state = data
            except (SerialManagerError, SocketManagerError,
                    BrokenPipeError, ConnectionResetError, OSError,
                    socket.timeout) as e:
                if self.node.connected:
                    Logger.log_formatted(LOG_LEVEL["warning"],
                           f'{self.node.key} -> Broken Connection', 'Timeout', 'notice')
                    self.node.reset_connection()
                    self._dht = None
        return None