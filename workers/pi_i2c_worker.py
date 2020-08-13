import time
import datetime
import json
import redis
import threading
import sys
sys.path.append('..')
from sensors.pi.i2c.bme680_sensor import (Bme680Sensor)

import variables

#r = redis.Redis(host='127.0.0.1', port=6379)
# def clamp(n, smallest, largest): return max(smallest, min(n, largest))

class PiI2CWorker():
	def __init__(self, config, main_thread_running, system_ready):
		#self.config = {**config, **self.config}
		self.config = config
		self.channel = config.get('channel', 'i2c').replace(" ", "_").lower()
		self.sleep_duration = config.get('sleep_duration', 30)
		self.main_thread_running = main_thread_running
		self.system_ready = system_ready
		self.sensors = []
		self.init_sensors()
		return

	def dynamic_import(self, name):
		#Split path of the class folder structure: {sensor name}_sensor . {SensorName}Sensor
		components = name.split('.')
		#Dynamically import root of component path
		module = __import__(components[0])
		#Get component attributes
		for component in components[1:]:
			module = getattr(module, component)
		return module

	def init_sensors(self):
		for sensor in self.config['sensors']:
			if sensor.get('type', None) is not None:
				#Get the sensor from the sensors folder {sensor name}_sensor.{SensorName}Sensor
				sensor_type = 'sensors.pi.i2c.' + sensor.get('type').lower() + '_sensor.' + sensor.get('type').capitalize() + 'Sensor'

				imported_sensor = self.dynamic_import(sensor_type)

				# Define default kwargs for all sensor types, conditionally include optional variables below if they exist
				sensor_kwargs = { 
					'name' : sensor.get('name', sensor.get('type')),
					'address' : int(sensor.get('address', 00)),
					'key'  : sensor.get('key', None)
				}

				# optional sensor variables 
				# Model is specific to DHT modules to specify DHT11 DHT22 or DHT2302
				if sensor.get('model'):
					sensor_kwargs['model'] = str(sensor.get('model'))

				new_sensor = imported_sensor(**sensor_kwargs)
				new_sensor.init_sensor()

				#Set the sensor type and determine if the readings are critical to operations
				new_sensor.type = sensor.get('type').lower()

				self.sensors.append(new_sensor)
				print('{type} Sensor (Pi) {address}...\t\t\033[1;32m Ready\033[0;0m'.format(**sensor))
		return

	def run(self): 
		t = threading.Thread(target=self.work, args=())
		t.start()
		print('Pi I2C Sensor Worker [' + str(len(self.sensors)) + ' Sensors]...\t\t\033[1;32m Running\033[0;0m')
		return t

	def work(self):

		while self.main_thread_running.is_set():
			if self.system_ready.is_set():
				message = {'event':'PiSensorUpdate'}
				readings = {}

				for sensor in self.sensors:
					result = sensor.read()
					readings[sensor.key] = result
					variables.r.set(sensor.key, json.dumps(result))
				
				message['data'] = readings
				print("Reaadings I2C: ", readings);
				variables.r.publish(self.channel, json.dumps(message))
				time.sleep(self.sleep_duration)
				
			time.sleep(2)
		#This is only ran after the main thread is shut down
		print("Pi I2C Sensor Worker Shutting Down...\t\033[1;32m Complete\033[0;0m")