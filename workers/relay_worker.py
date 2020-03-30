import time
import datetime
import json
import redis
import threading
import sys
import RPi.GPIO as GPIO
sys.path.append('..')

import variables

#r = redis.Redis(host='127.0.0.1', port=6379)
GPIO.setmode(GPIO.BCM)

# ToDO Update relay to make a key if one is not set in config

class RelayWorker():
	def __init__(self, config, main_thread_running, system_ready, relay_available, relay_active):
		#self.config = {**config, **self.config}
		self.config = config
		self.config['pin'] = int(self.config['pin']) #parse possbile strings to avoid errors

		#Events
		self.main_thread_running = main_thread_running
		self.system_ready = system_ready
		self.relay_available = relay_available
		self.relay_active = relay_active

		#Dynamic Properties based on config
		self.active = False
		self.topic = self.config['topic'].replace(" ", "/").lower() if self.config['topic'] is not None else 'mudpi/relay/'
		self.pin_state_off = GPIO.HIGH if self.config['normally_open'] is not None and self.config['normally_open'] else GPIO.LOW
		self.pin_state_on = GPIO.LOW if self.config['normally_open'] is not None and self.config['normally_open'] else GPIO.HIGH

		#Pubsub Listeners
		self.pubsub = variables.r.pubsub()
		self.pubsub.subscribe(**{self.topic: self.handleMessage})

		self.init()
		return

	def init(self):
		GPIO.setup(self.config['pin'], GPIO.OUT)
		#Close the relay by default, we use the pin state we determined based on the config at init
		GPIO.output(self.config['pin'], self.pin_state_off)
		time.sleep(0.1)

		#Feature to restore relay state in case of crash  or unexpected shutdown. This will check for last state stored in redis and set relay accordingly
		if(self.config.get('restore_last_known_state', None) is not None and self.config.get('restore_last_known_state', False) is True):
			if(variables.r.get(self.config['key']+'_state')):
				GPIO.output(self.config['pin'], self.pin_state_on)
				print('Restoring Relay \033[1;36m{0} On\033[0;0m'.format(self.config['key']))


		print('Relay Worker {key}...\t\t\t\033[1;32m Ready\033[0;0m'.format(**self.config))
		return

	def run(self): 
		t = threading.Thread(target=self.work, args=())
		t.start()
		print('Relay Worker {key}...\t\t\t\033[1;32m Running\033[0;0m'.format(**self.config))
		return t

	def decodeMessageData(self, message):
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

	def handleMessage(self, message):
		data = message['data']
		if data is not None:
			decoded_message = self.decodeMessageData(data)
			try:
				if decoded_message['event'] == 'Switch':
					if decoded_message.get('data', None):
						self.relay_active.set()
					elif decoded_message.get('data', None) == 0:
						self.relay_active.clear()
					print('Switch Relay \033[1;36m{0}\033[0;0m state to \033[1;36m{1}\033[0;0m'.format(self.config['key'], decoded_message['data']))
				elif decoded_message['event'] == 'Toggle':
					state = 'Off' if self.active else 'On'
					if self.relay_active.is_set():
						self.relay_active.clear()
					else:
						self.relay_active.set()
					print('Toggle Relay \033[1;36m{0} {1} \033[0;0m'.format(self.config['key'], state))
			except:
				print('Error Decoding Message for Relay {0}'.format(self.config['key']))

	def elapsedTime(self):
		self.time_elapsed = time.perf_counter() - self.time_start
		return self.time_elapsed

	def resetElapsedTime(self):
		self.time_start = time.perf_counter()
		pass
	
	def turnOn(self):
		#Turn on relay if its available
		if self.relay_available.is_set():
			if not self.active:
				GPIO.output(self.config['pin'], self.pin_state_on)
				message = {'event':'StateChanged', 'data':1}
				variables.r.set(self.config['key']+'_state', 1)
				variables.r.publish(self.topic, json.dumps(message))
				self.active = True
				#self.relay_active.set() This is handled by the redis listener now
				self.resetElapsedTime()	

	def turnOff(self):
		#Turn off volkeye to flip off relay
		if self.relay_available.is_set():
			if self.active:
				GPIO.output(self.config['pin'], self.pin_state_off)
				message = {'event':'StateChanged', 'data':0}
				variables.r.delete(self.config['key']+'_state')
				variables.r.publish(self.topic, json.dumps(message))
				#self.relay_active.clear() This is handled by the redis listener now
				self.active = False
				self.resetElapsedTime()

	def work(self):
		self.resetElapsedTime()
		while self.main_thread_running.is_set():
			if self.system_ready.is_set():

				try:
					self.pubsub.get_message()
					if self.relay_available.is_set():
						if self.relay_active.is_set():
							self.turnOn()
						else:
							self.turnOff()
					else:
						self.turnOff()
						time.sleep(1)
				except:
					print("Relay Worker \033[1;36m{key}\033[0;0m \t\033[1;31m Unexpected Error\033[0;0m".format(**self.config))

			else:
				#System not ready relay should be off
				self.turnOff()
				time.sleep(1)
				self.resetElapsedTime()
				
			time.sleep(0.1)


		#This is only ran after the main thread is shut down
		#Close the pubsub connection
		self.pubsub.close()
		print("Relay Worker {key} Shutting Down...\t\033[1;32m Complete\033[0;0m".format(**self.config))