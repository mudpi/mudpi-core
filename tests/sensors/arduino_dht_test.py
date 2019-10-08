import time
import datetime
import json
import redis
from nanpy import (ArduinoApi, SerialManager, DHT)

default_connection = SerialManager(device='/dev/ttyUSB0')
#r = redis.Redis(host='127.0.0.1', port=6379)


class HumiditySensor():

	def __init__(self, pin, connection=default_connection):
		self.pin = pin
		self.connection = connection
		self.api = ArduinoApi(connection)
		return

	def init_sensor(self):
		# prepare sensor on specified pin
		self.dht = DHT(self.pin, DHT.DHT11, connection=self.connection)

	def read(self):
		#Pass true to read in american degrees :)
		temperature = self.dht.readTemperature(True)
		humidity = self.dht.readHumidity()
		data = {'temperature': temperature, 'humidity': humidity}
		#r.set('temperature', temperature)
		#r.set('humidity', humidity)
		return data

	def readRaw(self):
		return self.read()

if __name__ == '__main__':
	pin = 3
	conn = SerialManager(device=str(input('Enter Device Serial Port: ')))
	temp = HumiditySensor(pin, connection=conn)
	temp.init_sensor()
	for i in range(400):
		print('Reading')
		temps = temp.read()
		print(temps)
		time.sleep(5)