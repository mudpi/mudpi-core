import RPi.GPIO as GPIO

from sensors.base_sensor import BaseSensor


# PIN MODE : OUT | IN

class FloatSensor(BaseSensor):

    def __init__(self, pin, name=None, key=None, redis_conn=None):
        super().__init__(pin, name=name, key=key, redis_conn=redis_conn)
        return

    def init_sensor(self):
        """
        Initialize the sensor here (i.e. set pin mode, get addresses, etc)
        this gets called by the worker

        Returns:

        """
        # GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)
        return

    def read(self):
        """
        Read the sensor(s), parse the data and store it in redis
        if redis is configured

        Returns:

        """
        value = GPIO.input(self.pin)
        return value

    def read_raw(self):
        """
        Read the sensor(s) but return the raw data, useful for debugging

        Returns:

        """
        return self.read()
