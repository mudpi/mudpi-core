""" 
    Nanpy LCD Display Interface
    Connects to a unit running Nanpy to 
    get display messages on an LCD.
"""
import socket
from nanpy.lcd import Lcd
from nanpy.lcd_i2c import Lcd_I2C
from mudpi.extensions import BaseInterface
from nanpy import (ArduinoApi, SerialManager)
from mudpi.logger.Logger import Logger, LOG_LEVEL
from nanpy.serialmanager import SerialManagerError
from mudpi.exceptions import MudPiError, ConfigError
from mudpi.extensions.char_display import CharDisplay
from nanpy.sockconnection import (SocketManager, SocketManagerError)


class Interface(BaseInterface):
    def load(self, config):
        """ Load Nanpy display components from configs """
        display = NanpyCharDisplay(self.mudpi, config)

        if display:
            node = self.extension.nodes[config['node']]
            if node:
                display.node = node
                self.add_component(display)
            else:
                raise MudPiError(f'Nanpy node {config["node"]} not found trying to connect {config["key"]}.')
        return True

    def validate(self, config):
        """ Validate the Nanpy display config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('key'):
                raise ConfigError('Missing `key` in Nanpy sensor config.')

            if not conf.get('node'):
                raise ConfigError(f'Missing `node` in Nanpy sensor {conf["key"]} config. You need to add a node key.')

            if not conf.get('address'):
            # raise ConfigError('Missing `address` in i2c char_lcd config.')
                conf['address'] = 0x27
            else:
                addr = conf['address']

                # Convert hex string/int to actual hex
                if isinstance(addr, str):
                    addr = hex(int(addr, 39))
                elif isinstance(addr, int):
                    addr = hex(addr)

                conf['address'] = addr

            if not conf.get('columns', 16):
                raise ConfigError('Missing `columns` must be an int.')

            if not conf.get('rows', 2):
                raise ConfigError('Missing `rows` must be an int.')

            if conf['type'].lower() not in ('gpio', 'i2c'):
                conf['type'] = 'i2c'

        return config


class NanpyCharDisplay(CharDisplay):
    """ Nanpy Character Display
        Display messages on a LCD connected to i2c
    """

    """ Properties """
    @property
    def address(self):
        """ Unique id or key """
        return self.config.get('address', 0x27)

    @property
    def type(self):
        """ Returns if using i2c or gpio for connection """
        return self.config.get('type', 'i2c').lower()


    """ Methods """
    def init(self):
        """ Connect to the Parent Device """
        self._state = None
        self._lcd = None
        return True

    def check_connection(self):
        """ Check connection to node and lcd """
        if self.node.connected:
            if not self._lcd:
                if self.type == 'i2c':
                    # PCF I2C Backpack
                    # [lcd_Addr, enable, Rw, Rs, d4, d5, d6, d7, backlighPin, pol]
                    pins = [0x27, 2, 1, 0, 4, 5, 6, 7, 3, 0]  
                    # TODO: Add other backback support
                    self._lcd = Lcd_I2C(pins, [self.columns, self.rows], connection=self.node.connection)
                else:
                    # GPIO Connection
                    # [rs, enable, d4, d5, d6, d7]
                    pins = [self.config.get('rs_pin', 7), 
                            self.config.get('enable_pin', 8), 
                            self.config.get('pin_1', 9), 
                            self.config.get('pin_2', 10), 
                            self.config.get('pin_3', 11), 
                            self.config.get('pin_4', 12)]
                    self._lcd = Lcd(pins, [self.columns, self.rows], connection=connection)

    def update(self):
        """ Control LCD display nanpy"""
        if self.node.connected:
            try:
                self.check_connection()
                super().update()
            except (SerialManagerError, SocketManagerError,
                    BrokenPipeError, ConnectionResetError, OSError,
                    socket.timeout) as e:
                if self.node.connected:
                    Logger.log_formatted(LOG_LEVEL["warning"],
                           f'{self.node.key} -> Broken Connection', 'Timeout', 'notice')
                    self.node.reset_connection()
        return None

    """ Actions """
    def clear(self, data=None):
        """ Clear the display screen """
        self._lcd.clear()
        Logger.log(LOG_LEVEL["debug"], 'Cleared the LCD Screen')

    def show(self, data={}):
        """ Show a message on the display """
        if not isinstance(data, dict):
            data = {'message': data}

        self._lcd.setCursor(0, 0)
        self._lcd.printString(data.get('message', ''))

    def turn_on_backlight(self):
        """ Turn the backlight on """
        self._lcd.setBacklight(0)

    def turn_off_backlight(self):
        """ Turn the backlight on """
        self._lcd.setBacklight(1)