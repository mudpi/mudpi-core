#!/usr/bin/env python

# Author: Andrea Stagi <stagi.andrea@gmail.com>
# Description: keeps your led blinking
# Dependencies: None

from nanpy import (ArduinoApi, SerialManager)
from time import sleep
import logging
logging.basicConfig(level=logging.DEBUG)

connection = SerialManager(device=str(input('Enter Device Port: ')),timeout=20)
a = ArduinoApi(connection=connection)

a.pinMode(13, a.OUTPUT)

for i in range(100):
    a.digitalWrite(13, (i + 1) % 2)
    sleep(0.2)