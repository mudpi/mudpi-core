from nanpy import (SerialManager)

from sensors.arduino.sensor import Sensor

default_connection = SerialManager(device='/dev/ttyUSB0')


class FloatSensor(Sensor):

    def __init__(self, pin, name=None, key=None, connection=default_connection,
                 redis_conn=None):
        super().__init__(pin, name=name, key=key, connection=connection,
                         redis_conn=redis_conn)

    def init_sensor(self):
        # read data using pin specified pin
        self.api.pinMode(self.pin, self.api.INPUT)

    def read(self):
        value = self.api.digitalRead(self.pin)
        self.r.set(self.key, value)
        return value

    def read_raw(self):
        return self.read()
