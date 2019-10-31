import time
import json
import redis
import sys
from .trigger import Trigger
sys.path.append('..')
import variables

class ControlTrigger(Trigger):

	def __init__(self, main_thread_running, system_ready, name='ControlTrigger',key=None, source=None, thresholds=None, channel="controls", trigger_active=None, frequency='once', actions=[], group=None):
		super().__init__(main_thread_running, system_ready, name=name, key=key, source=source, thresholds=thresholds, trigger_active=trigger_active, frequency=frequency, actions=actions, trigger_interval=0.5, group=group)
		self.channel = channel.replace(" ", "_").lower() if channel is not None else "controls"
		return

	def init_trigger(self):
		#Initialize the trigger here (i.e. set listeners or create cron jobs)
		#Pubsub Listeners
		self.pubsub = variables.r.pubsub()
		self.pubsub.subscribe(**{self.channel: self.handleEvent})
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
				if decoded_message['event'] == 'ControlUpdate':
					control_value = self.parseControlData(decoded_message["data"])
					if super().evaluateThresholds(control_value):
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

	def parseControlData(self, data):
		parsed_data = data.get(self.source, None)
		return parsed_data

	def shutdown(self):
		self.pubsub.close()
		return