import time
import datetime
import json
import redis
from .control import Control
from nanpy import (ArduinoApi, SerialManager)

default_connection = SerialManager(device='/dev/ttyUSB0')
r = redis.Redis(host='127.0.0.1', port=6379)

class SwitchControl(Control):

	def __init__(self, pin, name='SwitchControl', key=None, connection=default_connection, analog_pin_mode=False, topic=None):
		super().__init__(pin, name=name, key=key, connection=connection, analog_pin_mode=analog_pin_mode)
		self.topic = topic.replace(" ", "/").lower() if topic is not None else 'mudpi/relay/'
		self.state_counter = 3
		self.previous_state = 0
		self.trigger_delay = 2
		return

	def init_control(self):
		super().init_control()
		# Set initial state to prevent event on boot
		self.previous_state = super().read()

	def read(self):
		state = super().read()
		if state == self.previous_state:
			self.state_counter += 1
			if self.state_counter == self.trigger_delay:
				clean_state = 1 if state else 0
				super().emitEvent(clean_state)
		else:
			self.state_counter = 1

		self.previous_state = state
		return state

	def readRaw(self):
		return super().read()
