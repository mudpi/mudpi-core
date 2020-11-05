import time
import json
import redis
from .sensor import Sensor
import digitalio
import board


# PIN MODE : OUT | IN

class FloatSensor(Sensor):

    def __init__(self, pin, name=None, key=None, redis_conn=None):
        super().__init__(pin, name=name, key=key, redis_conn=redis_conn)
        self.pin_obj = getattr(board, pin)
        return

    def init_sensor(self):
        """Initialize the sensor here (i.e. set pin mode, get addresses, etc) this gets called by the worker"""
        self.gpio_pin = digitalio.DigitalInOut(self.pin_obj)  # Default to input : https://github.com/adafruit/Adafruit_Blinka/blob/master/src/digitalio.py#L111
        return

    def read(self):
        """Read the sensor(s), parse the data and store it in redis if redis is configured"""
        value = self.gpio_pin.value
        return value

    def readRaw(self):
        """Read the sensor(s) but return the raw data, useful for debugging"""
        return self.read()
