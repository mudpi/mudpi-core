import time
import json
import redis
import RPi.GPIO as GPIO
import sys
sys.path.append('..')

# Base sensor class to extend all other arduino sensors from.
class Control():

    def __init__(self, pin, name=None, key=None, resistor=None, edge_detection=None, debounce=None, redis_conn=None):
        self.pin = pin

        if key is None:
            raise Exception('No "key" Found in Control Config')
        else:
            self.key = key.replace(" ", "_").lower()

        if name is None:
            self.name = self.key.replace("_", " ").title()
        else:
            self.name = name

        self.gpio = GPIO
        self.debounce = debounce if debounce is not None else None
        try:
            self.r = redis_conn if redis_conn is not None else redis.Redis(host='127.0.0.1', port=6379)
        except KeyError:
            self.r = redis.Redis(host='127.0.0.1', port=6379)

        if resistor is not None:
            if resistor == "up" or resistor == GPIO.PUD_UP:
                self.resistor = GPIO.PUD_UP
            elif resistor == "down" or resistor == GPIO.PUD_DOWN:
                self.resistor = GPIO.PUD_DOWN
        else:
            self.resistor = resistor

        if edge_detection is not None:
            if edge_detection == "falling" or edge_detection == GPIO.FALLING:
                self.edge_detection = GPIO.FALLING
            elif edge_detection == "rising" or edge_detection == GPIO.RISING:
                self.edge_detection = GPIO.RISING
            elif edge_detection == "both" or edge_detection == GPIO.BOTH:
                self.edge_detection = GPIO.BOTH
        else:
            self.edge_detection = None

        return

    def init_control(self):
        #Initialize the control here (i.e. set pin mode, get addresses, etc)
        #Set the Pin for the button with the internal pull up resistor
        self.gpio.setup(self.pin, GPIO.IN, pull_up_down=self.resistor)
        # If edge detection has been configured lets take advantage of that
        if self.edge_detection is not None:
            GPIO.add_event_detect(self.pin, self.edge_detection, bouncetime=self.debounce)
        pass

    def read(self):
        #Read the sensor(s), parse the data and store it in redis if redis is configured
        #If edge detection is being used return the detection event instead
        return self.read_pin() if self.edge_detection is None else GPIO.event_detected(self.pin)

    def read_raw(self):
        #Read the sensor(s) but return the raw data, useful for debugging
        pass

    def read_pin(self):
        #Read the pin from the pi digital reads only
        data = self.gpio.input(self.pin)
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