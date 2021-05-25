""" 
    DHT Sensor Interface
    Connects to a DHT device to get
    humidity and temperature readings. 
"""
import time

import Adafruit_DHT

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

            if str(conf.get('model')) not in DHTSensor.models:
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
        '11': Adafruit_DHT.DHT11,
        '22': Adafruit_DHT.DHT22,
        '2302': Adafruit_DHT.AM2302
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
    def pin(self):
        """ Return a pin for the component """
        return self.config['pin']


    """ Methods """
    def init(self):
        """ Connect to the device """
        self._sensor = None

        if self.type in self.models:
            self._dht_device = self.models[self.type]

        self.check_dht()

        return True

    def check_dht(self):
        """ Check if the DHT device is setup """
        if self._sensor is None:
            try:
                self._sensor = self._dht_device
            except Exception as error:
                Logger.log(
                    LOG_LEVEL["error"],
                    'Sensor Initialize Error: DHT (Legacy) Failed to Init'
                )
                self._sensor = None
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

        if self.check_dht():
            try:
                humidity, temperature_c = Adafruit_DHT.read_retry(self._sensor, self.pin)
            except Exception as error:
                # Errors happen fairly often, DHT's are hard to read
                Logger.log(LOG_LEVEL["debug"], error)

            if humidity is not None and temperature_c is not None:
                _temperature = temperature_c if self.mudpi.unit_system == METRIC_SYSTEM else (temperature_c * 1.8 + 32)
                readings = {
                    'temperature': round(_temperature, 2),
                    'humidity': round(humidity, 2)
                }
                self._state = readings
                return readings
            else:
                Logger.log(
                    LOG_LEVEL["debug"],
                    f'DHT Reading was Invalid (Legacy).'
                )
            time.sleep(2.1)
        return None
