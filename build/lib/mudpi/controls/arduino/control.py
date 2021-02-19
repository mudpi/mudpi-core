import time
import json
import redis
from nanpy import (ArduinoApi, SerialManager)
import sys


default_connection = SerialManager()

# Base sensor class to extend all other arduino sensors from.
class Control():

    def __init__(self, pin, name=None, connection=default_connection, analog_pin_mode=False, key=None, redis_conn=None):
        self.pin = pin

        if key is None:
            raise Exception('No "key" Found in Control Config')
        else:
            self.key = key.replace(" ", "_").lower()

        if name is None:
            self.name = self.key.replace("_", " ").title()
        else:
            self.name = name
            
        self.analog_pin_mode = analog_pin_mode
        self.connection = connection
        self.api = ArduinoApi(connection)
        try:
            self.r = redis_conn if redis_conn is not None else redis.Redis(host='127.0.0.1', port=6379)
        except KeyError:
            self.r = redis.Redis(host='127.0.0.1', port=6379)
        return

    def init_control(self):
        #Initialize the control here (i.e. set pin mode, get addresses, etc)
        self.api.pinMode(self.pin, self.api.INPUT)
        pass

    def read(self):
        #Read the sensor(s), parse the data and store it in redis if redis is configured
        return self.read_pin()

    def read_raw(self):
        #Read the sensor(s) but return the raw data, useful for debugging
        pass

    def read_pin(self):
        #Read the pin from the ardiuno. Can be analog or digital based on "analog_pin_mode"
        data = self.api.analogRead(self.pin) if self.analog_pin_mode else self.api.digitalRead(self.pin)
        return data

    def emitEvent(self, data): 
        message = {
            'event':'ControlUpdate',
            'data': {
                self.key:data
            }
        }
        print(message["data"])
        self.r.publish('controls', json.dumps(message))