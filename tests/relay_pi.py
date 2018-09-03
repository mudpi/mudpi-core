#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  RGB_LED.py
#
# A short program to control an RGB LED by utilizing
# the PWM functions within the Python GPIO module
#
#  Copyright 2015  Ken Powers
#   

# Import the modules used in the script
import random, time
import RPi.GPIO as GPIO

# Set GPIO to Broadcom system and set RGB Pin numbers
RUNNING = True
GPIO.setmode(GPIO.BCM)
pin = int(input('Enter Pin: '))

# Set pins to output mode
GPIO.setup(pin, GPIO.OUT)

print("Light It Up!")
GPIO.output(pin, GPIO.HIGH)
time.sleep(5)
print("Off!")
GPIO.output(pin, GPIO.LOW)
time.sleep(5)
GPIO.cleanup()