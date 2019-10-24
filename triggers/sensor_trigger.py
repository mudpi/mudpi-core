import time
import json
import redis
import sys
from .trigger import Trigger
sys.path.append('..')
import variables

class SensorTrigger(Trigger):

	def __init__(self, name='SensorTrigger',key=None, source=None, thresholds=None, channel="sensors", trigger_active=None, frequency='once', actions=[]):
		super().__init__(name=name, key=key, source=source, thresholds=thresholds, trigger_active=trigger_active, frequency=frequency, actions=actions)
		self.channel = channel.replace(" ", "_").lower() if channel is not None else "sensors"
		return

	def init_trigger(self):
		#Initialize the trigger here (i.e. set listeners or create cron jobs)
		#Pubsub Listeners
		self.pubsub = variables.r.pubsub()
		self.pubsub.subscribe(**{self.channel: self.handleEvent})
		pass

	def check(self):
		self.pubsub.get_message()
		self.trigger_active.clear()
		return

	def handleEvent(self, message):
		data = message['data']
		if data is not None:
			decoded_message = super().decodeEventData(data)
			try:
				if decoded_message['event'] == 'SensorUpdate' or decoded_message['event'] == 'PiSensorUpdate':
					sensor_value = self.parseSensorData(decoded_message["data"])
					if super().evaluateThresholds(sensor_value):
						self.trigger_active.set()
						if self.previous_state != self.trigger_active.is_set():
							super().trigger(decoded_message['event'])
						else:
							if self.frequency == 'many':
								super().trigger(decoded_message['event'])
					else:
						self.trigger_active.clear()
			except:
				print('Error During Trigger Actions {0}'.format(self.key))
		self.previous_state = self.trigger_active.is_set()

	def parseSensorData(self, data):
		parsed_data = data.get(self.source, None)
		return parsed_data

	def shutdown(self):
		self.pubsub.close()
		return