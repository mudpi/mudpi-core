
# Import the modules used in the script
import random, time
import RPi.GPIO as GPIO

# Set GPIO to Broadcom system and set RGB Pin numbers
RUNNING = True
GPIO.setmode(GPIO.BCM)
pin = int(input('Enter Pin: '))

# Set pins to output mode
GPIO.setup(pin, GPIO.IN)

for i in range(400):
	print(GPIO.input(pin))
	time.sleep(5)
GPIO.cleanup()