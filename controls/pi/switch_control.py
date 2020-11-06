import time
import datetime
import json
import redis
from .control import Control
import RPi.GPIO as GPIO

r = redis.Redis(host='127.0.0.1', port=6379)

class SwitchControl(Control):

	def __init__(self, pin, name=None, key=None, resistor=None, edge_detection=None, debounce=None, topic=None, redis_conn=None):
		super().__init__(pin, name=name, key=key, resistor=resistor, edge_detection=edge_detection, debounce=debounce, redis_conn=redis_conn)
		self.topic = topic.replace(" ", "/").lower() if topic is not None else 'mudpi/controls/'+self.key
		# Keep counter 1 above delay to avoid event on boot
		self.state_counter = 3
		self.previous_state = 0
		self.trigger_delay = 2
		return

	def init_control(self):
		super().init_control()
		# Get current state on boot
		self.previous_state = super().read()

	def read(self):
		state = super().read()
		if state == self.previous_state:
			self.state_counter += 1
			if self.state_counter == self.trigger_delay:
				clean_state = 1 if state else 0
				super().emitEvent(clean_state)
		else:
			#Button State Changed
			self.state_counter = 1

		self.previous_state = state
		return state

	def read_raw(self):
		return super().read()

