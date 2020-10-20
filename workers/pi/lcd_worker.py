import re
import time
import json
import redis
import board
import busio
import datetime
import threading
import adafruit_character_lcd.character_lcd_rgb_i2c as character_rgb_lcd
import adafruit_character_lcd.character_lcd_i2c as character_lcd
from .worker import Worker

from logger.Logger import Logger, LOG_LEVEL

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
		try:
			self.default_duration = int(self.config['default_duration']) if self.config['default_duration'] is not None else 5
		except KeyError:
			self.default_duration = 5
			
		self.current_message = ""
		self.cached_message = {'message':'', 'duration': self.default_duration}
		self.need_new_message = True
		self.message_queue = []
		self.message_limit = nt(self.config['message_limit']) if self.config['message_limit'] is not None else 20

		# Events
		self.lcd_available = lcd_available

		# Dynamic Properties based on config
		try:
			self.topic = self.config['topic'].replace(" ", "/").lower() if self.config['topic'] is not None else 'mudpi/lcd'
		except KeyError:
			self.topic = 'mudpi/lcd'

		# Pubsub Listeners
		self.pubsub = self.r.pubsub()
		self.pubsub.subscribe(**{self.topic: self.handleMessage})

		self.init()
		return

	def init(self):
		Logger.log(LOG_LEVEL["info"], 'LCD Display Worker...\t\t\t\033[1;32m Initializing\033[0;0m'.format(**self.config))
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

		self.lcd.backlight = True
		self.lcd.clear()
		self.lcd.message = "MudPi\nGarden Online"
		time.sleep(2)
		self.lcd.clear()
		return

	def run(self): 
		Logger.log(LOG_LEVEL["info"], 'LCD Display Worker ...\t\t\t\033[1;32m Online\033[0;0m'.format(**self.config))
		return super().run()

	def handleMessage(self, message):
		data = message['data']
		if data is not None:
			decoded_message = self.decodeMessageData(data)
			try:
				if decoded_message['event'] == 'Message':
					if decoded_message.get('data', None):
						self.addMessageToQueue(decoded_message['data'].get('message', ''), int(decoded_message['data'].get('duration', self.default_duration)))
						Logger.log(LOG_LEVEL["debug"], 'LCD Message Queued: \033[1;36m{0}\033[0;0m'.format(decoded_message['data'].get('message', '')))

				elif decoded_message['event'] == 'Clear':
					self.lcd.clear()
					Logger.log(LOG_LEVEL["debug"], 'Cleared the LCD Screen')
				elif decoded_message['event'] == 'ClearQueue':
					self.message_queue = []
					Logger.log(LOG_LEVEL["debug"], 'Cleared the LCD Message Queue')
			except:
				Logger.log(LOG_LEVEL["error"], 'Error Decoding Message for LCD')
	
	def addMessageToQueue(self, message, duration = 3):
		#Add message to queue if LCD available
		if self.lcd_available.is_set():

			# Replace any codes such as [temperature] with a value found in redis
			short_codes = re.findall(r'\[(.*?) *\]', message)

			for code in short_codes:
				data = self.r.get(code)
				if data is None:
					data = ''
				else:
					try:
						data = data.decode('utf-8')
					except:
						data = ''
				message = message.replace('['+code+']', str(data))

			new_message = {
				"message": message.replace("\\n", "\n"),
				"duration": duration
			}

			if len(self.message_queue) = self.message_limit:
				 self.message_queue.pop(0)

			self.message_queue.append(new_message)

			msg = { 'event':'MessageQueued', 'data': new_message }
			self.r.publish(self.topic, json.dumps(msg))
			return

	def nextMessageFromQueue(self):
		if len(self.message_queue) > 0:
			self.need_new_message = False
			self.resetElapsedTime()
			return self.message_queue.pop(0)
		else:
			time.sleep(3) # pause to reduce system load on message loop
			return None

	def work(self):
		self.resetElapsedTime()
		self.lcd.clear()
		self.need_new_message = True
		while self.main_thread_running.is_set():
			if self.system_ready.is_set():
				try:
					self.pubsub.get_message()
					if self.lcd_available.is_set():
						if self.cached_message and not self.need_new_message:
							if self.current_message != self.cached_message['message']:
								self.lcd.clear()
								time.sleep(0.01)
								self.lcd.message = self.cached_message['message']
								self.current_message = self.cached_message['message'] # store message to only display once and prevent flickers
							if self.elapsedTime() > self.cached_message['duration'] + 1:
								self.need_new_message = True
						else:
							if self.need_new_message:
								# Get first time message after clear
								self.cached_message = self.nextMessageFromQueue()
					else:
						time.sleep(1)
				except Exception as e:
					Logger.log(LOG_LEVEL["error"], "LCD Worker \t\033[1;31m Unexpected Error\033[0;0m".format(**self.config))
					Logger.log(LOG_LEVEL["error"], "Exception: {0}".format(e)) 
			else:
				# System not ready
				time.sleep(1)
				self.resetElapsedTime()
				
			time.sleep(0.1)

		#This is only ran after the main thread is shut down
		#Close the pubsub connection
		self.pubsub.close()
		Logger.log(LOG_LEVEL["info"], "LCD Worker Shutting Down...\t\t\033[1;32m Complete\033[0;0m".format(**self.config))