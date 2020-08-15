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

class LightSensor(Sensor):

	def __init__(self, pin, name='LightSensor', key=None, connection=default_connection, redis_conn=None):
		super().__init__(pin, name=name, key=key, connection=connection, redis_conn=redis_conn)
		return

	def init_sensor(self):
		# read data using pin specified pin
		self.api.pinMode(self.pin, self.api.INPUT)

	def read(self):
		light_intesity = self.api.analogRead(self.pin)
		self.r.set(self.key, light_intesity)
		return light_intesity

	def readRaw(self):
		return self.read()