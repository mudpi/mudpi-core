import time
from nanpy import (ArduinoApi, SerialManager)

default_connection = SerialManager(device='/dev/ttyUSB1')

api = ArduinoApi(default_connection)

pin = int(input('Enter Soil Sensor Pin: '))

api.pinMode(pin, api.INPUT)

loop = 10

while loop > 0:
	resistance = api.analogRead(pin)
	print('Resistance: ', resistance)
	loop -=1
	time.sleep(5)