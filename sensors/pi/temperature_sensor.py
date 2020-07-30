#(import debugpy
#debugpy.listen(('192.168.1.191', 5678))
#debugpy.wait_for_client()
#
import time
import glob
import json
import redis
from .sensor import Sensor
from nanpy import SerialManager
import sys
 
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'
default_connection = SerialManager(device = device_file)

class TemperatureSensor(Sensor):
    def __init__(self, pin, name = 'TemperatureSensor'), key = None,\
        connection = default_connection):
        super().__init__(pin, name = name, key = key, connection = connection)
        return

    def init_sensor(self):
#        self.sensors = 

def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines
 
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f
 
while True:
    print(read_temp())
    time.sleep(1)