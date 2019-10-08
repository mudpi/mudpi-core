import time
import datetime
import json
import redis
from .control import Control
from nanpy import (ArduinoApi, SerialManager)

default_connection = SerialManager(device='/dev/ttyUSB0')
r = redis.Redis(host='127.0.0.1', port=6379)

class ButtonControl(Control):

	def __init__(self, pin, name='ButtonControl', key=None, connection=default_connection, analog_pin_mode=False, topic=None):
		super().__init__(pin, name=name, key=key, connection=connection, analog_pin_mode=False)
		self.topic = topic.replace(" ", "/").lower() if topic is not None else 'mudpi/relay/'
		return

	def init_control(self):
		super().init_control()

	def read(self):
		state = super().read()
		if state:
			#Button Pressed
			#eventually add multipress tracking
			print('{0} Pressed'.format(self.name))
			self.emitEvent()
		return state

	def readRaw(self):
		return super().read()

	def emitEvent(self):
		message = {
			'event': 'Toggle',
			'data': None
		}
		r.publish(self.topic, json.dumps(message))
