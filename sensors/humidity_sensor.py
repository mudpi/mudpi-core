import time
import datetime
import json
import redis
from .sensor import Sensor
from nanpy import (ArduinoApi, SerialManager, DHT)
import sys
sys.path.append('..')

import variables

default_connection = SerialManager(device='/dev/ttyUSB0')
#r = redis.Redis(host='127.0.0.1', port=6379)


class HumiditySensor(Sensor):

	def __init__(self, pin, name='HumiditySensor', key=None, connection=default_connection):
		super().__init__(pin, name=name, key=key, connection=connection)
		return

	def init_sensor(self):
		# prepare sensor on specified pin
		self.dht = DHT(self.pin, DHT.DHT11, connection=self.connection)

	def read(self):
		#Pass true to read in american degrees :)
		temperature = self.dht.readTemperature(True)
		humidity = self.dht.readHumidity()
		data = {'temperature': temperature, 'humidity': humidity}
		variables.r.set(self.key + '_temperature', temperature)
		variables.r.set(self.key + '_humidity', humidity)
		variables.r.set(self.key, json.dumps(data))
		return data

	def readRaw(self):
		return self.read()