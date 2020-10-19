import time
import datetime
import json
import redis
from .control import Control
from nanpy import (ArduinoApi, SerialManager)

default_connection = SerialManager(device='/dev/ttyUSB0')
# r = redis.Redis(host='127.0.0.1', port=6379)

class PotentiometerControl(Control):

	def __init__(self, pin, name=None, key=None, connection=default_connection, analog_pin_mode=True, topic=None, reading_buffer=3, redis_conn=None):
		super().__init__(pin, name=name, key=key, connection=connection, analog_pin_mode=analog_pin_mode, redis_conn=redis_conn)
		self.previous_state = 0
		# Reading buffer helps prevent multiple events when values are floating between small amounts
		self.reading_buffer = reading_buffer
		return

	def init_control(self):
		super().init_control()
		# Set initial state to prevent event on boot
		self.previous_state = super().read()

	def read(self):
		state = super().read()

		if (state < self.previous_state - self.reading_buffer) or (state > self.previous_state + self.reading_buffer):
			# Value changed
			# print('{0}: {1}'.format(self.name, state))
			super().emitEvent(state)

		self.previous_state = state
		return state

	def readRaw(self):
		return super().read()

