import time
import json
import redis
from nanpy import (ArduinoApi, SerialManager)
from sensors.base_sensor import BaseSensor

default_connection = SerialManager()


class Sensor(BaseSensor):
    """
    Base sensor class to extend all other arduino sensors from.
    """

    def __init__(self, pin, name=None, connection=default_connection,
                 analog_pin_mode=False, key=None, api=None, redis_conn=None):
        """

        Args:
            pin:
            name:
            connection:
            analog_pin_mode:
            key:
            api:
            redis_conn:
        """

        super().__init__(
            pin=pin,
            name=name,
            key=key,
            redis_conn=redis_conn
        )

        self.analog_pin_mode = analog_pin_mode
        self.connection = connection
        self.api = api if api is not None else ArduinoApi(connection)

    def read_pin(self):
        """
        Read the pin from the ardiuno. Can be analog or digital based on
        "analog_pin_mode"

        Returns:

        """

        if self.analog_pin_mode:
            data = self.api.analogRead(self.pin)

        else:
            data = self.api.digitalRead(self.pin)

        return data
