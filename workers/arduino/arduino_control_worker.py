import time
import json
import threading
import random
import socket
from nanpy import (SerialManager)
from nanpy.serialmanager import SerialManagerError
from nanpy.sockconnection import (SocketManager, SocketManagerError)
from .worker import Worker
import sys
sys.path.append('..')

import variables
import importlib

#r = redis.Redis(host='127.0.0.1', port=6379)

class ArduinoControlWorker(Worker):
	def __init__(self, config, main_thread_running, system_ready, node_connected, connection=None):
		super().__init__(config, main_thread_running, system_ready)
		self.controls_ready = False
		self.node_connected = node_connected
		self.connection = connection
		
		self.controls = []

		if node_connected.is_set():
			self.init()
			self.controls_ready = True
		return


	def init(self):
		try:
			for control in self.config['controls']:
				if control.get('type', None) is not None:
					#Get the control from the controls folder {control name}_control.{ControlName}Control
					control_type = 'controls.arduino.' + control.get('type').lower() + '_control.' + control.get('type').capitalize() + 'Control'
					
					analog_pin_mode = False if control.get('is_digital', False) else True

					imported_control = self.dynamic_import(control_type)
					
					# Define default kwargs for all control types, conditionally include optional variables below if they exist
					control_kwargs = { 
						'name' : control.get('name', None),
						'pin' : int(control.get('pin')),
						'connection': self.connection,
						'key'  : control.get('key', None),
						'analog_pin_mode': analog_pin_mode,
						'topic': control.get('topic', None)
					}

					# optional control variables 
					# add conditional control vars here...

					new_control = imported_control(**control_kwargs)

					new_control.init_control()
					self.controls.append(new_control)
					self.controls_ready = True
					print('{type} Control {pin}...\t\t\t\033[1;32m Ready\033[0;0m'.format(**control))
		except (SerialManagerError, SocketManagerError, BrokenPipeError, ConnectionResetError, OSError, socket.timeout) as e:
			# Connection error. Reset everything for reconnect
			self.controls_ready = False
			self.node_connected.clear()
			self.controls = []
		return

	def run(self):
		t = threading.Thread(target=self.work, args=())
		t.start()
		return t

	def work(self):
		while self.main_thread_running.is_set():
			if self.system_ready.is_set():
				if self.node_connected.is_set():
					if self.controls_ready:
						try:
							readings = {}
							for control in self.controls:
								result = control.read()
								readings[control.key] = result
						except (SerialManagerError, SocketManagerError, BrokenPipeError, ConnectionResetError, OSError, socket.timeout) as e:
							print('\033[1;36m{name}\033[0;0m -> \033[1;33mControls Timeout!\033[0;0m'.format(**self.config))
							self.controls_ready = False
							self.controls = []
							self.node_connected.clear()
							time.sleep(15)
					else:
						# Worker connected but controls not initialized
						self.init()
				else:
					# Node not connected. Wait for reconnect
					self.controls_ready = False
					self.controls = []
					time.sleep(10)
			#Will this nuke the connection?	
			time.sleep(0.05)
		#This is only ran after the main thread is shut down
		print("{name} Controls Shutting Down...\t\033[1;32m Complete\033[0;0m".format(**self.config))