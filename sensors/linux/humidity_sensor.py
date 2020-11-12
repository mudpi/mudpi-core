import json
import time

import adafruit_dht
import board

from logger.Logger import Logger, LOG_LEVEL
from sensors.linux.sensor import Sensor


class HumiditySensor(Sensor):

    def __init__(self, pin, name=None, key=None, model='11', redis_conn=None):
        super().__init__(pin, name=name, key=key, redis_conn=redis_conn)
        self.pin_obj = getattr(board, pin)
        self.type = model
        return

    def init_sensor(self):
        """
        Initialize the sensor here (i.e. set pin mode, get addresses, etc)
        this gets called by the worker
        """
        sensor_types = {
            '11': adafruit_dht.DHT11,
            '22': adafruit_dht.DHT22,
            '2302': adafruit_dht.DHT22
        }  # AM2302 = DHT22
        if self.type in sensor_types:
            self.sensor = sensor_types[self.type]
        else:
            Logger.log(
                LOG_LEVEL["warning"],
                'Sensor Model Error: Defaulting to DHT11'
            )
            self.sensor = adafruit_dht.DHT11
        return

    def read(self):
        """
        Read the sensor(s), parse the data and store it in redis if redis
        is configured
        """
        # Set values just in case we never set them up.

        humidity = None
        temperature_c = None

        dht_device = self.sensor(self.pin_obj)

        # read_retry() not implemented in new lib
        for i in range(15):

            try:
                dht_device.measure()
                temperature_c = dht_device.temperature
                humidity = dht_device.humidity
                if humidity is not None and temperature_c is not None:
                    dht_device.exit()
                    break

            except RuntimeError:
                # Errors happen fairly often, DHT's are hard to read,
                # just keep going:
                time.sleep(2)
                continue

        if humidity is not None and temperature_c is not None:
            self.r.set(
                self.key + '_temperature',
                round(temperature_c * 1.8 + 32, 2)
            )
            self.r.set(
                self.key + '_humidity', humidity
            )
            readings = {
                'temperature': round(temperature_c * 1.8 + 32, 2),
                'humidity': round(humidity, 2)
            }
            self.r.set(self.key, json.dumps(readings))
            dht_device.exit()

            return readings

        else:
            Logger.log(
                LOG_LEVEL["error"],
                'DHT Reading was Invalid. Trying again next cycle.'
            )
            return None

    def read_raw(self):
        """
        Read the sensor(s) but return the raw data, useful for debugging

        Returns:

        """
        return self.read()
