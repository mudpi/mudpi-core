""" 
    Nanpy Toggle Interface
    Connects to a unit running Nanpy to 
    toggle a GPIO pin on the device.
"""
import socket
from mudpi.extensions import BaseInterface
from mudpi.extensions.toggle import Toggle
from nanpy import (ArduinoApi, SerialManager, DHT)
from mudpi.logger.Logger import Logger, LOG_LEVEL
from nanpy.serialmanager import SerialManagerError
from mudpi.exceptions import MudPiError, ConfigError
from nanpy.sockconnection import (SocketManager, SocketManagerError)

UPDATE_THROTTLE = 2

class Interface(BaseInterface):

    def load(self, config):
        """ Load Nanpy Toggle components from configs """
        toggle = NanpyGPIOToggle(self.mudpi, config)
        if toggle:
            node = self.extension.nodes[config['node']]
            if node:
                toggle.node = node
                self.add_component(toggle)
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

            if not conf.get('pin'):
                raise ConfigError(f'Missing `pin` in Nanpy toggle {conf["key"]} config. You need to add a pin.')

        return config


class NanpyGPIOToggle(Toggle):
    """ Nanpy GPIO Toggle
        Get readings from GPIO (analog or digital)
    """

    """ Properties """
    @property
    def pin(self):
        """ The GPIO pin """
        return self.config.get('pin')


    """ Methods """
    def init(self):
        """ Connect to the Parent Device """
        self._pin_setup = False
        self.active = False
        return True

    def check_connection(self):
        """ Verify node connection and devices setup """
        if self.node.connected:
            if not self._pin_setup:
                self.node.api.pinMode(self.pin, self.node.api.OUTPUT)
                if self.invert_state:
                    self.pin_state_on = self.node.api.LOW
                    self.pin_state_off = self.node.api.HIGH
                else:
                    self.pin_state_on = self.node.api.HIGH
                    self.pin_state_off = self.node.api.LOW
                self.node.api.digitalWrite(self.pin, self.pin_state_off)
                self._pin_setup = True

    def update(self):
        """ Wrap the failsafe detection in connection handler for node """
        if self.node.connected:
            self.check_connection()
            try:
                # Pass to the Base Toggle for failsafe handling
                super().update()
            except (SerialManagerError, SocketManagerError,
                    BrokenPipeError, ConnectionResetError, OSError,
                    socket.timeout) as e:
                if self.node.connected:
                    Logger.log_formatted(LOG_LEVEL["warning"],
                           f'{self.node.key} -> Broken Connection', 'Timeout', 'notice')
                    self.node.reset_connection()
                    self._pin_setup = False
        return None

    def restore_state(self, state={}):
        """ This is called on start to 
            restore previous state """
        if self._pin_setup:
            state = self.pin_state_on if state.get('state', False) else self.pin_state_off
            self.node.api.digitalWrite(self.pin, state)
        return

    
    """ Actions """
    def toggle(self, data={}):
        # Toggle the GPIO state
        if self.mudpi.is_prepared:
            # Do inverted check and change value before setting active 
            # to avoid false state being provided in the event fired.
            if self.node.connected:
                self.check_connection()
                state = self.pin_state_on if not self.active else self.pin_state_off
                self.node.api.digitalWrite(self.pin, state)
                self.active = not self.active
                self.store_state()

    def turn_on(self, data={}):
        # Turn on GPIO if its not on
        if self.mudpi.is_prepared:
            if not self.active:
                if self.node.connected:
                    self.check_connection()
                    self.node.api.digitalWrite(self.pin, self.pin_state_on)
                    self.active = True
                    self.store_state()

    def turn_off(self, data={}):
        # Turn off GPIO if its not off
        if self.mudpi.is_prepared:
            if self.active:
                if self.node.connected:
                    self.check_connection()
                    self.node.api.digitalWrite(self.pin, self.pin_state_off)
                    self.active = False
                    self.store_state()