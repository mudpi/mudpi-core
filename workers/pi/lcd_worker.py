import time
import datetime
import json
import redis
import threading
import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as character_rgb_lcd
import adafruit_character_lcd.character_lcd_i2c as character_lcd
from .worker import Worker
import sys
sys.path.append('..')

import variables

class LcdWorker(Worker):
	def __init__(self, config, main_thread_running, system_ready, lcd_available):
		super().__init__(config, main_thread_running, system_ready)
		try:
			self.address = int(self.config['address']) if self.config['address'] is not None else None
		except KeyError:
			self.address = None
		try:
			self.model = str(self.config['model']) if self.config['model'] is not None else ''
		except KeyError:
			self.model = ''
		try:
			self.columns = int(self.config['columns']) if self.config['columns'] is not None else 16
		except KeyError:
			self.columns = 16
		try:
			self.rows = int(self.config['rows']) if self.config['rows'] is not None else 2
		except KeyError:
			self.rows = 2

		# Events
		self.lcd_available = lcd_available

		# Dynamic Properties based on config
		try:
			self.topic = self.config['topic'].replace(" ", "/").lower() if self.config['topic'] is not None else 'mudpi/lcd/'
		except KeyError:
			self.topic = 'mudpi/lcd/'
		self.message_queue = []

		#Pubsub Listeners
		self.pubsub = variables.r.pubsub()
		self.pubsub.subscribe(**{self.topic: self.handleMessage})

		self.init()
		return

	def init(self):
		# prepare sensor on specified pin
		self.i2c = busio.I2C(board.SCL, board.SDA)
		if(self.model):
			if (self.model.lower() == 'rgb'):
				self.lcd = character_lcd.Character_LCD_RGB_I2C(self.i2c, self.columns, self.rows, self.address)
			elif (self.model.lower() == 'pcf'):
				self.lcd = character_lcd.Character_LCD_I2C(self.i2c, self.columns, self.rows, address=self.address, usingPCF=True)
			else:
				self.lcd = character_lcd.Character_LCD_I2C(self.i2c, self.columns, self.rows, self.address)
		else:
			self.lcd = character_lcd.Character_LCD_I2C(self.i2c, self.columns, self.rows, self.address)
		self.lcd.clear()
		self.lcd.message = "MudPi\nGarden Online"
		print('LCD Display Worker...\t\t\t\033[1;32m Initialized\033[0;0m'.format(**self.config))
		return

	def run(self): 
		print('LCD Display Worker ...\t\t\t\033[1;32m Online\033[0;0m'.format(**self.config))
		return super().run()

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
	
	def addMessageToQueue(self, message, duration = 3):
		#Add message to queue if LCD available
		if self.lcd_available.is_set():

			new_message = {
				"message": message,
				"duration": duration
			}
			self.message_queue.append(message)

			msg = { 'event':'MessageQueued', 'data': new_message }
			variables.r.publish(self.topic, json.dumps(msg))

			self.resetElapsedTime()	

	def work(self):
		self.resetElapsedTime()
		self.lcd.clear()
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
		print("LCD Worker Shutting Down...\t\t\033[1;32m Complete\033[0;0m".format(**self.config))