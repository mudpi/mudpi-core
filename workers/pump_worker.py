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

class PumpWorker():
	def __init__(self, config, main_thread_running, system_ready, pump_ready, pump_should_be_running):
		#self.config = {**config, **self.config}
		self.config = config
		self.main_thread_running = main_thread_running
		self.system_ready = system_ready
		self.pump_ready = pump_ready
		self.pump_should_be_running = pump_should_be_running
		self.pump_running = False
		self.needs_first_water_cycle = True
		self.init()
		return

	def init(self):
		GPIO.setup(self.config['pin'], GPIO.OUT)
		#Close the relay by default
		GPIO.output(self.config['pin'], GPIO.HIGH)
		print('Pump Worker...\t\t\t\t\033[1;32m Ready\033[0;0m')
		return

	def run(self): 
		t = threading.Thread(target=self.work, args=())
		t.start()
		print('Pump Worker...\t\t\t\t\033[1;32m Running\033[0;0m')
		return t

	def elapsedTime(self):
		self.time_elapsed = time.perf_counter() - self.time_start
		return self.time_elapsed

	def resetElapsedTime(self):
		self.time_start = time.perf_counter()
		pass

	def checkFirstWaterCycle(self):
		if self.needs_first_water_cycle:
			self.turnPumpOn()
			self.needs_first_water_cycle = False
		else:
			if self.pump_ready.is_set():
				if self.pump_should_be_running.is_set() and not self.pump_running:
					self.needs_first_water_cycle = True
			else:
				self.turnPumpOff()
	
	def turnPumpOn(self):
		#Turn off voltage to flip on relay
		if not self.pump_running:
			message = {'event':'PumpTurnedOn', 'data':1}
			GPIO.output(self.config['pin'], GPIO.LOW)
			variables.r.set('pump_running', True)
			variables.r.publish('pump', json.dumps(message))
			variables.r.set('last_watered_at', datetime.datetime.now()) #Store current time to track watering times
			self.pump_running = True
		self.resetElapsedTime()
		print('Pump Turning On!')

	def turnPumpOff(self):
		#Turn off voltage to flip on relay
		if self.pump_running:
			message = {'event':'PumpTurnedOff', 'data':1}
			GPIO.output(self.config['pin'], GPIO.HIGH)
			self.pump_should_be_running.clear()
			variables.r.delete('pump_running', False)
			variables.r.publish('pump', json.dumps(message))
			self.pump_running = False
			print('Pump Turning Off!')

	def work(self):
		self.resetElapsedTime()
		while self.main_thread_running.is_set():
			if self.system_ready.is_set():
				while self.pump_should_be_running.is_set() and self.pump_ready.is_set():
					
					self.checkFirstWaterCycle()

					#Calculate elapsed time and check against system limit
					if (self.elapsedTime() >= self.config['max_duration']):
						self.turnPumpOff()

					time.sleep(1)
				#Waiting for next pump cycle
				self.turnPumpOff()
				time.sleep(5)
				self.resetElapsedTime()
			else:
				#System not ready pump should be off
				self.turnPumpOff()
				time.sleep(5)
				self.resetElapsedTime()
				
			time.sleep(5)
		#This is only ran after the main thread is shut down
		print("Pump Worker Shutting Down...\t\t\033[1;32m Complete\033[0;0m")