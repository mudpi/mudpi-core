import time
import datetime
import json
import redis
from .control import Control
import RPi.GPIO as GPIO

r = redis.Redis(host='127.0.0.1', port=6379)

class ButtonControl(Control):

	def __init__(self, pin, name='ButtonControl', key=None, resistor=None, edge_detection=None, debounce=None, topic=None, redis_conn=None):
		super().__init__(pin, name=name, key=key, resistor=resistor, edge_detection=edge_detection, debounce=debounce, redis_conn=redis_conn)
		self.topic = topic.replace(" ", "/").lower() if topic is not None else 'mudpi/relay/'
		return

	def init_control(self):
		super().init_control()

	def read(self):
		state = super().read()
		if state:
			#Button Pressed
			#eventually add multipress tracking
			super().emitEvent(1)
		return state

	def readRaw(self):
		return super().read()

