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

	def __init__(self, pin, name='HumiditySensor', key=None, connection=default_connection, model='11'):
		super().__init__(pin, name=name, key=key, connection=connection)
		self.type = model #DHT11 or DHT22 maybe AM2302
		return

	def init_sensor(self):
		# prepare sensor on specified pin
		sensor_types = { '11': DHT.DHT11,
						'22': DHT.DHT22,
						'2301': DHT.AM2301 }
		if len(self.type) == 3 and self.type in sensor_types:
			self.sensor = sensor_types[self.type]
		else:
			print('Sensor Type Error: Defaulting to DHT11')
			self.sensor = DHT.DHT11
		self.dht = DHT(self.pin, self.sensor, connection=self.connection)

	def read(self):
		#Pass true to read in american degrees :)
		temperature = self.dht.readTemperature(True)
		humidity = self.dht.readHumidity()
		data = {'temperature': round(temperature, 2), 'humidity': round(humidity, 2)}
		variables.r.set(self.key + '_temperature', temperature)
		variables.r.set(self.key + '_humidity', humidity)
		variables.r.set(self.key, json.dumps(data))
		return data

	def readRaw(self):
		return self.read()