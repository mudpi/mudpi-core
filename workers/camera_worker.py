import time
import datetime
import json
import redis
import threading
import sys
import RPi.GPIO as GPIO
from picamera import PiCamera
sys.path.append('..')

import variables

#r = redis.Redis(host='127.0.0.1', port=6379)
GPIO.setmode(GPIO.BCM)

class CameraWorker():
	def __init__(self, config, main_thread_running, system_ready, camera_available):
		#self.config = {**config, **self.config}
		self.config = config

		#Events
		self.main_thread_running = main_thread_running
		self.system_ready = system_ready
		self.camera_available = camera_available

		#Dynamic Properties based on config
		self.path = self.config['path'].replace(" ", "-") if self.config['path'] is not None else '/etc/mudpi/img/'
		self.topic = self.config['topic'].replace(" ", "/").lower() if self.config['topic'] is not None else 'mudpi/camera/'
		if self.config['resolution'] is not None:
			self.resolutionX = int(self.config['resolution'].get('x', 1920))
			self.resolutionY = int(self.config['resolution'].get('y', 1080))
		if self.config['delay'] is not None:
			self.hours = int(self.config['delay'].get('hours', 0))
			self.minutes = int(self.config['delay'].get('minutes', 0))
			self.seconds = int(self.config['delay'].get('seconds', 0))

		self.init()
		return

	def init(self):
		try:
			self.camera = PiCamera(resolution=(self.resolutionX, self.resolutionY))
		except:
			self.camera = PiCamera()
		#camera.start_preview()
		print('Camera Worker...\t\t\t\033[1;32m Ready\033[0;0m')
		return

	def run(self): 
		t = threading.Thread(target=self.work, args=())
		t.start()
		print('Camera Worker...\t\t\t\033[1;32m Running\033[0;0m')
		return t

	def wait(self):
		# Calculate the delay
		try:
			next_time = (datetime.datetime.now() + datetime.timedelta(hours=self.hours, minutes=self.minutes, seconds=self.seconds)).replace(microsecond=0)
		except:
			#Default every hour
			next_time = (datetime.datetime.now() + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
		delay = (next_time - datetime.datetime.now()).seconds
		time.sleep(delay)

	def elapsedTime(self):
		self.time_elapsed = time.perf_counter() - self.time_start
		return self.time_elapsed

	def resetElapsedTime(self):
		self.time_start = time.perf_counter()
		pass

	def work(self):
		self.resetElapsedTime()
		while self.main_thread_running.is_set():
			if self.system_ready.is_set():
				if self.camera_available.is_set():
					# try:
					for i, filename in enumerate(self.camera.capture_continuous(self.path + 'mudpi-{counter:05d}.jpg')):
						message = {'event':'StateChanged', 'data':filename}
						variables.r.set('last_camera_image', filename)
						variables.r.publish(self.topic, json.dumps(message))
						print('Image Captured \033[1;36m%s\033[0;0m' % filename)
						self.wait()
						if not self.camera_available.is_set():
							break;
					# except:
					# 	print("Camera Worker \t\033[1;31m Unexpected Error\033[0;0m")
					# 	time.sleep(30)

			else:
				#System not ready camera should be off
				time.sleep(1)
				self.resetElapsedTime()
				
			time.sleep(0.1)

		#This is only ran after the main thread is shut down
		self.camera.close()
		print("Camera Worker Shutting Down...\t\t\033[1;32m Complete\033[0;0m")