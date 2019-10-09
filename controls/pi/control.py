import time
import json
import redis
import RPi.GPIO as GPIO

# Base sensor class to extend all other arduino sensors from.
class Control():

	def __init__(self, pin, name='Control',key=None, resistor=None, edge_detection=None, debounce=None):
		self.pin = pin
		self.name = name
		self.key = key.replace(" ", "_").lower() if key is not None else self.name.replace(" ", "_").lower()
		self.gpio = GPIO
		self.debounce = debounce if debounce is not None else None

		if resistor is not None:
			if resistor == "up" or resistor == GPIO.PUD_UP:
				self.resistor = GPIO.PUD_UP
			elif resistor == "down" or resistor == GPIO.PUD_DOWN:
				self.resistor = GPIO.PUD_DOWN
		else:
			self.resistor = resistor

		if edge_detection is not None:
			if edge_detection == "falling" or edge_detection == GPIO.FALLING:
				self.edge_detection = GPIO.FALLING
			elif edge_detection == "rising" or edge_detection == GPIO.RISING:
				self.edge_detection = GPIO.RISING
			elif edge_detection == "both" or edge_detection == GPIO.BOTH:
				self.edge_detection = GPIO.BOTH
		else:
			self.edge_detection = None

		return

	def init_control(self):
		#Initialize the control here (i.e. set pin mode, get addresses, etc)
		#Set the Pin for the button with the internal pull up resistor
		self.gpio.setup(self.pin, GPIO.IN, pull_up_down=self.resistor)
		# If edge detection has been configured lets take advantage of that
		if self.edge_detection is not None:
			GPIO.add_event_detect(self.pin, self.edge_detection, bouncetime=self.debounce)
		pass

	def read(self):
		#Read the sensor(s), parse the data and store it in redis if redis is configured
		#If edge detection is being used return the detection event instead
		return self.readPin() if self.edge_detection is None else GPIO.event_detected(self.pin)

	def readRaw(self):
		#Read the sensor(s) but return the raw data, useful for debugging
		pass

	def readPin(self):
		#Read the pin from the pi digital reads only
		data = self.gpio.input(self.pin)
		return data