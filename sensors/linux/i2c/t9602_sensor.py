import json
import sys

import smbus

from logger.Logger import Logger, LOG_LEVEL
from sensors.linux.i2c.sensor import Sensor

sys.path.append('..')


class T9602Sensor(Sensor):

    def __init__(self, address=None, name=None, key=None, redis_conn=None):
        super().__init__(address, name=name, key=key, redis_conn=redis_conn)
        self.address = address
        return

    def init_sensor(self):
        self.bus = smbus.SMBus(1)
        return

    def read(self):
        data = self.bus.read_i2c_block_data(self.address, 0, 4)

        humidity = (((data[0] & 0x3F) << 8) + data[1]) / 16384.0 * 100.0
        temperature_c = ((data[2] * 64) + (data[3] >> 2)) / 16384.0 * 165.0 - 40.0

        if humidity is not None and temperature_c is not None:
            self.r.set(self.key + '_temperature', temperature_c)
            self.r.set(self.key + '_humidity', humidity)
            readings = {
                'temperature': temperature_c,
                'humidity': humidity
            }
            self.r.set(self.key, json.dumps(readings))
            return readings
        else:
            Logger.log(
                LOG_LEVEL["error"],
                'Failed to get reading [t9602]. Try again!'
            )

    def read_raw(self):
        """Read the sensor(s) but return the raw data, useful for debugging"""
        return self.read()
