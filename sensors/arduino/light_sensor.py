import time
import datetime
import json
import redis
from .sensor import Sensor
from nanpy import (ArduinoApi, SerialManager)

default_connection = SerialManager(device='/dev/ttyUSB0')
r = redis.Redis(host='127.0.0.1', port=6379)

class LightSensor(Sensor):

	def __init__(self, pin, name='LightSensor', key=None, connection=default_connection):
		super().__init__(pin, name=name, key=key, connection=connection)
		return

	def init_sensor(self):
		# read data using pin specified pin
		self.api.pinMode(self.pin, self.api.INPUT)

	def read(self):
		ldr_resistance = self.api.analogRead(self.pin)
		resistor1 = 10 #1k Resistor in the divider
		
		Vout = ldr_resistance * 0.0048828125 #Some frequency clock thing related to amps
		#lux = 500 / ( resistor1 * ( (5 - Vout) / Vout )) #calculate lux using voltage divider formula with LDR to lux conversion
		lux = ( 2500 / Vout - 500 ) / resistor1
		
		#print("ldr_resistance: %d" % ldr_resistance)
		r.set(self.key, lux)
		return lux

	def readRaw(self):
			resistance = self.api.analogRead(self.pin)
			#print("Resistance: %d" % resistance)
			r.set(self.key+'_raw', resistance)
			return resistance