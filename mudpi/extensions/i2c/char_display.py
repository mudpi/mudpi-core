""" 
    Character Display Interface
    Connects to a LCD character 
    display through a linux I2C.
"""
import time
import json
import redis
import board
import busio
import datetime
from mudpi.extensions import BaseInterface
from mudpi.logger.Logger import Logger, LOG_LEVEL
from mudpi.extensions.char_display import CharDisplay
import adafruit_character_lcd.character_lcd_rgb_i2c as character_rgb_lcd
import adafruit_character_lcd.character_lcd_i2c as character_lcd


class Interface(BaseInterface):

    def load(self, config):
        """ Load display component from configs """
        display = I2CCharDisplay(self.mudpi, config)
        if display:
            self.add_component(display)
        return True

    
    def validate(self, config):
        """ Validate the display configs """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('key'):
                raise ConfigError('Missing `key` in i2c display config.')

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

        return config


class I2CCharDisplay(CharDisplay):
    """ I2C Character Display
        Displays messages through i2c lcd.
    """

    @property
    def address(self):
        """ Unique id or key """
        return self.config.get('address', 0x27)

    @property
    def model(self):
        """ Return the model (rgb, i2c, pcf) """
        if self.config.get('model', 'i2c') not in ('rgb', 'i2c', 'pcf'):
            self.config['model'] = 'i2c'
        return self.config.get('model', 'i2c').lower()


    """ Actions """
    def clear(self, data=None):
        """ Clear the display screen """
        self.lcd.clear()
        Logger.log(LOG_LEVEL["debug"], 'Cleared the LCD Screen')

    def show(self, data={}):
        """ Show a message on the display """
        if not isinstance(data, dict):
            data = {'message': data}

        self.lcd.message = data.get('message', '')

    def turn_on_backlight(self):
        """ Turn the backlight on """
        self.lcd.backlight = True

    def turn_off_backlight(self):
        """ Turn the backlight on """
        self.lcd.backlight = False


    """ Methods """
    def init(self):
        """ Connect to the display over I2C """
        super().init()

        # Prepare the display i2c connection
        self.i2c = busio.I2C(board.SCL, board.SDA)

        if (self.model == 'rgb'):
            self.lcd = character_lcd.Character_LCD_RGB_I2C(
                self.i2c,
                self.columns,
                self.rows,
                self.address
            )

        elif (self.model == 'pcf'):
            self.lcd = character_lcd.Character_LCD_I2C(
                self.i2c,
                self.columns,
                self.rows,
                address=self.address,
                usingPCF=True
            )
        else:
            self.lcd = character_lcd.Character_LCD_I2C(
                self.i2c,
                self.columns,
                self.rows,
                self.address
            )

        self.turn_on_backlight()
        self.clear()
            