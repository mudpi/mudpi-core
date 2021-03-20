""" 
    GPIO Toggle Interface
    Connects to a linux board GPIO to
    toggle output on and off. Useful for 
    turning things on like lights or pumps. 
"""
import re
import board
import digitalio
from mudpi.extensions import BaseInterface
from mudpi.extensions.toggle import Toggle
from mudpi.exceptions import MudPiError, ConfigError


class Interface(BaseInterface):

    def load(self, config):
        """ Load GPIO toggle component from configs """
        toggle = GPIOToggle(self.mudpi, config)
        if toggle:
            self.add_component(toggle)
        return True

    def validate(self, config):
        """ Validate the dht config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if conf.get('key') is None:
                raise ConfigError('Missing `key` in GPIO toggle config.')

            if conf.get('pin') is None:
                raise ConfigError('Missing `pin` in GPIO toggle config.')

            if not re.match(r'D\d+$', conf['pin']) and not re.match(r'A\d+$', conf['pin']):
                raise ConfigError(
                    "Cannot detect pin type (Digital or analog), "
                    "should be D## or A## for digital or analog. "
                    "Please refer to "
                    "https://github.com/adafruit/Adafruit_Blinka/tree/master/src/adafruit_blinka/board"
                )

        return config


class GPIOToggle(Toggle):
    """ GPIO Toggle
        Turns a GPIO pin on or off
    """

    """ Properties """
    @property
    def state(self):
        """ Return the state of the component (from memory, no IO!) """
        return self.gpio_pin.value

    @property
    def pin(self):
        """ The GPIO pin """
        return self.config.get('pin')


    """ Methods """
    def init(self):
        """ Connect to the device """
        self.pin_obj = getattr(board, self.pin)

        if re.match(r'D\d+$', self.pin):
            self.is_digital = True
        elif re.match(r'A\d+$', self.pin):
            self.is_digital = False

        if self.invert_state:
            self.pin_state_on = False
            self.pin_state_off = True
        else:
            self.pin_state_on = True
            self.pin_state_off = False

        self.gpio = digitalio
        self.gpio_pin = digitalio.DigitalInOut(self.pin_obj)
        self.gpio_pin.switch_to_output()
        
        self.gpio_pin.value = self.pin_state_off
        # Active is used to keep track of durations
        self.active = False
        time.sleep(0.1)

        return True

    def restore_state(self, state={}):
        """ This is called on start to 
            restore previous state """
        self.gpio_pin.value = self.pin_state_on if state.get('state', False) else self.pin_state_off
        return


    """ Actions """
    def toggle(self, data={}):
        # Toggle the GPIO state
        if self.mudpi.is_prepared:
            # Do inverted check and change value before setting active 
            # to avoid false state being provided in the event fired.
            self.gpio_pin.value = self.pin_state_on if not self.active else self.pin_state_off
            self.active = not self.active
            self.store_state()

    def turn_on(self, data={}):
        # Turn on GPIO if its not on
        if self.mudpi.is_prepared:
            if not self.active:
                self.gpio_pin.value = self.pin_state_on
                self.active = True
                self.store_state()

    def turn_off(self, data={}):
        # Turn off GPIO if its not off
        if self.mudpi.is_prepared:
            if self.active:
                self.gpio_pin.value = self.pin_state_off
                self.active = False
                self.store_state()