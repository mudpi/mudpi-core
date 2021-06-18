""" 
    GPIO Control Interface
    Connects to a linux board GPIO to
    take analog or digital readings. 
"""
import re
import time
import board
import digitalio
from adafruit_debouncer import Debouncer
from mudpi.extensions import BaseInterface
from mudpi.extensions.control import Control
from mudpi.exceptions import MudPiError, ConfigError


UPDATE_THROTTLE = 2

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

            if conf.get('debounce') is not None and conf.get('edge_detection') is None:
                if conf.get('type','button') == 'switch':
                    conf['edge_detection'] = 'both'
                else:
                    raise ConfigError('`debounce` detected without required `edge_detection` in GPIO config.')
        return config


class GPIOControl(Control):
    """ GPIO Control
        Get GPIO input via button, switch, etc.
    """

    """ Properties """
    @property
    def state(self):
        """ Return the state of the component (from memory, no IO!) """
        return self._state if not self.invert_state else not self._state

    @property
    def state_changed(self):
        """ Return if the state changed from previous state"""
        return self.previous_state != self._state

    @property
    def elapsed_time(self):
        self.time_elapsed = time.perf_counter() - self.time_start
        return self.time_elapsed


    """ Methods """
    def init(self):
        """ Connect to the device """
        self.pin_obj = getattr(board, self.pin)
        self.gpio = digitalio
        self._state = 0
        # Used to track changes
        self.previous_state = self._state

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

        self.reset_elapsed_time()

        return True

    def update(self):
        """ Get data from GPIO connection"""
        data = None
        self.previous_state = self.state
        if self.edge_detection is not None:
            self._control.update()
            if self.edge_detection == "both":
                if self._control.fell or self._control.rose:
                    # Pressed or Released
                    self._state = 1 if self._control_pin.value else 0
                    _event = "ControlUpdated" 
                    if self._control.rose:
                        if self.invert_state:
                            _event = "ControlReleased"
                        else:
                            _event = "ControlPressed" 
                    elif self._control.fell:
                        if self.invert_state:
                            _event = "ControlPressed"
                        else:
                            _event = "ControlReleased"
                    self.fire({"event": _event})
            else:    # "fell" or "rose"
                if getattr(self._control, self.edge_detection):
                    _event = "ControlUpdated" 
                    if self.edge_detection == "rose":
                        if self.invert_state:
                            _event = "ControlReleased"
                        else:
                            _event = "ControlPressed" 
                    elif self.edge_detection == "fell":
                        if self.invert_state:
                            _event = "ControlPressed"
                        else:
                            _event = "ControlReleased"
                    self.fire({"event": _event})

                self._state = 1 if self._control_pin.value else 0
        else:
            # No edge detection
            self._state = 1 if self._control_pin.value else 0

        if self.type == 'switch':
            if self.state_changed:
                self.fire()
        elif self.type == 'button':
            if self.state:
                if self.elapsed_time > UPDATE_THROTTLE:
                    self.fire()
                    self.reset_elapsed_time()
            else:
                if self.state_changed:
                    self.fire()

        return data

    def reset_elapsed_time(self):
        """ Reset duration tracker """
        self.time_start = time.perf_counter()