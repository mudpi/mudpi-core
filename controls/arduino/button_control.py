import time
import datetime
import json
import redis
from .control import Control
from nanpy import (ArduinoApi, SerialManager)

default_connection = SerialManager(device='/dev/ttyUSB0')
# r = redis.Redis(host='127.0.0.1', port=6379)

class ButtonControl(Control):

	def __init__(self, pin, name='ButtonControl', key=None, connection=default_connection, analog_pin_mode=False, topic=None, redis_conn=None):
		super().__init__(pin, name=name, key=key, connection=connection, analog_pin_mode=analog_pin_mode, redis_conn=redis_conn)
		self.topic = topic.replace(" ", "/").lower() if topic is not None else 'mudpi/relay/'
		self.state_counter = 3
		self.previous_state = 0
		return

	def init_control(self):
		super().init_control()

	def read(self):
		state = super().read()
		if state == self.previous_state:
			self.state_counter += 1
			if self.state_counter % 2 == 0:
				if state:
					super().emitEvent(1)
				elif self.state_counter == 2:
					super().emitEvent(0)
		else:
			self.state_counter = 1

		self.previous_state = state
		return state

	def readRaw(self):
		return super().read()
