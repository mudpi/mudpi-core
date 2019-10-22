import time
import json
import redis
from nanpy import (ArduinoApi, SerialManager)
import sys
sys.path.append('..')
import variables

default_connection = SerialManager()

# Base sensor class to extend all other arduino sensors from.
class Control():

	def __init__(self, pin, name='Control', connection=default_connection, analog_pin_mode=False, key=None):
		self.pin = pin
		self.name = name
		self.key = key.replace(" ", "_").lower() if key is not None else self.name.replace(" ", "_").lower()
		self.analog_pin_mode = analog_pin_mode
		self.connection = connection
		self.api = ArduinoApi(connection)
		return

	def init_control(self):
		#Initialize the control here (i.e. set pin mode, get addresses, etc)
		self.api.pinMode(self.pin, self.api.INPUT)
		pass

	def read(self):
		#Read the sensor(s), parse the data and store it in redis if redis is configured
		return self.readPin()

	def readRaw(self):
		#Read the sensor(s) but return the raw data, useful for debugging
		pass

	def readPin(self):
		#Read the pin from the ardiuno. Can be analog or digital based on "analog_pin_mode"
		data = self.api.analogRead(self.pin) if self.analog_pin_mode else self.api.digitalRead(self.pin)
		return data

	def emitEvent(self, data): 
		message = {
			'event':'ControlUpdate',
			'data': {
				self.key:data
			}
		}
		print(message["data"])
		variables.r.publish('controls', json.dumps(message))