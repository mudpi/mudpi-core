import time
import datetime
import json
import redis
from .sensor import Sensor
from nanpy import (ArduinoApi, SerialManager)
import sys
sys.path.append('..')

import variables

default_connection = SerialManager(device='/dev/ttyUSB0')
#r = redis.Redis(host='127.0.0.1', port=6379)

class FloatSensor(Sensor):

	def __init__(self, pin, name='FloatSensor', key=None, connection=default_connection):
		super().__init__(pin, name=name, key=key, connection=connection)
		return

	def init_sensor(self):
		# read data using pin specified pin
		self.api.pinMode(self.pin, self.api.INPUT)

	def read(self):
		value = self.api.digitalRead(self.pin)
		variables.r.set(self.key, value)
		return value

	def readRaw(self):
		return self.read()