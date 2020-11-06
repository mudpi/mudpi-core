import time
import json
import redis
from .sensor import Sensor
import RPi.GPIO as GPIO


# PIN MODE : OUT | IN

class FloatSensor(Sensor):

    def __init__(self, pin, name=None, key=None, redis_conn=None):
        super().__init__(pin, name=name, key=key, redis_conn=redis_conn)
        return

    def init_sensor(self):
        # Initialize the sensor here (i.e. set pin mode, get addresses, etc) this gets called by the worker
        # GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)
        return

    def read(self):
        # Read the sensor(s), parse the data and store it in redis if redis is configured
        value = GPIO.input(self.pin)
        return value

    def read_raw(self):
        # Read the sensor(s) but return the raw data, useful for debugging
        return self.read()
