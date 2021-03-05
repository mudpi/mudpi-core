""" 
    DHT Sensor Interface
    Connects to a DHT device to get
    humidity and temperature readings. 
"""
import re
import board
import adafruit_dht
from mudpi.extensions import BaseInterface
from mudpi.extensions.sensor import Sensor
from mudpi.exceptions import MudPiError, ConfigError


class Interface(BaseInterface):

    def load(self, config):
        """ Load DHT sensor component from configs """
        sensor = DHTSensor(self.mudpi, config)
        if sensor.connect():
            self.add_component(sensor)
        return True

    def validate(self, config):
        """ Validate the dht config """
        if not config.get('pin'):
            raise ConfigError('Missing `pin` in DHT config.')

        if not re.match(r'D\d+$', config['pin']) and not re.match(r'A\d+$', config['pin']):
            raise ConfigError(
                "Cannot detect pin type (Digital or analog), "
                "should be Dxx or Axx for digital or analog. "
                "Please refer to "
                "https://github.com/adafruit/Adafruit_Blinka/tree/master/src/adafruit_blinka/board"
            )

        valid_models = ['11', '22', '2302']
        if config.get('model') not in valid_models:
            config['model'] = '11'
            Logger.log(
                LOG_LEVEL["warning"],
                'Sensor Model Error: Defaulting to DHT11'
            )
            
        return config


class DHTSensor(Sensor):
    """ DHT Sensor
        Returns a random number
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


    """ Methods """
    def connect(self):
        """ Connect to the device """
        self.pin_obj = getattr(board, self.config['pin'])
        self.type = self.config['model']

        sensor_types = {
            '11': adafruit_dht.DHT11,
            '22': adafruit_dht.DHT22,
            '2302': adafruit_dht.DHT22
        }  # AM2302 = DHT22

        if self.type in sensor_types:
            self._dht_device = sensor_types[self.type]

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
            return False
        return True

    def update(self):
        """ Get data from DHT device"""
        humidity = None
        temperature_c = None

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
                'DHT Device Encountered an Error.'
            )
            self._sensor.exit()

        if humidity is not None and temperature_c is not None:
            readings = {
                'temperature': round(temperature_c * 1.8 + 32, 2),
                'humidity': round(humidity, 2)
            }
            self._state = readings
        else:
            Logger.log(
                LOG_LEVEL["error"],
                'DHT Reading was Invalid. Trying again next cycle.'
            )
            return None
