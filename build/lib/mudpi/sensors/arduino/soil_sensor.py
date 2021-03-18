import time
import datetime
import json
import redis
from .sensor import Sensor
from nanpy import (ArduinoApi, SerialManager)
import sys



import constants

default_connection = SerialManager(device='/dev/ttyUSB0')
# r = redis.Redis(host='127.0.0.1', port=6379)

# Wet Water = 287
# Dry Air = 584
AirBounds = 590;
WaterBounds = 280;
intervals = int((AirBounds - WaterBounds) / 3);


class SoilSensor(Sensor):

    def __init__(self, pin, name=None, key=None, connection=default_connection,
                 redis_conn=None):
        super().__init__(pin, name=name, key=key, connection=connection,
                         redis_conn=redis_conn)
        return

    def init_sensor(self):
        # read data using pin specified pin
        self.api.pinMode(self.pin, self.api.INPUT)

    def read(self):
        resistance = self.api.analogRead(self.pin)
        moistpercent = ((resistance - WaterBounds) / (
                    AirBounds - WaterBounds)) * 100
        if moistpercent > 80:
            moisture = 'Very Dry - ' + str(int(moistpercent))
        elif 80 >= moistpercent > 45:
            moisture = 'Dry - ' + str(int(moistpercent))
        elif 45 >= moistpercent > 25:
            moisture = 'Wet - ' + str(int(moistpercent))
        else:
            moisture = 'Very Wet - ' + str(int(moistpercent))
        # print("Resistance: %d" % resistance)
        # TODO: Put redis store into sensor worker
        self.r.set(self.key,
                   resistance)  # TODO: CHANGE BACK TO 'moistpercent' (PERSONAL CONFIG)
        return resistance

    def read_raw(self):
        resistance = self.api.analogRead(self.pin)
        # print("Resistance: %d" % resistance)
        self.r.set(self.key + '_raw', resistance)
        return resistance
