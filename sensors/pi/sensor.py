import RPi.GPIO as GPIO

from sensors.base_sensor import BaseSensor


# PIN MODE : OUT | IN

class Sensor(BaseSensor):
    """

    """

    def __init__(self, pin, name=None, key=None, redis_conn=None):
        """

        Args:
            pin:
            name:
            key:
            redis_conn:
        """
        super().__init__(
            pin=pin,
            name=name,
            key=key,
            redis_conn=redis_conn
        )
        self.gpio = GPIO

    def read_pin(self):
        """
        Read the pin from the SBC which can only be digital.

        Returns:

        """
        data = self.gpio.input(self.pin)
        return data
