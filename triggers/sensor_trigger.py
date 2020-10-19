import time
import json
import redis
import sys
from .trigger import Trigger
sys.path.append('..')

from logger.Logger import Logger, LOG_LEVEL

class SensorTrigger(Trigger):

	def __init__(self, main_thread_running, system_ready, name='SensorTrigger',key=None, source=None, nested_source=None, thresholds=None, topic="sensors", trigger_active=None, frequency='once', actions=[], group=None, redis_conn=None, sequences=[]):
		super().__init__(main_thread_running, system_ready, name=name, key=key, source=source, thresholds=thresholds, trigger_active=trigger_active, frequency=frequency, actions=actions, trigger_interval=0.5, group=group, sequences=sequences)
		self.topic = topic.replace(" ", "_").lower() if topic is not None else "sensors"
		self.nested_source = nested_source.lower() if nested_source is not None else nested_source
		try:
			self.r = redis_conn if redis_conn is not None else redis.Redis(host='127.0.0.1', port=6379)
		except KeyError:
			self.r = redis.Redis(host='127.0.0.1', port=6379)
		return

	def init_trigger(self):
		#Initialize the trigger here (i.e. set listeners or create cron jobs)
		#Pubsub Listeners
		self.pubsub = self.r.pubsub()
		self.pubsub.subscribe(**{self.topic: self.handleEvent})
		pass

	def check(self):
		while self.main_thread_running.is_set():
			if self.system_ready.is_set():
				super().check()
				self.pubsub.get_message()
				# self.trigger_active.clear()
				time.sleep(self.trigger_interval)
			else:
				time.sleep(2)
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
							super().trigger(decoded_message)
						else:
							if self.frequency == 'many':
								super().trigger(decoded_message)
					else:
						self.trigger_active.clear()
			except:
				Logger.log(LOG_LEVEL["error"], 'Error Triggering Actions for {0}'.format(self.name))
		self.previous_state = self.trigger_active.is_set()

	def parseSensorData(self, data):
		parsed_data = data.get(self.source).get(self.nested_source, None) if self.nested_source is not None else data.get(self.source, None)
		return parsed_data

	def shutdown(self):
		self.pubsub.close()
		return