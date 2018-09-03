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

# Wet Water = 287
# Dry Air = 584
AirBounds = 590;
WaterBounds = 280;
intervals = int((AirBounds - WaterBounds)/3);
class SoilSensor(Sensor):

	def __init__(self, pin, name='SoilSensor', key=None, connection=default_connection):
		super().__init__(pin, name=name, key=key, connection=connection)
		return

	def init_sensor(self):
		# read data using pin specified pin
		self.api.pinMode(self.pin, self.api.INPUT)

	def read(self):
		resistance = self.api.analogRead(self.pin)
		moistpercent = ((resistance - WaterBounds) / (AirBounds - WaterBounds)) * 100
		if(moistpercent > 80):
	  		moisture = 'Very Dry - ' + str(int(moistpercent))
		elif(moistpercent <= 80 and moistpercent > 45):
	  		moisture = 'Dry - ' + str(int(moistpercent))
		elif(moistpercent <= 45 and moistpercent > 25):
			moisture = 'Wet - ' + str(int(moistpercent))
		else:
			moisture = 'Very Wet - ' + str(int(moistpercent))
		#print("Resistance: %d" % resistance)
		#TODO: Put redis store into sensor worker
		variables.r.set(self.key, resistance) #TODO: CHANGE BACK TO 'moistpercent' (PERSONAL CONFIG)
		return resistance

	def readRaw(self):
			resistance = self.api.analogRead(self.pin)
			#print("Resistance: %d" % resistance)
			variables.r.set(self.key+'_raw', resistance)
			return resistance