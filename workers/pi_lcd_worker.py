import time
import datetime
import json
import redis
import threading
import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as character_rgb_lcd
import adafruit_character_lcd.character_lcd_i2c as character_lcd
import sys
sys.path.append('..')

import variables

#r = redis.Redis(host='127.0.0.1', port=6379)


class LcdWorker():
	def __init__(self, config, main_thread_running, system_ready, lcd_available):
		self.config = config
		self.address = str(self.config['address']) if self.config['address'] is not None else None
		self.model = str(self.config['model']) if self.config['model'] is not None else None
		self.columns = int(self.config['columns']) if self.config['columns'] is not None else 16
		self.rows = int(self.config['rows']) if self.config['rows'] is not None else 2

		#Events
		self.main_thread_running = main_thread_running
		self.system_ready = system_ready
		self.lcd_available = lcd_available

		#Dynamic Properties based on config
		self.topic = self.config['topic'].replace(" ", "/").lower() if self.config['topic'] is not None else 'mudpi/lcd/'
		self.message_queue = []

		#Pubsub Listeners
		self.pubsub = variables.r.pubsub()
		self.pubsub.subscribe(**{self.topic: self.handleMessage})

		self.init()
		return

	def init(self):
		# prepare sensor on specified pin
		# 
		if (self.model.lower() == 'rgb'):
			self.lcd = character_lcd.Character_LCD_RGB_I2C(self.i2c, self.columns, self.rows, self.address)
		else:
			self.lcd = character_lcd.Character_LCD_I2C(self.i2c, self.columns, self.rows, self.address)

		self.lcd.message = "MudPi\nGarden Online"
		print('LCD Worker...\t\t\t\033[1;32m Initialized\033[0;0m'.format(**self.config))
		return

	def run(self): 
		t = threading.Thread(target=self.work, args=())
		t.start()
		print('LCD Worker ...\t\t\t\033[1;32m Online\033[0;0m'.format(**self.config))
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
				if decoded_message['event'] == 'Message':
					if decoded_message.get('data', None):
						self.lcd.message = decoded_message.get('data', '')
					elif decoded_message.get('data', None) == 0:
						self.lcd.clear()
					print('LCD Message to \033[1;36m{0}\033[0;0m'.format(decoded_message['data']))
				elif decoded_message['event'] == 'Clear':
					self.lcd.clear()
					print('Cleared the LCD Screen')
			except:
				print('Error Decoding Message for LCD')

	def elapsedTime(self):
		self.time_elapsed = time.perf_counter() - self.time_start
		return self.time_elapsed

	def resetElapsedTime(self):
		self.time_start = time.perf_counter()
		pass
	
	def addMessageToQueue(self, message):
		#Add message to queue if LCD available
		if self.lcd_available.is_set():
			if not self.active:
				message = {'event':'StateChanged', 'data':1}
				variables.r.set(self.config['key']+'_state', 1)
				variables.r.publish(self.topic, json.dumps(message))
				self.active = True
				#self.relay_active.set() This is handled by the redis listener now
				self.resetElapsedTime()	

	def work(self):
		self.resetElapsedTime()
		while self.main_thread_running.is_set():
			if self.system_ready.is_set():

				try:
					self.pubsub.get_message()
					if self.lcd_available.is_set():
						pass
					else:
						time.sleep(1)
				except:
					print("LCD Worker \t\033[1;31m Unexpected Error\033[0;0m".format(**self.config))

			else:
				#System not ready
				time.sleep(1)
				self.resetElapsedTime()
				
			time.sleep(0.1)


		#This is only ran after the main thread is shut down
		#Close the pubsub connection
		self.pubsub.close()
		print("LCD Worker Shutting Down...\t\033[1;32m Complete\033[0;0m".format(**self.config))