"""
    T9602 Sensor Interface
    Connects to a T9602 device to get
    environment and climate readings.
"""
import smbus
from mudpi.extensions import BaseInterface
from mudpi.extensions.sensor import Sensor
from mudpi.exceptions import MudPiError, ConfigError


class Interface(BaseInterface):

    def load(self, config):
        """ Load T9602 sensor component from configs """
        sensor = T9602Sensor(self.mudpi, config)
        if sensor.connect():
            self.add_component(sensor)
        return True

    def validate(self, config):
        """ Validate the T9602 config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('address'):
                # raise ConfigError('Missing `address` in T9602 config.')
                conf['address'] = 0x28
            else:
                addr = conf['address']

                if isinstance(addr, str):
                    addr = int(addr, 16)

                conf['address'] = addr

        return config



class T9602Sensor(Sensor):
    """ T9602 Sensor
        Get readings for humidity and temperature.
    """

    """ Properties """
    @property
    def id(self):
        """ Return a unique id for the component """
        return self.config['key']

    @property
    def name(self):
        """ Return the display name of the component """
        return self.config.get('name') or f"{self.id.replace('_', ' ').title()}"

    @property
    def state(self):
        """ Return the state of the component (from memory, no IO!) """
        return self._state

    @property
    def classifier(self):
        """ Classification further describing it, effects the data formatting """
        return 'climate'


    """ Methods """
    def connect(self):
        """ Connect to the Device
        This is the bus number : the 1 in "/dev/i2c-1"
        I enforced it to 1 because there is only one on Raspberry Pi.
        We might want to add this parameter in i2c sensor config in the future.
        We might encounter boards with several buses."""
        self.bus = smbus.SMBus(1)

        return True

    def update(self):
        """ Get data from T9602 device"""
        data = self.bus.read_i2c_block_data(self.config['address'], 0, 4)

        humidity = (((data[0] & 0x3F) << 8) + data[1]) / 16384.0 * 100.0
        temperature_c = ((data[2] * 64) + (data[3] >> 2)) / 16384.0 * 165.0 - 40.0

        humidity = round(humidity, 2)
        temperature_c = round(temperature_c, 2)

        if humidity is not None and temperature_c is not None:
            readings = {
                'temperature': temperature_c,
                'humidity': humidity
            }
            self._state = readings
            return readings
        else:
            Logger.log(
                LOG_LEVEL["error"],
                'Failed to get reading [t9602]. Try again!'
            )
        return None
