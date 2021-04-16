""" 
    BME280 Sensor Interface
    Connects to a BME280 device to get
    environment and climate readings. 
"""

import board
import adafruit_bme280

from busio import I2C
from mudpi.extensions import BaseInterface
from mudpi.extensions.sensor import Sensor
from mudpi.exceptions import MudPiError, ConfigError


class Interface(BaseInterface):

    def load(self, config):
        """ Load BME280 sensor component from configs """
        sensor = BME280Sensor(self.mudpi, config)
        if sensor:
            self.add_component(sensor)
        return True

    def validate(self, config):
        """ Validate the bme280 config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('key'):
                raise ConfigError('Missing `key` in i2c display config.')

            if not conf.get('address'):
                # raise ConfigError('Missing `address` in BME280 config.')
                conf['address'] = 0x77
            else:
                addr = conf['address']

                # Convert hex string/int to actual hex
                if isinstance(addr, str):
                    addr = int(addr, 16)

                conf['address'] = addr

        return config


class BME280Sensor(Sensor):
    """ BME280 Sensor
        Gets readings for pressure, humidity,
        temperature and altitude.
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
    def init(self):
        self.i2c = I2C(board.SCL, board.SDA)
        self._sensor = adafruit_bme280.Adafruit_BME280_I2C(
            self.i2c, address=self.config['address']
        )
        # Change this to match the location's pressure (hPa) at sea level
        self._sensor.sea_level_pressure = self.config.get('calibration_pressure', 1013.25)

        return True

    def update(self):
        """ Get data from BME280 device"""
        temperature = round(self._sensor.temperature * 1.8 + 32, 2)
        humidity = round(self._sensor.relative_humidity, 1)
        pressure = round(self._sensor.pressure, 2)
        altitude = round(self._sensor.altitude, 3)

        if humidity is not None and temperature is not None:
            readings = {
                'temperature': temperature,
                'humidity': humidity,
                'pressure': pressure,
                'altitude': altitude
            }
            self._state = readings
            return readings
        else:
            Logger.log(
                LOG_LEVEL["error"],
                'Failed to get reading [BME280]. Try again!'
            )

        return None
