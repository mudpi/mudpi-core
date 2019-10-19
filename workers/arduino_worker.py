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

class ArduinoWorker():
	def __init__(self, config, main_thread_running, system_ready, connection=None):
		#self.config = {**config, **self.config}
		self.config = config
		self.main_thread_running = main_thread_running
		self.system_ready = system_ready
		self.sleep_duration = config.get('sleep_duration', 15)
		self.node_ready = False
		self.connection = connection
		self.sensors = []
		if connection is None:
			self.connection = self.connect()
		return

	def connect(self):
		attempts = 3
		conn = None
		if self.config.get('use_wifi', False):
			while attempts > 0 and self.main_thread_running.is_set():
				try:
					print('\033[1;36m{0}\033[0;0m -> Connecting...         \t'.format(self.config["name"], (3-attempts)), end='\r', flush=True)
					attempts-= 1
					conn = SocketManager(host=str(self.config.get('address', 'mudpi.local')))
					self.connection = conn
					self.init_sensors()
				except (SocketManagerError, BrokenPipeError, ConnectionResetError) as e:
					print('{name} -> Connecting...\t\t\033[1;33m Timeout\033[0;0m           '.format(**self.config))
					if attempts > 0:
						print('{name} -> Preparing Reconnect...  \t'.format(**self.config), end='\r', flush=True)
					else:
						print('{name} -> Connection Attempts...\t\033[1;31m Failed\033[0;0m           '.format(**self.config))
					conn = None
					self.resetConnection()
					time.sleep(15)
				except (OSError, KeyError) as e:
					print('[{name}] \033[1;33m Node Not Found. (Is it online?)\033[0;0m'.format(**self.config))
					conn = None
					self.resetConnection()
					time.sleep(15)
				else:
					print('[{name}] Wifi Connection \t\t\033[1;32m Success\033[0;0m                 '.format(**self.config))
					self.node_ready = True
					break
		else:
			while attempts > 0 and self.main_thread_running.is_set():
				try:
					attempts-= 1
					connection = SerialManager(device=str(self.config.get('address', '/dev/ttyUSB1')))
				except SerialManagerError:
					print('[{name}] \033[1;33m Node Timeout\033[0;0m ['.format(**self.config), attempts, ' tries left]...')
					self.resetConnection()
					time.sleep(15)
					print('Retrying Connection...')
					conn = None
				else:
					if conn is not None:
						self.connection = conn
						print('[{name}] Serial Connection \t\033[1;32m Success\033[0;0m         '.format(**self.config))
						self.init_sensors()
						self.node_ready = True
					break
		return conn

	def resetConnection(self):
		self.connection = None
		self.sensors = []
		self.node_ready = False


	def dynamic_import(self, path):
		components = path.split('.')

		s = ''
		for component in components[:-1]:
			s += component + '.'

		parent = importlib.import_module(s[:-1])
		sensor = getattr(parent, components[-1])

		return sensor

	def init_sensors(self, connection=None):
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
					'pin' : sensor.get('pin'),
					'connection': self.connection,
					'key'  : sensor.get('key', None)
				}

				# optional sensor variables 
				# Model is specific to DHT modules to specify DHT11(11) DHT22(22) or DHT2301(21)
				if sensor.get('model'):
					sensor_kwargs['model'] = sensor.get('model')

				new_sensor = imported_sensor(**sensor_kwargs)

				new_sensor.init_sensor()
				self.sensors.append(new_sensor)
				print('{type} Sensor {pin}...\t\t\t\033[1;32m Ready\033[0;0m'.format(**sensor))
		return

	def run(self):
		t = threading.Thread(target=self.work, args=())
		t.start()
		if self.node_ready:
			print(str(self.config['name']) +' Node Worker [' + str(len(self.config['sensors'])) + ' Sensors]...\t\033[1;32m Running\033[0;0m')
		else:
			print(str(self.config['name']) +' Sensors...\t\t\t\033[1;33m Pending Reconnect\033[0;0m.')
		return t

	def work(self):
		while self.main_thread_running.is_set():
			if self.system_ready.is_set() and self.node_ready:
				try:
					message = {'event':'SensorUpdate'}
					readings = {}
					for sensor in self.sensors:
						result = sensor.read()
						readings[sensor.key] = result
						#r.set(sensor.get('key', sensor.get('type')), value)
						
					print(readings)
					message['data'] = readings
					variables.r.publish('sensors', json.dumps(message))
				except (SerialManagerError, SocketManagerError, BrokenPipeError, ConnectionResetError, OSError, socket.timeout) as e:
					print('[{name}] \033[1;33m Sensors Timeout!\033[0;0m \033[1;31m(Connection Failed)\033[0;0m'.format(**self.config))
					self.resetConnection()
					time.sleep(15)
			else:
				# Node not ready yet should try reconnect
				if self.connection is None:
					# Random delay before connections to offset multiple attempts
					random_delay = random.randrange(20,120)
					time.sleep(10)
					print("\033[1;36m{name}\033[0;0m -> Attempting Reconnect to \033[1;36mSensors\033[0;0m in".format(**self.config),'{0}s...'.format(random_delay))
					# Two separate checks for main thread event to prevent re-connections during shutdown
					if self.main_thread_running.is_set():
						time.sleep(random_delay)
					if self.main_thread_running.is_set():
						self.connection = self.connect()
			# Main loop delay between cycles			
			time.sleep(self.sleep_duration)

		#This is only ran after the main thread is shut down
		print("{name} Sensors Shutting Down...\t\033[1;32m Complete\033[0;0m".format(**self.config))