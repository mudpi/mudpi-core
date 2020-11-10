import re

import board
import digitalio

from logger.Logger import Logger, LOG_LEVEL
from sensors.base_sensor import BaseSensor


# PIN MODE : OUT | IN

class Sensor(BaseSensor):

    def __init__(self, pin, name=None, key=None, redis_conn=None):

        super().__init__(
            pin=pin,
            name=name,
            key=key,
            redis_conn=redis_conn
        )
        self.pin_obj = getattr(board, pin)

        if re.match(r'D\d+$', pin):
            self.is_digital = True
        elif re.match(r'A\d+$', pin):
            self.is_digital = False
        else:
            Logger.log(
                LOG_LEVEL["error"],
                "Cannot detect pin type (Digital or analog), "
                "should be Dxx or Axx for digital or analog. "
                "Please refer to "
                "https://github.com/adafruit/Adafruit_Blinka/tree/master/src/adafruit_blinka/board"
            )

        self.gpio = digitalio

    def read_pin(self):
        """Read the pin from the board.

        Pin value must be a blinka Pin.
        D for a digital input and A for an analog input, followed by the
        pin number.

        You check the board-specific pin mapping
        [here](https://github.com/adafruit/Adafruit_Blinka/blob/master/src/adafruit_blinka/board/).

        Examples:
        read_pin(board.D12)
        read_pin(board.A12)
        """
        if self.is_digital:
            data = self.gpio.DigitalInOut(self.pin_obj).value
        else:
            data = self.gpio.AnalogIn(self.pin_obj).value
        return data
