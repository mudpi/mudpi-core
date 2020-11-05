import time
import json
import redis
import digitalio
import board
import re
from logger.Logger import Logger, LOG_LEVEL


# PIN MODE : OUT | IN

class Sensor():

    def __init__(self, pin, name=None, key=None, redis_conn=None):
        self.pin_obj = getattr(board, pin)

        if re.match(r'D\d+$', pin):
            self.is_digital = True
        elif re.match(r'A\d+$', pin):
            self.is_digital = False
        else:
            Logger.log(LOG_LEVEL["error"], "Cannot detect pin type (Digital or analog), should be Dxx or Axx for digital or analog. Please refer to https://github.com/adafruit/Adafruit_Blinka/tree/master/src/adafruit_blinka/board")

        if key is None:
            raise Exception('No "key" Found in Sensor Config')
        else:
            self.key = key.replace(" ", "_").lower()

        if name is None:
            self.name = self.key.replace("_", " ").title()
        else:
            self.name = name

        self.gpio = digitalio
        try:
            self.r = redis_conn if redis_conn is not None else redis.Redis(host='127.0.0.1', port=6379)
        except KeyError:
            self.r = redis.Redis(host='127.0.0.1', port=6379)
        return

    def init_sensor(self):
        """Initialize the sensor here (i.e. set pin mode, get addresses, etc)"""
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setup(pin, GPIO.IN)
        pass

    def read(self):
        """Read the sensor(s), parse the data and store it in redis if redis is configured"""
        # GPIO.input(pin)
        pass

    def readRaw(self):
        # Read the sensor(s) but return the raw data, useful for debugging
        pass

    def readPin(self):
        """Read the pin from the board.

        pin value must be a blinka Pin. D for a digital input and A for an analog input, followed by the pin number.
        You check the board-specific pin mapping [here](https://github.com/adafruit/Adafruit_Blinka/blob/master/src/adafruit_blinka/board/).

        Examples:
        readPin(board.D12)
        readPin(board.A12)
        """
        if self.is_digital:
            data = self.gpio.DigitalInOut(self.pin_obj).value
        else:
            data = self.gpio.AnalogIn(self.pin_obj).value
        return data
