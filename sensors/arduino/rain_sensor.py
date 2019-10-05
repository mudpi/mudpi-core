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

#The resistor reads lower the more water on the sensor
NO_RAIN_BOUNDS = 1000 # and above
MIST_BOUNDS = 800
LIGHT_RAIN_BOUNDS = 750
RAIN_BOUNDS = 550
HEAVY_RAIN_BOUNDS = 400
DOWNPOUR_BOUNDS = 300 # and below

class RainSensor(Sensor):

	def __init__(self, pin, name='RainSensor', key=None, connection=default_connection):
		super().__init__(pin, name=name, key=key, connection=connection)
		return

	def init_sensor(self):
		# read data using pin specified pin
		self.api.pinMode(self.pin, self.api.INPUT)

	def read(self):
		rain = self.api.analogRead(self.pin) #TODO: REMOVE (PERSONAL CONFIG)
		#rain = self.parseSensorReading(self.api.analogRead(self.pin))
		variables.r.set(self.key, rain)
		return rain

	def readRaw(self):
			resistance = self.api.analogRead(self.pin)
			#print("Resistance: %d" % resistance)
			variables.r.set(self.key+'_raw', resistance)
			return resistance

	def parseSensorReading(self, raw_data):
		if(raw_data > MIST_BOUNDS):
			return 'No Rain'
		elif(raw_data <= MIST_BOUNDS and raw_data > LIGHT_RAIN_BOUNDS):
			return 'Mist'
		elif(raw_data <= LIGHT_RAIN_BOUNDS and raw_data > RAIN_BOUNDS):
			return 'Light Rain'
		elif(raw_data <= RAIN_BOUNDS and raw_data > HEAVY_RAIN_BOUNDS):
			return 'Rain'
		elif(raw_data <= HEAVY_RAIN_BOUNDS and raw_data > DOWNPOUR_BOUNDS):
			return 'Heavy Rain'
		elif(raw_data <= DOWNPOUR_BOUNDS):
			return 'Downpour'
		else:
			return 'Bad Sensor Data'

if __name__ == '__main__':
	try:
		loop_count = 10
		while (loop_count > 0):
			sensor = RainSensor(4)
			rainread = sensor.read()
			print('Rain: ', rainread)
			loop_count += 1
			time.sleep(1)
	except KeyboardInterrupt:
		pass
	finally:
		print('Rain Sensor Closing...')