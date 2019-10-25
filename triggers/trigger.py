import time
import json
import redis
import threading
import sys
sys.path.append('..')
import variables

class Trigger():

	def __init__(self, main_thread_running, system_ready, name='Trigger',key=None, source=None, thresholds=None, trigger_active=None, frequency='once', actions=[], trigger_interval=1):
		self.name = name
		self.key = key.replace(" ", "_").lower() if key is not None else self.name.replace(" ", "_").lower()
		self.thresholds = thresholds
		self.source = source
		self.frequency = frequency
		self.trigger_interval = trigger_interval
		self.actions = actions
		# Used to check if trigger already fired without reseting
		self.trigger_active = trigger_active
		self.previous_state = trigger_active.is_set()
		#Main thread events
		self.main_thread_running = main_thread_running
		self.system_ready = system_ready
		return

	def init_trigger(self):
		#Initialize the trigger here (i.e. set listeners or create cron jobs)
		pass

	def check(self):
		#Main trigger check loop to do things like fetch messages or check time
		return

	def run(self):
		t = threading.Thread(target=self.check, args=())
		t.start()
		return t

	def trigger(self, value=None):
		try:
			# Trigger the actions of the trigger
			for action in self.actions:
				action.trigger(value)
		except Exception as e:
			print("Error triggering action {0} ".format(self.key), e)
			pass
		return


	def evaluateThresholds(self, value):
		thresholds_passed = False
		for threshold in self.thresholds:
			comparison = threshold.get("comparison", "eq")
			if comparison == "eq":
				if value == threshold["value"]:
					thresholds_passed = True
				else:
					thresholds_passed = False
			elif comparison == "ne":
				if value != threshold["value"]:
					thresholds_passed = True
				else:
					thresholds_passed = False
			elif comparison == "gt":
				if value > threshold["value"]:
					thresholds_passed = True
				else:
					thresholds_passed = False
			elif comparison == "gte":
				if value >= threshold["value"]:
					thresholds_passed = True
				else:
					thresholds_passed = False
			elif comparison == "lt":
				if value < threshold["value"]:
					thresholds_passed = True
				else:
					thresholds_passed = False
			elif comparison == "lte":
				if value <= threshold["value"]:
					thresholds_passed = True
				else:
					thresholds_passed = False
		return thresholds_passed

	def decodeEventData(self, message):
		if isinstance(message, dict):
			#print('Dict Found')
			return message
		elif isinstance(message.decode('utf-8'), str):
			try:
				temp = json.loads(message.decode('utf-8'))
				#print('Json Found')
				return temp
			except:
				#print('Json Error. Str Found')
				return {'event':'Unknown', 'data':message}
		else:
			#print('Failed to detect type')
			return {'event':'Unknown', 'data':message}

	def shutdown(self):
		#Put any closing functions here that should be called as MudPi shutsdown (i.e. close connections)
		return