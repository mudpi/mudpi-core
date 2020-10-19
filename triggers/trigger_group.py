import time
import json
import redis
import threading
import sys
sys.path.append('..')

from logger.Logger import Logger, LOG_LEVEL

class TriggerGroup():

	def __init__(self, name='TriggerGroup', key=None, triggers=[], group_active=None, frequency='once', actions=[]):
		self.name = name
		self.key = key.replace(" ", "_").lower() if key is not None else self.name.replace(" ", "_").lower()
		self.frequency = frequency
		self.actions = actions
		# Used to check if trigger already fired without reseting
		self.group_active = group_active if group_active is not None else threading.Event()
		self.previous_state = self.group_active.is_set()
		self.trigger_count = 0
		self.triggers = triggers
		return

	def add_trigger(self, trigger):
		self.triggers.append(trigger)
		pass

	def check_group(self):
		group_check = True
		for trigger in self.triggers:
			if not trigger.trigger_active.is_set():
				group_check = False
		if group_check:
			self.group_active.set()
		else:
			self.group_active.clear()
			self.trigger_count = 0
		self.previous_state = self.group_active.is_set()
		return group_check

	def trigger(self, value=None):
		try:
			if self.check_group():
				self.trigger_count+=1
				if self.trigger_count == 1:
					for action in self.actions:
							action.trigger(value)
				else:
					if self.frequency == 'many':
						for action in self.actions:
							action.trigger(value)
			else:
				self.trigger_count = 0
		except Exception as e:
			Logger.log(LOG_LEVEL["error"], "Error triggering group {0} ".format(self.key), e)
			pass
		return

	def shutdown(self):
		#Put any closing functions here that should be called as MudPi shutsdown (i.e. close connections)
		return