""" 
    GPIO Control Interface
    Connects to a linux board GPIO to
    take analog or digital readings. 
"""
import re
import board
import digitalio
from adafruit_debouncer import Debouncer
from mudpi.extensions import BaseInterface
from mudpi.extensions.control import Control
from mudpi.exceptions import MudPiError, ConfigError


class Interface(BaseInterface):

    update_interval = 0.01

    def load(self, config):
        """ Load GPIO control component from configs """
        control = GPIOControl(self.mudpi, config)
        if control:
            self.add_component(control)
        return True

    def validate(self, config):
        """ Validate the control config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if conf.get('key') is None:
                raise ConfigError('Missing `key` in example control.')
                
            if conf.get('pin') is None:
                raise ConfigError('Missing `pin` in GPIO config.')
        return config


class GPIOControl(Control):
    """ GPIO Control
        Get GPIO input via button, switch, etc.
    """

    """ Properties """
    @property
    def state(self):
        """ Return the state of the component (from memory, no IO!) """
        return self._state


    """ Methods """
    def init(self):
        """ Connect to the device """
        self.pin_obj = getattr(board, self.pin)
        self.gpio = digitalio
        self.previous_state = 0

        if re.match(r'D\d+$', self.pin):
            self.is_digital = True
        elif re.match(r'A\d+$', self.pin):
            self.is_digital = False
        else:
            self.is_digital = True

        if self.resistor is not None:
            if self.resistor == "up" or self.resistor == digitalio.Pull.UP:
                self._resistor = digitalio.Pull.UP
            elif self.resistor == "down" or self.resistor == digitalio.Pull.DOWN:
                self._resistor = digitalio.Pull.DOWN
            else:
                # Unknown resistor pull, defaulting to None
                self.config['resistor'] = self._resistor = None

        self._control_pin = self.gpio.DigitalInOut(self.pin_obj)
        self._control_pin.switch_to_input(pull=self._resistor)

        # Switches use debounce for better detection
        # TODO: get rid of this to allow long press, release, and press detection
        if self.type == 'switch':
            self.config['edge_detection'] = 'both'

        if self.edge_detection is not None:
            self._control = Debouncer(self._control_pin)
            if self.debounce is not None:
                self._control.interval = self.debounce

        return True

    def update(self):
        """ Get data from GPIO connection"""
        data = None
        if self.edge_detection is not None:
            self._control.update()
            if self.edge_detection == "both":
                if self._control.fell or self._control.rose:
                    # Pressed or Released
                    data = 1
                else:
                    data = 0
            else:    # "fell" or "rose"
                data = 1 if getattr(self._control, self.edge_detection) else 0
        else:
            data = 1 if self._control_pin.value else 0
        self.previous_state = self._state
        self._state = data
        self.handle_state()
        return data

    def handle_state(self):
        """ Control logic depending on type of control """
        if self.type == 'button':
            if self._state:
                if not self.invert_state:
                    self.fire()
            else:
                if self.invert_state:
                    self.fire()
        elif self.type == 'switch':
            # Switches use debounce ensuring we only fire once
            if self._state:
                # State changed since we are using edge detect
                self.fire()

