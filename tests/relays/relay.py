#!/usr/bin/env python

# Author: Andrea Stagi <stagi.andrea@gmail.com>
# Description: keeps your led blinking
# Dependencies: None

from nanpy import (ArduinoApi, SerialManager)
from time import sleep

connection = SerialManager(device=str(input('Enter Device Port: ')),timeout=20)
a = ArduinoApi(connection=connection)


#a.pinMode(8, a.OUTPUT)
pin = int(input('Enter Pin: '))
delay = float(input('Enter Delay: '))

while True:
	a.digitalWrite(pin, a.LOW);
	sleep(delay)
	a.digitalWrite(pin, a.HIGH);