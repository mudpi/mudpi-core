import time
import datetime
import json
import redis
from .sensor import Sensor
from nanpy import (DallasTemperature, SerialManager)
import sys

from logger.Logger import Logger, LOG_LEVEL



import constants

default_connection = SerialManager(device='/dev/ttyUSB0')


# r = redis.Redis(host='127.0.0.1', port=6379)

class TemperatureSensor(Sensor):

    def __init__(self, pin, name=None, key=None, connection=default_connection,
                 redis_conn=None):
        super().__init__(pin, name=name, key=key, connection=connection,
                         redis_conn=redis_conn)
        return

    def init_sensor(self):
        self.sensors = DallasTemperature(self.pin, connection=self.connection)
        self.sensor_bus = self.sensors.getDeviceCount()
        # read data using pin specified pin
        Logger.log(LOG_LEVEL["debug"], "There are", self.sensor_bus,
                   "devices connected on pin ", self.sensors.pin)
        self.addresses = []

        for i in range(self.sensor_bus):
            self.addresses.append(self.sensors.getAddress(i))

        Logger.log(LOG_LEVEL["debug"], "Their addresses", self.addresses)
        # I guess this is something with bit rates? TODO: Look this up
        self.sensors.setResolution(10)

    # sensor = id of sensor you want in addresses[]
    def read(self):
        # temp = self.sensors.getTempF(sensor)
        # self.r.set('temp_'+str(sensor), temp)
        # return temp
        return self.readAll()

    def readAll(self):
        self.sensors.requestTemperatures()
        temps = {}
        for i in range(self.sensor_bus):
            temp = self.sensors.getTempC(i)
            temps['temp_' + str(i)] = temp
        # self.r.set(self.key+'_'+str(i), temp)
        # print("Device %d (%s) " % (i, self.addresses[i]))
        # print("Let's convert it in Fahrenheit degrees: %0.2f" % DallasTemperature.toFahrenheit(temp))
        self.r.set(self.key, temps)
        return temps


if __name__ == '__main__':
    try:
        loop_count = 10
        sensor = TemperatureSensor(2)
        sensor.init_sensor()
        while loop_count > 0:
            tempread = sensor.readAll()
            print('Temps: ', tempread)
            loop_count += 1
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        print('Temp Sensors Closing...')
