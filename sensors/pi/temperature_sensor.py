<<<<<<< HEAD
=======
#import debugpy
#debugpy.listen(('192.168.1.191', 5678))
#debugpy.wait_for_client()
#
>>>>>>> c2fb309f5c728abbc80b089de8ce5823e6d1bb55
import time
import glob
import json
import redis
from .sensor import Sensor
from nanpy import SerialManager
import sys
import RPi.GPIO as GPIO
 
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

class TemperatureSensor(Sensor):

    def __init__(self, pin, name = 'TemperatureSensor', key = None):
        super().__init__(pin, name = name, key = key)
        return

    def init_sensor(self):
        self.sensor = "DS18B20"

    def read_raw(self):
        f = open(device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines
 
    def read(self):
        lines = self.read_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = round(temp_c * 9.0 / 5.0 + 32.0, 2)
#            return temp_c, temp_f
        print('DS18B20 Temp:', temp_f)
 
#while True:
#    print(read_temp())
#    time.sleep(1)