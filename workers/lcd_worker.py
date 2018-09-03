#!/usr/bin/python
 
# The wiring for the LCD is as follows:
# 1 : GND
# 2 : 5V
# 3 : Contrast (0-5V)*
# 4 : RS (Register Select)
# 5 : R/W (Read Write)       - GROUND THIS PIN
# 6 : Enable or Strobe
# 7 : Data Bit 0             - NOT USED
# 8 : Data Bit 1             - NOT USED
# 9 : Data Bit 2             - NOT USED
# 10: Data Bit 3             - NOT USED
# 11: Data Bit 4
# 12: Data Bit 5
# 13: Data Bit 6
# 14: Data Bit 7
# 15: LCD Backlight +5V**
# 16: LCD Backlight GND
 
#import
import RPi.GPIO as GPIO
import time
import redis
import json
import threading
import logging

import sys
sys.path.append('..')
import variables
 
# Define GPIO to LCD mapping
LCD_RS = 7
LCD_E  = 8
LCD_D4 = 25
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 18
 
# Define some device constants
LCD_WIDTH = 16    # Maximum characters per line
LCD_CHR = True
LCD_CMD = False
 
LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
 
# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

MESSAGE_QUEUE = []

r = redis.Redis(host='127.0.0.1', port=6379)

class LCDWorker():

	def __init__(self, new_messages_waiting, main_thread_running, system_ready):
		self.new_messages_waiting = new_messages_waiting
		self.main_thread_running = main_thread_running
		self.system_ready = system_ready
		return

	def run(self): 
		t = threading.Thread(target=self.process_loop, args=())
		t.start()
		print('LCD Worker...\t\t\t\t\033[1;32m Running\033[0;0m')
		return t

	def process_loop(self):
		self.prepare_gpio()
		self.prepare_messages()
	 
		try:
			while self.main_thread_running.is_set():
				if(self.system_ready.is_set()):
					global MESSAGE_QUEUE
					
					#print('Message Queue Begin:')
					for msg in MESSAGE_QUEUE:
						if not (self.main_thread_running.is_set()):
							return

						#print('LCD MESSAGE\nLine 1: %s \nLine 2: %s' % (msg['line_1'],msg['line_2']))
						# Send some test
						self.lcd_string(msg['line_1'],LCD_LINE_1)
						self.lcd_string(msg['line_2'],LCD_LINE_2)
			 
						time.sleep(3) # 3 second delay

					#Display Control Messages
					#print('Main Messages Begin:')
					self.lcd_string(variables.lcd_message['line_1'],LCD_LINE_1)
					self.lcd_string(variables.lcd_message['line_2'],LCD_LINE_2)
					time.sleep(3)

					if ((not MESSAGE_QUEUE) or (self.new_messages_waiting.is_set()) and (self.main_thread_running.is_set())):
						#print('|| LCD Loading New Messages ||')
						time.sleep(5)
						self.prepare_messages()
						#Clear the event that tells us we should download messages
						self.new_messages_waiting.clear()

			#This is after the main thread has ended, clear out the lcd display
			print('LCD Worker Shutting Down...\t\t\033[1;32m Complete\033[0;0m')
			self.lcd_byte(0x01, LCD_CMD)
			self.lcd_string("Garden Control",LCD_LINE_1)
			self.lcd_string("Shutting Down...",LCD_LINE_2)
			GPIO.cleanup()
		except KeyboardInterrupt:
			self.lcd_byte(0x01, LCD_CMD)
			self.lcd_string("Garden Control",LCD_LINE_1)
			self.lcd_string("Shutting Down...",LCD_LINE_2)
			GPIO.cleanup()

	def prepare_messages(self):
		global MESSAGE_QUEUE
		if r.exists('lcdmessages'):
			MESSAGE_QUEUE = json.loads(r.get('lcdmessages').decode('utf-8'))
		#print('Message Pulled:', MESSAGE_QUEUE)


	def prepare_gpio(self):
		# Main program block
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
		GPIO.setup(LCD_E, GPIO.OUT)  # E
		GPIO.setup(LCD_RS, GPIO.OUT) # RS
		GPIO.setup(LCD_D4, GPIO.OUT) # DB4
		GPIO.setup(LCD_D5, GPIO.OUT) # DB5
		GPIO.setup(LCD_D6, GPIO.OUT) # DB6
		GPIO.setup(LCD_D7, GPIO.OUT) # DB7
		# Initialise display
		self.lcd_init()

	 
	def lcd_init(self):
		# Initialise display
		self.lcd_byte(0x33,LCD_CMD) # 110011 Initialise
		self.lcd_byte(0x32,LCD_CMD) # 110010 Initialise
		self.lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
		self.lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
		self.lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
		self.lcd_byte(0x01,LCD_CMD) # 000001 Clear display
		time.sleep(E_DELAY)
	 
	def lcd_byte(self, bits, mode):
		# Send byte to data pins
		# bits = data
		# mode = True  for character
		#        False for command
	 
		GPIO.output(LCD_RS, mode) # RS
	 
		# High bits
		GPIO.output(LCD_D4, False)
		GPIO.output(LCD_D5, False)
		GPIO.output(LCD_D6, False)
		GPIO.output(LCD_D7, False)
		if bits&0x10==0x10:
			GPIO.output(LCD_D4, True)
		if bits&0x20==0x20:
			GPIO.output(LCD_D5, True)
		if bits&0x40==0x40:
			GPIO.output(LCD_D6, True)
		if bits&0x80==0x80:
			GPIO.output(LCD_D7, True)
	 
		# Toggle 'Enable' pin
		self.lcd_toggle_enable()
	 
		# Low bits
		GPIO.output(LCD_D4, False)
		GPIO.output(LCD_D5, False)
		GPIO.output(LCD_D6, False)
		GPIO.output(LCD_D7, False)
		if bits&0x01==0x01:
			GPIO.output(LCD_D4, True)
		if bits&0x02==0x02:
			GPIO.output(LCD_D5, True)
		if bits&0x04==0x04:
			GPIO.output(LCD_D6, True)
		if bits&0x08==0x08:
			GPIO.output(LCD_D7, True)
	 
		# Toggle 'Enable' pin
		self.lcd_toggle_enable()
	 
	def lcd_toggle_enable(self):
		# Toggle enable
		time.sleep(E_DELAY)
		GPIO.output(LCD_E, True)
		time.sleep(E_PULSE)
		GPIO.output(LCD_E, False)
		time.sleep(E_DELAY)
	 
	def lcd_string(self,message,line):
		# Send string to display
	 
		message = message.ljust(LCD_WIDTH," ")
	 
		self.lcd_byte(line, LCD_CMD)
	 
		for i in range(LCD_WIDTH):
			self.lcd_byte(ord(message[i]),LCD_CHR)
 