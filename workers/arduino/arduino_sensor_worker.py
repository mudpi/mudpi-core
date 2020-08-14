import time
import json
import threading
import random
import socket
from nanpy import (SerialManager)
from nanpy.serialmanager import SerialManagerError
from nanpy.sockconnection import (SocketManager, SocketManagerError)
import sys
sys.path.append('..')

import variables
import importlib

#r = redis.Redis(host='127.0.0.1', port=6379)

class ArduinoSensorWorker():
	def __init__(self, config, main_thread_running, system_ready, node_connected, connection=None, api=None):
		#self.config = {**config, **self.config}
		self.config = config
		self.main_thread_running = main_thread_running
		self.system_ready = system_ready
		self.sleep_duration = config.get('sleep_duration', 15)
		self.topic = config.get('topic', 'sensors').replace(" ", "_").lower()
		self.sensors_ready = False
		self.node_connected = node_connected
		self.connection = connection
		self.api = api
		self.sensors = []
		if node_connected.is_set():
			self.init_sensors()
			self.sensors_ready = True
		return

	def dynamic_import(self, path):
		components = path.split('.')

		s = ''
		for component in components[:-1]:
			s += component + '.'

		parent = importlib.import_module(s[:-1])
		sensor = getattr(parent, components[-1])

		return sensor

	def init_sensors(self, connection=None):
		print('{name} Sensor Worker...\t\t\033[1;32m Preparing\033[0;0m'.format(**self.config))
		try:
			for sensor in self.config['sensors']:
				if sensor.get('type', None) is not None:
					#Get the sensor from the sensors folder {sensor name}_sensor.{SensorName}Sensor
					sensor_type = 'sensors.arduino.' + sensor.get('type').lower() + '_sensor.' + sensor.get('type').capitalize() + 'Sensor'
					
					#analog_pin_mode = False if sensor.get('is_digital', False) else True

					imported_sensor = self.dynamic_import(sensor_type)
					#new_sensor = imported_sensor(sensor.get('pin'), name=sensor.get('name', sensor.get('type')), connection=self.connection, key=sensor.get('key', None))
					
					# Define default kwargs for all sensor types, conditionally include optional variables below if they exist
					sensor_kwargs = { 
						'name' : sensor.get('name', sensor.get('type')),
						'pin' : int(sensor.get('pin')),
						'connection': self.connection,
						'key'  : sensor.get('key', None)
					}

					# optional sensor variables 
					# Model is specific to DHT modules to specify DHT11(11) DHT22(22) or DHT2301(21)
					if sensor.get('model'):
						sensor_kwargs['model'] = str(sensor.get('model'))
						sensor_kwargs['api'] = self.api

					new_sensor = imported_sensor(**sensor_kwargs)

					# print('{type} Sensor {pin}...\t\t\t\033[1;32m Preparing\033[0;0m'.format(**sensor))
					new_sensor.init_sensor()
					self.sensors.append(new_sensor)
					# print('{type} Sensor {pin}...\t\t\t\033[1;32m Ready\033[0;0m'.format(**sensor))
					self.sensors_ready = True
		except (SerialManagerError, SocketManagerError, BrokenPipeError, ConnectionResetError, OSError, socket.timeout) as e:
			# Connection error. Reset everything for reconnect
			self.sensors_ready = False
			self.node_connected.clear()
			self.sensors = []
		return

	def run(self):
		t = threading.Thread(target=self.work, args=())
		t.start()
		return t

	def work(self):
		while self.main_thread_running.is_set():
			if self.system_ready.is_set():
				if self.node_connected.is_set():
					if self.sensors_ready:
						try:
							message = {'event':'SensorUpdate'}
							readings = {}
							for sensor in self.sensors:
								result = sensor.read()
								readings[sensor.key] = result
								#r.set(sensor.get('key', sensor.get('type')), value)
								
							print("Node Readings: ", readings)
							message['data'] = readings
							variables.r.publish(self.topic, json.dumps(message))
						except (SerialManagerError, SocketManagerError, BrokenPipeError, ConnectionResetError, OSError, socket.timeout) as e:
							print('\033[1;36m{name}\033[0;0m -> \033[1;33mSensors Timeout!\033[0;0m'.format(**self.config))
							self.sensors = []
							self.node_connected.clear()
							time.sleep(15)
					else:
						# Worker connected but sensors not initialized
						self.init_sensors()
						self.sensors_ready = True
				else:
					#Node not connected, sensors not ready. Wait for reconnect
					self.sensors = []
					self.sensors_ready = False

			# Main loop delay between cycles			
			time.sleep(self.sleep_duration)

		#This is only ran after the main thread is shut down
		print("{name} Sensors Shutting Down...\t\033[1;32m Complete\033[0;0m".format(**self.config))