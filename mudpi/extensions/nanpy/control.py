""" 
    Nanpy Control Interface
    Connects to a unit running Nanpy to 
    read a switch, button or potentiometer.
"""
import time
import socket
from mudpi.extensions import BaseInterface
from mudpi.extensions.control import Control
from nanpy import (ArduinoApi, SerialManager, DHT)
from mudpi.logger.Logger import Logger, LOG_LEVEL
from nanpy.serialmanager import SerialManagerError
from mudpi.exceptions import MudPiError, ConfigError
from nanpy.sockconnection import (SocketManager, SocketManagerError)

UPDATE_THROTTLE = 2
DEBOUNCE = 0.05

class Interface(BaseInterface):

    def load(self, config):
        """ Load Nanpy control components from configs """
        control = NanpyGPIOControl(self.mudpi, config)
        if control:
            node = self.extension.nodes[config['node']]
            if node:
                control.node = node
                self.add_component(control)
            else:
                raise MudPiError(f'Nanpy node {config["node"]} not found trying to connect {config["key"]}.')
        return True

    def validate(self, config):
        """ Validate the Nanpy control config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('key'):
                raise ConfigError('Missing `key` in Nanpy sensor config.')

            if not conf.get('node'):
                raise ConfigError(f'Missing `node` in Nanpy sensor {conf["key"]} config. You need to add a node key.')

            if conf.get('pin') is None:
                raise ConfigError(f'Missing `pin` in Nanpy control {conf["key"]} config. You need to add a pin.')
            else:
                conf['pin'] = int(conf['pin'])
                
            if not conf.get('type'):
                # Default to the button type
                conf['type'] = 'button'
            elif conf.get('type').lower() not in ['button', 'switch', 'potentiometer']:
                # Unsupported type
                conf['type'] = 'button'

        return config


class NanpyGPIOControl(Control):
    """ Nanpy GPIO Control
        Get readings from GPIO (analog or digital)
    """

    """ Properties """
    @property
    def state(self):
        """ Return the state of the component (from memory, no IO!) """
        return self._state

    @property
    def analog(self):
        """ Return if gpio is digital or analog """
        return self.type == 'potentiometer'

    @property
    def buffer(self):
        """ Reading buffer to smooth out jumpy values """
        return self.config.get('buffer', 0)

    @property
    def elapsed_time(self):
        self.time_elapsed = time.perf_counter() - self.time_start
        return self.time_elapsed

    @property
    def state_changed(self):
        """ Return if the state changed from previous state"""
        return self.previous_state != self._state


    """ Methods """
    def init(self):
        """ Connect to the Parent Device """
        self._state = 0
        self.reset_elapsed_time()
        self._fired = False
        self._pin_setup = False
        self.previous_state = 0
        return True

    def check_connection(self):
        """ Verify node connection and devices setup """
        if self.node.connected:
            if not self._pin_setup:
                self.node.api.pinMode(self.pin, self.node.api.INPUT)
                self._pin_setup = True

    def update(self):
        """ Get data from GPIO through nanpy"""
        if self.node.connected:
            self.check_connection()
            try:
                data = self.node.api.analogRead(self.pin) if self.analog else self.node.api.digitalRead(self.pin)
                if self.type != 'potentiometer':
                    self.previous_state = self._state
                    self._state = data
                else:
                    if (data < self.previous_state - self.buffer) or (data > self.previous_state + self.buffer):
                        self.previous_state = self._state
                        self._state = data
                self.handle_state()
            except (SerialManagerError, SocketManagerError,
                    BrokenPipeError, ConnectionResetError, OSError,
                    socket.timeout) as e:
                if self.node.connected:
                    Logger.log_formatted(LOG_LEVEL["warning"],
                           f'{self.node.key} -> Broken Connection', 'Timeout', 'notice')
                    self.node.reset_connection()
                    self._pin_setup = False
        return None

    def handle_state(self):
        """ Control logic depending on type of control """
        if self.type == 'button':
            if self._state:
                if not self.invert_state:
                    if self.elapsed_time > UPDATE_THROTTLE:
                        self.fire()
                        self.reset_elapsed_time()
            else:
                if self.invert_state:
                    if self.elapsed_time > UPDATE_THROTTLE:
                        self.fire()
                        self.reset_elapsed_time()
                else:
                    if self.state_changed:
                        self.fire()
        elif self.type == 'switch':
            if not self.state_changed:
                if self.elapsed_time > DEBOUNCE and not self._fired:
                    self.fire()
                    self._fired = True
                    self.reset_elapsed_time()
            else:
                self._fired = False
        elif self.type == 'potentiometer':
            if self.state_changed:
                self.fire()
            
    def reset_elapsed_time(self):
        self.time_start = time.perf_counter()