import time
import datetime
import json
import redis
import threading
import sys
sys.path.append('..')
from triggers.trigger_group import TriggerGroup

import variables
import importlib

class TriggerWorker():
	def __init__(self, config, main_thread_running, system_ready, actions):
		#self.config = {**config, **self.config}
		self.config = config
		self.main_thread_running = main_thread_running
		self.system_ready = system_ready
		self.actions = actions
		self.triggers = []
		self.trigger_threads = []
		self.trigger_events = {}
		self.init_triggers()
		return

	def dynamic_import(self, path):
		components = path.split('.')

		s = ''
		for component in components[:-1]:
			s += component + '.'

		parent = importlib.import_module(s[:-1])
		sensor = getattr(parent, components[-1])

		return sensor

	def init_triggers(self):
		trigger_index = 0
		for trigger in self.config:
			if trigger.get("triggers", False):
				# Load a trigger group

				trigger_actions = []
				if trigger.get('actions'):
					for action in trigger.get("actions"):
						trigger_actions.append(self.actions[action])

				new_trigger_group = TriggerGroup(name=trigger.get("group"), actions=trigger_actions, frequency=trigger.get("frequency", "once"))

				for trigger in trigger.get("triggers"):
					new_trigger = self.init_trigger(trigger, trigger_index, group=new_trigger_group)
					self.triggers.append(new_trigger)
					new_trigger_group.add_trigger(new_trigger)
					#Start the trigger thread
					trigger_thread = new_trigger.run()
					self.trigger_threads.append(trigger_thread)
					trigger_index += 1
			else:
				new_trigger = self.init_trigger(trigger, trigger_index)
				self.triggers.append(new_trigger)
				#Start the trigger thread
				trigger_thread = new_trigger.run()
				self.trigger_threads.append(trigger_thread)
				trigger_index += 1
				# print('{type} - {name}...\t\t\033[1;32m Listening\033[0;0m'.format(**trigger))
		return

	def init_trigger(self, config, trigger_index, group=None):
		if config.get('type', None) is not None:
			#Get the trigger from the triggers folder {trigger name}_trigger.{SensorName}Sensor
			trigger_type = 'triggers.' + config.get('type').lower() + '_trigger.' + config.get('type').capitalize() + 'Trigger'

			imported_trigger = self.dynamic_import(trigger_type)

			trigger_state = {
				"active": threading.Event() #Event to signal relay to open/close
			}

			self.trigger_events[config.get("key", trigger_index)] = trigger_state

			# Define default kwargs for all trigger types, conditionally include optional variables below if they exist
			trigger_kwargs = { 
				'name' : config.get('name', config.get('type')),
				'key'  : config.get('key', None),
				'trigger_active' : trigger_state["active"],
				'main_thread_running' : self.main_thread_running,
				'system_ready' : self.system_ready
			}

			# optional trigger variables 
			if config.get('actions'):
				trigger_actions = []
				for action in config.get("actions"):
					trigger_actions.append(self.actions[action])
				trigger_kwargs['actions'] = trigger_actions

			if config.get('frequency'):
				trigger_kwargs['frequency'] = config.get('frequency')

			if config.get('schedule'):
				trigger_kwargs['schedule'] = config.get('schedule')

			if config.get('source'):
				trigger_kwargs['source'] = config.get('source')

			if config.get('nested_source'):
				trigger_kwargs['nested_source'] = config.get('nested_source')

			if config.get('channel'):
				trigger_kwargs['channel'] = config.get('channel')

			if config.get('thresholds'):
				trigger_kwargs['thresholds'] = config.get('thresholds')

			if group is not None:
				trigger_kwargs['group'] = group

			new_trigger = imported_trigger(**trigger_kwargs)
			new_trigger.init_trigger()

			new_trigger.type = config.get('type').lower()

			return new_trigger

	def run(self): 
		t = threading.Thread(target=self.work, args=())
		t.start()
		print('Trigger Worker [' + str(len(self.config)) + ' Triggers]...\t\t\033[1;32m Online\033[0;0m')
		return t

	def work(self):

		while self.main_thread_running.is_set():
			if self.system_ready.is_set():
				#Main Loop
				time.sleep(1)
				
			time.sleep(2)
		#This is only ran after the main thread is shut down
		for trigger in self.triggers:
			trigger.shutdown()
		#Join all our sub threads for shutdown
		for thread in self.trigger_threads:
			thread.join()
		print("Trigger Worker Shutting Down...\t\t\033[1;32m Complete\033[0;0m")