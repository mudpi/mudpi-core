import json
import sys

import smbus

from logger.Logger import Logger, LOG_LEVEL
from sensors.linux.i2c.sensor import Sensor




class T9602Sensor(Sensor):

    def __init__(self, address=None, name=None, key=None, redis_conn=None):
        super().__init__(address, name=name, key=key, redis_conn=redis_conn)
        self.address = address
        return

    def init_sensor(self):
        '''This is the bus number : the 1 in "/dev/i2c-1"
        I enforced it to 1 because there is only one on Raspberry Pi.
        We might want to add this parameter in i2c sensor config in the future.
        We might encounter boards with several buses.'''
        self.bus = smbus.SMBus(1)
        return

    def read(self):
        for i in range(5):   # 5 tries
            try:
                data = self.bus.read_i2c_block_data(self.address, 0, 4)
                break
            except OSError:
                Logger.log(
                    LOG_LEVEL["info"],
                    "Single reading error [t9602]. It happens, let's try again..."
                )
                time.sleep(2)

        humidity = (((data[0] & 0x3F) << 8) + data[1]) / 16384.0 * 100.0
        temperature_c = ((data[2] * 64) + (data[3] >> 2)) / 16384.0 * 165.0 - 40.0

        humidity = round(humidity, 2)
        temperature_c = round(temperature_c, 2)

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
