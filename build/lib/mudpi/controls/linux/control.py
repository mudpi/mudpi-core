import time
import json
import redis
import sys

try:
    import board
    import digitalio
    from adafruit_debouncer import Debouncer
    SUPPORTED_DEVICE = True
except:
    SUPPORTED_DEVICE = False




# Base sensor class to extend all other arduino sensors from.
class Control():

    def __init__(self, pin, name=None, key=None, resistor=None, edge_detection=None, debounce=None, redis_conn=None):
        if key is None:
            raise Exception('No "key" Found in Control Config')
        else:
            self.key = key.replace(" ", "_").lower()

        if name is None:
            self.name = self.key.replace("_", " ").title()
        else:
            self.name = name

        if SUPPORTED_DEVICE:
            self.pin_obj = getattr(board, pin)
            self.gpio = digitalio
            self.debounce = debounce if debounce is not None else None

            if resistor is not None:
                if resistor == "up" or resistor == digitalio.Pull.UP:
                    self.resistor = digitalio.Pull.UP
                elif resistor == "down" or resistor == digitalio.Pull.DOWN:
                    self.resistor = digitalio.Pull.DOWN
            else:
                self.resistor = resistor

        try:
            self.r = redis_conn if redis_conn is not None else redis.Redis(host='127.0.0.1', port=6379)
        except KeyError:
            self.r = redis.Redis(host='127.0.0.1', port=6379)

        if edge_detection is not None:
            if edge_detection == "falling" or edge_detection == "fell":
                self.edge_detection = "fell"
            elif edge_detection == "rising" or edge_detection == "rose":
                self.edge_detection = "rose"
            elif edge_detection == "both":
                self.edge_detection = "both"
        else:
            self.edge_detection = None

        return

    def init_control(self):
        """Initialize the control here (i.e. set pin mode, get addresses, etc)
        Set the Pin for the button with the internal pull up resistor"""
        if SUPPORTED_DEVICE:
            self.control_pin = self.gpio.DigitalInOut(self.pin_obj)
            self.control_pin.switch_to_input(pull=self.resistor)
            # If edge detection has been configured lets take advantage of that
            if self.edge_detection is not None:
                self.button = Debouncer(self.control_pin)
                if self.debounce is not None:
                    self.button.interval = self.debounce

    def read(self):
        """Read the sensor(s), parse the data and store it in redis if redis is configured
        If edge detection is being used return the detection event instead"""
        if SUPPORTED_DEVICE:
            if self.edge_detection is not None:
                self.button.update()
                if self.edge_detection == "both":
                    if self.button.fell or self.button.rose:
                        return True
                    else:
                        return False
                else:    # "fell" or "rose"
                    return getattr(self.button, self.edge_detection)
        return None

    def read_raw(self):
        """Read the sensor(s) but return the raw data, useful for debugging"""
        pass

    def read_pin(self):
        """Read the pin from the board digital reads only"""
        if SUPPORTED_DEVICE:
            data = self.gpio.DigitalInOut(self.pin_obj).value
            return data
        return {}

    def emitEvent(self, data):
        message = {
            'event': 'ControlUpdate',
            'data': {
                self.key: data
            }
        }
        print(message["data"])
        self.r.publish('controls', json.dumps(message))
