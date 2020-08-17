import time
import datetime
import json
import redis
import threading
from .worker import Worker
import sys
sys.path.append('..')
from controls.pi.button_control import (ButtonControl)
from controls.pi.switch_control import (SwitchControl)

from logger.Logger import Logger, LOG_LEVEL

class PiControlWorker(Worker):
	def __init__(self, config, main_thread_running, system_ready):
		super().__init__(config, main_thread_running, system_ready)
		self.topic = config.get('topic', 'controls').replace(" ", "_").lower()
		self.sleep_duration = config.get('sleep_duration', 0.5)

		self.controls = []
		self.init()
		return

	def init(self):
		for control in self.config['controls']:
			if control.get('type', None) is not None:
				#Get the control from the controls folder {control name}_control.{ControlName}Control
				control_type = 'controls.pi.' + control.get('type').lower() + '_control.' + control.get('type').capitalize() + 'Control'
				
				imported_control = self.dynamic_import(control_type)
				#new_control = imported_control(control.get('pin'), name=control.get('name', control.get('type')), connection=self.connection, key=control.get('key', None))
				
				# Define default kwargs for all control types, conditionally include optional variables below if they exist
				control_kwargs = { 
					'name' : control.get('name', control.get('type')),
					'pin' : int(control.get('pin')),
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
				Logger.log(LOG_LEVEL["info"], '{type} Control {pin}...\t\t\t\033[1;32m Ready\033[0;0m'.format(**control))
		return

	def run(self): 
		Logger.log(LOG_LEVEL["info"], 'Pi Control Worker [' + str(len(self.config['controls'])) + ' Controls]...\t\033[1;32m Online\033[0;0m')
		return super().run()

	def work(self):
		while self.main_thread_running.is_set():
			if self.system_ready.is_set():
				readings = {}
				for control in self.controls:
					result = control.read()
					readings[control.key] = result
			time.sleep(self.sleep_duration)
		#This is only ran after the main thread is shut down
		Logger.log(LOG_LEVEL["info"], "Pi Control Worker Shutting Down...\t\033[1;32m Complete\033[0;0m")