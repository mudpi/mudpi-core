import time
import datetime
import json
import redis
import threading
from nanpy import (ArduinoApi, SerialManager, DHT)
from nanpy.serialmanager import SerialManagerError
import sys
sys.path.append('..')
from sensors.float_sensor import (FloatSensor)
from sensors.rain_sensor import (RainSensor)
from sensors.light_sensor import (LightSensor)
from sensors.humidity_sensor import (HumiditySensor)
from sensors.soil_sensor import (SoilSensor)
from sensors.temperature_sensor import (TemperatureSensor)

import variables

#r = redis.Redis(host='127.0.0.1', port=6379)

class SensorWorker():
	def __init__(self, config, main_thread_running, system_ready):
		#self.config = {**config, **self.config}
		self.config = config
		self.main_thread_running = main_thread_running
		self.system_ready = system_ready
		self.node_ready = False
		attempts = 3
		while attempts > 0:
			try:
				attempts-= 1
				self.connection = SerialManager(device=str(self.config.get('address', '/dev/ttyUSB1')))
				self.sensors = []
				self.init_sensors()
			except SerialManagerError:
				print('[{name}] \033[1;33m Node Timeout\033[0;0m ['.format(**self.config), attempts, ' tries left]...')
				time.sleep(15)
				print('Retrying Connection...')
			else:
				print('[{name}] Serial Connected \t\033[1;32m Success\033[0;0m'.format(**self.config))
				self.node_ready = True
				break
		return

	def dynamic_sensor_import(self, name):
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
				sensor_type = 'sensors.' + sensor.get('type').lower() + '_sensor.' + sensor.get('type').capitalize() + 'Sensor'
				#analog_pin_mode = False if sensor.get('is_digital', False) else True
				imported_sensor = self.dynamic_sensor_import(sensor_type)
				new_sensor = imported_sensor(sensor.get('pin'), name=sensor.get('name', sensor.get('type')), connection=self.connection, key=sensor.get('key', None))
				new_sensor.init_sensor()
				self.sensors.append(new_sensor)
				print('{type} Sensor {pin}...\t\t\t\033[1;32m Ready\033[0;0m'.format(**sensor))
		return

	def run(self):
		if self.node_ready:
			t = threading.Thread(target=self.work, args=())
			t.start()
			print(str(self.config['name']) +' Node Worker [' + str(len(self.config['sensors'])) + ' Sensors]...\t\033[1;32m Running\033[0;0m')
			return t
		else:
			print("Node Connection...\t\t\t\033[1;31m Failed\033[0;0m")
			return None

	def work(self):

		while self.main_thread_running.is_set():
			if self.system_ready.is_set() and self.node_ready:
				message = {'event':'SensorUpdate'}
				readings = {}
				for sensor in self.sensors:
					result = sensor.read()
					readings[sensor.key] = result
					#r.set(sensor.get('key', sensor.get('type')), value)
					
				print(readings)
				message['data'] = readings
				variables.r.publish('sensors', json.dumps(message))
				
			time.sleep(15)
		#This is only ran after the main thread is shut down
		print("{name} Node Worker Shutting Down...\t\t\033[1;32m Complete\033[0;0m".format(**self.config))