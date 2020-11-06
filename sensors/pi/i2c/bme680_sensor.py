import time
import json
import redis
from .sensor import Sensor
import board
from busio import I2C
import adafruit_bme680

from logger.Logger import Logger, LOG_LEVEL

import sys

sys.path.append('..')

import variables


class Bme680Sensor(Sensor):

    def __init__(self, address=None, name=None, key=None, redis_conn=None):
        super().__init__(address, name=name, key=key, redis_conn=redis_conn)
        return

    def init_sensor(self):
        self.sensor = adafruit_bme680.Adafruit_BME680_I2C(self.i2c,
                                                          debug=False)
        # change this to match the location's pressure (hPa) at sea level
        self.sensor.sea_level_pressure = 1013.25
        return

    def read(self):
        temperature = round((self.sensor.temperature - 5) * 1.8 + 32, 2)
        gas = self.sensor.gas
        humidity = round(self.sensor.humidity, 1)
        pressure = round(self.sensor.pressure, 2)
        altitude = round(self.sensor.altitude, 3)

        if humidity is not None and temperature is not None:
            self.r.set(self.key + '_temperature', temperature)
            self.r.set(self.key + '_humidity', humidity)
            self.r.set(self.key + '_gas', gas)
            self.r.set(self.key + '_pressure', pressure)
            self.r.set(self.key + '_altitude', altitude)
            readings = {'temperature': temperature, 'humidity': humidity,
                        'pressure': pressure, 'gas': gas, 'altitude': altitude}
            self.r.set(self.key, json.dumps(readings))
            # print('BME680:', readings)
            return readings
        else:
            Logger.log(LOG_LEVEL["error"],
                       'Failed to get reading [BME680]. Try again!')

    def read_raw(self):
        # Read the sensor(s) but return the raw data, useful for debugging
        return self.read()
