""" 
    BME680 Sensor Interface
    Connects to a BME680 device to get
    environment and climate readings. 
"""
import board
import adafruit_bme680

from busio import I2C
from mudpi.extensions import BaseInterface
from mudpi.extensions.sensor import Sensor
from mudpi.exceptions import MudPiError, ConfigError


class Interface(BaseInterface):

    def load(self, config):
        """ Load BME680 sensor component from configs """
        sensor = BME680Sensor(self.mudpi, config)
        if sensor:
            self.add_component(sensor)
        return True

    def validate(self, config):
        """ Validate the bme680 config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('address'):
                # raise ConfigError('Missing `address` in BME680 config.')
                conf['address'] = 0x77
            else:
                addr = conf['address']

                # Convert hex string/int to actual hex
                if isinstance(addr, str):
                    addr = hex(int(addr, 16))
                elif isinstance(addr, int):
                    addr = hex(addr)

                conf['address'] = addr

        return config


class BME680Sensor(Sensor):
    """ BME680 Sensor
        Gets readins for gas, pressure, humidity, 
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
        """ Connect to the device """
        self.i2c = I2C(board.SCL, board.SDA)
        self._sensor = adafruit_bme680.Adafruit_BME680_I2C(
            self.i2c, address=self.config['address'], debug=False
        )
        # Change this to match the location's pressure (hPa) at sea level
        self._sensor.sea_level_pressure = self.config.get('calibration_pressure', 1013.25)

        return True

    def update(self):
        """ Get data from BME680 device"""
        temperature = round((self.sensor.temperature - 5) * 1.8 + 32, 2)
        gas = self.sensor.gas
        humidity = round(self.sensor.humidity, 1)
        pressure = round(self.sensor.pressure, 2)
        altitude = round(self.sensor.altitude, 3)

        if humidity is not None and temperature is not None:
            readings = {
                'temperature': temperature,
                'humidity': humidity,
                'pressure': pressure,
                'gas': gas,
                'altitude': altitude
            }
            self._state = readings
            return readings
        else:
            Logger.log(
                LOG_LEVEL["error"],
                'Failed to get reading [BME680]. Try again!'
            )

        return None
