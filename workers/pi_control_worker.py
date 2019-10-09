import time
import datetime
import json
import redis
import threading
import sys
sys.path.append('..')
from controls.pi.button_control import (ButtonControl)

import variables

#r = redis.Redis(host='127.0.0.1', port=6379)
# def clamp(n, smallest, largest): return max(smallest, min(n, largest))

class PiControlWorker():
	def __init__(self, config, main_thread_running, system_ready):
		#self.config = {**config, **self.config}
		self.config = config
		self.channel = config.get('channel', 'controls').replace(" ", "_").lower()
		self.sleep_duration = config.get('sleep_duration', 0.5)
		self.main_thread_running = main_thread_running
		self.system_ready = system_ready
		#Store pump event so we can shutdown pump with float readings
		self.controls = []
		self.init_controls()
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

	def init_controls(self):
		for control in self.config['controls']:
			if control.get('type', None) is not None:
				#Get the control from the controls folder {control name}_control.{ControlName}Control
				control_type = 'controls.pi.' + control.get('type').lower() + '_control.' + control.get('type').capitalize() + 'Control'
				
				imported_control = self.dynamic_import(control_type)
				#new_control = imported_control(control.get('pin'), name=control.get('name', control.get('type')), connection=self.connection, key=control.get('key', None))
				
				# Define default kwargs for all control types, conditionally include optional variables below if they exist
				control_kwargs = { 
					'name' : control.get('name', control.get('type')),
					'pin' : control.get('pin'),
					'key'  : control.get('key', None),
					'topic': control.get('topic', None),
					'resistor': control.get('resistor', None),
					'edge_detection': control.get('edge_detection', None),
					'debounce': control.get('debounce', None)
				}

				# optional control variables 
				# add conditional control vars here...

				new_control = imported_control(**control_kwargs)

				new_control.init_control()
				self.controls.append(new_control)
				print('{type} Control {pin}...\t\t\t\033[1;32m Ready\033[0;0m'.format(**control))
		return

	def run(self): 
		t = threading.Thread(target=self.work, args=())
		t.start()
		print('Pi Control Worker [' + str(len(self.config['controls'])) + ' Controls]...\t\t\033[1;32m Running\033[0;0m')
		return t

	def work(self):

		while self.main_thread_running.is_set():
			if self.system_ready.is_set():
				message = {'event':'ControlUpdate'}
				readings = {}
				for control in self.controls:
					result = control.read()
					readings[control.key] = result
					#r.set(sensor.get('key', sensor.get('type')), value)
					
				message['data'] = readings
				variables.r.publish(self.channel, json.dumps(message))
			#Will this nuke the connection?	
			time.sleep(self.sleep_duration)
		#This is only ran after the main thread is shut down
		print("Pi Control Worker Shutting Down...\t\033[1;32m Complete\033[0;0m")