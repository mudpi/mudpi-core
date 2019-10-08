import time
import datetime
import json
import redis
import threading
import sys
sys.path.append('..')
from pi_sensors.float_sensor import (FloatSensor)
from pi_sensors.humidity_sensor import (HumiditySensor)

import variables

#r = redis.Redis(host='127.0.0.1', port=6379)

class PiSensorWorker():
	def __init__(self, config, main_thread_running, system_ready):
		#self.config = {**config, **self.config}
		self.config = config
		self.main_thread_running = main_thread_running
		self.system_ready = system_ready
		#Store pump event so we can shutdown pump with float readings
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
		for sensor in self.config:
			if sensor.get('type', None) is not None:
				#Get the sensor from the sensors folder {sensor name}_sensor.{SensorName}Sensor
				sensor_type = 'pi_sensors.' + sensor.get('type').lower() + '_sensor.' + sensor.get('type').capitalize() + 'Sensor'

				imported_sensor = self.dynamic_import(sensor_type)

				# Define default kwargs for all sensor types, conditionally include optional variables below if they exist
				sensor_kwargs = { 
					'name' : sensor.get('name', sensor.get('type')),
					'pin' : sensor.get('pin'),
					'key'  : sensor.get('key', None)
				}

				# optional sensor variables 
				# Model is specific to DHT modules to specify DHT11 DHT22 or DHT2302
				if sensor.get('model'):
					sensor_kwargs['model'] = sensor.get('model')

				new_sensor = imported_sensor(**sensor_kwargs)
				new_sensor.init_sensor()

				#Set the sensor type and determine if the readings are critical to operations
				new_sensor.type = sensor.get('type').lower()
				if sensor.get('critical', None) is not None:
					new_sensor.critical = True
				else:
					new_sensor.critical = False

				self.sensors.append(new_sensor)
				print('{type} Sensor (Pi) {pin}...\t\t\t\033[1;32m Ready\033[0;0m'.format(**sensor))
		return

	def run(self): 
		t = threading.Thread(target=self.work, args=())
		t.start()
		print('Pi Sensor Worker [' + str(len(self.config)) + ' Sensors]...\t\t\033[1;32m Running\033[0;0m')
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
					#print(sensor.name, result)

					#Check for a critical water level from any float sensors
					if sensor.type == 'float':
						if sensor.critical:
							if result:
								pass
								#self.pump_ready.set()
							else:
								pass
								#self.pump_ready.clear()
						
							
								
						

				#print(readings)
				message['data'] = readings
				variables.r.publish('pi-sensors', json.dumps(message))
				time.sleep(30)
				
			time.sleep(2)
		#This is only ran after the main thread is shut down
		print("Pi Sensor Worker Shutting Down...\t\033[1;32m Complete\033[0;0m")