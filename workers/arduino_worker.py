import time
import json
import threading
import random
import socket
from nanpy import (SerialManager, ArduinoApi)
from nanpy.serialmanager import SerialManagerError
from nanpy.sockconnection import (SocketManager, SocketManagerError)
from workers.arduino_control_worker import ArduinoControlWorker
from workers.arduino_sensor_worker import ArduinoSensorWorker
from workers.arduino_relay_worker import ArduinoRelayWorker
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
		self.connection = connection
		self.threads = []
		self.node_ready = threading.Event()
		self.node_connected = threading.Event() #Event to signal if camera can be used
		self.workers = []
		self.relays = []
		self.relayEvents = {}
		self.relay_index = 0
		self.api = None
		if connection is None:
			self.connection = self.connect()

		try:
			if self.config['controls'] is not None:
				acw = ArduinoControlWorker(self.config, main_thread_running, system_ready, self.node_connected, self.connection)
				self.workers.append(acw)
				if acw is not None:
					self.threads.append(acw)
				time.sleep(3)
		except KeyError:
			print('No Node Controls Found to Load')

		try:
			if self.config['sensors'] is not None:
				asw = ArduinoSensorWorker(self.config, main_thread_running, system_ready, self.node_connected, self.connection)
				self.workers.append(asw)
				time.sleep(3)
		except KeyError:
			print('No Node Sensors Found to Load')

		try:
			if self.config['relays'] is not None:
				for relay in self.config['relays']:
					#Create a threading event for each relay to check status
					relayState = {
						"available": threading.Event(), #Event to allow relay to activate
						"active": threading.Event() #Event to signal relay to open/close
					}
					#Store the relays under the key or index if no key is found, this way we can reference the right relays
					self.relayEvents[relay.get("key", self.relay_index)] = relayState
					#Create sensor worker for a relay
					arw = ArduinoRelayWorker(relay, main_thread_running, system_ready, relayState['available'], relayState['active'], self.node_connected, self.connection, self.api)
					#Make the relays available, this event is toggled off elsewhere if we need to disable relays
					relayState['available'].set()
					self.relay_index +=1
					self.workers.append(arw)
					time.sleep(3)
		except KeyError:
			print('No Node Relays Found to Load')

		return

	def connect(self):
		attempts = 3
		conn = None
		if self.config.get('use_wifi', False):
			while attempts > 0 and self.main_thread_running.is_set():
				try:
					print('\033[1;36m{0}\033[0;0m -> Connecting...         \t'.format(self.config["name"], (3-attempts)))
					attempts-= 1
					conn = SocketManager(host=str(self.config.get('address', 'mudpi.local')))
					# Test the connection with api
					self.api = ArduinoApi(connection=conn)
				except (SocketManagerError, BrokenPipeError, ConnectionResetError, socket.timeout) as e:
					print('{name} -> Connecting...\t\t\033[1;33m Timeout\033[0;0m           '.format(**self.config))
					print(e);
					if attempts > 0:
						print('{name} -> Preparing Reconnect...  \t'.format(**self.config))
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
					print('{name} -> Wifi Connection \t\t\033[1;32m Success\033[0;0m                 '.format(**self.config))
					for worker in self.workers:
							worker.connection = conn
					self.node_connected.set()
					self.node_ready.set()
					break
		else:
			while attempts > 0 and self.main_thread_running.is_set():
				try:
					attempts-= 1
					conn = SerialManager(device=str(self.config.get('address', '/dev/ttyUSB1')))
				except SerialManagerError:
					print('{name} -> Connecting...\t\t\033[1;33m Timeout\033[0;0m           '.format(**self.config))
					if attempts > 0:
						print('{name} -> Preparing Reconnect...  \t'.format(**self.config), end='\r', flush=True)
					else:
						print('{name} -> Connection Attempts...\t\033[1;31m Failed\033[0;0m           '.format(**self.config))
					self.resetConnection()
					conn = None
					time.sleep(15)
				else:
					if conn is not None:
						print('[{name}] Serial Connection \t\033[1;32m Success\033[0;0m         '.format(**self.config))
						for worker in self.workers:
							worker.connection = conn
						self.node_connected.set()
						self.node_ready.set()
					break
		return conn

	def resetConnection(self):
		self.connection = None
		self.node_connected.clear()
		self.node_ready.clear()


	def run(self):
		for worker in self.workers:
			self.threads.append(worker.run())
			time.sleep(4)
			
		t = threading.Thread(target=self.work, args=())
		t.start()
		if self.node_ready.is_set():
			print(str(self.config['name']) +' Node Worker '+ '[S: ' + str(len(self.config['sensors'])) + ']' + '[C: ' + str(len(self.config['controls'])) + ']...\t\033[1;32m Running\033[0;0m')
		else:
			print(str(self.config['name']) +'...\t\t\t\t\033[1;33m Pending Reconnect\033[0;0m ')
		return t

	def work(self):
		delay_multiplier = 1
		while self.main_thread_running.is_set():
			if self.system_ready.is_set() and self.node_ready.is_set():
				if not self.node_connected.is_set():
					#Connection Broken - Reset Connection
					self.resetConnection()
					print('\033[1;36m{name}\033[0;0m -> \033[1;33mTimeout!\033[0;0m \t\t\t\033[1;31m Connection Broken\033[0;0m'.format(**self.config))
					time.sleep(30)
			else:
				# Node reconnection cycle
				if not self.node_connected.is_set():
					# Random delay before connections to offset multiple attempts (1-5 min delay)
					random_delay = random.randrange(30, self.config.get("max_reconnect_delay", 300)) * delay_multiplier
					time.sleep(10)
					print('\033[1;36m'+str(self.config['name']) +'\033[0;0m -> Retrying in '+ '{0}s...'.format(random_delay)+'\t\033[1;33m Pending Reconnect\033[0;0m ')
					# Two separate checks for main thread event to prevent re-connections during shutdown
					if self.main_thread_running.is_set():
						time.sleep(random_delay)
					if self.main_thread_running.is_set():
						self.connection = self.connect()
					if self.connection is None:
						delay_multiplier += 1
						if delay_multiplier > 6:
							delay_multiplier = 6
					else:
						delay_multiplier = 1
			# Main loop delay between cycles			
			time.sleep(self.sleep_duration)

		#This is only ran after the main thread is shut down
		#Join all our sub threads for shutdown
		for thread in self.threads:
			thread.join()
		print("{name} Shutting Down...\t\t\033[1;32m Complete\033[0;0m".format(**self.config))