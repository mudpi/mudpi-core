""" 
    I2C Toggle Interface
    Connects to a linux I2C bus to
    toggle output on and off. Useful for 
    turning things on like lights or pumps. 
"""
import smbus2
import time
from mudpi.extensions import BaseInterface
from mudpi.extensions.toggle import Toggle
from mudpi.exceptions import MudPiError, ConfigError


DEVICE_BUS = 1
DEVICE_ADDR = 0x10


class Interface(BaseInterface):

    def load(self, config):
        """ Load I2C toggle component from configs """
        toggle = I2CToggle(self.mudpi, config)
        if toggle:
            self.add_component(toggle)
        return True

    def validate(self, config):
        """ Validate the I2C config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if conf.get('key') is None:
                raise ConfigError('Missing `key` in i2c toggle config.')

            if not conf.get('address'):
            # raise ConfigError('Missing `address` in i2c toggle config.')
                conf['address'] = DEVICE_ADDR
            else:
                addr = conf['address']

                # Convert hex string/int to actual hex
                if isinstance(addr, str):
                    addr = int(addr, 16)

                conf['address'] = addr

            if not conf.get('register'):
            # raise ConfigError('Missing `address` in i2c toggle config.')
                conf['register'] = 0x01
            else:
                reg = conf['register']

                # Convert hex string/int to actual hex
                if isinstance(reg, str):
                    reg = int(reg, 16)

                conf['register'] = reg

        return config


class I2CToggle(Toggle):
    """ I2C Toggle
        Turns an I2C relay off and on
    """

    @property
    def address(self):
        """ I2C address """
        return self.config.get('address', DEVICE_ADDR)


    @property
    def register(self):
        """ Register to write to """
        return self.config.get('register', 0x01)


    """ Methods """
    def init(self):
        """ Connect to the relay over I2C """
        super().init()

        if self.invert_state:
            self.pin_state_on = 0x00
            self.pin_state_off = 0xFF
        else:
            self.pin_state_on = 0xFF
            self.pin_state_off = 0x00

        # Prepare the relay i2c connection
        self.bus = smbus2.SMBus(DEVICE_BUS)

        self.bus.write_byte_data(self.address, self.register, self.pin_state_off)
        # Active is used to keep track of durations
        self.active = False
        time.sleep(0.1)

        return True


    def restore_state(self, state):
        """ This is called on start to 
            restore previous state """
        self.active = True if state.state else False
        self.reset_duration()
        return


    """ Actions """
    def toggle(self, data={}):
        # Toggle the state
        if self.mudpi.is_prepared:
            self.active = not self.active
            self.bus.write_byte_data(self.address, self.register, self.pin_state_off if self.active else self.pin_state_on)
            self.store_state()

    def turn_on(self, data={}):
        # Turn on if its not on
        if self.mudpi.is_prepared:
            if not self.active:
                self.bus.write_byte_data(self.address, self.register, self.pin_state_on)
                self.active = True
                self.store_state()

    def turn_off(self, data={}):
        # Turn off if its not off
        if self.mudpi.is_prepared:
            if self.active:
                self.bus.write_byte_data(self.address, self.register, self.pin_state_off)
                self.active = False
                self.store_state()