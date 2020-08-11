import time
import json
import redis
from .sensor import Sensor
import RPi.GPIO as GPIO
import board
from busio import I2C
import adafruit_bme680

import sys
sys.path.append('..')

import variables

#r = redis.Redis(host='127.0.0.1', port=6379)
#PIN MODE : OUT | IN

class Bme680Sensor(Sensor):

	def __init__(self, pin = None, name='PressureSensor', key=None):
		super().__init__(pin, name=name, key=key)
		return

	def init_sensor(self):
		#Initialize the sensor here (i.e. set pin mode, get addresses, etc) this gets called by the worker
		self.i2c = I2C(board.SCL, board.SDA)
		self.sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
		# change this to match the location's pressure (hPa) at sea level
		self.sensor.sea_level_pressure = 1013.25
		return

	def read(self):
		#Read the sensor(s), parse the data and store it in redis if redis is configured

		temperature = round((self.sensor.temperature - 5) * 1.8 + 32, 2)
		gas = self.sensor.gas
		humidity = round(self.sensor.humidity, 1)
		pressure = self.sensor.pressure
		altitude = round(self.sensor.altitude, 3)
		
		if humidity is not None and temperature is not None:
			variables.r.set(self.key + '_temperature', temperature)
			variables.r.set(self.key + '_humidity', humidity)
			variables.r.set(self.key + '_gas', gas)
			variables.r.set(self.key + '_pressure', pressure)
			variables.r.set(self.key + '_altitude', altitude)
			readings = {'temperature': temperature, 'humidity': humidity, 'pressure': pressure, 'gas': gas, 'altitude': altitude}
			variables.r.set(self.key, json.dumps(readings))
			print('BME680:', readings)
			return readings
		else:
			print('Failed to get reading [BME680]. Try again!')


	def readRaw(self):
		#Read the sensor(s) but return the raw data, useful for debugging
		return self.read()
