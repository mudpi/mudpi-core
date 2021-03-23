""" 
    DHT Sensor Interface
    Connects to a DHT device to get
    humidity and temperature readings. 
"""
import time

import adafruit_dht
import board

from mudpi.constants import METRIC_SYSTEM
from mudpi.extensions import BaseInterface
from mudpi.extensions.sensor import Sensor
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.exceptions import MudPiError, ConfigError


class Interface(BaseInterface):

    def load(self, config):
        """ Load DHT sensor component from configs """
        sensor = DHTSensor(self.mudpi, config)
        if sensor:
            self.add_component(sensor)
        return True

    def validate(self, config):
        """ Validate the dht config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('pin'):
                raise ConfigError('Missing `pin` in DHT config.')

            if conf.get('model') not in DHTSensor.models:
                conf['model'] = '11'
                Logger.log(
                    LOG_LEVEL["warning"],
                    'Sensor Model Error: Defaulting to DHT11'
                )

        return config


class DHTSensor(Sensor):
    """ DHT Sensor
        Returns a random number
    """

    # Number of attempts to get a good reading (careful to not lock worker!)
    _read_attempts = 3

    # Models of dht devices
    models = {
        '11': adafruit_dht.DHT11,
        '22': adafruit_dht.DHT22,
        '2302': adafruit_dht.DHT22
    }  # AM2302 = DHT22

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
    def type(self):
        """ Model of the device """
        return str(self.config.get('model', '11'))

    @property
    def read_attempts(self):
        """ Number of times to try sensor for good data """
        return int(self.config.get('read_attempts', self._read_attempts))

    """ Methods """

    def init(self):
        """ Connect to the device """
        self._sensor = None
        self.pin_obj = getattr(board, self.config['pin'])

        if self.type in self.models:
            self._dht_device = self.models[self.type]

        try:
            self._sensor = self._dht_device(self.pin_obj)
            Logger.log(
                LOG_LEVEL["debug"],
                'Sensor Initializing: DHT'
            )
        except Exception as error:
            Logger.log(
                LOG_LEVEL["error"],
                'Sensor Initialize Error: DHT Failed to Init'
            )
            Logger.log(
                LOG_LEVEL["debug"],
                error
            )
            return False
        return True

    def update(self):
        """ Get data from DHT device"""
        humidity = None
        temperature_c = None
        _attempts = 0

        while _attempts < self.read_attempts:
            try:
                # Calling temperature or humidity triggers measure()
                temperature_c = self._sensor.temperature
                humidity = self._sensor.humidity
            except RuntimeError as error:
                # Errors happen fairly often, DHT's are hard to read
                Logger.log(LOG_LEVEL["error"], error)
            except Exception as error:
                Logger.log(
                    LOG_LEVEL["error"],
                    f'DHT Device Encountered an Error. Attempt {_attempts + 1}/{self.read_attempts}'
                )
                self._sensor.exit()

            if humidity is not None and temperature_c is not None:
                _temperature = temperature_c if self.mudpi.unit_system == METRIC_SYSTEM else (
                            temperature_c * 1.8 + 32)
                readings = {
                    'temperature': round(_temperature, 2),
                    'humidity': round(humidity, 2)
                }
                self._state = readings
                return readings
            else:
                Logger.log(
                    LOG_LEVEL["error"],
                    f'DHT Reading was Invalid. Attempt {_attempts + 1}/{self.read_attempts}'
                )
            time.sleep(1)
            _attempts += 1
        return None
